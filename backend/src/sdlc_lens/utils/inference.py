"""Document type and ID inference from filename patterns."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from sdlc_lens.utils.sdlc_ids import (
    DIR_TO_TYPE,
    SINGLETON_STEMS,
    id_head,
    type_for_prefix,
)


@dataclass(frozen=True)
class InferenceResult:
    """Result of type and ID inference for a document."""

    doc_type: str
    doc_id: str


def infer_type_and_id(filename: str, rel_path: str) -> InferenceResult | None:
    """Infer document type and ID from filename and relative path.

    Priority order:
    1. ``_index.md`` -> None (skip)
    2. Id prefix at the start of the stem (sequential ``US0001`` / ``CR-0003`` or v3
       ULID ``BG-01KX8B82``) whose prefix is a known artefact type.
    3. Singleton filename (``prd.md``, ``pvd.md``, ``decisions.md``, ...).
    4. Directory fallback (``change-requests/`` -> cr, ``rfcs/`` -> rfc, ...).
    5. Default: type ``other``, id = filename stem.

    The ``doc_id`` is the full filename stem (not just the id prefix) to avoid
    collisions between artefacts that share a numeric/ULID head.

    Args:
        filename: The filename (e.g. ``"CR-01KX8B82-token.md"``).
        rel_path: Relative path from project root (e.g. ``"change-requests/CR...md"``).

    Returns:
        InferenceResult with doc_type and doc_id, or None for ``_index.md``.
    """
    # 1. Skip _index.md
    if filename == "_index.md":
        return None

    stem = PurePosixPath(filename).stem

    # 2. Id prefix at the start of the stem (sequential or v3 ULID)
    head = id_head(stem)
    if head is not None:
        doc_type = type_for_prefix(head)
        if doc_type is not None:
            return InferenceResult(doc_type=doc_type, doc_id=stem)

    # 3. Singleton filenames
    stem_lower = stem.lower()
    if stem_lower in SINGLETON_STEMS:
        return InferenceResult(doc_type=SINGLETON_STEMS[stem_lower], doc_id=stem_lower)

    # 4. Directory fallback (nearest matching ancestor dir)
    path = PurePosixPath(rel_path)
    for part in path.parts[:-1]:  # skip the filename itself
        if part in DIR_TO_TYPE:
            return InferenceResult(doc_type=DIR_TO_TYPE[part], doc_id=stem)

    # 5. Default
    return InferenceResult(doc_type="other", doc_id=stem)
