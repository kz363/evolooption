from evolooption import __version__
from evolooption.agents import ActivationRule, AgentSelector, AgentSpec, QueryContext
from evolooption.evolution.models import Proposal, Signal
from evolooption.evolution.scaffolder import Scaffolder, ScaffoldRequest
from evolooption.learning import InMemoryLessonStore, Lesson
from evolooption.policy import ProtectedSurface


def test_version_is_exposed() -> None:
    assert __version__ == "0.1.0"


def test_selector_applies_declarative_activation_rule() -> None:
    selector = AgentSelector(
        always_active=["base"],
        optional_agents={
            "base": AgentSpec(name="base", prompt="Base"),
            "reviewer": AgentSpec(
                name="reviewer",
                prompt="Review",
                activation=ActivationRule(field="risk", operator="equals", value="high"),
            ),
        },
    )

    selected = selector.select(QueryContext({"risk": "high"}))

    assert [agent.name for agent in selected] == ["base", "reviewer"]


def test_scaffolder_calls_metric_snapshot_hook(tmp_path) -> None:
    proposal = Proposal(kind="new-agent", name="reviewer", rationale="needed")
    result = Scaffolder().scaffold(
        ScaffoldRequest(
            proposal=proposal,
            root=tmp_path,
            metric_snapshot_hook=lambda: {"metric": 1.0},
        )
    )

    assert result.metadata == {"metric_snapshot": {"metric": 1.0}}


def test_learning_store_returns_copy() -> None:
    store = InMemoryLessonStore()
    store.add(Lesson(text="Keep metrics protected.", source="test"))

    lessons = store.list()
    lessons.clear()

    assert len(store.list()) == 1


def test_protected_surface_matches_globs() -> None:
    surface = ProtectedSurface(globs=("metrics/**", "policy/**"))

    assert surface.protects("metrics/evaluator.py")
    assert not surface.protects("agents/selector.py")


def test_signal_model_accepts_metadata() -> None:
    signal = Signal(kind="gap", source="test", strength=0.75, metadata={"count": 3})

    assert signal.metadata["count"] == 3
