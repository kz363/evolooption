from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from evolooption.evolution.models import Proposal

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
        snapshot = request.metric_snapshot_hook() if request.metric_snapshot_hook else None
        written: list[Path] = []
        for relative_path, content in request.proposal.artifacts.items():
            target = (request.root / relative_path).resolve()
            root = request.root.resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"artifact escapes scaffold root: {relative_path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(target)
        return ScaffoldResult(
            written_paths=written,
            metadata={"metric_snapshot": snapshot},
        )
