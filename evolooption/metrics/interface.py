from typing import Any, Protocol

from evolooption.loop.contracts import Goal


class MetricEvaluator(Protocol):
    def evaluate(self, goal: Goal, state: dict[str, Any]) -> float: ...
