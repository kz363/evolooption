#!/usr/bin/env python3
"""
Self-contained AI assets validator for consumer repositories.

This script validates that the committed foundation bundle matches the
regenerated bundle from canonical manifests. It has no external dependencies
beyond the Python standard library.

Usage:
    python3 .agentic/bin/ai_assets.py check [--repo REPO_ROOT]
    python3 .agentic/bin/ai_assets.py lint [--repo REPO_ROOT]
    python3 .agentic/bin/ai_assets.py validate [--repo REPO_ROOT]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Embedded constants from generator
GENERATED_BY = "ADAPTER-002"
SCHEMA_VERSION = "1.0.0"

FOUNDATION_BUNDLE = "foundation.bundle.json"
FOUNDATION_LOCK = "foundation.lock.json"
GENERATED_INDEX = "generated-index.json"

# ---------------------------------------------------------------------------
# Embedded schema definitions (self-contained, no evolooption dependency)
# ---------------------------------------------------------------------------

AGENT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "evolooption:agent-entry",
    "title": "Agent manifest entry",
    "type": "object",
    "required": [
        "id", "owner", "title", "body_path", "version",
        "targets", "permission_profile", "trust_class",
        "data_class", "disposition", "mode", "role_mode",
        "scope", "risk_class",
    ],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "owner": {"type": "string", "minLength": 1},
        "title": {"type": "string", "minLength": 1},
        "body_path": {"type": "string", "minLength": 1},
        "version": {"type": "string"},
        "targets": {"type": "array", "minItems": 1, "items": {"type": "string"}},
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
        "eval_suites": {"type": "array", "items": {"type": "string"}},
        "stop_conditions": {"type": "array", "items": {"type": "string"}},
        "skills": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}

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
        "targets": {"type": "array", "items": {"type": "string"}},
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
        "agents": {"type": "array", "items": AGENT_SCHEMA},
        "commands": {"type": "array", "items": COMMAND_SCHEMA},
        "skills": {"type": "array", "items": SKILL_SCHEMA},
        "eval_suites": {"type": "array", "items": EVAL_SUITE_SCHEMA},
    },
    "additionalProperties": False,
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_against_schema(
    instance: dict[str, Any],
    schema: dict[str, Any],
    schema_id: str,
) -> list[str]:
    """Validate *instance* against *schema* using a minimal offline validator.

    This is a subset of JSON Schema validation — enough to catch manifest
    typos and missing required fields without external dependencies.
    """
    errors: list[str] = []

    if not isinstance(instance, dict):
        errors.append(f"{schema_id}: expected object, got {type(instance).__name__}")
        return errors

    for field in schema.get("required", []):
        if field not in instance:
            errors.append(f"{schema_id}: missing required field '{field}'")

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

            enum_values = prop_schema.get("enum")
            if enum_values is not None and value not in enum_values:
                errors.append(f"{schema_id}.{key}: '{value}' not in allowed values {enum_values}")

            min_len = prop_schema.get("minLength")
            if min_len is not None and isinstance(value, str) and len(value) < min_len:
                errors.append(f"{schema_id}.{key}: string too short (min {min_len})")

            minimum = prop_schema.get("minimum")
            if minimum is not None and isinstance(value, int) and value < minimum:
                errors.append(f"{schema_id}.{key}: {value} below minimum {minimum}")

    if not schema.get("additionalProperties", True) and isinstance(instance, dict):
        allowed_keys = set(props.keys())
        extra_keys = set(instance.keys()) - allowed_keys
        if extra_keys:
            errors.append(f"{schema_id}: unexpected fields {sorted(extra_keys)}")

    return errors


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Validate a full manifest against the top-level schema.

    Also validates each entry in agents, commands, skills, and eval_suites arrays.
    """
    errors = _validate_against_schema(manifest, MANIFEST_SCHEMA, "manifest")

    for idx, agent in enumerate(manifest.get("agents", [])):
        errors.extend(
            f"agents[{idx}]: {e}"
            for e in _validate_against_schema(agent, AGENT_SCHEMA, f"agents[{idx}]")
        )

    for idx, cmd in enumerate(manifest.get("commands", [])):
        errors.extend(
            f"commands[{idx}]: {e}"
            for e in _validate_against_schema(cmd, COMMAND_SCHEMA, f"commands[{idx}]")
        )

    for idx, skill in enumerate(manifest.get("skills", [])):
        errors.extend(
            f"skills[{idx}]: {e}"
            for e in _validate_against_schema(skill, SKILL_SCHEMA, f"skills[{idx}]")
        )

    for idx, evs in enumerate(manifest.get("eval_suites", [])):
        errors.extend(
            f"eval_suites[{idx}]: {e}"
            for e in _validate_against_schema(evs, EVAL_SUITE_SCHEMA, f"eval_suites[{idx}]")
        )

    return errors


def validate_foundation_bundle(repo_root: Path) -> int:
    """Validate foundation bundle against lock and index files."""
    bundle_path = repo_root / FOUNDATION_BUNDLE
    lock_path = repo_root / FOUNDATION_LOCK
    index_path = repo_root / GENERATED_INDEX

    if not bundle_path.exists():
        print(f"ERROR: {FOUNDATION_BUNDLE} not found", file=sys.stderr)
        return 1
    if not lock_path.exists():
        print(f"ERROR: {FOUNDATION_LOCK} not found", file=sys.stderr)
        return 1
    if not index_path.exists():
        print(f"ERROR: {GENERATED_INDEX} not found", file=sys.stderr)
        return 1

    try:
        committed_bundle = load_json(bundle_path)
        committed_lock = load_json(lock_path)
        committed_index = load_json(index_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: failed to load foundation files: {exc}", file=sys.stderr)
        return 1

    # Check lock matches bundle
    if committed_lock.get("foundation_version") != committed_bundle.get("foundation_version"):
        print("ERROR: foundation.lock version mismatch", file=sys.stderr)
        return 1

    # Check index matches bundle
    if committed_index.get("foundation_version") != committed_bundle.get("foundation_version"):
        print("ERROR: generated-index.json version mismatch", file=sys.stderr)
        return 1

    # Check source digest consistency
    if committed_lock.get("source_digest") != committed_bundle.get("source_digest"):
        print("ERROR: source digest mismatch between lock and bundle", file=sys.stderr)
        return 1

    # Verify index entries match bundle digests
    bundle = committed_bundle
    index_entries = committed_index.get("entries", {})

    # Check commands
    for cmd in bundle.get("commands", []):
        expected_path = f"kilo-global/commands/{cmd['id']}.md"
        if expected_path not in index_entries:
            print(f"ERROR: index missing command entry: {expected_path}", file=sys.stderr)
            return 1
        if index_entries[expected_path] != cmd["digest"]:
            print(f"ERROR: index digest mismatch for {expected_path}", file=sys.stderr)
            return 1

    # Check skills
    for skill in bundle.get("skills", []):
        expected_path = f"kilo-global/skills/{skill['id']}.md"
        if expected_path not in index_entries:
            print(f"ERROR: index missing skill entry: {expected_path}", file=sys.stderr)
            return 1
        if index_entries[expected_path] != skill["digest"]:
            print(f"ERROR: index digest mismatch for {expected_path}", file=sys.stderr)
            return 1

    # Check agents
    for agent in bundle.get("agents", []):
        expected_path = f"kilo-global/agent/{agent['id']}.md"
        if expected_path not in index_entries:
            print(f"ERROR: index missing agent entry: {expected_path}", file=sys.stderr)
            return 1
        if index_entries[expected_path] != agent["digest"]:
            print(f"ERROR: index digest mismatch for {expected_path}", file=sys.stderr)
            return 1

    print(f"OK: foundation bundle validated (version={bundle['foundation_version']})")
    return 0


def lint_repo(repo_root: Path) -> int:
    """Run lint checks on the repository."""
    errors: List[str] = []

    # Check foundation files exist
    for fname in (FOUNDATION_BUNDLE, FOUNDATION_LOCK, GENERATED_INDEX):
        if not (repo_root / fname).exists():
            errors.append(f"missing required file: {fname}")

    if errors:
        for e in errors:
            print(f"LINT: {e}", file=sys.stderr)
        return 1

    # Validate foundation bundle
    if validate_foundation_bundle(repo_root) != 0:
        errors.append("foundation bundle validation failed")

    # Check kilo-global structure
    kg = repo_root / "kilo-global"
    if not kg.exists():
        errors.append("missing kilo-global directory")
    else:
        for sub in ("commands", "skills", "agent"):
            if not (kg / sub).exists():
                errors.append(f"missing kilo-global/{sub}")

    if errors:
        for e in errors:
            print(f"LINT: {e}", file=sys.stderr)
        return 1

    print("lint: clean")
    return 0


def validate_cmd(repo_root: Path) -> int:
    """Validate the manifest against embedded schemas (self-contained)."""
    manifest_path = repo_root / ".agentic" / "manifest.json"
    if not manifest_path.exists():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: failed to load manifest: {exc}", file=sys.stderr)
        return 2
    errors = validate_manifest(manifest)
    if errors:
        for e in errors:
            print(f"invalid: {e}", file=sys.stderr)
        return 1
    print("manifest valid")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Self-contained AI assets validator (generated by ADAPTER-002)"
    )
    p.add_argument("--repo", default=".", help="Repository root (default: cwd)")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="Validate foundation bundle")
    c.add_argument("--repo", default=".", help="Repository root")

    l = sub.add_parser("lint", help="Run lint checks")
    l.add_argument("--repo", default=".", help="Repository root")

    v = sub.add_parser("validate", help="Validate manifest against schema")
    v.add_argument("--repo", default=".", help="Repository root")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo).resolve()

    if args.command == "check":
        return validate_foundation_bundle(repo_root)
    elif args.command == "lint":
        return lint_repo(repo_root)
    elif args.command == "validate":
        return validate_cmd(repo_root)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
