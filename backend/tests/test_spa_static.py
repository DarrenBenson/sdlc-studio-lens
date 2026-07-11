"""Tests for SPA static file serving and path traversal containment."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import sdlc_lens.main as main_module
from sdlc_lens.main import _safe_static_file, create_app


@pytest.fixture
def static_root(tmp_path: Path) -> Path:
    """Create a dummy static directory with index.html and an asset."""
    (tmp_path / "index.html").write_text("<!doctype html><title>app</title>")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('hi');")
    (tmp_path / "favicon.ico").write_text("icon")
    # A secret file living OUTSIDE the static root, one level up.
    (tmp_path.parent / "secret.txt").write_text("top secret")
    return tmp_path


class TestSafeStaticFile:
    """Unit tests for the pure containment helper."""

    def test_serves_legitimate_file(self, static_root: Path) -> None:
        result = _safe_static_file(static_root, "favicon.ico")
        assert result == (static_root / "favicon.ico").resolve()

    def test_serves_nested_asset(self, static_root: Path) -> None:
        result = _safe_static_file(static_root, "assets/app.js")
        assert result == (static_root / "assets" / "app.js").resolve()

    def test_empty_path_returns_none(self, static_root: Path) -> None:
        assert _safe_static_file(static_root, "") is None

    def test_missing_file_returns_none(self, static_root: Path) -> None:
        assert _safe_static_file(static_root, "does-not-exist.js") is None

    def test_traversal_outside_root_returns_none(self, static_root: Path) -> None:
        # Escapes the static root - must not be served even though it exists.
        assert _safe_static_file(static_root, "../secret.txt") is None

    def test_deep_traversal_returns_none(self, static_root: Path) -> None:
        assert _safe_static_file(static_root, "../../etc/passwd") is None


class TestSpaFallback:
    """Integration tests for the mounted SPA fallback handler."""

    @pytest.fixture
    def client(self, static_root: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
        monkeypatch.setattr(main_module, "_STATIC_DIR", static_root)
        return TestClient(create_app())

    def test_serves_static_file(self, client: TestClient) -> None:
        response = client.get("/favicon.ico")
        assert response.status_code == 200
        assert response.text == "icon"

    def test_unknown_route_serves_index_html(self, client: TestClient) -> None:
        response = client.get("/some/spa/route")
        assert response.status_code == 200
        assert "<!doctype html>" in response.text.lower()

    def test_unknown_api_path_returns_json_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/does-not-exist")
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/json")
        assert response.json()["error"]["code"] == "NOT_FOUND"
