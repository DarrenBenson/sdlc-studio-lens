"""Document type and ID inference from filename patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

# Prefix patterns: prefix -> doc_type
_PREFIX_PATTERNS: dict[str, str] = {
    "EP": "epic",
    "US": "story",
    "BG": "bug",
    "PL": "plan",
    "TS": "test-spec",
    "WF": "workflow",
}

# Compiled regex: matches PREFIX followed by 4+ digits at start of filename
_PREFIX_RE = re.compile(
    r"^(" + "|".join(_PREFIX_PATTERNS) + r")(\d{4,})"
)

# Singleton filenames (case-insensitive stem) -> doc_type
_SINGLETONS: dict[str, str] = {
    "prd": "prd",
    "trd": "trd",
    "tsd": "tsd",
    "personas": "personas",
}

# Directory name -> doc_type fallback
_DIR_FALLBACK: dict[str, str] = {
    "epics": "epic",
    "stories": "story",
    "bugs": "bug",
    "plans": "plan",
    "test-specs": "test-spec",
    "workflows": "workflow",
}


@dataclass(frozen=True)
class InferenceResult:
    """Result of type and ID inference for a document."""

    doc_type: str
    doc_id: str


def infer_type_and_id(
    filename: str, rel_path: str
) -> InferenceResult | None:
    """Infer document type and ID from filename and relative path.

    Priority order:
    1. _index.md -> None (skip)
    2. Prefix pattern (EP0001, US0045, etc.)
    3. Singleton filename (prd.md, trd.md, etc.)
    4. Directory fallback (epics/ -> epic, stories/ -> story)
    5. Default: type "other", id = filename stem

    Args:
        filename: The filename (e.g. "EP0001-project-management.md").
        rel_path: Relative path from project root
            (e.g. "epics/EP0001-project-management.md").

    Returns:
        InferenceResult with doc_type and doc_id, or None for
        _index.md files that should be skipped.
    """
    # 1. Skip _index.md
    if filename == "_index.md":
        return None

    stem = PurePosixPath(filename).stem

    # 2. Prefix pattern
    match = _PREFIX_RE.match(stem)
    if match:
        prefix = match.group(1)
        doc_type = _PREFIX_PATTERNS[prefix]
        return InferenceResult(doc_type=doc_type, doc_id=stem)

    # 3. Singleton filenames
    stem_lower = stem.lower()
    if stem_lower in _SINGLETONS:
        return InferenceResult(
            doc_type=_SINGLETONS[stem_lower], doc_id=stem_lower
        )

    # 4. Directory fallback
    path = PurePosixPath(rel_path)
    for part in path.parts[:-1]:  # skip the filename itself
        if part in _DIR_FALLBACK:
            return InferenceResult(
                doc_type=_DIR_FALLBACK[part], doc_id=stem
            )

    # 5. Default
    return InferenceResult(doc_type="other", doc_id=stem)
