from dataclasses import dataclass, field

from evolooption.agents.spec import AgentSpec, QueryContext


@dataclass
class AgentSelector:
    always_active: list[str] = field(default_factory=list)
    optional_agents: dict[str, AgentSpec] = field(default_factory=dict)
    specs: dict[str, AgentSpec] = field(default_factory=dict)

    def select(self, context: QueryContext) -> list[AgentSpec]:
        selected: list[AgentSpec] = []
        for name in self.always_active:
            spec = self.specs.get(name) or self.optional_agents.get(name)
            if spec is not None:
                selected.append(spec)
        for name, spec in self.optional_agents.items():
            if name in self.always_active:
                continue
            if spec.activation is None or spec.activation.matches(context.values):
                selected.append(spec)
        return selected


def select_agents(selector: AgentSelector, context: QueryContext) -> list[AgentSpec]:
    return selector.select(context)
