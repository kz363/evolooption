from dataclasses import dataclass, field


@dataclass
class RoleRegistry:
    roles: dict[str, str] = field(default_factory=dict)

    def set_model(self, role: str, model: str) -> None:
        if not role:
            raise ValueError("role is required")
        if not model:
            raise ValueError("model is required")
        self.roles[role] = model

    def model_for(self, role: str) -> str:
        try:
            return self.roles[role]
        except KeyError as exc:
            raise KeyError(f"unknown LLM role: {role}") from exc
