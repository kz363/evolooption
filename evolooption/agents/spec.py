from dataclasses import dataclass, field
from typing import Any, Literal

Operator = Literal["equals", "contains", "exists", "in"]


@dataclass(frozen=True)
class ActivationRule:
    field: str
    operator: Operator
    value: Any = None

    def matches(self, context: dict[str, Any]) -> bool:
        actual = context.get(self.field)
        if self.operator == "equals":
            return actual == self.value
        if self.operator == "contains":
            return isinstance(actual, str | list | tuple | set) and self.value in actual
        if self.operator == "exists":
            return self.field in context and actual is not None
        if self.operator == "in":
            return isinstance(self.value, list | tuple | set) and actual in self.value
        raise ValueError(f"unsupported activation operator: {self.operator}")


@dataclass(frozen=True)
class AgentSpec:
    name: str
    prompt: str
    schema: dict[str, Any] = field(default_factory=dict)
    activation: ActivationRule | None = None
    # Optional fields for multi-agent systems architect discipline (E4 resolved:
    # only evolution/registry.py constructs AgentSpec, using kwargs + defaults).
    context_budget: dict[str, Any] | None = None  # e.g., {"max_tokens": 4000}
    tools_permitted: list[str] | None = None  # subset of allowed tools for this agent
    fallback: str | None = None  # name of a fallback agent or rule-based handler
    not_responsible_for: list[str] | None = None  # behaviors this agent does NOT own


@dataclass(frozen=True)
class QueryContext:
    values: dict[str, Any]
