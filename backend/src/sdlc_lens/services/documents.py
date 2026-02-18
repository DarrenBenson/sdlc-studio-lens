"""Document service - business logic for document queries."""

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document

_DOC_PREFIX_RE = re.compile(r"^([A-Z]{2}\d{4})")


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
        if status == "none":
            base = base.where(Document.status.is_(None))
        else:
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


def _extract_doc_prefix(doc_id: str) -> str | None:
    """Extract clean prefix from a doc_id (e.g. 'EP0007' from 'EP0007-git-repo-sync')."""
    match = _DOC_PREFIX_RE.match(doc_id)
    return match.group(1) if match else None


async def _find_doc_by_clean_id(
    session: AsyncSession,
    project_id: int,
    clean_id: str,
) -> Document | None:
    """Find a document by its clean ID prefix (e.g. EP0007)."""
    stmt = (
        select(Document)
        .where(
            Document.project_id == project_id,
            Document.doc_id.like(f"{clean_id}%"),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_related_documents(
    session: AsyncSession,
    project_id: int,
    doc: Document,
) -> tuple[list[Document], list[Document]]:
    """Get parent chain and children for a document.

    Returns (parents, children) where parents are ordered nearest ancestor first.
    """
    parents = await _get_parent_chain(session, project_id, doc)
    children = await _get_children(session, project_id, doc)
    return parents, children


async def _get_parent_chain(
    session: AsyncSession,
    project_id: int,
    doc: Document,
) -> list[Document]:
    """Walk up the hierarchy using epic/story columns."""
    parents: list[Document] = []

    if doc.story:
        story_doc = await _find_doc_by_clean_id(session, project_id, doc.story)
        if story_doc:
            parents.append(story_doc)
            if story_doc.epic:
                epic_doc = await _find_doc_by_clean_id(
                    session, project_id, story_doc.epic
                )
                if epic_doc:
                    parents.append(epic_doc)
    elif doc.epic:
        epic_doc = await _find_doc_by_clean_id(session, project_id, doc.epic)
        if epic_doc:
            parents.append(epic_doc)

    return parents


async def _get_children(
    session: AsyncSession,
    project_id: int,
    doc: Document,
) -> list[Document]:
    """Find documents that reference this doc as their parent."""
    prefix = _extract_doc_prefix(doc.doc_id)
    if not prefix:
        return []

    if doc.doc_type == "epic":
        stmt = (
            select(Document)
            .where(
                Document.project_id == project_id,
                Document.epic == prefix,
                Document.story.is_(None),
            )
            .order_by(Document.doc_type, Document.doc_id)
        )
    elif doc.doc_type == "story":
        stmt = (
            select(Document)
            .where(
                Document.project_id == project_id,
                Document.story == prefix,
            )
            .order_by(Document.doc_type, Document.doc_id)
        )
    else:
        return []

    result = await session.execute(stmt)
    return list(result.scalars().all())
