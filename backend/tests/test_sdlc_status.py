"""CR-01KX8Y0M: status canonicalisation + v3 vocabulary."""

import pytest

from sdlc_lens.utils.sdlc_status import canonical_status, is_done


class TestCanonicalStatus:
    @pytest.mark.parametrize(
        "raw,doc_type,expected",
        [
            ("Done", "story", "Done"),
            ("Done — implemented 2026-07-08", "story", "Done"),
            ("**Done**", "story", "Done"),
            ("Done · **CR:** CR-0088 · **Points:** 5", "story", "Done"),
            ("Complete (81/88 ...)", "plan", "Complete"),
            ("In Progress", "story", "In Progress"),
            ("in progress", "story", "In Progress"),
            ("inbox", "bug", "inbox"),
            ("Fixed", "bug", "Fixed"),
            ("Proposed", "cr", "Proposed"),
            (None, "story", None),
            ("", "story", None),
        ],
    )
    def test_canonical(self, raw, doc_type, expected) -> None:
        assert canonical_status(raw, doc_type) == expected

    def test_in_progress_beats_in(self) -> None:
        # Longest token wins - "In Progress" is not truncated to "In".
        assert canonical_status("In Progress", "story") == "In Progress"

    def test_custom_status_preserved(self) -> None:
        # A project-specific status not in the vocab is returned stripped, not dropped.
        assert canonical_status("Gated — waiting on review", "story") == "Gated"

    def test_unknown_type_uses_global_vocab(self) -> None:
        assert canonical_status("Complete", None) == "Complete"

    def test_extra_vocab_canonicalises_project_status(self) -> None:
        # A project-defined status becomes a first-class token via extra_vocab.
        assert canonical_status("Gated", "story", extra_vocab=["Gated"]) == "Gated"
        assert canonical_status("Built - display shipped", "cr", extra_vocab=["Built"]) == "Built"

    def test_extra_vocab_none_keeps_two_arg_behaviour(self) -> None:
        assert canonical_status("Done", "story", extra_vocab=None) == "Done"


class TestIsDone:
    @pytest.mark.parametrize(
        "status,doc_type,expected",
        [
            ("Done", "story", True),
            ("Complete (5/5)", "plan", True),
            ("Fixed", "bug", True),
            ("Verified", "bug", True),
            ("In Progress", "story", False),
            ("inbox", "bug", False),
            (None, "story", False),
        ],
    )
    def test_is_done(self, status, doc_type, expected) -> None:
        assert is_done(status, doc_type) is expected
