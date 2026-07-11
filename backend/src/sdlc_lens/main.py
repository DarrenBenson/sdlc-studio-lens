"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from sdlc_lens.api.routes.projects import router as projects_router
from sdlc_lens.api.routes.search import router as search_router
from sdlc_lens.api.routes.stats import router as stats_router
from sdlc_lens.api.routes.system import router as system_router
from sdlc_lens.db.session import async_session_factory

_STATIC_DIR = Path("/app/static")


def _safe_static_file(static_dir: Path, path: str) -> Path | None:
    """Return the static file for path if it stays within static_dir, else None.

    Resolves the candidate to defend against path traversal (e.g. encoded
    ``../``): a resolved path escaping the static root is rejected.
    """
    if not path:
        return None
    root = static_dir.resolve()
    resolved = (static_dir / path).resolve()
    if resolved.is_file() and resolved.is_relative_to(root):
        return resolved
    return None


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

    # Serve frontend static files when running in Docker (directory exists)
    if _STATIC_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="assets")

        @app.get("/{path:path}")
        async def _spa_fallback(path: str) -> Response:
            """Serve static files or fall back to index.html for SPA routing."""
            # Unknown API paths must yield a JSON 404, not the SPA shell.
            if path.startswith("api/"):
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": {
                            "code": "NOT_FOUND",
                            "message": f"Resource not found: /{path}",
                        }
                    },
                )
            static_file = _safe_static_file(_STATIC_DIR, path)
            if static_file is not None:
                return FileResponse(static_file)
            return FileResponse(_STATIC_DIR / "index.html")

    return app
