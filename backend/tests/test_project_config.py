"""CR-01KX8Y6H: parsing a project's .config.yaml / .version."""

from pathlib import Path

from sdlc_lens.services.project_config import (
    ProjectConfig,
    parse_project_config,
    read_local_project_config,
)

_CONFIG_YAML = """\
schema_version: 3
profile: full

status_vocab:
  story:
    - Gated         # frontier-gated stories awaiting a human gate
  epic:
    - Proposed
    - Deferred
"""

_VERSION = """\
schema_version: 3
skill_version: "4.0.0"
"""


class TestParseProjectConfig:
    def test_reads_schema_version_profile_and_vocab(self) -> None:
        cfg = parse_project_config(_CONFIG_YAML, _VERSION)
        assert cfg.schema_version == "3"
        assert cfg.profile == "full"
        assert cfg.status_vocab == {
            "story": ["Gated"],
            "epic": ["Proposed", "Deferred"],
        }

    def test_inline_comments_are_stripped(self) -> None:
        cfg = parse_project_config(_CONFIG_YAML, None)
        assert cfg.status_vocab["story"] == ["Gated"]

    def test_falls_back_to_version_for_schema_version(self) -> None:
        cfg = parse_project_config("profile: lite\n", _VERSION)
        assert cfg.schema_version == "3"
        assert cfg.profile == "lite"

    def test_missing_config_yields_empty(self) -> None:
        cfg = parse_project_config(None, None)
        assert cfg == ProjectConfig()
        assert cfg.schema_version is None
        assert cfg.profile is None
        assert cfg.status_vocab == {}

    def test_unparseable_yaml_does_not_raise(self) -> None:
        cfg = parse_project_config("schema_version: 3\n  bad: [unclosed", None)
        assert cfg == ProjectConfig()

    def test_non_mapping_status_vocab_ignored(self) -> None:
        cfg = parse_project_config("schema_version: 3\nstatus_vocab: notamap\n", None)
        assert cfg.schema_version == "3"
        assert cfg.status_vocab == {}


class TestReadLocalProjectConfig:
    def test_reads_files_from_disk(self, tmp_path: Path) -> None:
        (tmp_path / ".config.yaml").write_text(_CONFIG_YAML, encoding="utf-8")
        (tmp_path / ".version").write_text(_VERSION, encoding="utf-8")
        cfg = read_local_project_config(str(tmp_path))
        assert cfg.schema_version == "3"
        assert cfg.profile == "full"
        assert cfg.status_vocab["story"] == ["Gated"]

    def test_missing_files_yield_empty_config(self, tmp_path: Path) -> None:
        cfg = read_local_project_config(str(tmp_path))
        assert cfg == ProjectConfig()
