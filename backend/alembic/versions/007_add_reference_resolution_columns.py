"""Add ref_id, depends_on, aliases columns for reference resolution.

Revision ID: 007
Revises: 006
Create Date: 2026-07-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("ref_id", sa.String(60), nullable=True))
    op.add_column("documents", sa.Column("depends_on", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("aliases", sa.Text(), nullable=True))
    op.create_index("ix_documents_ref_id", "documents", ["ref_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_ref_id", table_name="documents")
    op.drop_column("documents", "aliases")
    op.drop_column("documents", "depends_on")
    op.drop_column("documents", "ref_id")
