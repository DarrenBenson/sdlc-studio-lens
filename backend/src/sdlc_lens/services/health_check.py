"""Health check rules engine for project documentation analysis.

Analyses a project's documents for completeness, consistency, quality,
and integrity issues. Returns structured findings suitable for both
human review and AI agent consumption.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sdlc_lens.db.models.document import Document

_DOC_PREFIX_RE = re.compile(r"^([A-Z]{2}\d{4})")
_DONE_STATUSES = {"Done", "Complete"}
_INACTIVE_STATUSES = {"Done", "Complete", "Won't Implement", "Superseded"}

# Matches **Epic** (with optional colon inside/outside bold) followed by a doc ID
_CONTENT_EPIC_RE = re.compile(r"\*\*Epic:?\*\*:?\s*.*?([A-Z]{2}\d{4})")


def _is_archive(doc: Document) -> bool:
    """Check if a document is an archive file (not a real SDLC artefact)."""
    return doc.doc_id.startswith("_")


def _has_epic_in_content(doc: Document) -> bool:
    """Check if document content contains an **Epic:** field reference."""
    if not doc.content:
        return False
    return _CONTENT_EPIC_RE.search(doc.content) is not None


def _is_review_doc(doc: Document) -> bool:
    """Check if a document is a review (misclassified by file path)."""
    path = doc.file_path or ""
    return "/reviews/" in path or path.startswith("reviews/")


@dataclass(frozen=True)
class AffectedDocument:
    """A document referenced by a health finding."""

    doc_id: str
    doc_type: str
    title: str


@dataclass(frozen=True)
class HealthFinding:
    """A single health check finding."""

    rule_id: str
    severity: str  # critical | high | medium | low
    category: str  # completeness | consistency | quality | integrity
    message: str
    affected_documents: list[AffectedDocument]
    suggested_fix: str


@dataclass
class HealthCheckResult:
    """Complete health check result for a project."""

    project_slug: str
    checked_at: str
    total_documents: int
    findings: list[HealthFinding] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    score: int = 100


def _affected(doc: Document) -> AffectedDocument:
    """Build an AffectedDocument from a Document model."""
    return AffectedDocument(doc_id=doc.doc_id, doc_type=doc.doc_type, title=doc.title)


def _prefix(doc_id: str) -> str:
    """Extract clean prefix from doc_id (e.g. 'EP0001' from 'EP0001-git-sync').

    Returns the full doc_id if no prefix pattern matches.
    """
    m = _DOC_PREFIX_RE.match(doc_id)
    return m.group(1) if m else doc_id


def _build_prefix_set(docs: list[Document]) -> set[str]:
    """Build a set of doc_id prefixes for fast lookup."""
    return {_prefix(d.doc_id) for d in docs}


# ---------------------------------------------------------------------------
# Completeness rules
# ---------------------------------------------------------------------------


def _check_missing_prd(docs: list[Document]) -> list[HealthFinding]:
    """MISSING_PRD: project has no PRD document."""
    prd_docs = [d for d in docs if d.doc_type == "prd"]
    if not prd_docs and docs:
        return [
            HealthFinding(
                rule_id="MISSING_PRD",
                severity="critical",
                category="completeness",
                message="Project has no PRD document.",
                affected_documents=[],
                suggested_fix=(
                    "Create a PRD document defining the product requirements "
                    "for this project."
                ),
            )
        ]
    return []


def _check_missing_trd(docs: list[Document]) -> list[HealthFinding]:
    """MISSING_TRD: project has no TRD document."""
    trd_docs = [d for d in docs if d.doc_type == "trd"]
    if not trd_docs and docs:
        return [
            HealthFinding(
                rule_id="MISSING_TRD",
                severity="high",
                category="completeness",
                message="Project has no TRD document.",
                affected_documents=[],
                suggested_fix=(
                    "Create a TRD document defining the technical "
                    "requirements and architecture."
                ),
            )
        ]
    return []


def _check_missing_plan(docs: list[Document]) -> list[HealthFinding]:
    """MISSING_PLAN: story has no associated plan.

    Skips inactive stories (Done, Complete, Won't Implement) since plans
    are pre-implementation artefacts with no retroactive value.
    """
    stories = [
        d
        for d in docs
        if d.doc_type == "story"
        and not _is_archive(d)
        and d.status not in _INACTIVE_STATUSES
    ]
    plans = [d for d in docs if d.doc_type == "plan"]
    plan_stories = {p.story for p in plans if p.story}

    findings = []
    for story in stories:
        story_pfx = _prefix(story.doc_id)
        if story_pfx not in plan_stories:
            findings.append(
                HealthFinding(
                    rule_id="MISSING_PLAN",
                    severity="medium",
                    category="completeness",
                    message=f"Story '{story.title}' has no associated plan.",
                    affected_documents=[_affected(story)],
                    suggested_fix=(
                        f"Create a plan document for story {story.doc_id} "
                        f"with acceptance criteria coverage."
                    ),
                )
            )
    return findings


def _check_missing_test_spec(docs: list[Document]) -> list[HealthFinding]:
    """MISSING_TEST_SPEC: story has no associated test-spec.

    Skips inactive stories and stories whose epic has an epic-scoped
    test-spec (covering multiple stories by design).
    """
    stories = [
        d
        for d in docs
        if d.doc_type == "story"
        and not _is_archive(d)
        and d.status not in _INACTIVE_STATUSES
    ]
    test_specs = [d for d in docs if d.doc_type == "test-spec"]
    tested_stories = {ts.story for ts in test_specs if ts.story}

    # Build set of epics covered by epic-scoped test-specs
    epics_with_specs: set[str] = set()
    for ts in test_specs:
        if not ts.story and ts.epic:
            epics_with_specs.add(ts.epic)

    findings = []
    for story in stories:
        story_pfx = _prefix(story.doc_id)
        if story_pfx not in tested_stories:
            # Skip if the story's epic has an epic-scoped test-spec
            if story.epic and story.epic in epics_with_specs:
                continue
            findings.append(
                HealthFinding(
                    rule_id="MISSING_TEST_SPEC",
                    severity="medium",
                    category="completeness",
                    message=f"Story '{story.title}' has no associated test-spec.",
                    affected_documents=[_affected(story)],
                    suggested_fix=(
                        f"Create a test-spec document for story {story.doc_id} "
                        f"with test cases covering the acceptance criteria."
                    ),
                )
            )
    return findings


def _check_epic_no_stories(docs: list[Document]) -> list[HealthFinding]:
    """EPIC_NO_STORIES: epic has zero child stories."""
    epics = [d for d in docs if d.doc_type == "epic" and not _is_review_doc(d)]
    stories = [d for d in docs if d.doc_type == "story"]
    epics_with_stories = {s.epic for s in stories if s.epic}

    findings = []
    for epic in epics:
        epic_pfx = _prefix(epic.doc_id)
        if epic_pfx not in epics_with_stories:
            findings.append(
                HealthFinding(
                    rule_id="EPIC_NO_STORIES",
                    severity="high",
                    category="completeness",
                    message=f"Epic '{epic.title}' has no child stories.",
                    affected_documents=[_affected(epic)],
                    suggested_fix=(
                        f"Create story documents under epic {epic.doc_id} "
                        f"to break down the work into implementable units."
                    ),
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Consistency rules
# ---------------------------------------------------------------------------


def _check_story_no_epic(docs: list[Document]) -> list[HealthFinding]:
    """STORY_NO_EPIC: story has no epic reference."""
    stories = [d for d in docs if d.doc_type == "story" and not _is_archive(d)]
    findings = []
    for story in stories:
        if not story.epic and not _has_epic_in_content(story):
            findings.append(
                HealthFinding(
                    rule_id="STORY_NO_EPIC",
                    severity="high",
                    category="consistency",
                    message=f"Story '{story.title}' has no epic reference.",
                    affected_documents=[_affected(story)],
                    suggested_fix=(
                        f"Add an epic reference to story {story.doc_id} "
                        f"in its frontmatter metadata."
                    ),
                )
            )
    return findings


def _check_plan_no_story(docs: list[Document]) -> list[HealthFinding]:
    """PLAN_NO_STORY: plan has no story reference."""
    plans = [d for d in docs if d.doc_type == "plan"]
    findings = []
    for plan in plans:
        if not plan.story:
            findings.append(
                HealthFinding(
                    rule_id="PLAN_NO_STORY",
                    severity="medium",
                    category="consistency",
                    message=f"Plan '{plan.title}' has no story reference.",
                    affected_documents=[_affected(plan)],
                    suggested_fix=(
                        f"Add a story reference to plan {plan.doc_id} "
                        f"in its frontmatter metadata."
                    ),
                )
            )
    return findings


def _check_test_spec_no_story(docs: list[Document]) -> list[HealthFinding]:
    """TEST_SPEC_NO_STORY: test-spec has no story reference.

    Skips epic-scoped test-specs that reference an epic instead of a
    single story (they cover multiple stories by design).
    """
    test_specs = [d for d in docs if d.doc_type == "test-spec"]
    findings = []
    for ts in test_specs:
        if not ts.story:
            # Skip if the test-spec is epic-scoped (has an epic reference)
            if ts.epic or _has_epic_in_content(ts):
                continue
            findings.append(
                HealthFinding(
                    rule_id="TEST_SPEC_NO_STORY",
                    severity="medium",
                    category="consistency",
                    message=f"Test-spec '{ts.title}' has no story reference.",
                    affected_documents=[_affected(ts)],
                    suggested_fix=(
                        f"Add a story reference to test-spec {ts.doc_id} "
                        f"in its frontmatter metadata."
                    ),
                )
            )
    return findings


def _check_orphan_reference(docs: list[Document]) -> list[HealthFinding]:
    """ORPHAN_REFERENCE: document references non-existent parent."""
    prefixes = _build_prefix_set(docs)
    findings = []

    for doc in docs:
        # Check epic references (stored as clean prefix e.g. "EP0001")
        if doc.epic and doc.epic not in prefixes:
            findings.append(
                HealthFinding(
                    rule_id="ORPHAN_REFERENCE",
                    severity="medium",
                    category="consistency",
                    message=(
                        f"Document '{doc.title}' references non-existent "
                        f"epic '{doc.epic}'."
                    ),
                    affected_documents=[_affected(doc)],
                    suggested_fix=(
                        f"Update the epic reference in {doc.doc_id} to point to "
                        f"an existing epic, or create epic {doc.epic}."
                    ),
                )
            )
        # Check story references (stored as clean prefix e.g. "US0001")
        if doc.story and doc.story not in prefixes:
            findings.append(
                HealthFinding(
                    rule_id="ORPHAN_REFERENCE",
                    severity="medium",
                    category="consistency",
                    message=(
                        f"Document '{doc.title}' references non-existent "
                        f"story '{doc.story}'."
                    ),
                    affected_documents=[_affected(doc)],
                    suggested_fix=(
                        f"Update the story reference in {doc.doc_id} to point to "
                        f"an existing story, or create story {doc.story}."
                    ),
                )
            )

    return findings


def _check_status_mismatch(docs: list[Document]) -> list[HealthFinding]:
    """STATUS_MISMATCH: epic marked Done but has non-Done children.

    Treats Won't Implement as a terminal status (not incomplete).
    """
    epics = [d for d in docs if d.doc_type == "epic"]
    stories = [d for d in docs if d.doc_type == "story"]

    findings = []
    for epic in epics:
        if epic.status not in _DONE_STATUSES:
            continue
        epic_pfx = _prefix(epic.doc_id)
        child_stories = [s for s in stories if s.epic == epic_pfx]
        incomplete = [
            s for s in child_stories if s.status not in _INACTIVE_STATUSES
        ]
        if incomplete:
            findings.append(
                HealthFinding(
                    rule_id="STATUS_MISMATCH",
                    severity="low",
                    category="consistency",
                    message=(
                        f"Epic '{epic.title}' is marked Done but has "
                        f"{len(incomplete)} incomplete child stories."
                    ),
                    affected_documents=[_affected(epic)]
                    + [_affected(s) for s in incomplete],
                    suggested_fix=(
                        f"Either update the incomplete stories under {epic.doc_id} "
                        f"to Done, or change the epic status to reflect the actual state."
                    ),
                )
            )
    return findings


def _check_stale_artefact_status(docs: list[Document]) -> list[HealthFinding]:
    """STALE_ARTEFACT_STATUS: document not completed but parent story is Done.

    Flags plans, test-specs, workflows, and other artefacts that reference
    a completed story but still have a non-terminal status themselves.
    """
    # Build lookup of story prefix -> status
    story_status: dict[str, str] = {}
    for d in docs:
        if d.doc_type == "story" and d.status:
            story_status[_prefix(d.doc_id)] = d.status

    # Check non-story documents that reference a story
    findings = []
    for doc in docs:
        if doc.doc_type == "story" or not doc.story:
            continue
        if doc.status in _INACTIVE_STATUSES:
            continue
        parent_status = story_status.get(doc.story)
        if parent_status and parent_status in _INACTIVE_STATUSES:
            findings.append(
                HealthFinding(
                    rule_id="STALE_ARTEFACT_STATUS",
                    severity="low",
                    category="consistency",
                    message=(
                        f"{doc.doc_type.title()} '{doc.title}' is "
                        f"'{doc.status}' but its story is '{parent_status}'."
                    ),
                    affected_documents=[_affected(doc)],
                    suggested_fix=(
                        f"Update the status of {doc.doc_id} to Done to "
                        f"match its completed story."
                    ),
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Quality rules
# ---------------------------------------------------------------------------


_PROJECT_LEVEL_TYPES = {"prd", "trd", "tsd", "personas"}
_PROJECT_LEVEL_DOC_IDS = {"brand-guide", "personas"}


def _is_project_level(doc: Document) -> bool:
    """Check if a document is a project-level reference document."""
    return doc.doc_type in _PROJECT_LEVEL_TYPES or doc.doc_id in _PROJECT_LEVEL_DOC_IDS


def _check_missing_status(docs: list[Document]) -> list[HealthFinding]:
    """MISSING_STATUS: document has no status set.

    Skips project-level reference documents (PRD, TRD, TSD, etc.) which
    evolve continuously and don't follow the Draft→Done lifecycle.
    """
    findings = []
    for doc in docs:
        if _is_project_level(doc):
            continue
        if not doc.status:
            findings.append(
                HealthFinding(
                    rule_id="MISSING_STATUS",
                    severity="high",
                    category="quality",
                    message=f"Document '{doc.title}' has no status set.",
                    affected_documents=[_affected(doc)],
                    suggested_fix=(
                        f"Add a status field to {doc.doc_id} frontmatter "
                        f"(e.g. Draft, In Progress, Done)."
                    ),
                )
            )
    return findings


def _check_missing_owner(docs: list[Document]) -> list[HealthFinding]:
    """MISSING_OWNER: story/epic has no owner assigned."""
    applicable = [
        d
        for d in docs
        if d.doc_type in ("story", "epic")
        and not _is_archive(d)
        and not _is_review_doc(d)
    ]
    findings = []
    for doc in applicable:
        if not doc.owner:
            findings.append(
                HealthFinding(
                    rule_id="MISSING_OWNER",
                    severity="medium",
                    category="quality",
                    message=f"{doc.doc_type.title()} '{doc.title}' has no owner assigned.",
                    affected_documents=[_affected(doc)],
                    suggested_fix=(
                        f"Assign an owner to {doc.doc_id} in its frontmatter metadata."
                    ),
                )
            )
    return findings


def _check_missing_priority(docs: list[Document]) -> list[HealthFinding]:
    """MISSING_PRIORITY: story has no priority set.

    Skips inactive stories since priority is a planning field with
    no value on completed work.
    """
    stories = [
        d
        for d in docs
        if d.doc_type == "story"
        and not _is_archive(d)
        and d.status not in _INACTIVE_STATUSES
    ]
    findings = []
    for story in stories:
        if not story.priority:
            findings.append(
                HealthFinding(
                    rule_id="MISSING_PRIORITY",
                    severity="low",
                    category="quality",
                    message=f"Story '{story.title}' has no priority set.",
                    affected_documents=[_affected(story)],
                    suggested_fix=(
                        f"Add a priority field to {story.doc_id} frontmatter "
                        f"(e.g. P0, P1, P2)."
                    ),
                )
            )
    return findings


def _check_missing_story_points(docs: list[Document]) -> list[HealthFinding]:
    """MISSING_STORY_POINTS: story has no story points.

    Skips inactive stories since story points are a planning field.
    """
    stories = [
        d
        for d in docs
        if d.doc_type == "story"
        and not _is_archive(d)
        and d.status not in _INACTIVE_STATUSES
    ]
    findings = []
    for story in stories:
        if story.story_points is None:
            findings.append(
                HealthFinding(
                    rule_id="MISSING_STORY_POINTS",
                    severity="low",
                    category="quality",
                    message=f"Story '{story.title}' has no story points.",
                    affected_documents=[_affected(story)],
                    suggested_fix=(
                        f"Add story_points to {story.doc_id} frontmatter "
                        f"to help with sprint planning."
                    ),
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Integrity rules
# ---------------------------------------------------------------------------


def _check_duplicate_doc_id(docs: list[Document]) -> list[HealthFinding]:
    """DUPLICATE_DOC_ID: multiple documents share the same doc_id prefix."""
    seen: dict[str, list[Document]] = {}
    for doc in docs:
        # Use full doc_id as key (duplicates come from same doc_id on different types)
        key = doc.doc_id
        seen.setdefault(key, []).append(doc)

    findings = []
    for doc_id, group in seen.items():
        if len(group) > 1:
            findings.append(
                HealthFinding(
                    rule_id="DUPLICATE_DOC_ID",
                    severity="critical",
                    category="integrity",
                    message=(
                        f"Multiple documents share doc_id '{doc_id}': "
                        f"{', '.join(d.doc_type for d in group)}."
                    ),
                    affected_documents=[_affected(d) for d in group],
                    suggested_fix=(
                        f"Rename the duplicate documents so each has a unique doc_id. "
                        f"Affected: {', '.join(d.file_path for d in group)}."
                    ),
                )
            )
    return findings


def _check_empty_content(docs: list[Document]) -> list[HealthFinding]:
    """EMPTY_CONTENT: document has no meaningful content."""
    findings = []
    for doc in docs:
        stripped = doc.content.strip() if doc.content else ""
        # Consider content empty if it's just a heading or less than 50 chars
        if len(stripped) < 50:
            findings.append(
                HealthFinding(
                    rule_id="EMPTY_CONTENT",
                    severity="high",
                    category="integrity",
                    message=f"Document '{doc.title}' has no meaningful content.",
                    affected_documents=[_affected(doc)],
                    suggested_fix=(
                        f"Add content to {doc.doc_id} ({doc.file_path}). "
                        f"The document appears to be empty or a stub."
                    ),
                )
            )
    return findings


def _check_stale_document(
    docs: list[Document],
    now: datetime.datetime | None = None,
) -> list[HealthFinding]:
    """STALE_DOCUMENT: document not synced in 30+ days."""
    if now is None:
        now = datetime.datetime.now(tz=datetime.UTC)

    threshold = now - datetime.timedelta(days=30)
    findings = []
    for doc in docs:
        synced = doc.synced_at
        # Make offset-aware if naive
        if synced.tzinfo is None:
            synced = synced.replace(tzinfo=datetime.UTC)
        if synced < threshold:
            findings.append(
                HealthFinding(
                    rule_id="STALE_DOCUMENT",
                    severity="low",
                    category="integrity",
                    message=(
                        f"Document '{doc.title}' has not been synced in over 30 days "
                        f"(last synced {synced.date().isoformat()})."
                    ),
                    affected_documents=[_affected(doc)],
                    suggested_fix=(
                        f"Review and re-sync {doc.doc_id} to ensure it is still current."
                    ),
                )
            )
    return findings


# ---------------------------------------------------------------------------
# All rules in execution order
# ---------------------------------------------------------------------------

_ALL_RULES = [
    # Completeness
    _check_missing_prd,
    _check_missing_trd,
    _check_missing_plan,
    _check_missing_test_spec,
    _check_epic_no_stories,
    # Consistency
    _check_story_no_epic,
    _check_plan_no_story,
    _check_test_spec_no_story,
    _check_orphan_reference,
    _check_status_mismatch,
    _check_stale_artefact_status,
    # Quality
    _check_missing_status,
    _check_missing_owner,
    _check_missing_priority,
    _check_missing_story_points,
    # Integrity
    _check_duplicate_doc_id,
    _check_empty_content,
]


_SEVERITY_WEIGHTS = {
    "critical": 15,
    "high": 5,
    "medium": 2,
    "low": 1,
}


def run_health_check(
    documents: list[Document],
    project_slug: str,
    now: datetime.datetime | None = None,
) -> HealthCheckResult:
    """Run all health check rules against a list of documents.

    Pure function - no database access. Pass the full document list
    for the project.
    """
    findings: list[HealthFinding] = []

    for rule_fn in _ALL_RULES:
        findings.extend(rule_fn(documents))

    # Stale document check needs timestamp
    findings.extend(_check_stale_document(documents, now=now))

    # Build severity summary
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        summary[finding.severity] = summary.get(finding.severity, 0) + 1

    # Calculate health score
    penalty = sum(
        count * _SEVERITY_WEIGHTS.get(sev, 0) for sev, count in summary.items()
    )
    score = max(0, min(100, 100 - penalty))

    check_time = now or datetime.datetime.now(tz=datetime.UTC)

    return HealthCheckResult(
        project_slug=project_slug,
        checked_at=check_time.isoformat(),
        total_documents=len(documents),
        findings=findings,
        summary=summary,
        score=score,
    )
