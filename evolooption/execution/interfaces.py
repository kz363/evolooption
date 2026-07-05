from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ActionExecutor(Protocol):
    def tools(self) -> list[Tool]: ...

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...
