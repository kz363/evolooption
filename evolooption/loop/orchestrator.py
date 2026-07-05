from dataclasses import dataclass, field
from typing import Any, Protocol

from evolooption.loop.contracts import Goal, IterationResult


class TeamSynthesizer(Protocol):
    def synthesize(self, goal: Goal) -> list[str]: ...


@dataclass
class StaticTeamSynthesizer:
    agents: list[str]

    def synthesize(self, goal: Goal) -> list[str]:
        return list(self.agents)


@dataclass
class IterationLedger:
    results: list[IterationResult] = field(default_factory=list)

    def add(self, result: IterationResult) -> None:
        self.results.append(result)

    def latest(self) -> IterationResult | None:
        return self.results[-1] if self.results else None


@dataclass(frozen=True)
class LoopState:
    values: dict[str, Any] = field(default_factory=dict)
