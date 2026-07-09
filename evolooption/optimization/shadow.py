"""Shadow-traffic runner.

Routes a configurable fraction of live traffic asynchronously to a candidate
provider, grades the output against the baseline using :class:`LLMJudge`, and emits
a :class:`evolooption.evolution.Signal` when the candidate statistically outperforms
the baseline.

This module is intentionally synchronous: the caller decides whether to invoke the
runner on a background thread. The runner itself never blocks the main call path —
it returns a result describing what it observed, and the caller persists the signal
or hands it to the evolution loop.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass, field

from evolooption.evolution.models import Signal
from evolooption.llm.client import LLMClient, LLMMessage, LLMResponse
from evolooption.optimization.cost_tracker import (
    CostTracker,
    TokenUsage,
    extract_usage,
)
from evolooption.optimization.judge import LLMJudge, RubricCriterion
from evolooption.optimization.policy import OptimizationPolicy


@dataclass(frozen=True)
class ShadowResult:
    """The outcome of one shadow evaluation.

    ``sample_size`` is the number of paired observations accumulated. ``win_rate`` is
    the fraction of those observations where the candidate scored at least
    ``score_margin`` points above the baseline. ``emitted`` is the signal that was
    emitted (if any) to the evolution loop.
    """

    sample_size: int
    candidate_avg: float
    baseline_avg: float
    win_rate: float
    emitted: Signal | None = None


@dataclass
class ShadowRunner:
    """Routes a fraction of live traffic to a candidate provider for grading.

    The runner is stateful: it accumulates *paired* observations (baseline vs
    candidate) across calls. On each call the baseline (live) response always runs;
    the candidate runs only on the fraction of calls selected by
    :meth:`should_divert` (governed by ``policy.shadow_traffic_pct``). When the
    paired win-rate crosses ``win_rate_threshold`` with at least ``min_samples``,
    it emits a ``shadow-win`` :class:`Signal` so the evolution loop can propose a
    config-change to promote the candidate.
    """

    baseline: LLMClient
    candidate: LLMClient
    judge: LLMJudge
    policy: OptimizationPolicy
    rubric: Sequence[RubricCriterion]
    win_rate_threshold: float = 0.6
    score_margin: int = 0
    min_samples: int = 20
    seed: int | None = None
    tracker: CostTracker | None = None
    baseline_extractor: str = "ollama"
    candidate_extractor: str = "ollama"
    _samples: int = 0
    _candidate_total: float = 0.0
    _baseline_total: float = 0.0
    _wins: int = 0
    _emitted: bool = False
    _rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        if self.seed is not None:
            self._rng.seed(self.seed)

    def should_divert(self) -> bool:
        """Return ``True`` if the next live call should be shadowed."""
        if not self.policy.may_shadow():
            return False
        if self._emitted:
            return False
        return self._rng.random() < self.policy.shadow_traffic_pct

    def evaluate(
        self,
        messages: list[LLMMessage],
        *,
        role: str,
    ) -> ShadowResult:
        """Run one live (baseline) call and, on a shadow-diverted sample, grade it
        against the candidate.

        The baseline always runs — it is the caller's live response. The candidate
        runs only on the fraction of calls selected by :meth:`should_divert`
        (governed by ``policy.shadow_traffic_pct``); only those paired observations
        accumulate toward the win-rate and signal emission. This keeps candidate load
        at the configured percentage of live traffic instead of 100%.
        """
        baseline_response = self.baseline.complete(messages, role=role)
        self._record(self.baseline_extractor, baseline_response, self.tracker)

        if not self.should_divert():
            return self._result(emitted=None)

        baseline_verdict = self.judge.grade(
            output=baseline_response.content,
            rubric=self.rubric,
        )
        candidate_response = self.candidate.complete(messages, role=role)
        self._record(self.candidate_extractor, candidate_response, self.tracker)
        candidate_verdict = self.judge.grade(
            output=candidate_response.content,
            rubric=self.rubric,
        )

        self._samples += 1
        self._baseline_total += baseline_verdict.score
        self._candidate_total += candidate_verdict.score
        if candidate_verdict.score >= baseline_verdict.score + self.score_margin:
            self._wins += 1

        emitted = self._maybe_emit()
        return self._result(emitted=emitted)

    def _result(self, emitted: Signal | None) -> ShadowResult:
        samples = self._samples
        if samples == 0:
            return ShadowResult(
                sample_size=0,
                candidate_avg=0.0,
                baseline_avg=0.0,
                win_rate=0.0,
                emitted=emitted,
            )
        return ShadowResult(
            sample_size=samples,
            candidate_avg=self._candidate_total / samples,
            baseline_avg=self._baseline_total / samples,
            win_rate=self._wins / samples,
            emitted=emitted,
        )

    def _maybe_emit(self) -> Signal | None:
        if self._emitted:
            return None
        if self._samples < self.min_samples:
            return None
        win_rate = self._wins / self._samples
        if win_rate < self.win_rate_threshold:
            return None
        self._emitted = True
        return Signal(
            kind="shadow-win",
            source="shadow-runner",
            strength=win_rate,
            metadata={
                "sample_size": self._samples,
                "win_rate": win_rate,
                "candidate_avg": self._candidate_total / self._samples,
                "baseline_avg": self._baseline_total / self._samples,
            },
        )

    def _record(
        self,
        extractor: str,
        response: LLMResponse,
        tracker: CostTracker | None,
    ) -> TokenUsage:
        usage = extract_usage(response.raw, provider=extractor)
        if tracker is not None:
            tracker.record(extractor, usage)
        return usage


def collect_signals(results: Sequence[ShadowResult]) -> list[Signal]:
    """Extract emitted signals from a sequence of :class:`ShadowResult` objects."""
    return [result.emitted for result in results if result.emitted is not None]


__all__ = ["ShadowResult", "ShadowRunner", "collect_signals"]
