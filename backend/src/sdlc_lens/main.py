"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sdlc_lens.api.routes.projects import router as projects_router
from sdlc_lens.api.routes.search import router as search_router
from sdlc_lens.api.routes.stats import router as stats_router
from sdlc_lens.api.routes.system import router as system_router
from sdlc_lens.db.session import async_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - startup and shutdown."""
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="SDLC Studio Lens",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.session_factory = async_session_factory
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1")
    app.include_router(system_router, prefix="/api/v1")
    return app
