"""Add GitHub source columns to projects table.

Revision ID: 005
Revises: 004
Create Date: 2026-02-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns (simple adds work without batch mode)
    op.add_column(
        "projects",
        sa.Column("source_type", sa.String(20), nullable=False, server_default="local"),
    )
    op.add_column(
        "projects",
        sa.Column("repo_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("repo_branch", sa.String(255), nullable=False, server_default="main"),
    )
    op.add_column(
        "projects",
        sa.Column("repo_path", sa.String(500), nullable=False, server_default="sdlc-studio"),
    )
    op.add_column(
        "projects",
        sa.Column("access_token", sa.Text(), nullable=True),
    )

    # Make sdlc_path nullable (requires batch mode for SQLite)
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "sdlc_path",
            existing_type=sa.Text(),
            nullable=True,
        )


def downgrade() -> None:
    # Restore sdlc_path NOT NULL (batch mode for SQLite)
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "sdlc_path",
            existing_type=sa.Text(),
            nullable=False,
        )

    # Drop new columns
    op.drop_column("projects", "access_token")
    op.drop_column("projects", "repo_path")
    op.drop_column("projects", "repo_branch")
    op.drop_column("projects", "repo_url")
    op.drop_column("projects", "source_type")
