from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from evolooption.evolution.models import Proposal
from evolooption.evolution.retirement import RetiredFrameworkError

MetricSnapshotHook = Callable[[], dict[str, object]]


@dataclass(frozen=True)
class ScaffoldRequest:
    proposal: Proposal
    root: Path
    metric_snapshot_hook: MetricSnapshotHook | None = None


@dataclass(frozen=True)
class ScaffoldResult:
    written_paths: list[Path] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


class Scaffolder:
    def scaffold(self, request: ScaffoldRequest) -> ScaffoldResult:
        raise RetiredFrameworkError(
            "evolooption scaffolding is retired; artifact writes are unavailable"
        )
