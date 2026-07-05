from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

ProposalKind = Literal["new-agent", "new-skill", "config-change", "code-change"]


@dataclass(frozen=True)
class Signal:
    kind: str
    source: str
    strength: float
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Proposal:
    kind: ProposalKind
    name: str
    rationale: str
    artifacts: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Outcome:
    goal: str
    metric_value: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Postmortem:
    outcome: Outcome
    root_causes: list[str]
    lessons: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
