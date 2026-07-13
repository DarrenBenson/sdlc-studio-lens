"""Add poll state to projects: auto_sync and last_synced_commit_sha (CR-01KXCAZJ).

``auto_sync`` is per-project opt-in and defaults to FALSE: an existing project must keep
behaving exactly as it does today until the operator asks for something different.

``last_synced_commit_sha`` records the branch head as at the last SUCCESSFUL sync. The
poller compares the current head against it and syncs only when they differ.

That word "successful" is load-bearing. If this column advanced on a FAILED sync, the
repo would look unchanged for ever afterwards - so the failure would never be retried and
the project would stay silently stale while reporting nothing wrong. NULL means "never
successfully synced from a known commit", which correctly reads as "assume it moved".

Revision ID: 014
Revises: 013
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("auto_sync", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "projects",
        sa.Column("last_synced_commit_sha", sa.String(40), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "last_synced_commit_sha")
    op.drop_column("projects", "auto_sync")
