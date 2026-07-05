from dataclasses import dataclass
from typing import Protocol

from evolooption.evolution.models import Proposal, ProposalKind, Signal


class ProposalRule(Protocol):
    def evaluate(self, signals: list[Signal]) -> list[Proposal]: ...


@dataclass(frozen=True)
class ThresholdProposalRule:
    signal_kind: str
    threshold: float
    proposal_kind: ProposalKind
    proposal_name: str
    rationale: str

    def evaluate(self, signals: list[Signal]) -> list[Proposal]:
        matching = [signal for signal in signals if signal.kind == self.signal_kind]
        strength = sum(signal.strength for signal in matching)
        if strength < self.threshold:
            return []
        return [
            Proposal(
                kind=self.proposal_kind,
                name=self.proposal_name,
                rationale=self.rationale,
                metadata={
                    "signal_kind": self.signal_kind,
                    "signal_count": len(matching),
                    "signal_strength": strength,
                },
            )
        ]


class ProposalEngine:
    def __init__(self, rules: list[ProposalRule]) -> None:
        self._rules = rules

    def propose(self, signals: list[Signal]) -> list[Proposal]:
        proposals: list[Proposal] = []
        for rule in self._rules:
            proposals.extend(rule.evaluate(signals))
        return proposals
