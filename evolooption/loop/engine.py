from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evolooption.evolution.models import Outcome
from evolooption.evolution.postmortem import RootCauseAnalyzer
from evolooption.execution.interfaces import ActionExecutor
from evolooption.execution.policy import ActionPolicy
from evolooption.loop.contracts import Goal, IterationResult
from evolooption.loop.orchestrator import IterationLedger, StaticTeamSynthesizer, TeamSynthesizer
from evolooption.metrics.interface import MetricEvaluator
from evolooption.policy.autonomy import ProtectedSurface


@dataclass
class EvolutionLoop:
    metric_evaluator: MetricEvaluator
    action_executor: ActionExecutor
    action_policy: ActionPolicy
    protected_surface: ProtectedSurface
    root_cause_analyzer: RootCauseAnalyzer
    team_synthesizer: TeamSynthesizer | None = None
    max_iterations: int = 3
    approval_callback: Callable[[str, dict[str, Any]], bool] | None = None
    changed_paths_provider: Callable[[], list[str]] | None = None
    ledger_path: str | Path | None = None

    def run(self, goal: Goal, state: dict[str, Any]) -> IterationLedger:
        ledger = IterationLedger.from_path(self.ledger_path)
        synthesizer = self.team_synthesizer or StaticTeamSynthesizer([])
        team = synthesizer.synthesize(goal)
        for iteration in range(1, self.max_iterations + 1):
            proposed_action = state.get("action")
            if proposed_action is not None:
                try:
                    self._execute_allowed_action(proposed_action)
                except PermissionError as error:
                    ledger.add(
                        IterationResult(
                            iteration=iteration,
                            metric_value=0.0,
                            success=False,
                            metadata={
                                "team": team,
                                "blocked": True,
                                "reason": str(error),
                            },
                        )
                    )
                    break
            metric_value = self.metric_evaluator.evaluate(goal, state)
            success = metric_value >= float(state.get("target", 1.0))
            result = IterationResult(
                iteration=iteration,
                metric_value=metric_value,
                success=success,
                metadata={"team": team},
            )
            ledger.add(result)
            if success:
                break
            self.root_cause_analyzer.analyze(
                Outcome(goal=goal.prompt, metric_value=metric_value, success=False)
            )
        return ledger

    def _execute_allowed_action(self, action: dict[str, Any]) -> None:
        tool_name = str(action.get("tool", ""))
        arguments = dict(action.get("arguments", {}))
        estimated_cost = float(action.get("cost", 0.0))
        if not self.action_policy.allows(tool_name, estimated_cost=estimated_cost):
            raise PermissionError(f"tool is not allowed or budget-limited: {tool_name}")
        if self.action_policy.require_human_approval and (
            self.approval_callback is None or not self.approval_callback(tool_name, arguments)
        ):
            raise PermissionError(f"human approval required for tool: {tool_name}")
        self.action_executor.execute(tool_name, arguments)
        self.action_policy.record(cost=estimated_cost)
        if self.changed_paths_provider is not None:
            self.protected_surface.validate_changed_paths(self.changed_paths_provider())
