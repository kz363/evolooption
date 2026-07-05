from dataclasses import dataclass
from typing import Any, Protocol


class StructuredOutputError(ValueError):
    pass


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


def validate_structured_output(value: Any, schema: dict[str, Any]) -> dict[str, Any]:
    if schema.get("type", "object") != "object":
        raise StructuredOutputError("only object schemas are supported")
    if not isinstance(value, dict):
        raise StructuredOutputError("structured output must be an object")
    for key in schema.get("required", []):
        if key not in value:
            raise StructuredOutputError(f"structured output missing required key: {key}")
    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for key, property_schema in properties.items():
            if key in value and isinstance(property_schema, dict):
                _validate_type(key, value[key], property_schema.get("type"))
    return value


def _validate_type(key: str, value: Any, expected: Any) -> None:
    if expected is None:
        return
    expected_types = expected if isinstance(expected, list) else [expected]
    if not any(_matches_type(value, item) for item in expected_types):
        raise StructuredOutputError(f"structured output key has wrong type: {key}")


def _matches_type(value: Any, expected: str) -> bool:
    match expected:
        case "object":
            return isinstance(value, dict)
        case "array":
            return isinstance(value, list)
        case "string":
            return isinstance(value, str)
        case "number":
            return isinstance(value, int | float) and not isinstance(value, bool)
        case "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        case "boolean":
            return isinstance(value, bool)
        case "null":
            return value is None
        case _:
            return True
