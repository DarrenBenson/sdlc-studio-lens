"""Project API routes."""

import math
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.api.deps import get_db
from sdlc_lens.api.schemas.documents import (
    DocumentDetail,
    DocumentListItem,
    DocumentRelationships,
    PaginatedDocuments,
    RelatedDocumentItem,
    SortField,
)
from sdlc_lens.api.schemas.projects import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    SyncTriggerResponse,
    mask_token,
)
from sdlc_lens.api.schemas.stats import ProjectStats
from sdlc_lens.services.documents import (
    DocumentNotFoundError,
    get_document,
    get_related_documents,
    list_documents,
)
from sdlc_lens.services.project import (
    EmptySlugError,
    PathNotFoundError,
    ProjectNotFoundError,
    SlugConflictError,
    create_project,
    delete_project,
    get_document_count,
    get_project_by_slug,
    list_projects,
    update_project,
)
from sdlc_lens.services.stats import get_project_stats
from sdlc_lens.services.sync import SyncInProgressError, run_sync_task, trigger_sync

router = APIRouter(prefix="/projects", tags=["projects"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def _project_response(db: AsyncSession, project) -> ProjectResponse:
    """Build a ProjectResponse with computed document_count and masked token."""
    doc_count = await get_document_count(db, project.id)
    return ProjectResponse(
        slug=project.slug,
        name=project.name,
        sdlc_path=project.sdlc_path,
        source_type=project.source_type,
        repo_url=project.repo_url,
        repo_branch=project.repo_branch,
        repo_path=project.repo_path,
        masked_token=mask_token(project.access_token),
        sync_status=project.sync_status,
        sync_error=project.sync_error,
        last_synced_at=project.last_synced_at,
        document_count=doc_count,
        created_at=project.created_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
async def register_project(body: ProjectCreate, db: DbDep) -> ProjectResponse | JSONResponse:
    """Register a new sdlc-studio project."""
    try:
        project = await create_project(
            db,
            body.name,
            body.sdlc_path,
            source_type=body.source_type,
            repo_url=body.repo_url,
            repo_branch=body.repo_branch,
            repo_path=body.repo_path,
            access_token=body.access_token,
        )
    except PathNotFoundError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "PATH_NOT_FOUND", "message": exc.message}},
        )
    except SlugConflictError as exc:
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "CONFLICT", "message": exc.message}},
        )
    except EmptySlugError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": exc.message}},
        )

    return await _project_response(db, project)


@router.get("", response_model=list[ProjectResponse])
async def list_all_projects(db: DbDep) -> list[ProjectResponse]:
    """List all registered projects."""
    projects = await list_projects(db)
    return [await _project_response(db, p) for p in projects]


@router.get("/{slug}", response_model=ProjectResponse)
async def get_project(slug: str, db: DbDep) -> ProjectResponse | JSONResponse:
    """Get a project by its slug."""
    try:
        project = await get_project_by_slug(db, slug)
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )
    return await _project_response(db, project)


@router.get("/{slug}/stats", response_model=ProjectStats)
async def get_project_stats_endpoint(slug: str, db: DbDep) -> ProjectStats | JSONResponse:
    """Get statistics for a project."""
    try:
        project = await get_project_by_slug(db, slug)
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )
    stats = await get_project_stats(db, project)
    return ProjectStats(**stats)


@router.get("/{slug}/documents", response_model=PaginatedDocuments)
async def list_project_documents(
    slug: str,
    db: DbDep,
    type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    sort: SortField = Query(SortField.updated_at),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1),
) -> PaginatedDocuments | JSONResponse:
    """List documents for a project with filtering, sorting, and pagination."""
    try:
        project = await get_project_by_slug(db, slug)
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )

    # Cap per_page at 100
    actual_per_page = min(per_page, 100)

    docs, total = await list_documents(
        db,
        project.id,
        doc_type=type,
        status=status_filter,
        sort=sort.value,
        order=order,
        page=page,
        per_page=actual_per_page,
    )

    pages = math.ceil(total / actual_per_page) if total > 0 else 0

    items = [
        DocumentListItem(
            doc_id=doc.doc_id,
            type=doc.doc_type,
            title=doc.title,
            status=doc.status,
            owner=doc.owner,
            priority=doc.priority,
            story_points=doc.story_points,
            epic=doc.epic,
            story=doc.story,
            updated_at=doc.synced_at,
        )
        for doc in docs
    ]

    return PaginatedDocuments(
        items=items,
        total=total,
        page=page,
        per_page=actual_per_page,
        pages=pages,
    )


@router.get(
    "/{slug}/documents/{doc_type}/{doc_id}/related",
    response_model=DocumentRelationships,
)
async def get_document_related(
    slug: str,
    doc_type: str,
    doc_id: str,
    db: DbDep,
) -> DocumentRelationships | JSONResponse:
    """Get parent chain and children for a document."""
    try:
        project = await get_project_by_slug(db, slug)
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )

    try:
        doc = await get_document(db, project.id, doc_type, doc_id)
    except DocumentNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Document not found: {doc_type}/{doc_id}",
                }
            },
        )

    parents, children = await get_related_documents(db, project.id, doc)

    return DocumentRelationships(
        doc_id=doc.doc_id,
        type=doc.doc_type,
        title=doc.title,
        parents=[
            RelatedDocumentItem(
                doc_id=p.doc_id,
                type=p.doc_type,
                title=p.title,
                status=p.status,
            )
            for p in parents
        ],
        children=[
            RelatedDocumentItem(
                doc_id=c.doc_id,
                type=c.doc_type,
                title=c.title,
                status=c.status,
            )
            for c in children
        ],
    )


@router.get("/{slug}/documents/{doc_type}/{doc_id:path}", response_model=DocumentDetail)
async def get_document_detail(
    slug: str,
    doc_type: str,
    doc_id: str,
    db: DbDep,
) -> DocumentDetail | JSONResponse:
    """Get a single document by type and doc_id."""
    import json as json_mod

    try:
        project = await get_project_by_slug(db, slug)
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )

    try:
        doc = await get_document(db, project.id, doc_type, doc_id)
    except DocumentNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )

    metadata = None
    if doc.metadata_json:
        metadata = json_mod.loads(doc.metadata_json)

    return DocumentDetail(
        doc_id=doc.doc_id,
        type=doc.doc_type,
        title=doc.title,
        status=doc.status,
        owner=doc.owner,
        priority=doc.priority,
        story_points=doc.story_points,
        epic=doc.epic,
        story=doc.story,
        metadata=metadata,
        content=doc.content,
        file_path=doc.file_path,
        file_hash=doc.file_hash,
        synced_at=doc.synced_at,
    )


@router.put("/{slug}", response_model=ProjectResponse)
async def update_project_endpoint(
    slug: str, body: ProjectUpdate, db: DbDep
) -> ProjectResponse | JSONResponse:
    """Update a project's name and/or path."""
    try:
        project = await update_project(
            db,
            slug,
            name=body.name,
            sdlc_path=body.sdlc_path,
            source_type=body.source_type,
            repo_url=body.repo_url,
            repo_branch=body.repo_branch,
            repo_path=body.repo_path,
            access_token=body.access_token,
        )
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )
    except PathNotFoundError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "PATH_NOT_FOUND", "message": exc.message}},
        )
    return await _project_response(db, project)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_project_endpoint(slug: str, db: DbDep) -> Response | JSONResponse:
    """Delete a project and all its documents."""
    try:
        await delete_project(db, slug)
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{slug}/sync",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SyncTriggerResponse,
)
async def trigger_sync_endpoint(
    slug: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: DbDep,
) -> SyncTriggerResponse | JSONResponse:
    """Trigger a sync for a project. Returns 202 immediately."""
    try:
        project = await trigger_sync(db, slug)
    except ProjectNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "NOT_FOUND", "message": exc.message}},
        )
    except SyncInProgressError as exc:
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "SYNC_IN_PROGRESS", "message": exc.message}},
        )

    session_factory = request.app.state.session_factory
    background_tasks.add_task(run_sync_task, slug, session_factory)

    return SyncTriggerResponse(
        slug=project.slug,
        sync_status="syncing",
        message="Sync started",
    )
