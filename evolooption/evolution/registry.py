import json
from pathlib import Path
from typing import Any

from evolooption.agents.spec import ActivationRule, AgentSpec
from evolooption.evolution.retirement import RetiredFrameworkError


def activation_from_dict(data: dict[str, Any] | None) -> ActivationRule | None:
    if data is None:
        return None
    return ActivationRule(
        field=str(data["field"]),
        operator=data["operator"],
        value=data.get("value"),
    )


def activation_to_dict(rule: ActivationRule | None) -> dict[str, Any] | None:
    if rule is None:
        return None
    return {"field": rule.field, "operator": rule.operator, "value": rule.value}


def load_dynamic_entries(path: Path) -> list[AgentSpec]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    entries: list[AgentSpec] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        prompt = str(item.get("prompt", "")).strip()
        if not name or not prompt:
            continue
        entries.append(
            AgentSpec(
                name=name,
                prompt=prompt,
                schema=dict(item.get("schema", {})),
                activation=activation_from_dict(item.get("activation")),
            )
        )
    return entries


def write_dynamic_entry(path: Path, spec: AgentSpec) -> None:
    raise RetiredFrameworkError("evolooption dynamic registry is retired; writes are unavailable")


def remove_dynamic_entry(path: Path, name: str) -> bool:
    raise RetiredFrameworkError("evolooption dynamic registry is retired; writes are unavailable")


def merge_specs(
    base: dict[str, AgentSpec],
    dynamic_entries: list[AgentSpec],
) -> dict[str, AgentSpec]:
    merged = dict(base)
    for entry in dynamic_entries:
        merged[entry.name] = entry
    return merged


def _write_entries(path: Path, entries: list[AgentSpec]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps([_spec_to_dict(entry) for entry in entries], indent=2),
        encoding="utf-8",
    )
    temp_path.replace(path)


def _spec_to_dict(spec: AgentSpec) -> dict[str, Any]:
    return {
        "name": spec.name,
        "prompt": spec.prompt,
        "schema": spec.schema,
        "activation": activation_to_dict(spec.activation),
    }
