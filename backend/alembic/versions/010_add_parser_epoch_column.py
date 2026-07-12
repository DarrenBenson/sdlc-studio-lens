"""Add parser_epoch column to documents for parser-epoch self-healing.

Document-derived fields (doc_type, canonical status, epic/story, ref_id,
depends_on, aliases) are computed at parse time and stored. A sync hash-skips a
byte-unchanged file, so after an app upgrade that changes the parsing logic those
rows keep their old-computed values forever. ``parser_epoch`` records the epoch
that produced a row's derived fields; ``sync_engine`` reparses any row below the
current ``PARSER_EPOCH`` even on a matching hash (see BG-01KXARHJ).

This migration only adds the column. Existing rows default to 0 (pre-epoch) and
re-parse on the next sync of each file to reach the current epoch, so no backfill
is needed here.

Revision ID: 010
Revises: 009
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("parser_epoch", sa.Integer(), nullable=True, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("documents", "parser_epoch")
