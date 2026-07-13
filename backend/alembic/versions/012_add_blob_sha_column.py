"""Add blob_sha column to documents for incremental GitHub sync.

GitHub's Trees API returns, for every path, the **git blob SHA** -
``sha1("blob {len}\\0" + bytes)``. To diff a Trees response against what we already
hold, without downloading anything, each document must carry that same value.

``documents.file_hash`` cannot be reused: it is a sha256 of the bytes, a different
algorithm over a different preimage. And the blob SHA is not recomputed from the
stored ``content`` column, because that column holds already-decoded text -
reconstructing the original bytes would mean re-encoding and restoring any stripped
BOM, a round-trip whose failure mode is a silent, undetectable mismatch.

NULL means "unknown" - every row written before this migration. No data migration is
needed here because ``sync_engine`` self-heals them: its ``needs_blob_sha_backfill``
clause makes a NULL row ineligible for the byte-unchanged skip, so the next sync
rewrites it once and it settles.

That clause is load-bearing, not an optimisation. Without it a byte-unchanged file is
skipped before its attributes are ever rebuilt, the NULL survives every future sync,
and the project can never leave the "unknown" state - so incremental sync would never
engage for any pre-existing install (see RFC-01KXARHK, D1/D3).

Revision ID: 012
Revises: 011
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("blob_sha", sa.String(40), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "blob_sha")
