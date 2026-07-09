"""Domain-agnostic LLM optimization primitives.

Provides provider-level circuit breaking, cost tracking, weight-based routing with
fallback, LLM-as-a-Judge grading, and shadow-traffic evaluation. The optimization
layer is *advisory*: it never mutates providers, brokers, or protected surfaces
directly. Routing changes flow back through :class:`evolooption.evolution.Proposal`
objects and the existing ``ActionPolicy`` / ``ProtectedSurface`` gates.
"""

from evolooption.optimization.circuit_breaker import ProviderCircuitBreaker
from evolooption.optimization.cost_tracker import (
    CostTracker,
    ProviderPricing,
    TokenUsage,
    cost_for_usage,
    extract_ollama_usage,
    extract_openai_usage,
    extract_usage,
)
from evolooption.optimization.judge import JudgeVerdict, LLMJudge, RubricCriterion
from evolooption.optimization.policy import OptimizationPolicy
from evolooption.optimization.router import Provider, ProviderRouter
from evolooption.optimization.shadow import ShadowResult, ShadowRunner, collect_signals
from evolooption.optimization.signals import (
    OptimizationProposalRule,
    OptimizationSignalKind,
    build_default_optimization_rules,
)

__all__ = [
    "CostTracker",
    "JudgeVerdict",
    "LLMJudge",
    "OptimizationPolicy",
    "OptimizationProposalRule",
    "OptimizationSignalKind",
    "Provider",
    "ProviderCircuitBreaker",
    "ProviderPricing",
    "ProviderRouter",
    "RubricCriterion",
    "ShadowResult",
    "ShadowRunner",
    "TokenUsage",
    "build_default_optimization_rules",
    "collect_signals",
    "cost_for_usage",
    "extract_ollama_usage",
    "extract_openai_usage",
    "extract_usage",
]
