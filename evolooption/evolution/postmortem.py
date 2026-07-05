from typing import Protocol

from evolooption.evolution.models import Outcome, Postmortem


class RootCauseAnalyzer(Protocol):
    def analyze(self, outcome: Outcome) -> Postmortem: ...


class StaticRootCauseAnalyzer:
    def __init__(self, taxonomy: list[str]) -> None:
        self._taxonomy = taxonomy

    def analyze(self, outcome: Outcome) -> Postmortem:
        root_causes = [] if outcome.success else self._taxonomy[:1]
        lessons = [] if outcome.success else ["Review failed outcome against project taxonomy."]
        return Postmortem(outcome=outcome, root_causes=root_causes, lessons=lessons)
