"""Optimization signals and the proposal rule that turns them into config changes.

The optimization layer is advisory: it never mutates routing weights, breakers, or
budgets directly. Instead it emits :class:`evolooption.evolution.Signal` records that
flow through the existing :class:`evolooption.evolution.ProposalEngine`. The
:class:`OptimizationProposalRule` in this module is the only place that maps
optimization signals into :class:`evolooption.evolution.Proposal` objects of kind
``config-change`` — and those proposals still pass through ``ActionPolicy``,
``ProtectedSurface``, and any configured ``VerificationRunner`` before they take
effect.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from evolooption.evolution.analyzer import ProposalRule
from evolooption.evolution.models import Proposal, Signal


class OptimizationSignalKind:
    """String constants for the signal kinds emitted by the optimization layer.

    Using a class of constants (rather than a :class:`enum`) keeps the signal
    ``kind`` field as a plain string, which is how :class:`Signal` stores it and
    how downstream code (logs, JSON persistence, proposal rules) consumes it.
    """

    HIGH_LLM_COST = "high-llm-cost"
    PROVIDER_DEGRADED = "provider-degraded"
    SHADOW_WIN = "shadow-win"


@dataclass(frozen=True)
class OptimizationProposalRule:
    """Proposal rule that turns optimization signals into ``config-change`` proposals.

    Parameters
    ----------
    signal_kind:
        The kind of signal this rule reacts to. One of :class:`OptimizationSignalKind`.
    threshold:
        Minimum cumulative signal strength required to emit a proposal.
    proposal_name:
        Stable identifier embedded in the emitted proposal (used by humans to
        recognize a recurring recommendation in the ledger).
    rationale:
        Human-readable explanation. The rule is intentionally not LLM-driven: the
        rationale is static so the architect's outputs are deterministic and
        auditable.
    metadata_provider:
        Optional callable that extracts a metadata dict from the matching signals
        (e.g. provider name, sample size). Defaults to the first matching signal's
        ``metadata``.
    """

    signal_kind: str
    threshold: float
    proposal_name: str
    rationale: str
    metadata_provider: object = None

    def evaluate(self, signals: Sequence[Signal]) -> list[Proposal]:
        matching = [signal for signal in signals if signal.kind == self.signal_kind]
        if not matching:
            return []
        strength = sum(signal.strength for signal in matching)
        if strength < self.threshold:
            return []
        metadata = self._metadata(matching)
        return [
            Proposal(
                kind="config-change",
                name=self.proposal_name,
                rationale=self.rationale,
                metadata=metadata
                | {
                    "signal_kind": self.signal_kind,
                    "signal_count": len(matching),
                    "signal_strength": strength,
                },
            )
        ]

    def _metadata(self, matching: Sequence[Signal]) -> dict:
        if self.metadata_provider is None:
            return dict(matching[0].metadata)
        value = self.metadata_provider(matching)
        if isinstance(value, dict):
            return dict(value)
        return {}


def build_default_optimization_rules(
    *,
    cost_threshold: float = 1.0,
    degradation_threshold: float = 0.8,
    shadow_threshold: float = 0.6,
) -> list[ProposalRule]:
    """Return a starter set of optimization proposal rules.

    These three rules cover the three signal kinds the optimization layer emits.
    Callers can compose them with existing domain rules inside a
    :class:`evolooption.evolution.ProposalEngine`.
    """
    return [
        OptimizationProposalRule(
            signal_kind=OptimizationSignalKind.HIGH_LLM_COST,
            threshold=cost_threshold,
            proposal_name="routing-cost-review",
            rationale=(
                "Cumulative LLM cost signal exceeded threshold. Review provider weights "
                "and consider routing more traffic to a cheaper provider."
            ),
        ),
        OptimizationProposalRule(
            signal_kind=OptimizationSignalKind.PROVIDER_DEGRADED,
            threshold=degradation_threshold,
            proposal_name="routing-failover-review",
            rationale=(
                "Provider failure signal exceeded threshold. Review breaker configuration "
                "and consider lowering weight or tripping the breaker for the failing provider."
            ),
        ),
        OptimizationProposalRule(
            signal_kind=OptimizationSignalKind.SHADOW_WIN,
            threshold=shadow_threshold,
            proposal_name="routing-shadow-promote",
            rationale=(
                "Shadow evaluation found a candidate provider outperforming the baseline. "
                "Consider promoting the candidate by adjusting routing weights."
            ),
        ),
    ]


__all__ = [
    "OptimizationProposalRule",
    "OptimizationSignalKind",
    "build_default_optimization_rules",
]
