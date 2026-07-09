"""Optimization policy.

Combines :class:`evolooption.execution.ActionPolicy` (spend limit, rate limit, approval
gate) with the optimization-specific knobs: shadow-traffic percentage, breaker
configuration, and the LLM roles the architect is allowed to propose changes for.

The policy itself is a pure data record. It does not enforce any limits — it is the
data the router, judge, and shadow runner consult to decide what to do.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from evolooption.execution.policy import ActionPolicy


@dataclass
class OptimizationPolicy:
    """Policy bundle for the optimization layer.

    Parameters
    ----------
    action_policy:
        The existing :class:`ActionPolicy` (spend, rate, approval). Not modified;
        callers can share one with the rest of the system.
    shadow_traffic_pct:
        Fraction of live traffic (in ``[0.0, 1.0]``) the shadow runner may divert
        to a candidate provider. ``0.0`` disables shadow testing entirely.
    breaker_failure_threshold:
        Consecutive provider failures required to trip the breaker.
    breaker_cooldown_seconds:
        Cooldown after a trip before the breaker auto-recovers to half-open.
    max_cost_per_run_usd:
        Hard cap on cumulative tracked cost per router run. ``None`` disables the cap.
    roles_under_optimization:
        LLM roles the architect may propose routing changes for. Empty means
        no role is mutable.
    """

    action_policy: ActionPolicy = field(default_factory=ActionPolicy)
    shadow_traffic_pct: float = 0.0
    breaker_failure_threshold: int = 5
    breaker_cooldown_seconds: float = 30.0
    max_cost_per_run_usd: float | None = None
    roles_under_optimization: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.shadow_traffic_pct <= 1.0:
            raise ValueError("shadow_traffic_pct must be in [0.0, 1.0]")
        if self.breaker_failure_threshold < 0:
            raise ValueError("breaker_failure_threshold must be >= 0")
        if self.breaker_cooldown_seconds < 0:
            raise ValueError("breaker_cooldown_seconds must be >= 0")

    def may_shadow(self) -> bool:
        return self.shadow_traffic_pct > 0.0

    def may_optimize_role(self, role: str) -> bool:
        return role in self.roles_under_optimization

    def fail_closed(self) -> bool:
        return bool(self.action_policy.require_human_approval)


__all__ = ["OptimizationPolicy"]
