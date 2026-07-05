import time
from dataclasses import dataclass, field


@dataclass
class ActionPolicy:
    allowed_tools: set[str] = field(default_factory=set)
    require_human_approval: bool = True
    spend_limit: float | None = None
    rate_limit_per_minute: int | None = None
    spent: float = 0.0
    _timestamps: list[float] = field(default_factory=list)

    def allows(self, tool_name: str, *, estimated_cost: float = 0.0) -> bool:
        if tool_name not in self.allowed_tools:
            return False
        if self.spend_limit is not None and self.spent + estimated_cost > self.spend_limit:
            return False
        if self.rate_limit_per_minute is None:
            return True
        now = time.monotonic()
        self._timestamps = [item for item in self._timestamps if now - item < 60]
        return len(self._timestamps) < self.rate_limit_per_minute

    def record(self, *, cost: float = 0.0) -> None:
        self.spent += cost
        self._timestamps.append(time.monotonic())
