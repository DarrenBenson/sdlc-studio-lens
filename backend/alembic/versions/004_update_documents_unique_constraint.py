"""Update documents unique constraint to use file_path.

Revision ID: 004
Revises: 003
Create Date: 2026-02-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite batch mode recreates the table, applying constraint changes.
    naming = {"uq": "uq_%(table_name)s_%(column_0_N_name)s"}
    with op.batch_alter_table(
        "documents",
        naming_convention=naming,
        recreate="always",
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_documents_project_id_doc_type_doc_id", type_="unique"
        )
        batch_op.alter_column("doc_id", type_=sa.String(200))
        batch_op.create_unique_constraint(
            "uq_documents_project_id_file_path",
            ["project_id", "file_path"],
        )


def downgrade() -> None:
    naming = {"uq": "uq_%(table_name)s_%(column_0_N_name)s"}
    with op.batch_alter_table(
        "documents",
        naming_convention=naming,
        recreate="always",
    ) as batch_op:
        batch_op.drop_constraint(
            "uq_documents_project_id_file_path", type_="unique"
        )
        batch_op.alter_column("doc_id", type_=sa.String(50))
        batch_op.create_unique_constraint(
            "uq_documents_project_id_doc_type_doc_id",
            ["project_id", "doc_type", "doc_id"],
        )
