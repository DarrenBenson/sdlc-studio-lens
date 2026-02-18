"""Relationship data extraction tests.

Test cases: TC0343-TC0357 from TS0033.
Covers extract_doc_id utility, _STANDARD_FIELDS update, _build_doc_attrs
with clean ID extraction, and integration sync tests.
"""

import textwrap

from sdlc_lens.services.sync_engine import (
    _STANDARD_FIELDS,
    _build_doc_attrs,
    extract_doc_id,
)

# ---------------------------------------------------------------------------
# TC0343-TC0348: extract_doc_id unit tests
# ---------------------------------------------------------------------------


class TestExtractDocId:
    """Unit tests for the extract_doc_id utility function."""

    # TC0343: extracts ID from markdown link with title
    def test_markdown_link_with_title(self) -> None:
        result = extract_doc_id(
            "[EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)"
        )
        assert result == "EP0007"

    def test_markdown_link_story(self) -> None:
        result = extract_doc_id(
            "[US0028: Database Schema](../stories/US0028-database-github-fields.md)"
        )
        assert result == "US0028"

    # TC0344: returns plain ID unchanged
    def test_plain_id(self) -> None:
        assert extract_doc_id("EP0007") == "EP0007"

    def test_plain_id_story(self) -> None:
        assert extract_doc_id("US0028") == "US0028"

    # TC0345: returns None for None input
    def test_none_input(self) -> None:
        assert extract_doc_id(None) is None

    # TC0346: returns None for empty string
    def test_empty_string(self) -> None:
        assert extract_doc_id("") is None

    def test_whitespace_only(self) -> None:
        assert extract_doc_id("   ") is None

    # TC0347: handles link without colon-title
    def test_link_without_title(self) -> None:
        result = extract_doc_id("[EP0007](../epics/EP0007-git-repository-sync.md)")
        assert result == "EP0007"

    # TC0348: returns raw value for non-matching format
    def test_non_matching_format(self) -> None:
        assert extract_doc_id("Some Random Text") == "Some Random Text"

    def test_malformed_link_no_id(self) -> None:
        # Link text doesn't start with a document ID pattern
        result = extract_doc_id("[No ID here](path)")
        assert result == "[No ID here](path)"

    def test_bug_reference(self) -> None:
        result = extract_doc_id("[BG0001: Login Failure](../bugs/BG0001-login-failure.md)")
        assert result == "BG0001"

    def test_test_spec_reference(self) -> None:
        result = extract_doc_id("[TS0028: Database Tests](../test-specs/TS0028-database-tests.md)")
        assert result == "TS0028"

    def test_plan_reference(self) -> None:
        result = extract_doc_id("[PL0028: Database Plan](../plans/PL0028-database-plan.md)")
        assert result == "PL0028"

    def test_leading_whitespace(self) -> None:
        result = extract_doc_id("  [EP0007: Title](path)  ")
        assert result == "EP0007"

    def test_plain_id_with_whitespace(self) -> None:
        assert extract_doc_id("  EP0007  ") == "EP0007"


# ---------------------------------------------------------------------------
# TC0349: _STANDARD_FIELDS includes "story"
# ---------------------------------------------------------------------------


class TestStandardFields:
    def test_includes_story(self) -> None:
        assert "story" in _STANDARD_FIELDS

    def test_includes_epic(self) -> None:
        assert "epic" in _STANDARD_FIELDS

    def test_all_expected_fields(self) -> None:
        expected = {"status", "owner", "priority", "story_points", "epic", "story"}
        assert expected == _STANDARD_FIELDS


# ---------------------------------------------------------------------------
# TC0350-TC0353: _build_doc_attrs cleans values
# ---------------------------------------------------------------------------


class TestBuildDocAttrs:
    """Tests that _build_doc_attrs produces clean epic/story IDs."""

    def test_cleans_epic_markdown_link(self) -> None:
        """TC0350: epic markdown link cleaned to plain ID."""
        meta = {
            "status": "Done",
            "epic": "[EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)",
        }
        attrs = _build_doc_attrs(
            parsed_meta=meta,
            parsed_title="US0028: Database Schema",
            parsed_body="body content",
            doc_type="story",
            doc_id="US0028",
            file_path="stories/US0028-database-github-fields.md",
            file_hash="abc123",
            project_id=1,
        )
        assert attrs["epic"] == "EP0007"

    def test_populates_story_from_metadata(self) -> None:
        """TC0351: story field extracted and cleaned."""
        meta = {
            "status": "Done",
            "story": "[US0028: Database Schema](../stories/US0028-database-github-fields.md)",
        }
        attrs = _build_doc_attrs(
            parsed_meta=meta,
            parsed_title="PL0028: Database Plan",
            parsed_body="body",
            doc_type="plan",
            doc_id="PL0028",
            file_path="plans/PL0028-database-plan.md",
            file_hash="def456",
            project_id=1,
        )
        assert attrs["story"] == "US0028"

    def test_null_epic_and_story(self) -> None:
        """TC0352: docs without epic/story have None values."""
        meta = {"status": "Done"}
        attrs = _build_doc_attrs(
            parsed_meta=meta,
            parsed_title="PRD",
            parsed_body="body",
            doc_type="prd",
            doc_id="prd",
            file_path="prd.md",
            file_hash="ghi789",
            project_id=1,
        )
        assert attrs["epic"] is None
        assert attrs["story"] is None

    def test_plain_id_preserved(self) -> None:
        """TC0353: already-clean values stored unchanged."""
        meta = {"status": "Done", "epic": "EP0001"}
        attrs = _build_doc_attrs(
            parsed_meta=meta,
            parsed_title="US0001: Title",
            parsed_body="body",
            doc_type="story",
            doc_id="US0001",
            file_path="stories/US0001-title.md",
            file_hash="jkl012",
            project_id=1,
        )
        assert attrs["epic"] == "EP0001"

    def test_story_not_in_extra_metadata(self) -> None:
        """story field should be extracted as a standard field, not in metadata_json."""
        meta = {
            "status": "Done",
            "story": "[US0028: Title](path)",
            "custom_field": "custom_value",
        }
        attrs = _build_doc_attrs(
            parsed_meta=meta,
            parsed_title="Title",
            parsed_body="body",
            doc_type="plan",
            doc_id="PL0001",
            file_path="plans/PL0001.md",
            file_hash="xyz",
            project_id=1,
        )
        assert attrs["story"] == "US0028"
        # custom_field should be in metadata_json, but story should not
        import json

        extra = json.loads(attrs["metadata_json"])
        assert "story" not in extra
        assert "custom_field" in extra


# ---------------------------------------------------------------------------
# TC0354-TC0357: Document model and integration tests
# ---------------------------------------------------------------------------


class TestDocumentModelStoryColumn:
    """Verify the Document model has the story column."""

    def test_story_column_exists(self) -> None:
        """TC0354: Document model has story column."""
        from sdlc_lens.db.models.document import Document

        assert hasattr(Document, "story")

    def test_story_column_in_table(self) -> None:
        """TC0355: story column is in the table definition."""
        from sdlc_lens.db.models.document import Document

        columns = {c.name for c in Document.__table__.columns}
        assert "story" in columns

    def test_epic_column_still_exists(self) -> None:
        """Regression: epic column still present."""
        from sdlc_lens.db.models.document import Document

        columns = {c.name for c in Document.__table__.columns}
        assert "epic" in columns


class TestParserExtractsStory:
    """Verify the parser extracts story metadata from frontmatter."""

    def test_parser_extracts_story_field(self) -> None:
        """TC0356: parser extracts story from blockquote frontmatter."""
        from sdlc_lens.services.parser import parse_document

        content = textwrap.dedent("""\
            # PL0028: Database Plan

            > **Status:** Done
            > **Story:** [US0028: Database Schema](../stories/US0028-database-github-fields.md)
            > **Owner:** Darren

            ## Overview
            Plan content here.
        """)
        result = parse_document(content)
        assert "story" in result.metadata
        assert "[US0028" in result.metadata["story"]

    def test_parser_extracts_epic_field(self) -> None:
        """TC0357: parser extracts epic from blockquote frontmatter."""
        from sdlc_lens.services.parser import parse_document

        content = textwrap.dedent("""\
            # US0028: Database Schema

            > **Status:** Done
            > **Epic:** [EP0007: Git Repository Sync](../epics/EP0007-git-repository-sync.md)
            > **Owner:** Darren

            ## User Story
            Story content here.
        """)
        result = parse_document(content)
        assert "epic" in result.metadata
        assert "[EP0007" in result.metadata["epic"]
