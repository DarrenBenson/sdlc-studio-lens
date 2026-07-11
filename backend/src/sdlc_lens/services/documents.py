"""Document service - business logic for document queries."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.db.models.document import Document
from sdlc_lens.utils.sdlc_ids import id_head, norm_id


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
    base = base.order_by(col.asc()) if order == "asc" else base.order_by(col.desc())

    # Pagination
    offset = (page - 1) * per_page
    base = base.offset(offset).limit(per_page)

    result = await session.execute(base)
    documents = list(result.scalars().all())

    return documents, total


async def get_all_documents(
    session: AsyncSession,
    project_id: int,
) -> list[Document]:
    """Fetch all documents for a project (no pagination)."""
    stmt = select(Document).where(Document.project_id == project_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


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


def _doc_ref(doc: Document) -> str | None:
    """The document's own normalised reference id (stored, or derived as a fallback)."""
    return doc.ref_id or norm_id(id_head(doc.doc_id))


async def _find_doc_by_clean_id(
    session: AsyncSession,
    project_id: int,
    ref: str | None,
) -> Document | None:
    """Find a document by any reference form, resolved through the normalised id.

    Matches on the document's ``ref_id`` (so ``CR-0003`` / ``CR0003`` / ``[[CR-0496]]``
    / a v3 ULID all resolve), then falls back to a migration ``Aliases`` match so an
    old sequential-id reference finds the renumbered document.
    """
    normed = norm_id(ref)
    if not normed:
        return None
    stmt = (
        select(Document)
        .where(
            Document.project_id == project_id,
            or_(
                Document.ref_id == normed,
                Document.aliases == normed,
                Document.aliases.like(f"{normed},%"),
                Document.aliases.like(f"%,{normed},%"),
                Document.aliases.like(f"%,{normed}"),
            ),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_related_documents(
    session: AsyncSession,
    project_id: int,
    doc: Document,
) -> tuple[list[Document], list[Document], list[Document], list[Document]]:
    """Get parents, children, dependencies, and dependents for a document.

    ``parents`` are ordered nearest ancestor first. ``depends_on`` are the documents
    this one declares a dependency on; ``dependents`` declare a dependency on this one.
    """
    parents = await _get_parent_chain(session, project_id, doc)
    children = await _get_children(session, project_id, doc)
    depends_on = await _get_dependencies(session, project_id, doc)
    dependents = await _get_dependents(session, project_id, doc)
    return parents, children, depends_on, dependents


async def _get_parent_chain(
    session: AsyncSession,
    project_id: int,
    doc: Document,
) -> list[Document]:
    """Walk up the hierarchy using epic/story columns."""
    parents: list[Document] = []

    if doc.story:
        story_doc = await _find_doc_by_clean_id(session, project_id, doc.story)
        if story_doc and story_doc.id != doc.id:
            parents.append(story_doc)
            if story_doc.epic:
                epic_doc = await _find_doc_by_clean_id(session, project_id, story_doc.epic)
                if epic_doc and epic_doc.id not in {doc.id, story_doc.id}:
                    parents.append(epic_doc)
    elif doc.epic:
        epic_doc = await _find_doc_by_clean_id(session, project_id, doc.epic)
        if epic_doc and epic_doc.id != doc.id:
            parents.append(epic_doc)

    return parents


async def _get_children(
    session: AsyncSession,
    project_id: int,
    doc: Document,
) -> list[Document]:
    """Find documents that reference this doc as their parent (by normalised id)."""
    ref = _doc_ref(doc)
    if not ref:
        return []

    if doc.doc_type == "epic":
        stmt = (
            select(Document)
            .where(
                Document.project_id == project_id,
                Document.epic == ref,
                Document.story.is_(None),
                Document.id != doc.id,  # a doc naming its own id is not its own child
            )
            .order_by(Document.doc_type, Document.doc_id)
        )
    elif doc.doc_type == "story":
        stmt = (
            select(Document)
            .where(
                Document.project_id == project_id,
                Document.story == ref,
                Document.id != doc.id,
            )
            .order_by(Document.doc_type, Document.doc_id)
        )
    else:
        return []

    result = await session.execute(stmt)
    return list(result.scalars().all())


def _split_ref_list(value: str | None) -> list[str]:
    """Split a stored comma-joined normalised id list into individual ids."""
    if not value:
        return []
    return [part for part in value.split(",") if part]


async def _get_dependencies(
    session: AsyncSession,
    project_id: int,
    doc: Document,
) -> list[Document]:
    """Documents this one declares a `Depends on` dependency upon.

    Resolves every declared id in a single query - a ``ref_id`` match plus a
    supplementary ``aliases`` match so an old sequential id still finds its
    renumbered document - then reorders the results to the declared order,
    dedupes, and excludes the document itself.
    """
    dep_ids: list[str] = []
    for dep in _split_ref_list(doc.depends_on):
        normed = norm_id(dep)
        if normed and normed not in dep_ids:
            dep_ids.append(normed)
    if not dep_ids:
        return []

    conditions = [Document.ref_id.in_(dep_ids)]
    for dep_id in dep_ids:
        conditions.extend(
            (
                Document.aliases == dep_id,
                Document.aliases.like(f"{dep_id},%"),
                Document.aliases.like(f"%,{dep_id},%"),
                Document.aliases.like(f"%,{dep_id}"),
            )
        )

    stmt = select(Document).where(
        Document.project_id == project_id,
        Document.id != doc.id,  # a doc naming its own id is not its own dependency
        or_(*conditions),
    )
    result = await session.execute(stmt)
    candidates = list(result.scalars().all())

    # Reorder to the declared dependency order, deduping so each target appears
    # once even when named twice or reachable by both its ref_id and an alias.
    results: list[Document] = []
    seen: set[int] = set()
    for dep_id in dep_ids:
        for target in candidates:
            if target.id in seen:
                continue
            aliases = set(_split_ref_list(target.aliases))
            if target.ref_id == dep_id or dep_id in aliases:
                seen.add(target.id)
                results.append(target)
                break
    return results


async def _get_dependents(
    session: AsyncSession,
    project_id: int,
    doc: Document,
) -> list[Document]:
    """Documents that declare a `Depends on` dependency upon this one."""
    ref = _doc_ref(doc)
    if not ref:
        return []
    stmt = (
        select(Document)
        .where(
            Document.project_id == project_id,
            Document.id != doc.id,
            or_(
                Document.depends_on == ref,
                Document.depends_on.like(f"{ref},%"),
                Document.depends_on.like(f"%,{ref},%"),
                Document.depends_on.like(f"%,{ref}"),
            ),
        )
        .order_by(Document.doc_type, Document.doc_id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
