"""Tests for the app-wide exception handlers registered in create_app().

Verifies that Pydantic validation errors (422) and unexpected server errors
(500) return the project's canonical ``{"error": {"code", "message"}}`` shape
rather than FastAPI's default ``{"detail": ...}`` body.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from sdlc_lens.main import create_app


class TestValidationErrorHandler:
    """A request that fails Pydantic validation yields the canonical shape."""

    @pytest.fixture
    def client(self, app) -> TestClient:
        # ``app`` fixture wires an in-memory DB via dependency_overrides.
        return TestClient(app)

    def test_missing_required_field_returns_canonical_422(self, client: TestClient) -> None:
        # ``name`` is required for project registration.
        response = client.post("/api/v1/projects", json={"sdlc_path": "/tmp/x"})
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/json")
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert isinstance(body["error"]["message"], str)
        assert body["error"]["message"]
        assert "detail" not in body


class TestCatchAllExceptionHandler:
    """An endpoint that raises an unexpected error yields a canonical 500."""

    def test_unexpected_error_returns_canonical_500(self) -> None:
        app = create_app()

        # Throwaway route lives only on this test app, not production main.py.
        @app.get("/api/v1/_boom")
        async def _boom() -> None:
            raise RuntimeError("kaboom - should not leak to the client")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/_boom")

        assert response.status_code == 500
        assert response.headers["content-type"].startswith("application/json")
        body = response.json()
        assert body["error"]["code"] == "INTERNAL"
        assert body["error"]["message"] == "Internal server error"
        # The exception detail / stack must not leak to the client.
        assert "kaboom" not in response.text

    def test_http_exception_is_not_swallowed_as_500(self) -> None:
        app = create_app()

        @app.get("/api/v1/_notfound")
        async def _notfound() -> None:
            raise HTTPException(status_code=404, detail="nope")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/_notfound")

        # HTTPException must reach its own handler, not the catch-all.
        assert response.status_code == 404
