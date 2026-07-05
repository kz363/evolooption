from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    raw: dict[str, Any] | None = None


class LLMClient(Protocol):
    def complete(self, messages: list[LLMMessage], *, role: str) -> LLMResponse: ...

    def structured(
        self,
        messages: list[LLMMessage],
        *,
        role: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]: ...
