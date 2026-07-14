"""Centralized registry for evolooption agents, commands, skills, and eval suites.

Provides typed dataclasses for each entry kind, a typed Manifest container,
and loading functions that validate against the evolooption schemas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from evolooption.schemas import load_manifest as _load_raw_manifest
from evolooption.schemas import validate_manifest

# ---------------------------------------------------------------------------
# Typed entry dataclasses
# ---------------------------------------------------------------------------

TrustClass = Literal["mutating", "read-only", "sandboxed"]
DataClass = Literal["public", "internal", "confidential"]
Disposition = Literal["retain", "replace", "ephemeral"]


@dataclass(frozen=True)
class AgentEntry:
    """Typed agent entry in the manifest registry."""

    id: str
    owner: str
    title: str
    body_path: str
    version: str
    targets: list[str] = field(default_factory=list)
    permission_profile: str = ""
    trust_class: str = "mutating"
    data_class: str = "internal"
    disposition: str = "retain"
    mode: str = ""
    role_mode: str = ""
    scope: str = ""
    risk_class: str = "low"
    budgets: dict[str, Any] | None = None
    eval_suites: list[str] | None = None
    stop_conditions: list[str] | None = None
    skills: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentEntry:
        return cls(
            id=data["id"],
            owner=data.get("owner", ""),
            title=data.get("title", ""),
            body_path=data.get("body_path", ""),
            version=data.get("version", "0.1.0"),
            targets=data.get("targets", []),
            permission_profile=data.get("permission_profile", ""),
            trust_class=data.get("trust_class", "mutating"),
            data_class=data.get("data_class", "internal"),
            disposition=data.get("disposition", "retain"),
            mode=data.get("mode", ""),
            role_mode=data.get("role_mode", ""),
            scope=data.get("scope", ""),
            risk_class=data.get("risk_class", "low"),
            budgets=data.get("budgets"),
            eval_suites=data.get("eval_suites"),
            stop_conditions=data.get("stop_conditions"),
            skills=data.get("skills"),
        )


@dataclass(frozen=True)
class CommandEntry:
    """Typed command entry in the manifest registry."""

    id: str
    owner: str
    title: str
    body_path: str
    version: str
    targets: list[str] = field(default_factory=list)
    permission_profile: str = ""
    trust_class: str = "mutating"
    data_class: str = "internal"
    disposition: str = "retain"
    scope: str = ""
    risk_class: str = "low"
    skills: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CommandEntry:
        return cls(
            id=data["id"],
            owner=data.get("owner", ""),
            title=data.get("title", ""),
            body_path=data.get("body_path", ""),
            version=data.get("version", "0.1.0"),
            targets=data.get("targets", []),
            permission_profile=data.get("permission_profile", ""),
            trust_class=data.get("trust_class", "mutating"),
            data_class=data.get("data_class", "internal"),
            disposition=data.get("disposition", "retain"),
            scope=data.get("scope", ""),
            risk_class=data.get("risk_class", "low"),
            skills=data.get("skills"),
        )


@dataclass(frozen=True)
class SkillEntry:
    """Typed skill entry in the manifest registry."""

    id: str
    owner: str
    title: str
    body_path: str
    version: str
    targets: list[str] = field(default_factory=list)
    scope: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkillEntry:
        return cls(
            id=data["id"],
            owner=data.get("owner", ""),
            title=data.get("title", ""),
            body_path=data.get("body_path", ""),
            version=data.get("version", "0.1.0"),
            targets=data.get("targets", []),
            scope=data.get("scope", ""),
        )


@dataclass(frozen=True)
class EvalSuiteEntry:
    """Typed eval-suite entry in the manifest registry."""

    id: str
    owner: str
    title: str
    min_cases: int
    suite_path: str
    version: str = "0.1.0"
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvalSuiteEntry:
        return cls(
            id=data["id"],
            owner=data.get("owner", ""),
            title=data.get("title", ""),
            min_cases=data.get("min_cases", 1),
            suite_path=data.get("suite_path", ""),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
        )


# ---------------------------------------------------------------------------
# Typed Manifest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Manifest:
    """Typed evolooption manifest container."""

    schema_version: str
    manifest_version: str
    canonical_layer_version: str
    agents: dict[str, AgentEntry] = field(default_factory=dict)
    commands: dict[str, CommandEntry] = field(default_factory=dict)
    skills: dict[str, SkillEntry] = field(default_factory=dict)
    eval_suites: dict[str, EvalSuiteEntry] = field(default_factory=dict)
    generated_by: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Manifest:
        agents: dict[str, AgentEntry] = {}
        for agent_data in data.get("agents", []):
            entry = AgentEntry.from_dict(agent_data)
            agents[entry.id] = entry

        commands: dict[str, CommandEntry] = {}
        for cmd_data in data.get("commands", []):
            entry = CommandEntry.from_dict(cmd_data)
            commands[entry.id] = entry

        skills: dict[str, SkillEntry] = {}
        for skill_data in data.get("skills", []):
            entry = SkillEntry.from_dict(skill_data)
            skills[entry.id] = entry

        eval_suites: dict[str, EvalSuiteEntry] = {}
        for evs_data in data.get("eval_suites", []):
            entry = EvalSuiteEntry.from_dict(evs_data)
            eval_suites[entry.id] = entry

        return cls(
            schema_version=data.get("schema_version", "1.0.0"),
            manifest_version=data.get("manifest_version", "1.0.0"),
            canonical_layer_version=data.get("canonical_layer_version", "1.0.0"),
            generated_by=data.get("generated_by", ""),
            agents=agents,
            commands=commands,
            skills=skills,
            eval_suites=eval_suites,
        )

    def get_agent(self, agent_id: str) -> AgentEntry | None:
        """Look up an agent by its id."""
        return self.agents.get(agent_id)

    def get_command(self, command_id: str) -> CommandEntry | None:
        """Look up a command by its id."""
        return self.commands.get(command_id)

    def get_skill(self, skill_id: str) -> SkillEntry | None:
        """Look up a skill by its id."""
        return self.skills.get(skill_id)

    def get_eval_suite(self, suite_id: str) -> EvalSuiteEntry | None:
        """Look up an eval suite by its id."""
        return self.eval_suites.get(suite_id)

    def list_eval_suites_for_agent(self, agent_id: str) -> list[EvalSuiteEntry]:
        """Return eval suites referenced by a specific agent via its eval_suites field."""
        agent = self.agents.get(agent_id)
        if agent is None or not agent.eval_suites:
            return []
        return [
            self.eval_suites[suite_id]
            for suite_id in agent.eval_suites
            if suite_id in self.eval_suites
        ]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_manifest(path: str | Path) -> tuple[Manifest | None, list[str]]:
    """Load and validate a manifest file, returning a typed Manifest.

    Returns (manifest, errors). If validation fails, manifest is None.
    """
    raw, errors = _load_raw_manifest(str(path))
    if raw is None:
        return None, errors
    manifest = Manifest.from_dict(raw)
    return manifest, errors


def validate_manifest_file(path: str | Path) -> list[str]:
    """Validate a manifest file and return error list (empty = valid)."""
    raw, errors = _load_raw_manifest(str(path))
    if raw is None:
        return errors
    return validate_manifest(raw)


__all__ = [
    "AgentEntry",
    "CommandEntry",
    "DataClass",
    "Disposition",
    "EvalSuiteEntry",
    "Manifest",
    "SkillEntry",
    "TrustClass",
    "load_manifest",
    "validate_manifest_file",
]
