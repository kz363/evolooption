import pytest

from evolooption import __version__
from evolooption.agents import ActivationRule, AgentSelector, AgentSpec, QueryContext
from evolooption.evolution.models import Proposal, Signal
from evolooption.evolution.retirement import RetiredFrameworkError
from evolooption.evolution.scaffolder import Scaffolder, ScaffoldRequest
from evolooption.learning import InMemoryLessonStore, Lesson
from evolooption.policy import AutonomyTier, ProtectedSurface, action_policy_for_tier


def test_version_is_exposed() -> None:
    assert __version__ == "0.1.0"


def test_selector_applies_declarative_activation_rule() -> None:
    selector = AgentSelector(
        always_active=["base"],
        specs={
            "base": AgentSpec(name="base", prompt="Base"),
        },
        optional_agents={
            "reviewer": AgentSpec(
                name="reviewer",
                prompt="Review",
                activation=ActivationRule(field="risk", operator="equals", value="high"),
            ),
        },
    )

    selected = selector.select(QueryContext({"risk": "high"}))

    assert [agent.name for agent in selected] == ["base", "reviewer"]


def test_selector_applies_activation_from_specs() -> None:
    selector = AgentSelector(
        specs={
            "reviewer": AgentSpec(
                name="reviewer",
                prompt="Review",
                activation=ActivationRule(field="risk", operator="equals", value="high"),
            ),
        },
    )

    selected = selector.select(QueryContext({"risk": "high"}))

    assert [agent.name for agent in selected] == ["reviewer"]


def test_scaffolder_rejects_retired_writes(tmp_path) -> None:
    proposal = Proposal(kind="new-agent", name="reviewer", rationale="needed")
    with pytest.raises(RetiredFrameworkError):
        Scaffolder().scaffold(
            ScaffoldRequest(
                proposal=proposal,
                root=tmp_path,
                metric_snapshot_hook=lambda: {"metric": 1.0},
            )
        )


def test_learning_store_returns_copy() -> None:
    store = InMemoryLessonStore()
    store.add(Lesson(text="Keep metrics protected.", source="test"))

    lessons = store.list()
    lessons.clear()

    assert len(store.list()) == 1


def test_protected_surface_matches_globs() -> None:
    surface = ProtectedSurface(globs=("metrics/**", "policy/**"))

    assert surface.protects("metrics/evaluator.py")
    assert surface.protects("metrics/nested/evaluator.py")
    assert surface.protects("policy\\autonomy.py")
    assert not surface.protects("metrics_other/evaluator.py")
    assert not surface.protects("agents/selector.py")


def test_autonomy_tier_derives_action_policy() -> None:
    conservative = action_policy_for_tier(
        AutonomyTier.CONSERVATIVE,
        allowed_tools={"inspect"},
        spend_limit=1.0,
        rate_limit_per_minute=2,
    )
    full_auto = action_policy_for_tier(AutonomyTier.FULL_AUTO, allowed_tools={"inspect"})

    assert conservative.require_human_approval is True
    assert conservative.allows("inspect", estimated_cost=0.5)
    assert full_auto.require_human_approval is False


def test_non_conservative_tier_overridden_for_protected_surface_changes() -> None:
    surface = ProtectedSurface(globs=("trading/**", "calibration/**", "scoring.py"))

    conservative = action_policy_for_tier(
        AutonomyTier.CONSERVATIVE,
        allowed_tools={"edit"},
        protected_surface=surface,
        changed_paths=["trading/alpaca_gateway.py"],
    )
    assisted = action_policy_for_tier(
        AutonomyTier.ASSISTED,
        allowed_tools={"edit"},
        protected_surface=surface,
        changed_paths=["trading/alpaca_gateway.py"],
    )
    full_auto = action_policy_for_tier(
        AutonomyTier.FULL_AUTO,
        allowed_tools={"edit"},
        protected_surface=surface,
        changed_paths=["trading/alpaca_gateway.py"],
    )

    assert conservative.require_human_approval is True
    assert assisted.require_human_approval is True
    assert full_auto.require_human_approval is True


def test_non_conservative_tier_preserved_for_safe_changes() -> None:
    surface = ProtectedSurface(globs=("trading/**", "calibration/**", "scoring.py"))

    assisted = action_policy_for_tier(
        AutonomyTier.ASSISTED,
        allowed_tools={"edit"},
        protected_surface=surface,
        changed_paths=["agents/new_specialist.md"],
    )
    full_auto = action_policy_for_tier(
        AutonomyTier.FULL_AUTO,
        allowed_tools={"edit"},
        protected_surface=surface,
        changed_paths=["agents/new_specialist.md"],
    )

    assert assisted.require_human_approval is False
    assert full_auto.require_human_approval is False


def test_protected_surface_validate_changed_paths_for_approval() -> None:
    surface = ProtectedSurface(globs=("trading/**", "calibration/**"))

    assert surface.validate_changed_paths_for_approval(["trading/alpaca_gateway.py"]) is True
    assert surface.validate_changed_paths_for_approval(["calibration/ledger.py"]) is True
    assert surface.validate_changed_paths_for_approval(["agents/new.md"]) is False
    assert surface.validate_changed_paths_for_approval([]) is False


def test_signal_model_accepts_metadata() -> None:
    signal = Signal(kind="gap", source="test", strength=0.75, metadata={"count": 3})

    assert signal.metadata["count"] == 3


def test_proposal_accepts_dependencies() -> None:
    proposal = Proposal(
        kind="new-agent",
        name="reviewer",
        rationale="needed",
        dependencies=("base",),
    )

    assert proposal.dependencies == ("base",)
