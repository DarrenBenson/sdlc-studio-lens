"""Full-text search API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from sdlc_lens.api.deps import get_db
from sdlc_lens.api.schemas.search import SearchResponse
from sdlc_lens.services.search import search_documents

router = APIRouter(prefix="/search", tags=["search"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=SearchResponse)
async def search(
    db: DbDep,
    q: Annotated[str, Query(min_length=1, max_length=500)],
    project: str | None = None,
    type: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=50)] = 20,
) -> SearchResponse:
    """Search documents using full-text search.

    Returns matching documents ranked by relevance with highlighted
    snippets and optional filtering by project or document type.
    """
    result = await search_documents(
        db,
        query=q,
        project_slug=project,
        doc_type=type,
        page=page,
        per_page=per_page,
    )
    return SearchResponse(**result)
