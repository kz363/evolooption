"""Tests for the offline manifest validator embedded in .agentic/bin/ai_assets.py."""

import importlib.util
import json
import sys
from pathlib import Path


def _load_ai_assets():
    """Import ai_assets.py as a module via importlib."""
    script_path = Path(__file__).resolve().parent.parent / ".agentic" / "bin" / "ai_assets.py"
    spec = importlib.util.spec_from_file_location("ai_assets", script_path)
    assert spec is not None and spec.loader is not None, f"Could not load {script_path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ai_assets"] = mod
    spec.loader.exec_module(mod)
    return mod


ai = _load_ai_assets()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_agent_entry():
    return {
        "id": "test-agent",
        "owner": "evolooption:domain",
        "title": "Test Agent",
        "body_path": "agents/test.md",
        "version": "1.0.0",
        "targets": ["kilo"],
        "permission_profile": "implementer",
        "trust_class": "mutating",
        "data_class": "internal",
        "disposition": "retain",
        "mode": "implementer",
        "role_mode": "implementer",
        "scope": "testing",
        "risk_class": "low",
    }


def _valid_manifest():
    return {
        "schema_version": "1.0.0",
        "manifest_version": "1.0.0",
        "canonical_layer_version": "1.0.0",
        "agents": [_valid_agent_entry()],
        "commands": [],
        "skills": [],
    }


# ---------------------------------------------------------------------------
# _validate_against_schema – basic type checks
# ---------------------------------------------------------------------------

def test_validate_against_schema_non_dict_instance():
    errors = ai._validate_against_schema([], ai.AGENT_SCHEMA, "root")
    assert any("expected object" in e for e in errors)


def test_validate_against_schema_missing_required():
    entry = {}
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("missing required field 'id'" in e for e in errors)


def test_validate_against_schema_wrong_type_string():
    entry = _valid_agent_entry()
    entry["id"] = 123
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("root.id: expected string" in e for e in errors)


def test_validate_against_schema_wrong_type_array():
    entry = _valid_agent_entry()
    entry["targets"] = "not-an-array"
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("root.targets: expected array" in e for e in errors)


def test_validate_against_schema_wrong_type_object():
    entry = _valid_agent_entry()
    entry["budgets"] = [1, 2, 3]
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("root.budgets: expected object" in e for e in errors)


def test_validate_against_schema_invalid_enum():
    entry = _valid_agent_entry()
    entry["trust_class"] = "nuclear"
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("'nuclear' not in allowed values" in e for e in errors)


def test_validate_against_schema_valid_enum():
    entry = _valid_agent_entry()
    entry["trust_class"] = "read-only"
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert not any("not in allowed values" in e for e in errors)


def test_validate_against_schema_min_length():
    entry = _valid_agent_entry()
    entry["id"] = ""
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("string too short" in e for e in errors)


def test_validate_against_schema_minimum():
    entry = _valid_agent_entry()
    entry["budgets"] = {"context_bytes": 0, "max_files_changed": 5}
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("below minimum" in e for e in errors)


def test_validate_against_schema_additional_properties_forbidden():
    entry = _valid_agent_entry()
    entry["extra_junk"] = "unexpected"
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("unexpected fields" in e for e in errors)


# ---------------------------------------------------------------------------
# _validate_against_schema – nested object recursion
# ---------------------------------------------------------------------------

def test_validate_nested_object_valid():
    entry = _valid_agent_entry()
    entry["budgets"] = {"context_bytes": 4096, "max_files_changed": 5}
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert not errors


def test_validate_nested_object_wrong_type():
    entry = _valid_agent_entry()
    entry["budgets"] = {"context_bytes": "too-much", "max_files_changed": 5}
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("expected integer" in e for e in errors)


def test_validate_nested_object_below_minimum():
    entry = _valid_agent_entry()
    entry["budgets"] = {"context_bytes": 4096, "max_files_changed": 0}
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("below minimum" in e for e in errors)


# ---------------------------------------------------------------------------
# _validate_against_schema – array item validation
# ---------------------------------------------------------------------------

def test_validate_array_items_valid():
    entry = _valid_agent_entry()
    entry["targets"] = ["kilo", "github"]
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert not any("root.targets" in e for e in errors)


def test_validate_array_items_wrong_type():
    entry = _valid_agent_entry()
    entry["targets"] = ["kilo", 42]
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("expected string" in e for e in errors)


def test_validate_array_min_items():
    entry = _valid_agent_entry()
    entry["targets"] = []
    errors = ai._validate_against_schema(entry, ai.AGENT_SCHEMA, "root")
    assert any("min 1" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_manifest – top-level and entry validation
# ---------------------------------------------------------------------------

def test_validate_manifest_valid():
    manifest = _valid_manifest()
    errors = ai.validate_manifest(manifest)
    assert errors == []


def test_validate_manifest_missing_top_level_field():
    manifest = _valid_manifest()
    del manifest["schema_version"]
    errors = ai.validate_manifest(manifest)
    assert any("missing required field 'schema_version'" in e for e in errors)


def test_validate_manifest_agent_missing_required():
    manifest = _valid_manifest()
    manifest["agents"][0] = {"id": "bare-minimum"}
    errors = ai.validate_manifest(manifest)
    assert len(errors) >= 1
    assert any("missing required field" in e for e in errors)


def test_validate_manifest_agent_bad_enum():
    manifest = _valid_manifest()
    manifest["agents"][0]["trust_class"] = "evil"
    errors = ai.validate_manifest(manifest)
    assert any("not in allowed values" in e for e in errors)


def test_validate_manifest_agent_extra_field():
    manifest = _valid_manifest()
    manifest["agents"][0]["bonus_field"] = "should-not-be-here"
    errors = ai.validate_manifest(manifest)
    assert any("unexpected fields" in e for e in errors)


def test_validate_manifest_agent_bad_budgets_nested():
    manifest = _valid_manifest()
    manifest["agents"][0]["budgets"] = {"context_bytes": "abc"}
    errors = ai.validate_manifest(manifest)
    assert any("expected integer" in e for e in errors)


def test_validate_manifest_command_valid():
    manifest = _valid_manifest()
    manifest["commands"] = [{
        "id": "test-cmd",
        "owner": "user:domain",
        "title": "Test Command",
        "body_path": "commands/test.md",
        "version": "1.0.0",
    }]
    errors = ai.validate_manifest(manifest)
    assert errors == []


def test_validate_manifest_skill_valid():
    manifest = _valid_manifest()
    manifest["skills"] = [{
        "id": "test-skill",
        "owner": "user:domain",
        "title": "Test Skill",
        "body_path": "skills/test.md",
        "version": "1.0.0",
    }]
    errors = ai.validate_manifest(manifest)
    assert errors == []


def test_validate_manifest_eval_suite_valid():
    manifest = _valid_manifest()
    manifest["eval_suites"] = [{
        "id": "test-suite",
        "owner": "user:domain",
        "title": "Test Suite",
        "min_cases": 3,
        "suite_path": "eval/test.py",
    }]
    errors = ai.validate_manifest(manifest)
    assert errors == []


def test_validate_manifest_multiple_errors_accumulate():
    manifest = _valid_manifest()
    manifest["agents"][0]["id"] = 42  # type error
    manifest["agents"][0]["trust_class"] = "bad"  # enum error
    del manifest["agents"][0]["title"]  # missing required
    errors = ai.validate_manifest(manifest)
    assert len(errors) >= 3


# ---------------------------------------------------------------------------
# validate_cmd – integration via temp manifest
# ---------------------------------------------------------------------------

def test_validate_cmd_real_manifest(tmp_path: Path):
    """Run validate_cmd against a temp manifest to avoid coupling to the real manifest."""
    manifest = _valid_manifest()
    agentic_dir = tmp_path / ".agentic"
    agentic_dir.mkdir()
    manifest_path = agentic_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    exit_code = ai.validate_cmd(tmp_path)
    assert exit_code == 0


def test_validate_cmd_missing_manifest(tmp_path: Path):
    exit_code = ai.validate_cmd(tmp_path)
    assert exit_code == 2


def test_validate_cmd_bad_json(tmp_path: Path):
    agentic_dir = tmp_path / ".agentic"
    agentic_dir.mkdir()
    manifest_path = agentic_dir / "manifest.json"
    manifest_path.write_text("not json")

    exit_code = ai.validate_cmd(tmp_path)
    assert exit_code == 2


def test_validate_cmd_invalid_manifest(tmp_path: Path):
    manifest = _valid_manifest()
    del manifest["schema_version"]
    del manifest["agents"][0]["title"]

    agentic_dir = tmp_path / ".agentic"
    agentic_dir.mkdir()
    manifest_path = agentic_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    exit_code = ai.validate_cmd(tmp_path)
    assert exit_code == 1
