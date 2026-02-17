"""Document type and ID inference tests.

Test cases: TC0084-TC0096 from TS0011.
"""

import pytest

from sdlc_lens.utils.inference import InferenceResult, infer_type_and_id


# TC0084: EP prefix infers type "epic"
class TestEpicPrefix:
    def test_ep_prefix_type(self) -> None:
        result = infer_type_and_id(
            "EP0001-project-management.md",
            "epics/EP0001-project-management.md",
        )
        assert result is not None
        assert result.doc_type == "epic"

    def test_ep_prefix_id(self) -> None:
        result = infer_type_and_id(
            "EP0001-project-management.md",
            "epics/EP0001-project-management.md",
        )
        assert result is not None
        assert result.doc_id == "EP0001-project-management"


# TC0085: US prefix infers type "story"
class TestStoryPrefix:
    def test_us_prefix_type(self) -> None:
        result = infer_type_and_id(
            "US0045-login-form.md",
            "stories/US0045-login-form.md",
        )
        assert result is not None
        assert result.doc_type == "story"

    def test_us_prefix_id(self) -> None:
        result = infer_type_and_id(
            "US0045-login-form.md",
            "stories/US0045-login-form.md",
        )
        assert result is not None
        assert result.doc_id == "US0045-login-form"


# TC0086: BG prefix infers type "bug"
class TestBugPrefix:
    def test_bg_prefix_type(self) -> None:
        result = infer_type_and_id(
            "BG0003-timeout-error.md",
            "bugs/BG0003-timeout-error.md",
        )
        assert result is not None
        assert result.doc_type == "bug"

    def test_bg_prefix_id(self) -> None:
        result = infer_type_and_id(
            "BG0003-timeout-error.md",
            "bugs/BG0003-timeout-error.md",
        )
        assert result is not None
        assert result.doc_id == "BG0003-timeout-error"


# TC0087: PL prefix infers type "plan"
class TestPlanPrefix:
    def test_pl_prefix_type(self) -> None:
        result = infer_type_and_id(
            "PL0001-register-new-project.md",
            "plans/PL0001-register-new-project.md",
        )
        assert result is not None
        assert result.doc_type == "plan"

    def test_pl_prefix_id(self) -> None:
        result = infer_type_and_id(
            "PL0001-register-new-project.md",
            "plans/PL0001-register-new-project.md",
        )
        assert result is not None
        assert result.doc_id == "PL0001-register-new-project"


# TC0088: TS prefix infers type "test-spec"
class TestTestSpecPrefix:
    def test_ts_prefix_type(self) -> None:
        result = infer_type_and_id(
            "TS0001-register-new-project.md",
            "test-specs/TS0001-register-new-project.md",
        )
        assert result is not None
        assert result.doc_type == "test-spec"

    def test_ts_prefix_id(self) -> None:
        result = infer_type_and_id(
            "TS0001-register-new-project.md",
            "test-specs/TS0001-register-new-project.md",
        )
        assert result is not None
        assert result.doc_id == "TS0001-register-new-project"


# TC0089: prd.md infers type "prd"
class TestPrdSingleton:
    def test_prd_type(self) -> None:
        result = infer_type_and_id("prd.md", "prd.md")
        assert result is not None
        assert result.doc_type == "prd"

    def test_prd_id(self) -> None:
        result = infer_type_and_id("prd.md", "prd.md")
        assert result is not None
        assert result.doc_id == "prd"


# TC0090: trd.md infers type "trd"
class TestTrdSingleton:
    def test_trd_type(self) -> None:
        result = infer_type_and_id("trd.md", "trd.md")
        assert result is not None
        assert result.doc_type == "trd"


# TC0091: tsd.md infers type "tsd"
class TestTsdSingleton:
    def test_tsd_type(self) -> None:
        result = infer_type_and_id("tsd.md", "tsd.md")
        assert result is not None
        assert result.doc_type == "tsd"


# TC0092: Unknown pattern defaults to type "other"
class TestUnknownPattern:
    def test_other_type(self) -> None:
        result = infer_type_and_id("brand-guide.md", "brand-guide.md")
        assert result is not None
        assert result.doc_type == "other"

    def test_other_id(self) -> None:
        result = infer_type_and_id("brand-guide.md", "brand-guide.md")
        assert result is not None
        assert result.doc_id == "brand-guide"


# TC0093: Document ID extracted from prefixed filenames (parametrised)
class TestPrefixedIds:
    @pytest.mark.parametrize(
        ("filename", "rel_path", "expected_id"),
        [
            (
                "EP0001-project-management.md",
                "epics/EP0001-project-management.md",
                "EP0001-project-management",
            ),
            (
                "US0045-login-form.md",
                "stories/US0045-login-form.md",
                "US0045-login-form",
            ),
            (
                "BG0003-timeout-error.md",
                "bugs/BG0003-timeout-error.md",
                "BG0003-timeout-error",
            ),
            (
                "PL0001-register-new-project.md",
                "plans/PL0001-register-new-project.md",
                "PL0001-register-new-project",
            ),
            (
                "TS0001-register-new-project.md",
                "test-specs/TS0001-register-new-project.md",
                "TS0001-register-new-project",
            ),
        ],
    )
    def test_id_extraction(
        self, filename: str, rel_path: str, expected_id: str
    ) -> None:
        result = infer_type_and_id(filename, rel_path)
        assert result is not None
        assert result.doc_id == expected_id


# TC0094: Singleton document IDs extracted correctly
class TestSingletonIds:
    @pytest.mark.parametrize(
        ("filename", "expected_id"),
        [
            ("prd.md", "prd"),
            ("trd.md", "trd"),
            ("tsd.md", "tsd"),
            ("personas.md", "personas"),
        ],
    )
    def test_singleton_id(self, filename: str, expected_id: str) -> None:
        result = infer_type_and_id(filename, filename)
        assert result is not None
        assert result.doc_id == expected_id


# TC0095: _index.md files excluded from import
class TestIndexExclusion:
    def test_index_returns_none(self) -> None:
        result = infer_type_and_id("_index.md", "stories/_index.md")
        assert result is None

    def test_index_in_epics(self) -> None:
        result = infer_type_and_id("_index.md", "epics/_index.md")
        assert result is None

    def test_index_in_plans(self) -> None:
        result = infer_type_and_id("_index.md", "plans/_index.md")
        assert result is None


# TC0096: Directory context used as fallback for type inference
class TestDirectoryFallback:
    def test_epics_dir_fallback(self) -> None:
        result = infer_type_and_id("overview.md", "epics/overview.md")
        assert result is not None
        assert result.doc_type == "epic"
        assert result.doc_id == "overview"

    def test_stories_dir_fallback(self) -> None:
        result = infer_type_and_id("notes.md", "stories/notes.md")
        assert result is not None
        assert result.doc_type == "story"

    def test_bugs_dir_fallback(self) -> None:
        result = infer_type_and_id("triage.md", "bugs/triage.md")
        assert result is not None
        assert result.doc_type == "bug"


# Additional edge case tests from the plan
class TestEdgeCases:
    def test_prefix_in_wrong_directory(self) -> None:
        """EP0001.md in stories/ still infers as epic (prefix priority)."""
        result = infer_type_and_id(
            "EP0001-overview.md", "stories/EP0001-overview.md"
        )
        assert result is not None
        assert result.doc_type == "epic"

    def test_prefix_without_number(self) -> None:
        """EP-overview.md does not match EP\\d{4}; falls through."""
        result = infer_type_and_id("EP-overview.md", "epics/EP-overview.md")
        assert result is not None
        # Should fall through to directory fallback
        assert result.doc_type == "epic"
        assert result.doc_id == "EP-overview"

    def test_nested_subdirectory(self) -> None:
        """File in nested dir still inferred from filename prefix."""
        result = infer_type_and_id(
            "EP0001-archived.md", "epics/archive/EP0001-archived.md"
        )
        assert result is not None
        assert result.doc_type == "epic"
        assert result.doc_id == "EP0001-archived"

    def test_readme_as_other(self) -> None:
        """readme.md has no known pattern; defaults to other."""
        result = infer_type_and_id("readme.md", "readme.md")
        assert result is not None
        assert result.doc_type == "other"
        assert result.doc_id == "readme"

    def test_wf_prefix(self) -> None:
        """WF prefix infers type workflow."""
        result = infer_type_and_id(
            "WF0001-workflow.md", "workflows/WF0001-workflow.md"
        )
        assert result is not None
        assert result.doc_type == "workflow"
        assert result.doc_id == "WF0001-workflow"

    def test_personas_singleton(self) -> None:
        """personas.md is a known singleton."""
        result = infer_type_and_id("personas.md", "personas.md")
        assert result is not None
        assert result.doc_type == "personas"
        assert result.doc_id == "personas"

    def test_inference_result_type(self) -> None:
        """Return type is InferenceResult."""
        result = infer_type_and_id("prd.md", "prd.md")
        assert isinstance(result, InferenceResult)
