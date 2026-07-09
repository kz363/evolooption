"""Provider-level circuit breaker.

Distinct concern from any application-level (e.g. trading-plan) circuit breaker: this
breaker watches *provider* failure velocity (HTTP 429/5xx, timeouts, ``URLError``) and
trips a single provider so subsequent calls fall through to a cheaper fallback.

Fail-closed by default: once tripped, the provider is skipped until either the cooldown
elapses or :meth:`reset` is called explicitly. State is intentionally in-memory; the
breaker is meant to wrap a session, not persist across process restarts.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ProviderCircuitBreaker:
    """Tracks consecutive failures per provider and trips after a threshold.

    Parameters
    ----------
    failure_threshold:
        Number of consecutive failures required to trip the breaker. ``0`` disables
        the breaker (it never trips).
    cooldown_seconds:
        Seconds that must elapse after a trip before the breaker auto-recovers and
        a single call is allowed through to probe the provider.
    """

    failure_threshold: int = 5
    cooldown_seconds: float = 30.0
    _consecutive_failures: dict[str, int] = field(default_factory=dict)
    _tripped_at: dict[str, float] = field(default_factory=dict)

    def is_open(self, provider: str, *, now: float | None = None) -> bool:
        """Return ``True`` if the breaker is currently tripping the provider.

        If the cooldown has elapsed, the breaker auto-recovers to a *half-open* state
        and reports ``False`` so one probe call can be attempted.
        """
        tripped_at = self._tripped_at.get(provider)
        if tripped_at is None:
            return False
        current = now if now is not None else time.monotonic()
        if current - tripped_at >= self.cooldown_seconds:
            self._tripped_at.pop(provider, None)
            self._consecutive_failures[provider] = 0
            return False
        return True

    def record_failure(self, provider: str) -> None:
        """Record a provider failure. Trips the breaker if the threshold is reached."""
        if self.failure_threshold <= 0:
            return
        self._consecutive_failures[provider] = self._consecutive_failures.get(provider, 0) + 1
        if self._consecutive_failures[provider] >= self.failure_threshold:
            self._tripped_at[provider] = time.monotonic()

    def record_success(self, provider: str) -> None:
        """Record a provider success, clearing any prior consecutive-failure count."""
        self._consecutive_failures[provider] = 0

    def trip(self, provider: str) -> None:
        """Manually trip the breaker (e.g. from a halt-on-anomaly signal)."""
        if self.failure_threshold <= 0:
            return
        self._tripped_at[provider] = time.monotonic()

    def reset(self, provider: str) -> None:
        """Force-reset the breaker for a provider."""
        self._consecutive_failures.pop(provider, None)
        self._tripped_at.pop(provider, None)


__all__ = ["ProviderCircuitBreaker"]
