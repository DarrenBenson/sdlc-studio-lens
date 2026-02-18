"""Unit tests for the health check rules engine.

Tests all 17 rules across completeness, consistency, quality, and integrity
categories.
"""

import datetime

from sdlc_lens.db.models.document import Document
from sdlc_lens.services.health_check import (
    HealthCheckResult,
    run_health_check,
)

_NOW = datetime.datetime(2026, 2, 18, 12, 0, 0, tzinfo=datetime.UTC)
_RECENT = datetime.datetime(2026, 2, 17, 12, 0, 0, tzinfo=datetime.UTC)
_STALE = datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=datetime.UTC)


def _doc(
    doc_type: str = "story",
    doc_id: str = "US0001",
    title: str = "Test Story",
    status: str | None = "Draft",
    owner: str | None = "Darren",
    priority: str | None = "P0",
    story_points: int | None = 5,
    epic: str | None = None,
    story: str | None = None,
    content: str = (
        "# Test Story\n\nThis is a test story with enough content "
        "to pass the empty check."
    ),
    synced_at: datetime.datetime | None = None,
    file_path: str | None = None,
) -> Document:
    """Create a Document instance for testing (not persisted)."""
    return Document(
        project_id=1,
        doc_type=doc_type,
        doc_id=doc_id,
        title=title,
        status=status,
        owner=owner,
        priority=priority,
        story_points=story_points,
        epic=epic,
        story=story,
        content=content,
        file_path=file_path or f"{doc_type}s/{doc_id}.md",
        file_hash="a" * 64,
        synced_at=synced_at or _RECENT,
    )


def _run(docs: list[Document]) -> HealthCheckResult:
    """Run health check with standard test parameters."""
    return run_health_check(docs, project_slug="test-project", now=_NOW)


def _find(result: HealthCheckResult, rule_id: str):
    """Get all findings with the given rule_id."""
    return [f for f in result.findings if f.rule_id == rule_id]


# ---------------------------------------------------------------------------
# Empty project
# ---------------------------------------------------------------------------


class TestEmptyProject:
    def test_empty_project_returns_perfect_score(self):
        result = _run([])
        assert result.score == 100
        assert result.total_documents == 0
        assert result.findings == []

    def test_result_metadata(self):
        result = _run([])
        assert result.project_slug == "test-project"
        assert result.checked_at == _NOW.isoformat()


# ---------------------------------------------------------------------------
# Completeness rules
# ---------------------------------------------------------------------------


class TestMissingPrd:
    def test_fires_when_no_prd(self):
        docs = [_doc(doc_type="story", doc_id="US0001")]
        result = _run(docs)
        findings = _find(result, "MISSING_PRD")
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert findings[0].category == "completeness"

    def test_does_not_fire_when_prd_exists(self):
        docs = [
            _doc(doc_type="prd", doc_id="PRD-main", title="Product Requirements"),
            _doc(doc_type="story", doc_id="US0001"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_PRD") == []

    def test_does_not_fire_for_empty_project(self):
        result = _run([])
        assert _find(result, "MISSING_PRD") == []


class TestMissingTrd:
    def test_fires_when_no_trd(self):
        docs = [_doc(doc_type="story", doc_id="US0001")]
        result = _run(docs)
        findings = _find(result, "MISSING_TRD")
        assert len(findings) == 1
        assert findings[0].severity == "high"

    def test_does_not_fire_when_trd_exists(self):
        docs = [
            _doc(doc_type="trd", doc_id="TRD-main", title="Technical Requirements"),
            _doc(doc_type="story", doc_id="US0001"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_TRD") == []


class TestMissingPlan:
    def test_fires_for_story_without_plan(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", title="My Story"),
        ]
        result = _run(docs)
        findings = _find(result, "MISSING_PLAN")
        assert len(findings) == 1
        assert "US0001" in findings[0].affected_documents[0].doc_id

    def test_does_not_fire_when_plan_exists(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001"),
            _doc(doc_type="plan", doc_id="PL0001", story="US0001"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_PLAN") == []

    def test_matches_by_prefix(self):
        """Plan references clean prefix, story has full doc_id."""
        docs = [
            _doc(doc_type="story", doc_id="US0001-register-project"),
            _doc(doc_type="plan", doc_id="PL0001-plan", story="US0001"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_PLAN") == []

    def test_skips_done_story(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="Done"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_PLAN") == []

    def test_skips_wont_implement_story(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="Won't Implement"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_PLAN") == []

    def test_fires_for_in_progress_story(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="In Progress"),
        ]
        result = _run(docs)
        findings = _find(result, "MISSING_PLAN")
        assert len(findings) == 1
        assert findings[0].severity == "medium"

    def test_skips_archive_files(self):
        docs = [_doc(doc_type="story", doc_id="_archive-v1", title="Archive")]
        result = _run(docs)
        assert _find(result, "MISSING_PLAN") == []


class TestMissingTestSpec:
    def test_fires_for_story_without_test_spec(self):
        docs = [_doc(doc_type="story", doc_id="US0001")]
        result = _run(docs)
        findings = _find(result, "MISSING_TEST_SPEC")
        assert len(findings) == 1

    def test_does_not_fire_when_test_spec_exists(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001"),
            _doc(doc_type="test-spec", doc_id="TS0001", story="US0001"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_TEST_SPEC") == []

    def test_skips_done_story(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="Complete"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_TEST_SPEC") == []

    def test_skips_wont_implement_story(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="Won't Implement"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_TEST_SPEC") == []

    def test_skips_story_covered_by_epic_scoped_spec(self):
        """Story under an epic with an epic-scoped test-spec is covered."""
        docs = [
            _doc(doc_type="story", doc_id="US0001", epic="EP0001"),
            _doc(doc_type="test-spec", doc_id="TS0001", story=None, epic="EP0001"),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_TEST_SPEC") == []

    def test_skips_archive_files(self):
        docs = [_doc(doc_type="story", doc_id="_archive-v2-done", title="Archive")]
        result = _run(docs)
        assert _find(result, "MISSING_TEST_SPEC") == []


class TestEpicNoStories:
    def test_fires_for_epic_without_stories(self):
        docs = [_doc(doc_type="epic", doc_id="EP0001", title="Lonely Epic")]
        result = _run(docs)
        findings = _find(result, "EPIC_NO_STORIES")
        assert len(findings) == 1
        assert findings[0].severity == "high"

    def test_does_not_fire_when_stories_exist(self):
        docs = [
            _doc(doc_type="epic", doc_id="EP0001"),
            _doc(doc_type="story", doc_id="US0001", epic="EP0001"),
        ]
        result = _run(docs)
        assert _find(result, "EPIC_NO_STORIES") == []

    def test_matches_by_prefix(self):
        """Epic has full doc_id, stories reference clean prefix."""
        docs = [
            _doc(doc_type="epic", doc_id="EP0001-git-repo-sync"),
            _doc(doc_type="story", doc_id="US0001", epic="EP0001"),
        ]
        result = _run(docs)
        assert _find(result, "EPIC_NO_STORIES") == []

    def test_skips_review_docs(self):
        """Review docs in reviews/ are not real epics."""
        docs = [
            _doc(
                doc_type="epic",
                doc_id="EP0004-remediation-review",
                title="Code Review: EP0004",
                file_path="reviews/EP0004-remediation-review.md",
            )
        ]
        result = _run(docs)
        assert _find(result, "EPIC_NO_STORIES") == []


# ---------------------------------------------------------------------------
# Consistency rules
# ---------------------------------------------------------------------------


class TestStoryNoEpic:
    def test_fires_for_story_without_epic(self):
        docs = [_doc(doc_type="story", doc_id="US0001", epic=None)]
        result = _run(docs)
        findings = _find(result, "STORY_NO_EPIC")
        assert len(findings) == 1
        assert findings[0].severity == "high"

    def test_does_not_fire_when_epic_set(self):
        docs = [_doc(doc_type="story", doc_id="US0001", epic="EP0001")]
        result = _run(docs)
        assert _find(result, "STORY_NO_EPIC") == []

    def test_does_not_fire_when_epic_in_content(self):
        """Epic field present in content but not parsed into DB column."""
        content = (
            "# US0198: Package Held-Back Detection\n\n"
            "> **Epic:** [EP0001 - Core Monitoring]"
            "(../epics/EP0001-core-monitoring.md)\n"
            "> **Status:** Done\n\n"
            "This story covers detection of held-back packages."
        )
        docs = [
            _doc(
                doc_type="story",
                doc_id="US0198-package-held-back-detection",
                epic=None,
                content=content,
            )
        ]
        result = _run(docs)
        assert _find(result, "STORY_NO_EPIC") == []

    def test_skips_archive_files(self):
        """Archive files (doc_id starting with _) are not flagged."""
        docs = [
            _doc(
                doc_type="story",
                doc_id="_archive-v1",
                title="v1.0 Stories Archive",
                epic=None,
            )
        ]
        result = _run(docs)
        assert _find(result, "STORY_NO_EPIC") == []


class TestPlanNoStory:
    def test_fires_for_plan_without_story(self):
        docs = [_doc(doc_type="plan", doc_id="PL0001", story=None)]
        result = _run(docs)
        findings = _find(result, "PLAN_NO_STORY")
        assert len(findings) == 1

    def test_does_not_fire_when_story_set(self):
        docs = [_doc(doc_type="plan", doc_id="PL0001", story="US0001")]
        result = _run(docs)
        assert _find(result, "PLAN_NO_STORY") == []


class TestTestSpecNoStory:
    def test_fires_for_test_spec_without_story(self):
        docs = [_doc(doc_type="test-spec", doc_id="TS0001", story=None)]
        result = _run(docs)
        findings = _find(result, "TEST_SPEC_NO_STORY")
        assert len(findings) == 1

    def test_does_not_fire_when_story_set(self):
        docs = [_doc(doc_type="test-spec", doc_id="TS0001", story="US0001")]
        result = _run(docs)
        assert _find(result, "TEST_SPEC_NO_STORY") == []

    def test_skips_epic_scoped_test_spec_with_epic_column(self):
        """Test-specs covering multiple stories reference an epic instead."""
        docs = [
            _doc(doc_type="test-spec", doc_id="TS0001", story=None, epic="EP0001")
        ]
        result = _run(docs)
        assert _find(result, "TEST_SPEC_NO_STORY") == []

    def test_skips_epic_scoped_test_spec_with_epic_in_content(self):
        """Epic reference in content but not in DB column."""
        content = (
            "# TS0001: Core Monitoring API Tests\n\n"
            "> **Epic:** [EP0001 - Core Monitoring]"
            "(../epics/EP0001-core-monitoring.md)\n\n"
            "This test spec covers multiple stories."
        )
        docs = [
            _doc(
                doc_type="test-spec",
                doc_id="TS0001",
                story=None,
                epic=None,
                content=content,
            )
        ]
        result = _run(docs)
        assert _find(result, "TEST_SPEC_NO_STORY") == []


class TestOrphanReference:
    def test_fires_for_orphan_epic_reference(self):
        docs = [_doc(doc_type="story", doc_id="US0001", epic="EP9999")]
        result = _run(docs)
        findings = _find(result, "ORPHAN_REFERENCE")
        assert len(findings) == 1
        assert "EP9999" in findings[0].message

    def test_fires_for_orphan_story_reference(self):
        docs = [_doc(doc_type="plan", doc_id="PL0001", story="US9999")]
        result = _run(docs)
        findings = _find(result, "ORPHAN_REFERENCE")
        assert len(findings) == 1
        assert "US9999" in findings[0].message

    def test_does_not_fire_for_valid_references(self):
        docs = [
            _doc(doc_type="epic", doc_id="EP0001"),
            _doc(doc_type="story", doc_id="US0001", epic="EP0001"),
        ]
        result = _run(docs)
        assert _find(result, "ORPHAN_REFERENCE") == []

    def test_matches_by_prefix(self):
        """References to clean prefix match full doc_ids."""
        docs = [
            _doc(doc_type="epic", doc_id="EP0001-git-sync"),
            _doc(doc_type="story", doc_id="US0001-register", epic="EP0001"),
        ]
        result = _run(docs)
        assert _find(result, "ORPHAN_REFERENCE") == []


class TestStatusMismatch:
    def test_fires_when_done_epic_has_incomplete_children(self):
        docs = [
            _doc(doc_type="epic", doc_id="EP0001", status="Done"),
            _doc(doc_type="story", doc_id="US0001", status="Done", epic="EP0001"),
            _doc(
                doc_type="story",
                doc_id="US0002",
                status="In Progress",
                epic="EP0001",
            ),
        ]
        result = _run(docs)
        findings = _find(result, "STATUS_MISMATCH")
        assert len(findings) == 1
        assert findings[0].severity == "low"
        # Should list the epic + incomplete story
        assert len(findings[0].affected_documents) == 2

    def test_does_not_fire_when_all_children_done(self):
        docs = [
            _doc(doc_type="epic", doc_id="EP0001", status="Done"),
            _doc(doc_type="story", doc_id="US0001", status="Done", epic="EP0001"),
            _doc(doc_type="story", doc_id="US0002", status="Complete", epic="EP0001"),
        ]
        result = _run(docs)
        assert _find(result, "STATUS_MISMATCH") == []

    def test_does_not_fire_when_epic_not_done(self):
        docs = [
            _doc(doc_type="epic", doc_id="EP0001", status="In Progress"),
            _doc(
                doc_type="story",
                doc_id="US0001",
                status="In Progress",
                epic="EP0001",
            ),
        ]
        result = _run(docs)
        assert _find(result, "STATUS_MISMATCH") == []

    def test_matches_children_by_prefix(self):
        """Epic with full doc_id still finds children by prefix."""
        docs = [
            _doc(
                doc_type="epic",
                doc_id="EP0001-git-sync",
                status="Done",
            ),
            _doc(
                doc_type="story",
                doc_id="US0001",
                status="In Progress",
                epic="EP0001",
            ),
        ]
        result = _run(docs)
        findings = _find(result, "STATUS_MISMATCH")
        assert len(findings) == 1

    def test_wont_implement_is_terminal(self):
        """Won't Implement is a terminal status, not incomplete."""
        docs = [
            _doc(doc_type="epic", doc_id="EP0001", status="Done"),
            _doc(doc_type="story", doc_id="US0001", status="Done", epic="EP0001"),
            _doc(
                doc_type="story",
                doc_id="US0002",
                status="Won't Implement",
                epic="EP0001",
            ),
        ]
        result = _run(docs)
        assert _find(result, "STATUS_MISMATCH") == []

    def test_superseded_is_terminal(self):
        """Superseded is a terminal status, not incomplete."""
        docs = [
            _doc(doc_type="epic", doc_id="EP0001", status="Done"),
            _doc(doc_type="story", doc_id="US0001", status="Done", epic="EP0001"),
            _doc(
                doc_type="story",
                doc_id="US0002",
                status="Superseded",
                epic="EP0001",
            ),
        ]
        result = _run(docs)
        assert _find(result, "STATUS_MISMATCH") == []


class TestStaleArtefactStatus:
    def test_fires_for_draft_plan_with_done_story(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="Done"),
            _doc(doc_type="plan", doc_id="PL0001", story="US0001", status="Draft"),
        ]
        result = _run(docs)
        findings = _find(result, "STALE_ARTEFACT_STATUS")
        assert len(findings) == 1
        assert findings[0].severity == "low"
        assert "Draft" in findings[0].message
        assert "Done" in findings[0].message

    def test_does_not_fire_when_artefact_also_done(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="Done"),
            _doc(doc_type="plan", doc_id="PL0001", story="US0001", status="Done"),
        ]
        result = _run(docs)
        assert _find(result, "STALE_ARTEFACT_STATUS") == []

    def test_does_not_fire_when_story_not_done(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="In Progress"),
            _doc(doc_type="plan", doc_id="PL0001", story="US0001", status="Draft"),
        ]
        result = _run(docs)
        assert _find(result, "STALE_ARTEFACT_STATUS") == []

    def test_fires_for_in_progress_test_spec(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="Complete"),
            _doc(
                doc_type="test-spec",
                doc_id="TS0001",
                story="US0001",
                status="In Progress",
            ),
        ]
        result = _run(docs)
        findings = _find(result, "STALE_ARTEFACT_STATUS")
        assert len(findings) == 1

    def test_does_not_fire_for_story_documents(self):
        """Stories are not artefacts - they have their own status rules."""
        docs = [
            _doc(doc_type="story", doc_id="US0001", status="Done"),
            _doc(doc_type="story", doc_id="US0002", status="Draft", story="US0001"),
        ]
        result = _run(docs)
        assert _find(result, "STALE_ARTEFACT_STATUS") == []


# ---------------------------------------------------------------------------
# Quality rules
# ---------------------------------------------------------------------------


class TestMissingStatus:
    def test_fires_for_document_without_status(self):
        docs = [_doc(doc_type="story", doc_id="US0001", status=None)]
        result = _run(docs)
        findings = _find(result, "MISSING_STATUS")
        assert len(findings) == 1
        assert findings[0].severity == "high"

    def test_does_not_fire_when_status_set(self):
        docs = [_doc(doc_type="story", doc_id="US0001", status="Draft")]
        result = _run(docs)
        assert _find(result, "MISSING_STATUS") == []

    def test_skips_project_level_docs(self):
        """PRD, TRD, TSD, etc. don't need status fields."""
        docs = [
            _doc(doc_type="trd", doc_id="TRD-main", status=None),
            _doc(doc_type="tsd", doc_id="TSD-main", status=None),
            _doc(doc_type="prd", doc_id="PRD-main", status=None),
            _doc(doc_type="brand-guide", doc_id="brand-guide", status=None),
            _doc(doc_type="personas", doc_id="personas", status=None),
            # brand-guide may be classified as "other" by parser
            _doc(doc_type="other", doc_id="brand-guide", status=None),
        ]
        result = _run(docs)
        assert _find(result, "MISSING_STATUS") == []


class TestMissingOwner:
    def test_fires_for_story_without_owner(self):
        docs = [_doc(doc_type="story", doc_id="US0001", owner=None)]
        result = _run(docs)
        findings = _find(result, "MISSING_OWNER")
        assert len(findings) == 1

    def test_fires_for_epic_without_owner(self):
        docs = [_doc(doc_type="epic", doc_id="EP0001", owner=None)]
        result = _run(docs)
        findings = _find(result, "MISSING_OWNER")
        assert len(findings) == 1

    def test_does_not_fire_for_plan_without_owner(self):
        """Only stories and epics are checked for owner."""
        docs = [_doc(doc_type="plan", doc_id="PL0001", owner=None)]
        result = _run(docs)
        assert _find(result, "MISSING_OWNER") == []

    def test_does_not_fire_when_owner_set(self):
        docs = [_doc(doc_type="story", doc_id="US0001", owner="Darren")]
        result = _run(docs)
        assert _find(result, "MISSING_OWNER") == []

    def test_skips_review_docs(self):
        """Review docs misclassified as epics should not be flagged."""
        docs = [
            _doc(
                doc_type="epic",
                doc_id="EP0004-remediation-review",
                owner=None,
                file_path="reviews/EP0004-remediation-review.md",
            )
        ]
        result = _run(docs)
        assert _find(result, "MISSING_OWNER") == []


class TestMissingPriority:
    def test_fires_for_active_story_without_priority(self):
        docs = [_doc(doc_type="story", doc_id="US0001", priority=None)]
        result = _run(docs)
        findings = _find(result, "MISSING_PRIORITY")
        assert len(findings) == 1
        assert findings[0].severity == "low"

    def test_does_not_fire_when_priority_set(self):
        docs = [_doc(doc_type="story", doc_id="US0001", priority="P1")]
        result = _run(docs)
        assert _find(result, "MISSING_PRIORITY") == []

    def test_skips_done_story(self):
        docs = [_doc(doc_type="story", doc_id="US0001", priority=None, status="Done")]
        result = _run(docs)
        assert _find(result, "MISSING_PRIORITY") == []

    def test_skips_superseded_story(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", priority=None, status="Superseded")
        ]
        result = _run(docs)
        assert _find(result, "MISSING_PRIORITY") == []


class TestMissingStoryPoints:
    def test_fires_for_active_story_without_story_points(self):
        docs = [_doc(doc_type="story", doc_id="US0001", story_points=None)]
        result = _run(docs)
        findings = _find(result, "MISSING_STORY_POINTS")
        assert len(findings) == 1
        assert findings[0].severity == "low"

    def test_does_not_fire_when_story_points_set(self):
        docs = [_doc(doc_type="story", doc_id="US0001", story_points=3)]
        result = _run(docs)
        assert _find(result, "MISSING_STORY_POINTS") == []

    def test_skips_done_story(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", story_points=None, status="Done")
        ]
        result = _run(docs)
        assert _find(result, "MISSING_STORY_POINTS") == []


# ---------------------------------------------------------------------------
# Integrity rules
# ---------------------------------------------------------------------------


class TestDuplicateDocId:
    def test_fires_for_duplicate_doc_ids(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", file_path="stories/US0001.md"),
            _doc(
                doc_type="story",
                doc_id="US0001",
                file_path="stories/US0001-copy.md",
            ),
        ]
        result = _run(docs)
        findings = _find(result, "DUPLICATE_DOC_ID")
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert len(findings[0].affected_documents) == 2

    def test_does_not_fire_for_unique_doc_ids(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001"),
            _doc(doc_type="story", doc_id="US0002"),
        ]
        result = _run(docs)
        assert _find(result, "DUPLICATE_DOC_ID") == []


class TestEmptyContent:
    def test_fires_for_stub_document(self):
        docs = [_doc(doc_type="story", doc_id="US0001", content="# Title")]
        result = _run(docs)
        findings = _find(result, "EMPTY_CONTENT")
        assert len(findings) == 1
        assert findings[0].severity == "high"

    def test_does_not_fire_for_substantial_content(self):
        docs = [
            _doc(
                doc_type="story",
                doc_id="US0001",
                content="# Title\n\nThis document has enough content to pass the check easily.",
            )
        ]
        result = _run(docs)
        assert _find(result, "EMPTY_CONTENT") == []


class TestStaleDocument:
    def test_fires_for_old_document(self):
        docs = [_doc(doc_type="story", doc_id="US0001", synced_at=_STALE)]
        result = _run(docs)
        findings = _find(result, "STALE_DOCUMENT")
        assert len(findings) == 1
        assert findings[0].severity == "low"

    def test_does_not_fire_for_recent_document(self):
        docs = [_doc(doc_type="story", doc_id="US0001", synced_at=_RECENT)]
        result = _run(docs)
        assert _find(result, "STALE_DOCUMENT") == []


# ---------------------------------------------------------------------------
# Score calculation
# ---------------------------------------------------------------------------


class TestScoreCalculation:
    def test_perfect_project(self):
        """Fully documented project scores 100."""
        docs = [
            _doc(doc_type="prd", doc_id="PRD-main", title="Product Requirements"),
            _doc(doc_type="trd", doc_id="TRD-main", title="Technical Requirements"),
            _doc(doc_type="epic", doc_id="EP0001", title="Epic One", status="Done"),
            _doc(
                doc_type="story",
                doc_id="US0001",
                epic="EP0001",
                status="Done",
            ),
            _doc(doc_type="plan", doc_id="PL0001", story="US0001", status="Done"),
            _doc(doc_type="test-spec", doc_id="TS0001", story="US0001", status="Done"),
        ]
        result = _run(docs)
        assert result.score == 100
        assert result.findings == []

    def test_critical_issues_penalise_heavily(self):
        """A critical issue costs 15 points."""
        docs = [
            _doc(doc_type="story", doc_id="US0001", file_path="a.md"),
            _doc(doc_type="story", doc_id="US0001", file_path="b.md"),
        ]
        result = _run(docs)
        criticals = _find(result, "DUPLICATE_DOC_ID")
        assert len(criticals) == 1
        # Score should be reduced by at least 15
        assert result.score <= 85

    def test_score_never_below_zero(self):
        """Score is clamped to 0 minimum."""
        # Create many issues
        docs = [
            _doc(
                doc_type="story",
                doc_id=f"US{i:04d}",
                status=None,
                owner=None,
                priority=None,
                story_points=None,
                epic=None,
            )
            for i in range(20)
        ]
        result = _run(docs)
        assert result.score >= 0

    def test_summary_counts_severities(self):
        docs = [
            _doc(doc_type="story", doc_id="US0001", status=None, owner=None),
        ]
        result = _run(docs)
        assert "high" in result.summary
        assert result.summary["high"] >= 1  # MISSING_STATUS + MISSING_TRD
