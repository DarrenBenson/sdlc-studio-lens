"""Content hashes used by the sync engine.

Two different hashes, for two different jobs. Keeping them straight matters:

- ``compute_hash`` - **our** sha256 of the raw bytes. Used to skip a byte-unchanged
  file once its content is already in hand.
- ``compute_blob_sha`` - **git's** blob SHA-1 of the raw bytes. This is the value
  GitHub's Trees API reports for every path, so it is what an incremental sync diffs
  against to decide which blobs are even worth fetching (RFC-01KXARHK, D1).

They are not interchangeable. Comparing a sha256 against a Trees blob SHA never
matches, which would make every file look changed on every sync.
"""

import hashlib


def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hex digest of content bytes."""
    return hashlib.sha256(content).hexdigest()


def compute_blob_sha(content: bytes) -> str:
    """Compute the git blob SHA-1 of content bytes.

    Git does not hash the content alone: it hashes ``blob {byte_length}\\0`` followed
    by the content. Hashing the bare bytes yields a different digest that will never
    match anything GitHub reports.

    Returns a 40-character hex digest, identical to ``git hash-object``.
    """
    header = b"blob %d\0" % len(content)
    return hashlib.sha1(header + content).hexdigest()  # noqa: S324 - git's format, not a security hash
