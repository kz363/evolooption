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


def make_loop(
    executor=None,
    policy=None,
    protected_surface=None,
    approval_callback=None,
    changed_paths_provider=None,
    ledger_path=None,
) -> EvolutionLoop:
    return EvolutionLoop(
        metric_evaluator=FakeMetricEvaluator(),
        action_executor=executor or FakeActionExecutor(),
        action_policy=policy
        or ActionPolicy(allowed_tools={"improve"}, require_human_approval=False),
        protected_surface=protected_surface or ProtectedSurface(),
        root_cause_analyzer=StaticRootCauseAnalyzer(["low_score"]),
        approval_callback=approval_callback,
        changed_paths_provider=changed_paths_provider,
        ledger_path=ledger_path,
    )


def test_loop_runs_fake_domain_to_success() -> None:
    executor = FakeActionExecutor()
    loop = make_loop(
        executor=executor,
        protected_surface=ProtectedSurface(globs=("metrics/**",)),
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"score": 1.0, "target": 1.0, "action": {"tool": "improve", "arguments": {}}},
    )

    assert ledger.latest().success
    assert executor.calls == [("improve", {})]


def test_loop_records_unallowed_action_as_blocked_iteration() -> None:
    executor = FakeActionExecutor()
    loop = make_loop(
        executor=executor,
        policy=ActionPolicy(allowed_tools=set(), require_human_approval=False),
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"action": {"tool": "blocked", "arguments": {}}},
    )

    assert ledger.latest().success is False
    assert ledger.latest().metadata["blocked"] is True
    assert "tool is not allowed" in ledger.latest().metadata["reason"]
    assert executor.calls == []


def test_loop_blocks_missing_human_approval_fail_closed() -> None:
    executor = FakeActionExecutor()
    loop = make_loop(
        executor=executor,
        policy=ActionPolicy(allowed_tools={"improve"}, require_human_approval=True),
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"action": {"tool": "improve", "arguments": {}, "approved": True}},
    )

    assert ledger.latest().metadata["blocked"] is True
    assert "human approval required" in ledger.latest().metadata["reason"]
    assert executor.calls == []


def test_loop_allows_operator_approved_action() -> None:
    executor = FakeActionExecutor()
    loop = make_loop(
        executor=executor,
        policy=ActionPolicy(allowed_tools={"improve"}, require_human_approval=True),
        approval_callback=lambda tool, arguments: tool == "improve" and arguments == {"safe": True},
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {
            "score": 1.0,
            "target": 1.0,
            "action": {"tool": "improve", "arguments": {"safe": True}},
        },
    )

    assert ledger.latest().success
    assert executor.calls == [("improve", {"safe": True})]


def test_loop_records_spend_and_blocks_later_iteration() -> None:
    executor = FakeActionExecutor()
    loop = make_loop(
        executor=executor,
        policy=ActionPolicy(
            allowed_tools={"improve"},
            require_human_approval=False,
            spend_limit=1.0,
        ),
        ledger_path=None,
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"score": 0.0, "target": 1.0, "action": {"tool": "improve", "cost": 0.75}},
    )

    assert [result.metadata.get("blocked", False) for result in ledger.results] == [False, True]
    assert len(executor.calls) == 1


def test_loop_records_rate_and_blocks_later_iteration() -> None:
    executor = FakeActionExecutor()
    loop = make_loop(
        executor=executor,
        policy=ActionPolicy(
            allowed_tools={"improve"},
            require_human_approval=False,
            rate_limit_per_minute=1,
        ),
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"score": 0.0, "target": 1.0, "action": {"tool": "improve"}},
    )

    assert [result.metadata.get("blocked", False) for result in ledger.results] == [False, True]
    assert len(executor.calls) == 1


def test_loop_blocks_protected_surface_changes_from_provider() -> None:
    executor = FakeActionExecutor()
    loop = make_loop(
        executor=executor,
        protected_surface=ProtectedSurface(globs=("metrics/**",)),
        changed_paths_provider=lambda: ["metrics/evaluator.py"],
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"action": {"tool": "improve", "arguments": {}}},
    )

    assert ledger.latest().metadata["blocked"] is True
    assert "protected surface modified" in ledger.latest().metadata["reason"]
    assert executor.calls == [("improve", {})]


def test_loop_allows_unprotected_changed_paths() -> None:
    executor = FakeActionExecutor()
    loop = make_loop(
        executor=executor,
        protected_surface=ProtectedSurface(globs=("metrics/**",)),
        changed_paths_provider=lambda: ["agents/selector.py"],
    )

    ledger = loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"score": 1.0, "target": 1.0, "action": {"tool": "improve", "arguments": {}}},
    )

    assert ledger.latest().success
    assert executor.calls == [("improve", {})]


def test_loop_persists_iteration_ledger_jsonl(tmp_path) -> None:
    loop = make_loop(ledger_path=tmp_path / "ledger.jsonl")

    loop.run(
        Goal(prompt="raise score", target_metric="score"),
        {"score": 1.0, "target": 1.0, "action": {"tool": "improve", "arguments": {}}},
    )

    assert "raise score" not in (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")
    assert '"success": true' in (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")


def test_protected_surface_rejects_reward_hacking_path() -> None:
    surface = ProtectedSurface(globs=("metrics/**", "policy/**", "tests/baseline/**"))

    with pytest.raises(PermissionError):
        surface.validate_changed_paths(["metrics/evaluator.py"])


def test_action_policy_enforces_spend_limit() -> None:
    policy = ActionPolicy(allowed_tools={"run"}, spend_limit=1.0)
    policy.record(cost=0.75)

    assert not policy.allows("run", estimated_cost=0.5)
