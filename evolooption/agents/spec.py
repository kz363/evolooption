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


@dataclass(frozen=True)
class QueryContext:
    values: dict[str, Any]
