"""Tests for the git blob SHA helper (US-01KXCC76, RFC-01KXARHK D1).

The value must be the *git* blob SHA - sha1("blob {len}\\0" + bytes) - because that is
what GitHub's Trees API reports per path, and an incremental sync diffs against it. A
bare sha1 of the content, or our own sha256 (``compute_hash``), would silently never
match and every file would look changed on every sync.

So these tests assert against **real git**, via ``git hash-object``. An implementation
that merely agrees with its own arithmetic proves nothing.
"""

import shutil
import subprocess

import pytest

from sdlc_lens.utils.hashing import compute_blob_sha, compute_hash

CASES = [
    pytest.param(b"", id="empty-file"),
    pytest.param(b"hello", id="no-trailing-newline"),
    pytest.param(b"# Story\n\n> **Status:** Done\n", id="typical-markdown"),
    pytest.param(b"\xef\xbb\xbf# BOM leads\n", id="utf8-bom"),
    pytest.param("# Café — naïve\n".encode(), id="non-ascii"),
    pytest.param(b"a\r\nb\r\n", id="crlf-line-endings"),
    pytest.param(b"\x00\x01\x02binary\xff", id="binary-ish"),
    pytest.param(b"x" * 100_000, id="large"),
]


def _git_hash_object(data: bytes) -> str:
    """Ask real git for the blob SHA of these exact bytes."""
    return (
        subprocess.run(
            ["git", "hash-object", "--stdin"],
            input=data,
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .strip()
    )


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
@pytest.mark.parametrize("data", CASES)
def test_blob_sha_matches_git(data: bytes) -> None:
    """Our blob SHA is byte-for-byte what `git hash-object` produces."""
    assert compute_blob_sha(data) == _git_hash_object(data)


def test_blob_sha_is_not_a_bare_sha1_of_content() -> None:
    """Guard the classic mistake: git prefixes a header before hashing."""
    import hashlib

    data = b"hello"
    assert compute_blob_sha(data) != hashlib.sha1(data).hexdigest()  # noqa: S324


def test_blob_sha_is_distinct_from_file_hash() -> None:
    """blob_sha (sha1, 40 chars) and file_hash (sha256, 64 chars) are different things.

    Conflating them is the bug that would make every file look changed forever.
    """
    data = b"# Story\n"
    blob = compute_blob_sha(data)
    assert blob != compute_hash(data)
    assert len(blob) == 40
    assert len(compute_hash(data)) == 64


def test_blob_sha_is_stable() -> None:
    """Same bytes, same SHA - the whole change-detection scheme rests on this."""
    data = b"# Story\n\n> **Status:** Done\n"
    assert compute_blob_sha(data) == compute_blob_sha(data)


def test_blob_sha_differs_on_a_one_byte_change() -> None:
    assert compute_blob_sha(b"# Story\n") != compute_blob_sha(b"# StorY\n")


class TestMigration012:
    def test_upgrade_head_adds_blob_sha_column(self, tmp_path) -> None:
        """Migration 012 adds documents.blob_sha, nullable, and downgrade removes it.

        Nullable matters: existing rows must be left NULL ("unknown"), which is the
        signal that sends a project down the tarball path once to backfill.
        """
        import sqlite3
        from pathlib import Path

        from alembic import command
        from alembic.config import Config

        backend_root = Path(__file__).resolve().parents[1]
        db_file = tmp_path / "migrate012.db"

        # Build the config in memory rather than from alembic.ini: loading the ini
        # would run fileConfig(), which disables every existing logger.
        cfg = Config()
        cfg.set_main_option("script_location", str(backend_root / "alembic"))
        cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_file}")
        command.upgrade(cfg, "head")

        conn = sqlite3.connect(db_file)
        try:
            cols = {r[1]: r for r in conn.execute("PRAGMA table_info(documents)")}
        finally:
            conn.close()

        assert "blob_sha" in cols, "migration 012 did not add documents.blob_sha"
        # PRAGMA table_info columns: (cid, name, type, notnull, dflt_value, pk)
        assert cols["blob_sha"][3] == 0, "blob_sha must be nullable (NULL = unknown)"

        command.downgrade(cfg, "011")
        conn = sqlite3.connect(db_file)
        try:
            cols_after = {r[1] for r in conn.execute("PRAGMA table_info(documents)")}
        finally:
            conn.close()
        assert "blob_sha" not in cols_after, "downgrade did not drop blob_sha"
