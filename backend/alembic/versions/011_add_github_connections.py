"""Create github_connections and add projects.connection_id (CR-01KXAZX9).

A GitHub PAT was previously stored only in ``projects.access_token``, so the same
secret was duplicated across every project pointing at the same account and had
to be re-pasted for each new repo. ``github_connections`` makes the credential a
first-class, reusable entity (label + resolved login + encrypted token), and
``projects.connection_id`` points a project at one.

The column is nullable and no stored token is migrated: a project that carries
its own ``access_token`` keeps working exactly as before (see the sync token
precedence in ``services/sync_engine``).

Revision ID: 011
Revises: 010
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "github_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("login", sa.String(length=255), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_validated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("label"),
    )
    op.create_index("ix_github_connections_label", "github_connections", ["label"], unique=True)

    # SQLite cannot ALTER-add a foreign-key constraint, so the column is added
    # plain here; the ORM declares the FK (see db/models/project.py) and the
    # in-use guard in services/github_connection refuses to delete a connection
    # a project still references.
    op.add_column("projects", sa.Column("connection_id", sa.Integer(), nullable=True))
    op.create_index("ix_projects_connection_id", "projects", ["connection_id"])


def downgrade() -> None:
    op.drop_index("ix_projects_connection_id", table_name="projects")
    op.drop_column("projects", "connection_id")
    op.drop_index("ix_github_connections_label", table_name="github_connections")
    op.drop_table("github_connections")
