"""Blockquote frontmatter parser tests.

Test cases: TC0069-TC0083 from TS0006.
"""

from sdlc_lens.services.parser import ParseResult, parse_document


# TC0069: Parse status field from frontmatter
class TestParseStatusField:
    def test_extracts_status(self) -> None:
        content = "> **Status:** Done\n\n# Title\n\nBody."
        result = parse_document(content)
        assert result.metadata["status"] == "Done"


# TC0070: Parse owner field from frontmatter
class TestParseOwnerField:
    def test_extracts_owner(self) -> None:
        content = "> **Owner:** Darren\n\n# Title\n\nBody."
        result = parse_document(content)
        assert result.metadata["owner"] == "Darren"


# TC0071: Parse priority field from frontmatter
class TestParsePriorityField:
    def test_extracts_priority(self) -> None:
        content = "> **Priority:** P0\n\n# Title\n\nBody."
        result = parse_document(content)
        assert result.metadata["priority"] == "P0"


# TC0072: Parse story_points as integer
class TestParseStoryPoints:
    def test_story_points_as_integer(self) -> None:
        content = "> **Story Points:** 5\n\n# Title\n\nBody."
        result = parse_document(content)
        assert result.metadata["story_points"] == 5
        assert isinstance(result.metadata["story_points"], int)


# TC0073: Parse epic reference field
class TestParseEpicReference:
    def test_extracts_epic_link(self) -> None:
        epic_link = "[EP0001: Project Management](../epics/EP0001-project-management.md)"
        content = f"> **Epic:** {epic_link}\n\n# Title\n\nBody."
        result = parse_document(content)
        assert "EP0001" in result.metadata["epic"]


# TC0074: Extract title from first heading
class TestExtractTitle:
    def test_title_from_heading(self) -> None:
        content = "> **Status:** Done\n\n# EP0001: Project Management\n\nBody."
        result = parse_document(content)
        assert result.title == "EP0001: Project Management"

    def test_title_without_hash_prefix(self) -> None:
        content = "# Simple Title\n\nBody."
        result = parse_document(content)
        assert result.title == "Simple Title"
        assert not result.title.startswith("# ")


# TC0075: Handle multi-line blockquote values
class TestMultiLineValues:
    def test_concatenates_continuation_lines(self) -> None:
        content = (
            "> **Description:** This is a long description\n"
            "> that spans multiple lines\n"
            "> and continues here\n"
            "> **Status:** Draft\n"
            "\n"
            "# Title\n"
            "\nBody."
        )
        result = parse_document(content)
        assert (
            result.metadata["description"]
            == "This is a long description that spans multiple lines and continues here"
        )
        assert result.metadata["status"] == "Draft"


# TC0076: Return empty metadata for no frontmatter
class TestNoFrontmatter:
    def test_empty_metadata(self) -> None:
        content = "# Just a Title\n\nBody content with no metadata."
        result = parse_document(content)
        assert result.metadata == {}

    def test_body_contains_content(self) -> None:
        content = "# Just a Title\n\nBody content with no metadata."
        result = parse_document(content)
        assert "Body content with no metadata." in result.body

    def test_title_extracted(self) -> None:
        content = "# Just a Title\n\nBody content with no metadata."
        result = parse_document(content)
        assert result.title == "Just a Title"


# TC0077: Skip malformed blockquote lines
class TestMalformedLines:
    def test_valid_lines_parsed(self) -> None:
        content = (
            "> **Status:** Done\n> This is not a key-value pair\n> **Owner:** Darren\n\nBody."
        )
        result = parse_document(content)
        assert result.metadata["status"] == "Done"
        assert result.metadata["owner"] == "Darren"

    def test_malformed_not_in_metadata(self) -> None:
        content = (
            "> **Status:** Done\n> This is not a key-value pair\n> **Owner:** Darren\n\nBody."
        )
        result = parse_document(content)
        assert "This is not a key-value pair" not in result.metadata.values()


# TC0078: Handle colons in values
class TestColonsInValues:
    def test_colon_in_url_value(self) -> None:
        content = "> **URL:** http://example.com:8080/path\n\nBody."
        result = parse_document(content)
        assert result.metadata["url"] == "http://example.com:8080/path"


# TC0079: Handle empty values
class TestEmptyValues:
    def test_empty_string_value(self) -> None:
        content = "> **Owner:**\n\nBody."
        result = parse_document(content)
        assert result.metadata["owner"] == ""

    def test_empty_value_with_space(self) -> None:
        content = "> **Owner:** \n\nBody."
        result = parse_document(content)
        assert result.metadata["owner"] == ""


# TC0080: Non-numeric story_points returns None
class TestNonNumericStoryPoints:
    def test_returns_none(self) -> None:
        content = "> **Story Points:** Large\n\nBody."
        result = parse_document(content)
        assert result.metadata["story_points"] is None


# TC0081: Additional fields stored in metadata dict
class TestAdditionalFields:
    def test_non_standard_field(self) -> None:
        content = "> **Reviewer:** Alice\n\nBody."
        result = parse_document(content)
        assert result.metadata["reviewer"] == "Alice"


# TC0082: Body content correctly separated from frontmatter
class TestBodySeparation:
    def test_body_excludes_frontmatter(self) -> None:
        content = "> **Status:** Done\n> **Owner:** Darren\n\n# Title\n\nBody content here."
        result = parse_document(content)
        assert "> **Status:**" not in result.body
        assert "> **Owner:**" not in result.body

    def test_body_contains_content(self) -> None:
        content = "> **Status:** Done\n> **Owner:** Darren\n\n# Title\n\nBody content here."
        result = parse_document(content)
        assert "Body content here." in result.body

    def test_body_not_empty(self) -> None:
        content = "> **Status:** Done\n\n# Title\n\nBody content here."
        result = parse_document(content)
        assert result.body.strip() != ""


# TC0083: Windows line endings handled
class TestWindowsLineEndings:
    def test_crlf_metadata(self) -> None:
        content = "> **Status:** Done\r\n> **Owner:** Darren\r\n\r\n# Title\r\n\r\nBody."
        result = parse_document(content)
        assert result.metadata["status"] == "Done"
        assert result.metadata["owner"] == "Darren"

    def test_no_carriage_returns_in_values(self) -> None:
        content = "> **Status:** Done\r\n> **Owner:** Darren\r\n\r\n# Title\r\n\r\nBody."
        result = parse_document(content)
        for value in result.metadata.values():
            if isinstance(value, str):
                assert "\r" not in value

    def test_crlf_body(self) -> None:
        content = "> **Status:** Done\r\n\r\n# Title\r\n\r\nBody."
        result = parse_document(content)
        assert "Body." in result.body


# Additional edge case tests from the plan
class TestEdgeCases:
    def test_only_frontmatter_no_body(self) -> None:
        content = "> **Status:** Done\n> **Owner:** Darren"
        result = parse_document(content)
        assert result.metadata["status"] == "Done"
        assert result.body.strip() == ""

    def test_nested_blockquotes_not_parsed(self) -> None:
        content = ">> **Status:** Done\n\n# Title\n\nBody."
        result = parse_document(content)
        assert "status" not in result.metadata

    def test_multiple_blockquote_blocks(self) -> None:
        content = "> **Status:** Done\n\n# Title\n\nBody.\n\n> **Other:** Value"
        result = parse_document(content)
        assert result.metadata["status"] == "Done"
        assert "other" not in result.metadata

    def test_frontmatter_after_blank_lines(self) -> None:
        content = "\n\n> **Status:** Done\n\n# Title\n\nBody."
        result = parse_document(content)
        assert result.metadata["status"] == "Done"

    def test_all_standard_fields(self) -> None:
        content = (
            "> **Status:** Done\n"
            "> **Owner:** Darren\n"
            "> **Priority:** P0\n"
            "> **Story Points:** 5\n"
            "> **Epic:** [EP0001](../epics/EP0001.md)\n"
            "> **Created:** 2026-02-17\n"
            "> **Type:** story\n"
            "\n"
            "# US0001: Register a New Project\n"
            "\nBody content."
        )
        result = parse_document(content)
        assert result.metadata["status"] == "Done"
        assert result.metadata["owner"] == "Darren"
        assert result.metadata["priority"] == "P0"
        assert result.metadata["story_points"] == 5
        assert "EP0001" in result.metadata["epic"]
        assert result.metadata["created"] == "2026-02-17"
        assert result.metadata["type"] == "story"
        assert result.title == "US0001: Register a New Project"

    def test_parse_result_type(self) -> None:
        content = "> **Status:** Done\n\n# Title\n\nBody."
        result = parse_document(content)
        assert isinstance(result, ParseResult)
        assert isinstance(result.metadata, dict)
        assert isinstance(result.body, str)


class TestHeadingBeforeFrontmatter:
    """Real sdlc-studio documents have heading first, then blockquote."""

    def test_extracts_metadata_after_heading(self) -> None:
        content = "# US0001: Register a New Project\n\n> **Status:** Done\n> **Owner:** Darren\n\n## Section\n\nBody."
        result = parse_document(content)
        assert result.metadata["status"] == "Done"
        assert result.metadata["owner"] == "Darren"

    def test_extracts_title_before_frontmatter(self) -> None:
        content = "# US0001: Register a New Project\n\n> **Status:** Done\n\n## Section\n\nBody."
        result = parse_document(content)
        assert result.title == "US0001: Register a New Project"

    def test_body_after_frontmatter(self) -> None:
        content = "# US0001: Register a New Project\n\n> **Status:** Done\n> **Owner:** Darren\n\n## Section\n\nBody."
        result = parse_document(content)
        assert "## Section" in result.body
        assert "Body." in result.body
        assert "> **Status:**" not in result.body
