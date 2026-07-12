"""Single source of truth for the application version.

The version is declared in ``pyproject.toml`` and resolved at runtime from the
installed package metadata, so no module hardcodes the version string.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

_PACKAGE_NAME = "sdlc-lens"
_FALLBACK_VERSION = "0.0.0"


def get_version() -> str:
    """Return the installed package version, or a safe fallback if unresolved."""
    try:
        return version(_PACKAGE_NAME)
    except PackageNotFoundError:
        return _FALLBACK_VERSION
