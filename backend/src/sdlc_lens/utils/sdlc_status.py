"""Schema-v3 status vocabulary and canonicalisation.

Mirrors the skill's ``sdlc_md`` ``STATUS_VOCAB`` / ``TERMINAL_STATUS`` /
``canonical_status``. Real-world status values carry trailing prose
(``Done - implemented 2026-07-08``), surrounding bold (``**Done**``), or a
parenthetical (``Complete (81/88)``); :func:`canonical_status` reduces such a value to
its vocabulary token so grouping, colouring, and completion counting are accurate.
"""

from __future__ import annotations

import re

# Per-type status vocabulary (verbatim from the skill's STATUS_VOCAB).
STATUS_VOCAB: dict[str, list[str]] = {
    "epic": ["Draft", "Ready", "Approved", "In Progress", "Done"],
    "story": [
        "Proposed",
        "Draft",
        "Ready",
        "Planned",
        "In Progress",
        "Review",
        "Blocked",
        "Done",
        "Won't Implement",
        "Deferred",
        "Superseded",
    ],
    "plan": ["Draft", "In Progress", "Complete", "Superseded"],
    "bug": ["Open", "In Progress", "Fixed", "Verified", "Closed", "Won't Fix", "Superseded"],
    "cr": [
        "Proposed",
        "Approved",
        "In Progress",
        "Complete",
        "Rejected",
        "Deferred",
        "Superseded",
        "Blocked",
    ],
    "rfc": ["Draft", "In Review", "Accepted", "Superseded", "Withdrawn"],
    "test-spec": ["Draft", "Ready", "In Progress", "Complete", "Superseded"],
    "workflow": [
        "Created",
        "Planning",
        "Testing",
        "Implementing",
        "Verifying",
        "Reviewing",
        "Checking",
        "Done",
        "Paused",
        "Superseded",
    ],
}

# Finding types gain an `inbox` triage lane under schema v3.
FINDING_TYPES = frozenset({"bug", "cr", "rfc"})
INBOX_STATUS = "inbox"

# Absorbing (terminal) statuses per type - a unit here is closed/complete.
TERMINAL_STATUS: dict[str, set[str]] = {
    "epic": {"Done"},
    "story": {"Done", "Won't Implement", "Superseded"},
    "plan": {"Complete", "Superseded"},
    "bug": {"Fixed", "Verified", "Closed", "Won't Fix", "Superseded"},
    "cr": {"Complete", "Rejected", "Superseded"},
    "rfc": {"Accepted", "Superseded", "Withdrawn"},
    "test-spec": {"Complete", "Superseded"},
    "workflow": {"Done", "Superseded"},
}

# The full set of vocabulary tokens across all types, plus inbox. Used for
# canonicalising a status whose type is unknown.
ALL_STATUSES: list[str] = sorted(
    {INBOX_STATUS, *(s for vocab in STATUS_VOCAB.values() for s in vocab)},
    key=len,
    reverse=True,
)

# Statuses considered "done" for completion metrics (union of terminal-and-complete).
DONE_STATUSES = frozenset({"Done", "Complete", "Fixed", "Verified", "Closed", "Accepted"})

# ``Done``/``Complete`` read as terminal for any lifecycle type, so mixed-era
# projects (a plan marked ``Done`` rather than the v3 ``Complete``) are not
# falsely flagged as unfinished.
_UNIVERSAL_TERMINAL = frozenset({"Done", "Complete"})

# Union of every type's terminal set, used when the doc type is unknown.
_ANY_TERMINAL = frozenset().union(*TERMINAL_STATUS.values())

_LEADING_STRIP = re.compile(r"^[>\s*_`]+")


def _strip_light(status: str) -> str:
    """Remove only bold/blockquote wrapping, keeping any internal prose intact.

    ``> **Ready - for QA**`` -> ``Ready - for QA``. Unlike :func:`_strip_decoration`
    this does NOT cut at a trailing-prose separator, so a custom vocabulary token
    that itself contains ``' - '`` survives for a whole-token match.
    """
    text = _LEADING_STRIP.sub("", status).strip()
    return text.strip("*_` ").strip()


def _strip_decoration(status: str) -> str:
    """Remove bold/blockquote decoration and any trailing prose after the token.

    ``**Done** - implemented`` -> ``Done``; ``Done · **CR:** ...`` -> ``Done``;
    ``Complete (81/88)`` -> ``Complete``.
    """
    text = _strip_light(status)
    # Cut at the first separator that introduces trailing prose.
    for sep in (" - ", " — ", " – ", " · ", " | ", " (", "("):
        idx = text.find(sep)
        if idx != -1:
            text = text[:idx]
    return text.strip("*_` ").strip()


def _match_token(text: str, candidates: list[str]) -> str | None:
    """Return the first candidate token that matches ``text`` (case-insensitive).

    A token matches when it equals ``text`` or prefixes it on a word boundary, so
    ``Done`` matches ``Done - shipped``. Candidates are expected longest-first, so
    ``In Progress`` wins over ``In``.
    """
    lowered = text.strip().lower()
    if not lowered:
        return None
    for token in candidates:
        lower_token = token.lower()
        if lowered == lower_token or lowered.startswith(lower_token + " "):
            return token
    return None


def canonical_status(
    status: str | None,
    doc_type: str | None = None,
    extra_vocab: list[str] | None = None,
) -> str | None:
    """Reduce a raw status value to its vocabulary token, or None.

    Matches the longest vocabulary token that prefixes the decoration-stripped text
    (case-insensitive), so ``In Progress`` wins over ``In``. When ``doc_type`` names a
    known type, that type's vocabulary (plus ``inbox`` for findings) is tried first;
    otherwise the global token set is used. ``extra_vocab`` appends project-defined
    tokens (e.g. ``Gated``, ``Built``) so they canonicalise to themselves as
    first-class tokens. A value that matches no token is returned stripped (never
    dropped), so custom project statuses still display.
    """
    if not status or not status.strip():
        return None

    candidates = ALL_STATUSES
    if doc_type in STATUS_VOCAB:
        vocab = list(STATUS_VOCAB[doc_type])
        if doc_type in FINDING_TYPES:
            vocab.append(INBOX_STATUS)
        candidates = sorted(vocab, key=len, reverse=True)

    if extra_vocab:
        candidates = sorted({*candidates, *extra_vocab}, key=len, reverse=True)

    # First match against the lightly-cleaned text (wrapping stripped, trailing prose
    # kept) so a custom token containing an internal ' - ' is matched whole before any
    # truncation could split it. Longest-first ordering means the full token wins.
    matched = _match_token(_strip_light(status), candidates)
    if matched is not None:
        return matched

    # No token in the lightly-cleaned text: cut trailing prose and re-match. A value
    # that still matches nothing is returned stripped (never dropped) so custom
    # project statuses ('Gated — waiting') display as their leading token ('Gated').
    stripped = _strip_decoration(status)
    if not stripped:
        return None
    return _match_token(stripped, candidates) or stripped


def is_done(status: str | None, doc_type: str | None = None) -> bool:
    """True when the canonical status counts as done/complete for metrics."""
    canonical = canonical_status(status, doc_type)
    return canonical in DONE_STATUSES if canonical else False


def is_terminal(doc_type: str | None, status: str | None) -> bool:
    """True when ``status`` means the artefact of ``doc_type`` is closed/complete.

    Canonicalises the status (stripping bold/blockquote/prose decoration) then
    checks membership in that type's :data:`TERMINAL_STATUS` set. ``Done`` and
    ``Complete`` are treated as universally terminal so mixed-era artefacts are not
    falsely flagged; an unknown ``doc_type`` falls back to the union of every
    type's terminal statuses. This is the single source of truth for the
    terminal/stale checks in the health-check and stats services.
    """
    canonical = canonical_status(status, doc_type)
    if not canonical:
        return False
    if canonical in _UNIVERSAL_TERMINAL:
        return True
    terminal = TERMINAL_STATUS.get(doc_type) if doc_type else None
    if terminal is None:
        terminal = _ANY_TERMINAL
    return canonical in terminal
