import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
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
    jsonl_path: Path | None = None

    @classmethod
    def from_path(cls, path: str | Path | None) -> "IterationLedger":
        if path is None:
            return cls()
        jsonl_path = Path(path)
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        return cls(jsonl_path=jsonl_path)

    def add(self, result: IterationResult) -> None:
        self.results.append(result)
        if self.jsonl_path is not None:
            with self.jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(result), sort_keys=True) + "\n")

    def latest(self) -> IterationResult | None:
        return self.results[-1] if self.results else None


@dataclass(frozen=True)
class LoopState:
    values: dict[str, Any] = field(default_factory=dict)
