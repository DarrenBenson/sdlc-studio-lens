"""Shared sdlc-studio id and type recognition.

Single source of truth for artefact-type inference and cross-reference resolution,
reused by ``utils/inference.py`` (sync-time typing), ``services/documents.py`` and
``services/sync_engine.py`` (relationship resolution), and ``services/health_check.py``.

Handles BOTH id eras that appear in real projects:

- **Legacy sequential** - ``US0001``, ``EP0012``, ``RFC0001``, ``RETRO0001``, and the
  hyphenated display form ``CR-0003`` (file ``CR0003``). Prefix is 1-6 letters, an
  optional hyphen, then 4+ digits.
- **Schema-v3 short-ULID** - ``BG-01KX8B82``, ``US-01JQK3F8``. Prefix, a mandatory
  hyphen, then an 8+ character Crockford base32 tail (alphabet excludes I, L, O, U).

Behaviour mirrors the skill's ``scripts/lib/sdlc_md.py`` (``ID_RE`` / ``norm_id``); the
lens is standalone, so the logic is reimplemented here rather than imported.
"""

from __future__ import annotations

import re

# Id prefix -> canonical document type (pipeline + meta types).
PREFIX_TO_TYPE: dict[str, str] = {
    "EP": "epic",
    "US": "story",
    "PL": "plan",
    "TS": "test-spec",
    "BG": "bug",
    "CR": "cr",
    "RFC": "rfc",
    "WF": "workflow",
    "RETRO": "retro",
    "RV": "review",
}

# Directory name -> canonical document type (fallback when a filename carries no id prefix).
DIR_TO_TYPE: dict[str, str] = {
    "epics": "epic",
    "stories": "story",
    "plans": "plan",
    "test-specs": "test-spec",
    "bugs": "bug",
    "change-requests": "cr",
    "rfcs": "rfc",
    "workflows": "workflow",
    "retros": "retro",
    "reviews": "review",
    "decisions": "decision",
    "personas": "persona",
    "product": "pvd",
}

# Root-level singleton document stems (case-insensitive) -> canonical type.
SINGLETON_STEMS: dict[str, str] = {
    "prd": "prd",
    "trd": "trd",
    "tsd": "tsd",
    "pvd": "pvd",
    "personas": "personas",
    "decisions": "decisions",
    "constitution": "constitution",
    "brand-guide": "brand-guide",
}

# Crockford base32 tail (excludes I, L, O, U), 8+ chars. Case-insensitive at match time.
_ULID_TAIL = r"[0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{8,}"

# An artefact id at the START of a string: PREFIX then either a hyphenated ULID tail
# or an optional-hyphen 4+ digit sequential tail. The ULID branch is tried first so a
# genuine ULID is never truncated to a 4-digit read.
_ID_HEAD_RE = re.compile(
    r"^(?P<prefix>[A-Za-z]{1,6})(?:-(?P<ulid>" + _ULID_TAIL + r")|-?(?P<seq>\d{4,}))"
)


def id_head(text: str) -> str | None:
    """Return the artefact id at the start of ``text`` (prefix + tail), or ``None``.

    The tail may be sequential (``US0001``, ``CR-0003``) or a v3 ULID
    (``BG-01KX8B82``). The descriptive slug after the id is ignored, so
    ``id_head("BG-01KX8B82-path-traversal") == "BG-01KX8B82"``. Returns ``None`` when
    the leading token is not a recognised artefact prefix, so arbitrary slugs
    (``audit-event-matrix``) and bare-number files (``0001-framework``) are rejected.
    """
    if not text:
        return None
    match = _ID_HEAD_RE.match(text.strip())
    if not match:
        return None
    if match.group("prefix").upper() not in PREFIX_TO_TYPE:
        return None
    return match.group(0)


def type_for_prefix(id_str: str) -> str | None:
    """The canonical document type for an id's prefix, or ``None`` if unrecognised."""
    match = _ID_HEAD_RE.match(id_str.strip())
    if not match:
        return None
    return PREFIX_TO_TYPE.get(match.group("prefix").upper())


def norm_id(value: str | None) -> str | None:
    """Normalise an id for equality matching: strip non-alphanumerics, upper-case.

    Collapses the display variants of one id to a single key so a reference resolves to
    its file regardless of hyphenation or wrapping:
    ``CR-0003`` / ``CR0003`` / ``[[CR-0496]]`` -> ``CR0003`` / ``CR0496``;
    ``US-01JQK3F8`` -> ``US01JQK3F8``. Returns ``None`` for empty input.
    """
    if not value:
        return None
    cleaned = re.sub(r"[^0-9A-Za-z]", "", value).upper()
    return cleaned or None


# Matches an id token anywhere in a reference string (markdown link, wiki-link, plain
# prose). Prefix must be a known artefact prefix; tail is ULID or optional-hyphen digits.
_ID_TOKEN_RE = re.compile(
    r"\b(?P<id>(?P<prefix>"
    + "|".join(sorted(PREFIX_TO_TYPE, key=len, reverse=True))
    + r")(?:-(?:" + _ULID_TAIL + r")|-?\d{4,}))",
)


def extract_ref_id(value: str | None) -> str | None:
    """Extract the first artefact id from a reference value, else ``None``.

    Handles ``[EP0007: title](../epics/EP0007-...md)``, ``[[CR-0496]]``, ``US0163: …``,
    a bare ``BG-01KX8B82``, and the em-dash / empty "none" placeholders. Returns the id
    as written (call :func:`norm_id` to compare).
    """
    if not value or not value.strip():
        return None
    stripped = value.strip()
    if stripped in {"-", "--", "—", "–"}:
        return None
    match = _ID_TOKEN_RE.search(stripped)
    return match.group("id") if match else None
