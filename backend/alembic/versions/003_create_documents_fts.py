"""Create documents_fts FTS5 virtual table.

Revision ID: 003
Revises: 002
Create Date: 2026-02-17
"""

from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE VIRTUAL TABLE documents_fts USING fts5("
        "title, content, "
        "content=documents, content_rowid=id, "
        "tokenize=\"unicode61 tokenchars '_'\")"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS documents_fts")
