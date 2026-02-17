"""Document service - business logic for document queries."""

import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document


async def list_documents(
    session: AsyncSession,
    project_id: int,
    *,
    doc_type: str | None = None,
    status: str | None = None,
    sort: str = "updated_at",
    order: str = "desc",
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Document], int]:
    """List documents for a project with filtering, sorting, and pagination.

    Returns a tuple of (documents, total_count).
    """
    # Column mapping for sort
    sort_columns = {
        "title": Document.title,
        "type": Document.doc_type,
        "status": Document.status,
        "updated_at": Document.synced_at,
    }

    base = select(Document).where(Document.project_id == project_id)

    if doc_type is not None:
        base = base.where(Document.doc_type == doc_type)
    if status is not None:
        base = base.where(Document.status == status)

    # Count query
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    # Sort
    col = sort_columns.get(sort, Document.synced_at)
    if order == "asc":
        base = base.order_by(col.asc())
    else:
        base = base.order_by(col.desc())

    # Pagination
    offset = (page - 1) * per_page
    base = base.offset(offset).limit(per_page)

    result = await session.execute(base)
    documents = list(result.scalars().all())

    return documents, total


class DocumentNotFoundError(Exception):
    """Raised when a document is not found."""

    def __init__(self, message: str = "Document not found"):
        self.message = message
        super().__init__(self.message)


async def get_document(
    session: AsyncSession,
    project_id: int,
    doc_type: str,
    doc_id: str,
) -> Document:
    """Get a single document by type and doc_id.

    Raises:
        DocumentNotFoundError: If no matching document exists.
    """
    stmt = select(Document).where(
        Document.project_id == project_id,
        Document.doc_type == doc_type,
        Document.doc_id == doc_id,
    )
    result = await session.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None:
        raise DocumentNotFoundError
    return doc
