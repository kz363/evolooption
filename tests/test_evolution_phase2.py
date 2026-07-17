import json
from pathlib import Path

import pytest

from evolooption.agents import ActivationRule, AgentSpec
from evolooption.evolution.analyzer import ProposalEngine, ThresholdProposalRule
from evolooption.evolution.eval import EvalCase, EvalRunner, EvalSuite, check_promotion_gate
from evolooption.evolution.models import Outcome, Postmortem, Proposal, Signal
from evolooption.evolution.postmortem import StaticRootCauseAnalyzer
from evolooption.evolution.registry import (
    load_dynamic_entries,
    remove_dynamic_entry,
    write_dynamic_entry,
)
from evolooption.evolution.retirement import RetiredFrameworkError
from evolooption.evolution.scaffolder import Scaffolder, ScaffoldRequest
from evolooption.evolution.tracker import SQLiteSignalStore
from evolooption.learning import JSONLessonStore


def test_retired_eval_runner_rejects_execution() -> None:
    suite = EvalSuite(agent_name="docs", cases=[EvalCase(name="case", input={})])

    with pytest.raises(RetiredFrameworkError):
        EvalRunner().run({}, suite)


def test_retired_promotion_gate_blocks_even_complete_suite() -> None:
    suite = EvalSuite(
        agent_name="docs",
        cases=[EvalCase(name=f"case-{index}", input={}) for index in range(20)],
    )

    accepted, reason = check_promotion_gate("docs", suite, Path("baseline.json"))

    assert accepted is False
    assert "retired" in reason


def test_threshold_rule_emits_proposal() -> None:
    engine = ProposalEngine([
        ThresholdProposalRule(
            signal_kind="gap",
            threshold=2.0,
            proposal_kind="new-agent",
            proposal_name="gap-reviewer",
            rationale="Repeated gaps need review.",
        )
    ])

    proposals = engine.propose([
        Signal(kind="gap", source="a", strength=1.0),
        Signal(kind="gap", source="b", strength=1.5),
    ])

    assert len(proposals) == 1
    assert proposals[0].metadata["signal_strength"] == 2.5


def test_sqlite_signal_store_round_trips(tmp_path) -> None:
    store = SQLiteSignalStore(tmp_path / "signals.sqlite3")
    store.add(Signal(kind="query", source="test", strength=0.5, metadata={"focus": "docs"}))

    signals = store.list()

    assert len(signals) == 1
    assert signals[0].metadata == {"focus": "docs"}


def test_registry_write_load_remove_is_declarative(tmp_path) -> None:
    path = tmp_path / "agents.json"
    spec = AgentSpec(
        name="docs",
        prompt="docs.md",
        schema={"type": "object"},
        activation=ActivationRule(field="focus", operator="equals", value="docs"),
    )

    with pytest.raises(RetiredFrameworkError):
        write_dynamic_entry(path, spec)

    path.write_text(
        json.dumps([{
            "name": spec.name,
            "prompt": spec.prompt,
            "schema": spec.schema,
            "activation": {
                "field": spec.activation.field,
                "operator": spec.activation.operator,
                "value": spec.activation.value,
            },
        }]),
        encoding="utf-8",
    )
    loaded = load_dynamic_entries(path)

    assert loaded == [spec]
    with pytest.raises(RetiredFrameworkError):
        remove_dynamic_entry(path, "docs")


def test_scaffolder_is_unavailable_after_retirement(tmp_path) -> None:
    proposal = Proposal(
        kind="new-skill",
        name="docs-skill",
        rationale="needed",
        artifacts={".agents/skills/docs/SKILL.md": "# Docs\n"},
    )

    with pytest.raises(RetiredFrameworkError):
        Scaffolder().scaffold(ScaffoldRequest(proposal=proposal, root=tmp_path))

    assert not (tmp_path / ".agents/skills/docs/SKILL.md").exists()


def test_postmortem_lessons_persist_to_json_store(tmp_path) -> None:
    analyzer = StaticRootCauseAnalyzer(["missing_context"])
    postmortem = analyzer.analyze(Outcome(goal="demo", metric_value=0.0, success=False))
    store = JSONLessonStore(tmp_path / "lessons.json")
    store.add_postmortem(postmortem)

    assert store.list()[0].text == "Review failed outcome against project taxonomy."


def test_json_store_adds_all_postmortem_lessons(tmp_path) -> None:
    store = JSONLessonStore(tmp_path / "lessons.json")
    postmortem = Postmortem(
        outcome=Outcome(goal="demo", metric_value=0.0, success=False),
        root_causes=["a"],
        lessons=["one", "two"],
    )

    store.add_postmortem(postmortem)

    assert [lesson.text for lesson in store.list()] == ["one", "two"]


def test_json_store_caps_old_lessons(tmp_path) -> None:
    store = JSONLessonStore(tmp_path / "lessons.json", max_lessons=2)
    postmortem = Postmortem(
        outcome=Outcome(goal="demo", metric_value=0.0, success=False),
        root_causes=["a"],
        lessons=["one", "two", "three"],
    )

    store.add_postmortem(postmortem)

    assert [lesson.text for lesson in store.list()] == ["two", "three"]
