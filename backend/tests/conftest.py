"""Test fixtures for the backend test suite."""

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from sdlc_lens.db.models import Base
from sdlc_lens.main import create_app


@pytest.fixture
async def engine():
    """Create an in-memory async SQLite engine for tests."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    @event.listens_for(eng.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    """Create an async session bound to the test engine."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as sess:
        yield sess


@pytest.fixture
def app(engine):
    """Create a FastAPI app with the test database."""
    from sdlc_lens.api.deps import get_db

    application = create_app()

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as sess:
            yield sess

    application.dependency_overrides[get_db] = override_get_db
    application.state.session_factory = session_factory
    return application
