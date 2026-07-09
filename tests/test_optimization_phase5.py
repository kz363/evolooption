"""Offline tests for the evolooption.optimization subpackage (Phase 5)."""

from __future__ import annotations

from dataclasses import dataclass, field

from evolooption.evolution.models import Signal
from evolooption.execution.policy import ActionPolicy
from evolooption.llm.client import LLMMessage, LLMResponse
from evolooption.optimization import (
    CostTracker,
    LLMJudge,
    OptimizationPolicy,
    OptimizationProposalRule,
    OptimizationSignalKind,
    Provider,
    ProviderCircuitBreaker,
    ProviderPricing,
    ProviderRouter,
    RubricCriterion,
    ShadowResult,
    ShadowRunner,
    TokenUsage,
    build_default_optimization_rules,
    collect_signals,
    cost_for_usage,
    extract_ollama_usage,
    extract_openai_usage,
    extract_usage,
)


@dataclass
class FakeClient:
    """Deterministic fake LLMClient for tests.

    ``respond`` is a callable that maps the incoming messages to an ``LLMResponse``.
    It is the only hook tests need to drive behaviour.
    """

    respond: object
    call_count: int = 0

    def complete(self, messages, *, role):
        self.call_count += 1
        return self.respond(messages, role=role)


def _ok(content: str = "ok", raw: dict | None = None) -> LLMResponse:
    return LLMResponse(content=content, raw=raw)


def _boom(message: str = "boom") -> FakeClient:
    def _respond(messages, *, role):
        raise RuntimeError(message)
    return FakeClient(respond=_respond)


def test_extract_ollama_usage_reads_known_fields() -> None:
    raw = {"prompt_eval_count": 10, "eval_count": 5, "other": "ignore"}
    usage = extract_ollama_usage(raw)
    assert usage == TokenUsage(input_tokens=10, output_tokens=5)


def test_extract_ollama_usage_handles_missing_keys() -> None:
    assert extract_ollama_usage(None) == TokenUsage()
    assert extract_ollama_usage({}) == TokenUsage()


def test_extract_openai_usage_reads_usage_block() -> None:
    raw = {"usage": {"prompt_tokens": 7, "completion_tokens": 3}}
    assert extract_openai_usage(raw) == TokenUsage(input_tokens=7, output_tokens=3)


def test_extract_usage_dispatches_by_provider() -> None:
    ollama_raw = {"prompt_eval_count": 2, "eval_count": 1}
    openai_raw = {"usage": {"prompt_tokens": 4, "completion_tokens": 1}}
    assert extract_usage(ollama_raw, provider="ollama").input_tokens == 2
    assert extract_usage(openai_raw, provider="openai-compatible").input_tokens == 4
    assert extract_usage(ollama_raw, provider="unknown") == TokenUsage()


def test_cost_for_usage_uses_per_million_pricing() -> None:
    pricing = ProviderPricing(input_per_million=1.0, output_per_million=2.0)
    cost = cost_for_usage(TokenUsage(input_tokens=500_000, output_tokens=250_000), pricing)
    assert cost == 1.0  # 0.5 * 1 + 0.5 * 2


def test_cost_for_usage_treats_none_pricing_as_free() -> None:
    cost = cost_for_usage(TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000),
                          ProviderPricing(input_per_million=None, output_per_million=None))
    assert cost == 0.0


def test_cost_tracker_records_and_aggregates() -> None:
    tracker = CostTracker(pricing={"a": ProviderPricing(input_per_million=1.0)})
    tracker.record("a", TokenUsage(input_tokens=1_000_000))
    tracker.record("a", TokenUsage(input_tokens=500_000))
    tracker.record("b", TokenUsage(input_tokens=10_000_000))

    assert tracker.total == 1.5
    assert tracker.calls == 3
    assert tracker.per_provider() == {"a": 1.5, "b": 0.0}
    assert tracker.within_budget(2.0)
    assert not tracker.within_budget(1.0)


def test_circuit_breaker_trips_after_threshold_and_recovers_after_cooldown() -> None:
    breaker = ProviderCircuitBreaker(failure_threshold=2, cooldown_seconds=60.0)
    breaker.record_failure("p")
    assert not breaker.is_open("p")
    breaker.record_failure("p")
    assert breaker.is_open("p")
    breaker._tripped_at["p"] -= 120.0
    assert not breaker.is_open("p")


def test_circuit_breaker_manual_trip_and_reset() -> None:
    breaker = ProviderCircuitBreaker(failure_threshold=10, cooldown_seconds=60.0)
    breaker.trip("p")
    assert breaker.is_open("p")
    breaker.reset("p")
    assert not breaker.is_open("p")


def test_circuit_breaker_disabled_when_threshold_zero() -> None:
    breaker = ProviderCircuitBreaker(failure_threshold=0, cooldown_seconds=0.0)
    for _ in range(50):
        breaker.record_failure("p")
    assert not breaker.is_open("p")


def test_router_prefers_highest_weight_and_records_success() -> None:
    tracker = CostTracker(pricing={"expensive": ProviderPricing(input_per_million=10.0)})
    expensive = FakeClient(
        respond=lambda msgs, *, role: _ok("from expensive", {"prompt_eval_count": 1_000_000})
    )
    cheap = FakeClient(
        respond=lambda msgs, *, role: _ok("from cheap", {"prompt_eval_count": 1_000_000})
    )
    router = ProviderRouter(
        providers=[
            Provider(name="expensive", client=expensive, weight=1),
            Provider(name="cheap", client=cheap, weight=10),
        ],
        tracker=tracker,
    )
    response = router.complete([LLMMessage(role="user", content="hi")], role="r")
    assert response.content == "from cheap"
    assert cheap.call_count == 1
    assert expensive.call_count == 0
    assert tracker.total == 0.0
    assert tracker.calls == 1
    assert tracker.per_provider() == {"cheap": 0.0}


def test_router_falls_back_when_primary_fails() -> None:
    tracker = CostTracker()
    boom = _boom("primary dead")
    ok = FakeClient(respond=lambda msgs, *, role: _ok("ok"))
    router = ProviderRouter(
        providers=[
            Provider(name="primary", client=boom, weight=10),
            Provider(name="secondary", client=ok, weight=1),
        ],
        breaker=ProviderCircuitBreaker(failure_threshold=1, cooldown_seconds=60.0),
        tracker=tracker,
    )
    response = router.complete([LLMMessage(role="user", content="hi")], role="r")
    assert response.content == "ok"
    assert boom.call_count == 1
    assert ok.call_count == 1


def test_router_skips_tripped_breakers() -> None:
    breaker = ProviderCircuitBreaker(failure_threshold=1, cooldown_seconds=60.0)
    breaker.trip("primary")
    secondary = FakeClient(respond=lambda msgs, *, role: _ok("from secondary"))
    router = ProviderRouter(
        providers=[
            Provider(name="primary", client=_boom(), weight=10),
            Provider(name="secondary", client=secondary, weight=1),
        ],
        breaker=breaker,
    )
    response = router.complete([LLMMessage(role="user", content="hi")], role="r")
    assert response.content == "from secondary"


def test_router_enforces_max_cost_per_run() -> None:
    tracker = CostTracker(pricing={"p": ProviderPricing(input_per_million=1.0)})
    tracker.total = 0.6
    expensive = FakeClient(respond=lambda msgs, *, role: _ok("x", {"prompt_eval_count": 1_000_000}))
    router = ProviderRouter(
        providers=[Provider(name="p", client=expensive, weight=1)],
        tracker=tracker,
        max_cost_per_run=0.5,
    )
    import pytest
    with pytest.raises(RuntimeError, match="over max_cost_per_run"):
        router.complete([LLMMessage(role="user", content="hi")], role="r")


def test_router_raises_when_no_providers_configured() -> None:
    import pytest
    router = ProviderRouter(providers=[])
    with pytest.raises(RuntimeError, match="no providers"):
        router.complete([LLMMessage(role="user", content="hi")], role="r")


def test_router_raises_when_every_provider_fails() -> None:
    import pytest
    router = ProviderRouter(
        providers=[Provider(name="a", client=_boom("dead"), weight=1)],
        breaker=ProviderCircuitBreaker(failure_threshold=1, cooldown_seconds=60.0),
    )
    with pytest.raises(RuntimeError, match="all providers failed"):
        router.complete([LLMMessage(role="user", content="hi")], role="r")


@dataclass
class ScriptedJudgeClient:
    """Returns a scripted structured response each call."""

    responses: list[dict] = field(default_factory=list)
    call_count: int = 0

    def complete(self, messages, *, role):
        self.call_count += 1
        return LLMResponse(content="unused", raw=None)

    def structured(self, messages, *, role, schema):
        self.call_count += 1
        if not self.responses:
            raise AssertionError("scripted responses exhausted")
        return self.responses.pop(0)


def test_llm_judge_uses_first_response_and_caps_score() -> None:
    rubric = [
        RubricCriterion(name="format", description="JSON ok", points=5),
        RubricCriterion(name="latency", description="fast", points=3),
    ]
    client = ScriptedJudgeClient(
        responses=[
            {"per_criterion": {"format": 5, "latency": 3}, "score": 999, "rationale": "good"},
        ]
    )
    judge = LLMJudge(judge_client=client)
    verdict = judge.grade(output="{}", rubric=rubric)
    assert verdict.score == 8
    assert verdict.per_criterion == {"format": 5, "latency": 3}
    assert verdict.rationale == "good"


def test_llm_judge_clamps_per_criterion_to_max() -> None:
    rubric = [RubricCriterion(name="x", description="d", points=2)]
    client = ScriptedJudgeClient(
        responses=[{"per_criterion": {"x": 100}, "score": 0, "rationale": ""}]
    )
    verdict = LLMJudge(judge_client=client).grade(output="x", rubric=rubric)
    assert verdict.per_criterion == {"x": 2}


def test_llm_judge_rejects_empty_rubric() -> None:
    import pytest
    judge = LLMJudge(judge_client=ScriptedJudgeClient())
    with pytest.raises(ValueError, match="at least one criterion"):
        judge.grade(output="x", rubric=[])


def test_optimization_policy_rejects_invalid_shadow_pct() -> None:
    import pytest
    with pytest.raises(ValueError, match="shadow_traffic_pct"):
        OptimizationPolicy(shadow_traffic_pct=1.5)


def test_optimization_policy_rejects_negative_breaker_threshold() -> None:
    import pytest
    with pytest.raises(ValueError, match="breaker_failure_threshold"):
        OptimizationPolicy(breaker_failure_threshold=-1)


def test_optimization_policy_fail_closed_reflects_action_policy() -> None:
    permissive = OptimizationPolicy(action_policy=ActionPolicy(require_human_approval=False))
    restrictive = OptimizationPolicy(action_policy=ActionPolicy(require_human_approval=True))
    assert not permissive.fail_closed()
    assert restrictive.fail_closed()


def test_shadow_runner_emits_signal_when_candidate_wins() -> None:
    rubric = [RubricCriterion(name="format", description="d", points=5)]
    baseline = FakeClient(respond=lambda msgs, *, role: _ok("baseline"))
    candidate = FakeClient(respond=lambda msgs, *, role: _ok("candidate"))
    judge = LLMJudge(
        judge_client=ScriptedJudgeClient(
            responses=[
                {"per_criterion": {"format": 1}, "score": 1, "rationale": "ok"},  # baseline #1
                {"per_criterion": {"format": 5}, "score": 5, "rationale": "ok"},  # candidate #1
                {"per_criterion": {"format": 1}, "score": 1, "rationale": "ok"},  # baseline #2
                {"per_criterion": {"format": 5}, "score": 5, "rationale": "ok"},  # candidate #2
            ]
        )
    )
    runner = ShadowRunner(
        baseline=baseline,
        candidate=candidate,
        judge=judge,
        policy=OptimizationPolicy(shadow_traffic_pct=1.0),
        rubric=rubric,
        win_rate_threshold=0.6,
        score_margin=1,
        min_samples=2,
        seed=42,
    )
    a = runner.evaluate([LLMMessage(role="user", content="x")], role="r")
    b = runner.evaluate([LLMMessage(role="user", content="x")], role="r")
    assert a.emitted is None
    assert b.emitted is not None
    assert b.emitted.kind == "shadow-win"
    assert b.emitted.strength == 1.0
    assert b.emitted.metadata["sample_size"] == 2


def test_shadow_runner_does_not_emit_when_samples_below_min() -> None:
    rubric = [RubricCriterion(name="x", description="d", points=1)]
    judge = LLMJudge(
        judge_client=ScriptedJudgeClient(
            responses=[
                {"per_criterion": {"x": 0}, "score": 0, "rationale": ""},
                {"per_criterion": {"x": 1}, "score": 1, "rationale": ""},
            ]
        )
    )
    runner = ShadowRunner(
        baseline=FakeClient(respond=lambda msgs, *, role: _ok()),
        candidate=FakeClient(respond=lambda msgs, *, role: _ok()),
        judge=judge,
        policy=OptimizationPolicy(shadow_traffic_pct=1.0),
        rubric=rubric,
        min_samples=10,
        seed=1,
    )
    result = runner.evaluate([LLMMessage(role="user", content="x")], role="r")
    assert result.emitted is None
    assert result.sample_size == 1


def test_shadow_runner_should_divert_respects_policy_and_emission() -> None:
    rubric = [RubricCriterion(name="x", description="d", points=1)]
    runner = ShadowRunner(
        baseline=FakeClient(respond=lambda msgs, *, role: _ok()),
        candidate=FakeClient(respond=lambda msgs, *, role: _ok()),
        judge=LLMJudge(
            judge_client=ScriptedJudgeClient(
                responses=[{"per_criterion": {"x": 1}, "score": 1, "rationale": ""}]
            )
        ),
        policy=OptimizationPolicy(shadow_traffic_pct=0.0),
        rubric=rubric,
    )
    assert not runner.should_divert()
    runner.policy.shadow_traffic_pct = 1.0
    runner._rng.seed(0)
    assert runner.should_divert()
    runner._emitted = True
    assert not runner.should_divert()


def test_shadow_runner_never_runs_candidate_when_pct_is_zero() -> None:
    rubric = [RubricCriterion(name="x", description="d", points=1)]
    baseline = FakeClient(respond=lambda msgs, *, role: _ok("baseline"))
    candidate = FakeClient(respond=lambda msgs, *, role: _ok("candidate"))
    judge = LLMJudge(
        judge_client=ScriptedJudgeClient(
            responses=[{"per_criterion": {"x": 1}, "score": 1, "rationale": ""}]
        )
    )
    runner = ShadowRunner(
        baseline=baseline,
        candidate=candidate,
        judge=judge,
        policy=OptimizationPolicy(shadow_traffic_pct=0.0),
        rubric=rubric,
        seed=7,
    )
    result = runner.evaluate([LLMMessage(role="user", content="x")], role="r")
    # Baseline (live call) always runs; the candidate must NOT run when pct == 0.
    assert baseline.call_count == 1
    assert candidate.call_count == 0
    assert judge.judge_client.call_count == 0
    assert result.sample_size == 0
    assert result.emitted is None


def test_shadow_runner_runs_candidate_on_every_diverted_call() -> None:
    rubric = [RubricCriterion(name="x", description="d", points=1)]
    baseline = FakeClient(respond=lambda msgs, *, role: _ok("baseline"))
    candidate = FakeClient(respond=lambda msgs, *, role: _ok("candidate"))
    judge = LLMJudge(
        judge_client=ScriptedJudgeClient(
            responses=[
                {"per_criterion": {"x": 1}, "score": 1, "rationale": ""},  # baseline #1
                {"per_criterion": {"x": 1}, "score": 1, "rationale": ""},  # candidate #1
                {"per_criterion": {"x": 1}, "score": 1, "rationale": ""},  # baseline #2
                {"per_criterion": {"x": 1}, "score": 1, "rationale": ""},  # candidate #2
            ]
        )
    )
    runner = ShadowRunner(
        baseline=baseline,
        candidate=candidate,
        judge=judge,
        policy=OptimizationPolicy(shadow_traffic_pct=1.0),
        rubric=rubric,
        seed=3,
    )
    runner.evaluate([LLMMessage(role="user", content="x")], role="r")
    runner.evaluate([LLMMessage(role="user", content="x")], role="r")
    # With pct == 1.0 every call is diverted, so the candidate runs on both.
    assert baseline.call_count == 2
    assert candidate.call_count == 2
    assert runner._samples == 2


def test_collect_signals_filters_none_entries() -> None:
    sig = Signal(kind="shadow-win", source="x", strength=0.9)
    assert collect_signals([ShadowResult(1, 1.0, 1.0, 1.0, None),
                            ShadowResult(2, 1.0, 0.5, 0.75, sig)]) == [sig]


def test_extract_usage_handles_invalid_types() -> None:
    assert extract_usage({"prompt_eval_count": "not-a-number"}, provider="ollama") == TokenUsage()
    raw = {"usage": {"prompt_tokens": None}}
    assert extract_usage(raw, provider="openai-compatible") == TokenUsage()


def test_optimization_signal_kind_constants() -> None:
    assert OptimizationSignalKind.HIGH_LLM_COST == "high-llm-cost"
    assert OptimizationSignalKind.PROVIDER_DEGRADED == "provider-degraded"
    assert OptimizationSignalKind.SHADOW_WIN == "shadow-win"


def test_optimization_proposal_rule_emits_when_threshold_met() -> None:
    rule = OptimizationProposalRule(
        signal_kind=OptimizationSignalKind.SHADOW_WIN,
        threshold=0.5,
        proposal_name="routing-shadow-promote",
        rationale="candidate wins",
    )
    proposals = rule.evaluate([
        Signal(kind=OptimizationSignalKind.SHADOW_WIN, source="shadow", strength=0.6),
    ])
    assert len(proposals) == 1
    assert proposals[0].kind == "config-change"
    assert proposals[0].name == "routing-shadow-promote"
    assert proposals[0].metadata["signal_kind"] == OptimizationSignalKind.SHADOW_WIN
    assert proposals[0].metadata["signal_strength"] == 0.6


def test_optimization_proposal_rule_silent_when_below_threshold() -> None:
    rule = OptimizationProposalRule(
        signal_kind=OptimizationSignalKind.HIGH_LLM_COST,
        threshold=2.0,
        proposal_name="x",
        rationale="r",
    )
    assert rule.evaluate([
        Signal(kind=OptimizationSignalKind.HIGH_LLM_COST, source="a", strength=0.5),
    ]) == []


def test_optimization_proposal_rule_ignores_other_signal_kinds() -> None:
    rule = OptimizationProposalRule(
        signal_kind=OptimizationSignalKind.PROVIDER_DEGRADED,
        threshold=0.1,
        proposal_name="x",
        rationale="r",
    )
    assert rule.evaluate([
        Signal(kind=OptimizationSignalKind.HIGH_LLM_COST, source="a", strength=1.0),
    ]) == []


def test_optimization_proposal_rule_uses_metadata_provider() -> None:
    rule = OptimizationProposalRule(
        signal_kind=OptimizationSignalKind.SHADOW_WIN,
        threshold=0.5,
        proposal_name="x",
        rationale="r",
        metadata_provider=lambda signals: {"candidate": "fast-model"},
    )
    proposals = rule.evaluate([
        Signal(kind=OptimizationSignalKind.SHADOW_WIN, source="shadow", strength=0.9),
    ])
    assert proposals[0].metadata["candidate"] == "fast-model"
    assert proposals[0].metadata["signal_strength"] == 0.9


def test_build_default_optimization_rules_returns_three_rules() -> None:
    rules = build_default_optimization_rules()
    assert len(rules) == 3
    kinds = {rule.signal_kind for rule in rules}  # type: ignore[attr-defined]
    assert kinds == {
        OptimizationSignalKind.HIGH_LLM_COST,
        OptimizationSignalKind.PROVIDER_DEGRADED,
        OptimizationSignalKind.SHADOW_WIN,
    }
    for rule in rules:
        assert rule.evaluate([]) == []
