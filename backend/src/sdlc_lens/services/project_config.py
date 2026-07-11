"""Best-effort parsing of a project's ``.config.yaml`` / ``.version``.

The sync engine only collects ``.md`` files, so the schema-version and profile
metadata that sdlc-studio keeps in ``.config.yaml`` (with ``.version`` as a
fallback) is read here instead. Parsing is deliberately forgiving: a missing or
malformed config must never fail a sync, so failures degrade to an empty
:class:`ProjectConfig` and are logged at debug level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_CONFIG_FILENAME = ".config.yaml"
_VERSION_FILENAME = ".version"


@dataclass
class ProjectConfig:
    """Parsed schema/profile metadata for a project."""

    schema_version: str | None = None
    profile: str | None = None
    status_vocab: dict[str, list[str]] = field(default_factory=dict)


def _safe_load(text: str | None) -> dict:
    """Parse YAML text into a mapping, or return an empty dict on any failure."""
    if not text or not text.strip():
        return {}
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        logger.debug("Could not parse project config YAML: %s", exc)
        return {}
    return data if isinstance(data, dict) else {}


def _coerce_vocab(value: object) -> dict[str, list[str]]:
    """Coerce a raw ``status_vocab`` value into ``{doc_type: [token, ...]}``."""
    if not isinstance(value, dict):
        return {}
    vocab: dict[str, list[str]] = {}
    for doc_type, tokens in value.items():
        if isinstance(tokens, list):
            vocab[str(doc_type)] = [str(token) for token in tokens]
    return vocab


def parse_project_config(
    config_text: str | None, version_text: str | None = None
) -> ProjectConfig:
    """Parse ``.config.yaml`` (and optional ``.version``) into a :class:`ProjectConfig`.

    ``schema_version`` and ``profile`` prefer ``.config.yaml`` and fall back to
    ``.version``. Best-effort: unparseable input yields an empty config.
    """
    config = _safe_load(config_text)
    version = _safe_load(version_text)

    schema_version = config.get("schema_version", version.get("schema_version"))
    profile = config.get("profile", version.get("profile"))

    return ProjectConfig(
        schema_version=str(schema_version) if schema_version is not None else None,
        profile=str(profile) if profile is not None else None,
        status_vocab=_coerce_vocab(config.get("status_vocab")),
    )


def _read_text(path: Path) -> str | None:
    """Read a text file, returning None if it is absent or unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def read_local_project_config(sdlc_path: str) -> ProjectConfig:
    """Read ``.config.yaml`` / ``.version`` from the root of a local sdlc dir."""
    root = Path(sdlc_path)
    return parse_project_config(
        _read_text(root / _CONFIG_FILENAME),
        _read_text(root / _VERSION_FILENAME),
    )
