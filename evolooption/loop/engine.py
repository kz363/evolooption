from dataclasses import dataclass
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

    def run(self, goal: Goal, state: dict[str, Any]) -> IterationLedger:
        ledger = IterationLedger()
        synthesizer = self.team_synthesizer or StaticTeamSynthesizer([])
        team = synthesizer.synthesize(goal)
        for iteration in range(1, self.max_iterations + 1):
            proposed_action = state.get("action")
            if proposed_action is not None:
                self._execute_allowed_action(proposed_action)
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
        if not self.action_policy.allows(tool_name):
            raise PermissionError(f"tool is not allowed: {tool_name}")
        self.action_executor.execute(tool_name, arguments)
