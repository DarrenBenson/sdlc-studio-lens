"""Add projects.config_blob_shas for incremental sync's config-change detection.

A GitHub sync also reads ``.config.yaml`` / ``.version`` from the repo_path root, which
set the project's schema_version, profile and status_vocab. Under the tarball path those
came free - the bytes were already in the archive.

An incremental sync must not fetch them blindly: "nothing changed" has to cost ONE Trees
call and ZERO blob requests, and unconditionally pulling two config blobs every sync
would break that. But it also must not ignore them, or a config edit that changes status
canonicalisation would never be applied until some unrelated document happened to change.

The Trees response already reports each config file's blob SHA for free. Storing the SHAs
we last read lets us diff them at zero API cost and fetch a config blob only when it has
actually moved.

JSON object: {".config.yaml": "<sha>", ".version": "<sha>"} - absent keys mean the file
is not present in the repo. NULL means "unknown" (a project synced before this column
existed), which forces a config re-read on the next sync.

Revision ID: 013
Revises: 012
Create Date: 2026-07-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("config_blob_shas", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("projects", "config_blob_shas")
