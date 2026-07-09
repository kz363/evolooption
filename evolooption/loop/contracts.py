from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Goal:
    prompt: str
    target_metric: str
    metadata: dict[str, Any] = field(default_factory=dict)
    # trace_id for multi-hop observability (multi-agent systems architect discipline)
    trace_id: str | None = None


@dataclass(frozen=True)
class IterationResult:
    iteration: int
    metric_value: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    # trace_id propagates through the ledger for per-iteration debugging
    trace_id: str | None = None
