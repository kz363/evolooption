from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath


class AutonomyTier(str, Enum):
    CONSERVATIVE = "conservative"
    ASSISTED = "assisted"
    FULL_AUTO = "full-auto"


@dataclass(frozen=True)
class ProtectedSurface:
    globs: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()
    baseline_tests: tuple[str, ...] = ()

    def protects(self, path: str) -> bool:
        pure_path = PurePath(path)
        return any(pure_path.match(pattern) for pattern in self.globs)

    def validate_changed_paths(self, changed_paths: list[str]) -> None:
        blocked = [path for path in changed_paths if self.protects(path)]
        if blocked:
            raise PermissionError("protected surface modified: " + ", ".join(blocked))
