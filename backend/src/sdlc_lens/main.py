"""FastAPI application factory."""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from sdlc_lens.api.routes.connections import router as connections_router
from sdlc_lens.api.routes.projects import router as projects_router
from sdlc_lens.api.routes.search import router as search_router
from sdlc_lens.api.routes.stats import router as stats_router
from sdlc_lens.api.routes.system import router as system_router
from sdlc_lens.config import settings
from sdlc_lens.db.session import async_session_factory
from sdlc_lens.version import get_version

logger = logging.getLogger(__name__)

_STATIC_DIR = Path("/app/static")

# Identity of the handler we own, so configure_logging() is idempotent.
_LOG_HANDLER_NAME = "sdlc-lens-stdout"


def configure_logging() -> None:
    """Give the application's loggers somewhere to go (BG-01KXDGA1).

    Uvicorn configures only its OWN loggers (`uvicorn`, `uvicorn.access`,
    `uvicorn.error`). It does not touch the root logger. So without this, the root logger
    has no handler and **every** `logger.info`/`warning`/`exception` in `sdlc_lens.*` is
    silently discarded - which was true in production for the entire life of this project.

    That was survivable while the app was purely request/response: a failure surfaced as a
    500 and an error on the project. The freshness poller changed it. The poller runs
    unattended, for ever, with nobody watching a response, and its documented failure mode
    is that it stops QUIETLY. For that component the log is not a nicety - it is the only
    mechanism by which a human ever finds out.

    Idempotent, and it adds OUR handler when OUR handler is absent - not merely "when there
    are no handlers at all". Those are different questions, and the second is wrong:
    anything else that attaches a root handler (a test fixture, a library, an APM agent)
    would make us skip, and the app would fall silent again in exactly the way this bug is
    about. The handler's name is its identity, so repeat calls stay idempotent.
    """
    root = logging.getLogger()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    if not any(h.get_name() == _LOG_HANDLER_NAME for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.set_name(_LOG_HANDLER_NAME)
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s - %(message)s"))
        root.addHandler(handler)


def _summarise_validation_errors(exc: RequestValidationError) -> str:
    """Build a concise, human-readable summary of validation problems."""
    parts: list[str] = []
    for err in exc.errors():
        location = ".".join(str(loc) for loc in err.get("loc", ()) if loc != "body")
        message = err.get("msg", "invalid value")
        parts.append(f"{location}: {message}" if location else message)
    return "; ".join(parts) or "Request validation failed"


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


def _warn_if_tokens_are_plaintext() -> None:
    """Warn loudly when stored GitHub credentials are not encrypted at rest.

    Encryption is opt-in so an existing deployment keeps working after an
    upgrade, which means the default is plaintext PATs in the database. That is
    a security posture the operator must choose knowingly, not discover later.
    """
    if settings.token_encryption_key:
        return
    logger.warning(
        "No token encryption key is configured: stored GitHub credentials are held "
        "in PLAINTEXT in the database. Generate a key with "
        '`python -c "from cryptography.fernet import Fernet; '
        'print(Fernet.generate_key().decode())"` and set it as '
        "SDLC_LENS_TOKEN_ENCRYPTION_KEY. Existing plaintext tokens keep working; "
        "tokens written after the key is set are encrypted."
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - startup and shutdown."""
    from sdlc_lens.services.poller import reset_stuck_syncing, start_poller, stop_poller

    _warn_if_tokens_are_plaintext()

    # A project left in "syncing" by a hard stop (a container redeploy, an OOM) is locked
    # out for ever: trigger_sync refuses it and nothing else resets it. A "syncing" status
    # at startup cannot be real - no sync survived the process running it - so clear it.
    #
    # Best-effort by design. This is housekeeping, and housekeeping must never stop the app
    # from BOOTING: a database that is not ready yet is a reason to log and carry on, not a
    # reason to take the whole service down.
    try:
        await reset_stuck_syncing(app.state.session_factory)
    except Exception:
        logger.exception("Could not reset stuck 'syncing' projects at startup; continuing")

    # The freshness poller (CR-01KXCAZJ). Returns None when disabled
    # (sync_poll_interval_seconds=0), in which case no task exists at all.
    poller = start_poller(app.state.session_factory)
    try:
        yield
    finally:
        # Cancel AND await, so shutdown never leaves an orphaned task behind.
        await stop_poller(poller)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()
    app = FastAPI(
        title="SDLC Studio Lens",
        version=get_version(),
        lifespan=lifespan,
    )
    app.state.session_factory = async_session_factory

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return Pydantic validation failures in the canonical error shape."""
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": _summarise_validation_errors(exc),
                }
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Return unexpected errors as a canonical 500 without leaking detail."""
        logger.exception("Unhandled exception processing %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL",
                    "message": "Internal server error",
                }
            },
        )

    app.include_router(connections_router, prefix="/api/v1")
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
            if path == "api" or path.startswith("api/"):
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
