"""Unit tests for slug generation utility.

Test cases: TC0003-TC0006 from TS0001.
"""

from sdlc_lens.utils.slug import generate_slug


# TC0003: Slug from name with spaces
class TestSlugFromSpaces:
    def test_spaces_become_hyphens(self) -> None:
        assert generate_slug("My Cool Project") == "my-cool-project"

    def test_single_word(self) -> None:
        assert generate_slug("HomelabCmd") == "homelabcmd"


# TC0004: Slug from name with special characters
class TestSlugSpecialCharacters:
    def test_exclamation_stripped(self) -> None:
        assert generate_slug("Hello World!") == "hello-world"

    def test_underscores_become_hyphens(self) -> None:
        assert generate_slug("test__project") == "test-project"

    def test_leading_trailing_hyphens_stripped(self) -> None:
        assert generate_slug("--leading-trailing--") == "leading-trailing"

    def test_multiple_spaces_collapsed(self) -> None:
        assert generate_slug("Multiple   Spaces") == "multiple-spaces"

    def test_mixed_special_characters(self) -> None:
        assert generate_slug("Hello @World #2024!") == "hello-world-2024"


# TC0005: Slug from name with unicode characters
class TestSlugUnicode:
    def test_accented_characters_stripped(self) -> None:
        result = generate_slug("Projet Numero Un")
        assert result == "projet-numero-un"

    def test_result_is_ascii_only(self) -> None:
        import re

        result = generate_slug("Cafe Resume")
        assert re.match(r"^[a-z0-9-]+$", result)


# TC0006: Slug from name producing empty result
class TestSlugEmptyResult:
    def test_only_special_chars_returns_empty(self) -> None:
        assert generate_slug("!!!") == ""

    def test_only_spaces_returns_empty(self) -> None:
        assert generate_slug("   ") == ""

    def test_empty_string_returns_empty(self) -> None:
        assert generate_slug("") == ""
