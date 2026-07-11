"""CR-01KX8Y32: shared id/type recognition for sequential + v3 ULID ids."""

import pytest

from sdlc_lens.utils.sdlc_ids import (
    PREFIX_TO_TYPE,
    extract_ref_id,
    id_head,
    norm_id,
    type_for_prefix,
)


class TestIdHead:
    @pytest.mark.parametrize(
        "stem,expected",
        [
            ("US0001-register-new-project", "US0001"),
            ("EP0012-something", "EP0012"),
            ("RFC0001-design", "RFC0001"),
            ("RETRO0001-sprint", "RETRO0001"),
            ("CR-0003-hyphenated", "CR-0003"),
            ("BG-01KX8B82-path-traversal", "BG-01KX8B82"),
            ("US-01JQK3F8-story", "US-01JQK3F8"),
            ("RV0001-repository-review", "RV0001"),
        ],
    )
    def test_recognised_ids(self, stem: str, expected: str) -> None:
        assert id_head(stem) == expected

    @pytest.mark.parametrize(
        "stem",
        [
            "audit-event-matrix",  # arbitrary slug
            "0001-framework-v3",  # bare-number decision file
            "database-migrations",  # long leading word
            "SPR-G-plan",  # non-numeric, non-ULID tail
            "_index",
            "",
        ],
    )
    def test_non_ids_rejected(self, stem: str) -> None:
        assert id_head(stem) is None

    @pytest.mark.parametrize(
        "stem",
        [
            "PL-answered",  # known prefix + 8-letter word, no digit - not a ULID
            "US-abcdefgh",  # 8 base32 letters, no digit
            "TS-standbys",  # base32 letters only, no digit
            "BG-defghjkm",  # base32 letters only, no digit
        ],
    )
    def test_hyphenated_word_not_read_as_ulid(self, stem: str) -> None:
        # A genuine short-ULID tail always contains at least one digit; a
        # letters-only base32 word must not be mistaken for one.
        assert id_head(stem) is None


class TestTypeForPrefix:
    @pytest.mark.parametrize(
        "id_str,expected",
        [
            ("US0001", "story"),
            ("CR-0003", "cr"),
            ("BG-01KX8B82", "bug"),
            ("RFC0001", "rfc"),
            ("RETRO0001", "retro"),
            ("RV0001", "review"),
        ],
    )
    def test_type_lookup(self, id_str: str, expected: str) -> None:
        assert type_for_prefix(id_str) == expected

    def test_rfc_not_read_as_cr(self) -> None:
        # RFC must not be mis-read as CR + "FC..."
        assert type_for_prefix("RFC0001") == "rfc"

    def test_unknown_prefix(self) -> None:
        assert type_for_prefix("ZZ0001") is None


class TestNormId:
    @pytest.mark.parametrize(
        "a,b",
        [
            ("CR-0003", "CR0003"),
            ("[[CR-0496]]", "CR0496"),
            ("cr-0003", "CR0003"),
            ("US-01JQK3F8", "US01JQK3F8"),
        ],
    )
    def test_variants_normalise_equal(self, a: str, b: str) -> None:
        assert norm_id(a) == norm_id(b)

    def test_empty(self) -> None:
        assert norm_id("") is None
        assert norm_id(None) is None


class TestExtractRefId:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("[EP0007: Git Repository Sync](../epics/EP0007-x.md)", "EP0007"),
            ("[US0028](../stories/US0028-x.md)", "US0028"),
            ("US0163: Container Service Status", "US0163"),
            ("[[CR-0496]]", "CR-0496"),
            ("BG-01KX8B82", "BG-01KX8B82"),
            ("[CR-0221](../change-requests/CR0221-x.md)", "CR-0221"),
        ],
    )
    def test_extract(self, value: str, expected: str) -> None:
        assert extract_ref_id(value) == expected

    @pytest.mark.parametrize("value", ["-", "—", "", "   ", "no id here"])
    def test_none(self, value: str) -> None:
        assert extract_ref_id(value) is None

    @pytest.mark.parametrize("value", ["PL-answered", "US-abcdefgh", "see BG-defghjkm here"])
    def test_hyphenated_word_not_extracted_as_ulid(self, value: str) -> None:
        # No digit in the tail means it is not a ULID reference.
        assert extract_ref_id(value) is None


def test_prefix_map_covers_new_types() -> None:
    for prefix in ("CR", "RFC", "RETRO", "RV"):
        assert prefix in PREFIX_TO_TYPE
