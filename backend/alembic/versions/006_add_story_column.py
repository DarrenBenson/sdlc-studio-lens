"""Add story column and indexes to documents table.

Revision ID: 006
Revises: 005
Create Date: 2026-02-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("story", sa.String(50), nullable=True),
    )
    op.create_index("ix_documents_story", "documents", ["story"])
    op.create_index("ix_documents_epic", "documents", ["epic"])


def downgrade() -> None:
    op.drop_index("ix_documents_epic", table_name="documents")
    op.drop_index("ix_documents_story", table_name="documents")
    op.drop_column("documents", "story")
