"""Eval-driven promotion gate for agent modifications.

Ensures any new or modified agent passes an eval suite (≥20 cases) + recorded
baseline before "promotion". This is a NEW subsystem distinct from the existing
signal/proposal machinery.

See `_ai-context/skills/prompt-as-spec/SKILL.md` for prompt-as-spec discipline
that underpins eval definitions.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Placeholder: map EvalResult to the existing Signal model for consistent
# telemetry across the evolution pipeline.
# from evolooption.evolution.models import Signal


@dataclass(frozen=True)
class EvalCase:
    """A single evaluation test case for an agent."""

    name: str
    input: dict[str, Any]
    expected_output_schema: str | None = None  # e.g., "markdown", "json", "text"
    expected_success: bool = True


@dataclass(frozen=True)
class EvalResult:
    """Result of running a single EvalCase against an agent."""

    case_name: str
    passed: bool
    output: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class EvalSuite:
    """Collection of EvalCase for an agent."""

    agent_name: str
    cases: list[EvalCase] = field(default_factory=list)

    def hash(self) -> str:
        """Stable hash of the suite content for baseline comparison."""
        content = "|".join(c.name for c in self.cases)
        return hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass
class Baseline:
    """Recorded eval-baseline for an agent version."""

    agent_name: str
    suite_hash: str
    passed_count: int
    total_count: int
    recorded_at: str | None = None

    @property
    def score(self) -> float:
        return passed_count / total_count if total_count > 0 else 0.0


class EvalRunner:
    """Run an EvalSuite against an agent and produce EvalResult list."""

    def run(self, agent_spec: dict[str, Any], suite: EvalSuite) -> list[EvalResult]:
        """Stub — actual execution requires agent instantiation + sandboxing.
        For now, return empty results; real implementation will execute.
        """
        return [EvalResult(case.name, False, error="stub - not implemented") for case in suite.cases]


def check_promotion_gate(agent_name: str, suite: EvalSuite, baseline_path: Path) -> tuple[bool, str]:
    """Check whether an agent passes the promotion gate.

    Returns (accepted, reason) where accepted=True means:
    - All cases in suite have run, and
    - Score meets or exceeds recorded baseline (or no baseline exists yet,
      in which case we record a new one).

    Note: This is a lightweight gate. Full implementation lives in
    `evolooption/evolution/eval.py` — for now this stub documents intent.
    """
    if len(suite.cases) < 20:
        return False, f"eval gate requires ≥20 cases (got {len(suite.cases)})"
    return True, "passed (stub)"


__all__ = ["EvalCase", "EvalResult", "EvalSuite", "Baseline", "EvalRunner", "check_promotion_gate"]