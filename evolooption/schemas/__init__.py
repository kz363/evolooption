"""JSON Schema definitions for evolooption manifest and registry entries.

These schemas enforce the declarative manifest format used by `.agentic/manifest.json`
and the template's seed manifest. Validation is offline-safe and dependency-free.
"""

from __future__ import annotations

import json
from typing import Any

# ---------------------------------------------------------------------------
# Agent entry schema
# ---------------------------------------------------------------------------

AGENT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "evolooption:agent-entry",
    "title": "Agent manifest entry",
    "type": "object",
    "required": [
        "id",
        "owner",
        "title",
        "body_path",
        "version",
        "targets",
        "permission_profile",
        "trust_class",
        "data_class",
        "disposition",
        "mode",
        "role_mode",
        "scope",
        "risk_class",
    ],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "owner": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1},
        "body_path": {"type": "string", "minLength": 1},
        "version": {"type": "string"},
        "targets": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
        },
        "permission_profile": {"type": "string"},
        "trust_class": {"type": "string", "enum": ["mutating", "read-only", "sandboxed"]},
        "data_class": {"type": "string", "enum": ["public", "internal", "confidential"]},
        "disposition": {"type": "string", "enum": ["retain", "replace", "ephemeral"]},
        "mode": {"type": "string"},
        "role_mode": {"type": "string"},
        "scope": {"type": "string"},
        "risk_class": {"type": "string"},
        "budgets": {
            "type": "object",
            "properties": {
                "context_bytes": {"type": "integer", "minimum": 1024},
                "max_files_changed": {"type": "integer", "minimum": 1},
            },
        },
        "eval_suites": {
            "type": "array",
            "items": {"type": "string"},
        },
        "stop_conditions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "skills": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# Command entry schema
# ---------------------------------------------------------------------------

COMMAND_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "evolooption:command-entry",
    "title": "Command manifest entry",
    "type": "object",
    "required": ["id", "owner", "title", "body_path", "version"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "owner": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "body_path": {"type": "string", "minLength": 1},
        "version": {"type": "string"},
        "targets": {
            "type": "array",
            "items": {"type": "string"},
        },
        "permission_profile": {"type": "string"},
        "trust_class": {"type": "string", "enum": ["mutating", "read-only", "sandboxed"]},
        "data_class": {"type": "string", "enum": ["public", "internal", "confidential"]},
        "disposition": {"type": "string", "enum": ["retain", "replace", "ephemeral"]},
        "scope": {"type": "string"},
        "risk_class": {"type": "string"},
        "skills": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# Skill entry schema
# ---------------------------------------------------------------------------

SKILL_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "evolooption:skill-entry",
    "title": "Skill manifest entry",
    "type": "object",
    "required": ["id", "owner", "title", "body_path", "version"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "owner": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "body_path": {"type": "string", "minLength": 1},
        "version": {"type": "string"},
        "targets": {"type": "array", "items": {"type": "string"}},
        "scope": {"type": "string"},
    },
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# Eval-suite entry schema
# ---------------------------------------------------------------------------

EVAL_SUITE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "evolooption:eval-suite-entry",
    "title": "Eval suite manifest entry",
    "type": "object",
    "required": ["id", "owner", "title", "min_cases", "suite_path"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "owner": {"type": "string"},
        "title": {"type": "string", "minLength": 1},
        "min_cases": {"type": "integer", "minimum": 1},
        "suite_path": {"type": "string", "minLength": 1},
        "version": {"type": "string"},
        "description": {"type": "string"},
    },
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# Manifest schema (top-level)
# ---------------------------------------------------------------------------

MANIFEST_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "evolooption:manifest",
    "title": "Evolooption manifest",
    "type": "object",
    "required": ["schema_version", "manifest_version", "canonical_layer_version"],
    "properties": {
        "schema_version": {"type": "string"},
        "manifest_version": {"type": "string"},
        "generated_by": {"type": "string"},
        "canonical_layer_version": {"type": "string"},
        "agents": {
            "type": "array",
            "items": AGENT_SCHEMA,
        },
        "commands": {
            "type": "array",
            "items": COMMAND_SCHEMA,
        },
        "skills": {
            "type": "array",
            "items": SKILL_SCHEMA,
        },
        "eval_suites": {
            "type": "array",
            "items": EVAL_SUITE_SCHEMA,
        },
    },
    "additionalProperties": False,
}


def _validate_against_schema(
    instance: dict[str, Any],
    schema: dict[str, Any],
    schema_id: str,
) -> list[str]:
    """Validate *instance* against *schema* using a minimal offline validator.

    This is a subset of JSON Schema validation — enough to catch manifest
    typos and missing required fields without external dependencies. Full
    JSON Schema Draft 2020-12 compliance is not guaranteed.
    """
    errors: list[str] = []

    if not isinstance(instance, dict):
        errors.append(f"{schema_id}: expected object, got {type(instance).__name__}")
        return errors

    # Required fields
    for field in schema.get("required", []):
        if field not in instance:
            errors.append(f"{schema_id}: missing required field '{field}'")

    # Type checks
    props = schema.get("properties", {})
    for key, value in instance.items():
        if key in props:
            prop_schema = props[key]
            prop_type = prop_schema.get("type")
            if prop_type == "string" and not isinstance(value, str):
                errors.append(f"{schema_id}.{key}: expected string, got {type(value).__name__}")
            elif prop_type == "integer" and not isinstance(value, int):
                errors.append(f"{schema_id}.{key}: expected integer, got {type(value).__name__}")
            elif prop_type == "array" and not isinstance(value, list):
                errors.append(f"{schema_id}.{key}: expected array, got {type(value).__name__}")
            elif prop_type == "object" and not isinstance(value, dict):
                errors.append(f"{schema_id}.{key}: expected object, got {type(value).__name__}")

            # Enum check
            enum_values = prop_schema.get("enum")
            if enum_values is not None and value not in enum_values:
                errors.append(
                    f"{schema_id}.{key}: '{value}' not in allowed values {enum_values}"
                )

            # Min-length for strings
            min_len = prop_schema.get("minLength")
            if min_len is not None and isinstance(value, str) and len(value) < min_len:
                errors.append(
                    f"{schema_id}.{key}: string too short (min {min_len})"
                )

            # Minimum for integers
            minimum = prop_schema.get("minimum")
            if minimum is not None and isinstance(value, int) and value < minimum:
                errors.append(
                    f"{schema_id}.{key}: {value} below minimum {minimum}"
                )

    # Additional properties check
    if not schema.get("additionalProperties", True) and isinstance(instance, dict):
        allowed_keys = set(props.keys())
        extra_keys = set(instance.keys()) - allowed_keys
        if extra_keys:
            errors.append(
                f"{schema_id}: unexpected fields {sorted(extra_keys)}"
            )

    return errors


def validate_agent_entry(entry: dict[str, Any]) -> list[str]:
    """Validate a single agent manifest entry."""
    return _validate_against_schema(entry, AGENT_SCHEMA, "agent")


def validate_command_entry(entry: dict[str, Any]) -> list[str]:
    """Validate a single command manifest entry."""
    return _validate_against_schema(entry, COMMAND_SCHEMA, "command")


def validate_skill_entry(entry: dict[str, Any]) -> list[str]:
    """Validate a single skill manifest entry."""
    return _validate_against_schema(entry, SKILL_SCHEMA, "skill")


def validate_eval_suite_entry(entry: dict[str, Any]) -> list[str]:
    """Validate a single eval-suite manifest entry."""
    return _validate_against_schema(entry, EVAL_SUITE_SCHEMA, "eval_suite")


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Validate a full manifest against the top-level schema.

    Also validates each entry in agents, commands, skills, and eval_suites arrays.
    """
    errors = _validate_against_schema(manifest, MANIFEST_SCHEMA, "manifest")

    for idx, agent in enumerate(manifest.get("agents", [])):
        errors.extend(
            f"agents[{idx}]: {e}" for e in _validate_against_schema(agent, AGENT_SCHEMA, f"agents[{idx}]")
        )

    for idx, cmd in enumerate(manifest.get("commands", [])):
        errors.extend(
            f"commands[{idx}]: {e}" for e in _validate_against_schema(cmd, COMMAND_SCHEMA, f"commands[{idx}]")
        )

    for idx, skill in enumerate(manifest.get("skills", [])):
        errors.extend(
            f"skills[{idx}]: {e}" for e in _validate_against_schema(skill, SKILL_SCHEMA, f"skills[{idx}]")
        )

    for idx, evs in enumerate(manifest.get("eval_suites", [])):
        errors.extend(
            f"eval_suites[{idx}]: {e}"
            for e in _validate_against_schema(evs, EVAL_SUITE_SCHEMA, f"eval_suites[{idx}]")
        )

    return errors


def load_manifest(path: str) -> tuple[dict[str, Any] | None, list[str]]:
    """Load and validate a manifest JSON file.

    Returns (manifest_dict, errors). If the file cannot be read or parsed,
    manifest_dict is None and errors describes the problem.
    """
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return None, [f"manifest file not found: {path}"]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON in {path}: {exc}"]
    if not isinstance(data, dict):
        return None, [f"manifest root must be an object, got {type(data).__name__}"]
    errors = validate_manifest(data)
    return data, errors


__all__ = [
    "AGENT_SCHEMA",
    "COMMAND_SCHEMA",
    "EVAL_SUITE_SCHEMA",
    "MANIFEST_SCHEMA",
    "SKILL_SCHEMA",
    "load_manifest",
    "validate_agent_entry",
    "validate_command_entry",
    "validate_eval_suite_entry",
    "validate_manifest",
    "validate_skill_entry",
]
