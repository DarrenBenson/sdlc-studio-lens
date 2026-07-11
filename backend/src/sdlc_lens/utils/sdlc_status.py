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
DONE_STATUSES = frozenset(
    {"Done", "Complete", "Fixed", "Verified", "Closed", "Accepted"}
)

_LEADING_STRIP = re.compile(r"^[>\s*_`]+")


def _strip_decoration(status: str) -> str:
    """Remove bold/blockquote decoration and any trailing prose after the token.

    ``**Done** - implemented`` -> ``Done``; ``Done · **CR:** ...`` -> ``Done``;
    ``Complete (81/88)`` -> ``Complete``.
    """
    text = _LEADING_STRIP.sub("", status).strip()
    text = text.strip("*_` ")
    # Cut at the first separator that introduces trailing prose.
    for sep in (" - ", " — ", " – ", " · ", " | ", " (", "("):
        idx = text.find(sep)
        if idx != -1:
            text = text[:idx]
    return text.strip("*_` ").strip()


def canonical_status(status: str | None, doc_type: str | None = None) -> str | None:
    """Reduce a raw status value to its vocabulary token, or None.

    Matches the longest vocabulary token that prefixes the decoration-stripped text
    (case-insensitive), so ``In Progress`` wins over ``In``. When ``doc_type`` names a
    known type, that type's vocabulary (plus ``inbox`` for findings) is tried first;
    otherwise the global token set is used. A value that matches no token is returned
    stripped (never dropped), so custom project statuses still display.
    """
    if not status or not status.strip():
        return None
    stripped = _strip_decoration(status)
    if not stripped:
        return None
    lowered = stripped.lower()

    candidates = ALL_STATUSES
    if doc_type in STATUS_VOCAB:
        vocab = list(STATUS_VOCAB[doc_type])
        if doc_type in FINDING_TYPES:
            vocab.append(INBOX_STATUS)
        candidates = sorted(vocab, key=len, reverse=True)

    for token in candidates:
        if lowered == token.lower() or lowered.startswith(token.lower() + " "):
            return token
    return stripped


def is_done(status: str | None, doc_type: str | None = None) -> bool:
    """True when the canonical status counts as done/complete for metrics."""
    canonical = canonical_status(status, doc_type)
    return canonical in DONE_STATUSES if canonical else False
