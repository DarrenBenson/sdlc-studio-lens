"""Add schema_version, profile, status_vocab columns to projects.

Revision ID: 008
Revises: 007
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("schema_version", sa.String(20), nullable=True))
    op.add_column("projects", sa.Column("profile", sa.String(50), nullable=True))
    op.add_column("projects", sa.Column("status_vocab", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "status_vocab")
    op.drop_column("projects", "profile")
    op.drop_column("projects", "schema_version")
