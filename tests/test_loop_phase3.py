import pytest

from evolooption.evolution.postmortem import StaticRootCauseAnalyzer
from evolooption.execution.interfaces import Tool
from evolooption.execution.policy import ActionPolicy
from evolooption.loop import EvolutionLoop, Goal
from evolooption.policy import ProtectedSurface


class FakeMetricEvaluator:
    def evaluate(self, goal, state):
        return float(state.get("score", 0.0))


class FakeActionExecutor:
    def __init__(self) -> None:
        self.calls = []

    def tools(self):
        return [Tool(name="improve", description="improve fake score")]

    def execute(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        return {"ok": True}


def test_loop_runs_fake_domain_to_success() -> None:
    executor = FakeActionExecutor()
    loop = EvolutionLoop(
        metric_evaluator=FakeMetricEvaluator(),
        action_executor=executor,
        action_policy=ActionPolicy(allowed_tools={"improve"}, require_human_approval=False),
        protected_surface=ProtectedSurface(globs=("metrics/**",)),
        root_cause_analyzer=StaticRootCauseAnalyzer(["low_score"]),
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"score": 1.0, "target": 1.0, "action": {"tool": "improve", "arguments": {}}},
    )

    assert ledger.latest().success
    assert executor.calls == [("improve", {})]


def test_loop_rejects_unallowed_action() -> None:
    loop = EvolutionLoop(
        metric_evaluator=FakeMetricEvaluator(),
        action_executor=FakeActionExecutor(),
        action_policy=ActionPolicy(allowed_tools=set()),
        protected_surface=ProtectedSurface(),
        root_cause_analyzer=StaticRootCauseAnalyzer(["low_score"]),
    )

    with pytest.raises(PermissionError):
        loop.run(
            Goal(prompt="raise score", target_metric="score"),
            {"action": {"tool": "blocked", "arguments": {}}},
        )


def test_protected_surface_rejects_reward_hacking_path() -> None:
    surface = ProtectedSurface(globs=("metrics/**", "policy/**", "tests/baseline/**"))

    with pytest.raises(PermissionError):
        surface.validate_changed_paths(["metrics/evaluator.py"])


def test_action_policy_enforces_spend_limit() -> None:
    policy = ActionPolicy(allowed_tools={"run"}, spend_limit=1.0)
    policy.record(cost=0.75)

    assert not policy.allows("run", estimated_cost=0.5)
