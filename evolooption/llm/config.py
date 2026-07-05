import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LLMConfig:
    provider: str
    roles: dict[str, str] = field(default_factory=dict)
    base_url: str | None = None
    api_key_env: str | None = None

    @classmethod
    def load(cls, path: Path) -> "LLMConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            provider=str(data["provider"]),
            roles={str(k): str(v) for k, v in data.get("roles", {}).items()},
            base_url=data.get("base_url"),
            api_key_env=data.get("api_key_env"),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "provider": self.provider,
                    "roles": self.roles,
                    "base_url": self.base_url,
                    "api_key_env": self.api_key_env,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
