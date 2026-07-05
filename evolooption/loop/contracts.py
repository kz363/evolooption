from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Goal:
    prompt: str
    target_metric: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IterationResult:
    iteration: int
    metric_value: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)
