from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatchcase

from evolooption.execution.policy import ActionPolicy


class AutonomyTier(str, Enum):
    CONSERVATIVE = "conservative"
    ASSISTED = "assisted"
    FULL_AUTO = "full-auto"


@dataclass(frozen=True)
class ProtectedSurface:
    globs: tuple[str, ...] = ()

    def protects(self, path: str) -> bool:
        normalized = path.replace("\\", "/")
        return any(_matches_glob(normalized, pattern.replace("\\", "/")) for pattern in self.globs)

    def validate_changed_paths(self, changed_paths: list[str]) -> None:
        blocked = [path for path in changed_paths if self.protects(path)]
        if blocked:
            raise PermissionError("protected surface modified: " + ", ".join(blocked))


def action_policy_for_tier(
    tier: AutonomyTier,
    *,
    allowed_tools: set[str] | None = None,
    spend_limit: float | None = None,
    rate_limit_per_minute: int | None = None,
) -> ActionPolicy:
    require_human_approval = tier is AutonomyTier.CONSERVATIVE
    return ActionPolicy(
        allowed_tools=allowed_tools or set(),
        require_human_approval=require_human_approval,
        spend_limit=spend_limit,
        rate_limit_per_minute=rate_limit_per_minute,
    )


def _matches_glob(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-2]
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return fnmatchcase(path, pattern)
