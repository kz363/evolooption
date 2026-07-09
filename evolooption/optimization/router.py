"""Multi-provider router with weight-based selection and breaker awareness.

Picks the highest-weight provider whose breaker is not currently open, falls back to
the next provider on failure, and stops at the first successful call. The router
itself never mutates the breaker or the cost tracker directly — it calls the public
``record_*`` methods on whichever objects the caller supplies.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from evolooption.llm.client import LLMClient, LLMMessage, LLMResponse
from evolooption.optimization.circuit_breaker import ProviderCircuitBreaker
from evolooption.optimization.cost_tracker import (
    CostTracker,
    TokenUsage,
    extract_usage,
)


@dataclass(frozen=True)
class Provider:
    """One provider the router can pick.

    ``name`` is a stable identifier used for telemetry and breaker tracking.
    ``client`` is the provider's LLM client. ``weight`` is a non-negative integer;
    the router prefers the highest-weight non-tripped provider. ``cost_provider`` is
    the key passed to the :class:`CostTracker` (defaults to ``name``).
    """

    name: str
    client: LLMClient
    weight: int = 1
    cost_provider: str | None = None
    extractor: str = "ollama"

    def provider_key(self) -> str:
        return self.cost_provider or self.name


@dataclass
class ProviderRouter:
    """Routes LLM calls across weighted providers, skipping tripped ones.

    The router is *advisory* for breaker and cost: it asks the breaker
    ``is_open(provider)`` before each call and records usage on the tracker. It
    never mutates the breaker past the public ``record_failure`` / ``record_success``
    contract.
    """

    providers: Sequence[Provider]
    breaker: ProviderCircuitBreaker = field(default_factory=ProviderCircuitBreaker)
    tracker: CostTracker | None = None
    max_cost_per_run: float | None = None
    on_failure: Callable[[str, BaseException], None] | None = None
    on_success: Callable[[str, LLMResponse, TokenUsage, float], None] | None = None

    def _ordered(self) -> list[Provider]:
        return sorted(
            (provider for provider in self.providers if provider.weight > 0),
            key=lambda provider: (-provider.weight, provider.name),
        )

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        role: str,
    ) -> LLMResponse:
        """Call the best non-tripped provider; fall back on failure.

        Returns the :class:`LLMResponse` from the first successful call. Raises
        :class:`RuntimeError` if every eligible provider is tripped or fails; the
        caller is responsible for surfacing that error to a human or the evolution
        loop. Schema enforcement is the caller's responsibility (use
        ``client.structured`` directly or parse ``response.content``).
        """
        if not self.providers:
            raise RuntimeError("router has no providers configured")
        last_error: BaseException | None = None
        for provider in self._ordered():
            if self.breaker.is_open(provider.name):
                continue
            if self._over_budget():
                raise RuntimeError("router over max_cost_per_run; refusing further calls")
            try:
                response = provider.client.complete(messages, role=role)
            except Exception as exc:
                self.breaker.record_failure(provider.name)
                if self.on_failure is not None:
                    self.on_failure(provider.name, exc)
                last_error = exc
                continue
            usage = extract_usage(response.raw, provider=provider.extractor)
            cost = self._record_success(provider, usage)
            self.breaker.record_success(provider.name)
            if self.on_success is not None:
                self.on_success(provider.name, response, usage, cost)
            return response
        raise RuntimeError(
            "all providers failed or tripped; last error: "
            f"{type(last_error).__name__ if last_error else 'none'}: {last_error}"
        )

    def _record_success(self, provider: Provider, usage: TokenUsage) -> float:
        if self.tracker is None:
            return 0.0
        return self.tracker.record(provider.provider_key(), usage)

    def _over_budget(self) -> bool:
        if self.max_cost_per_run is None or self.tracker is None:
            return False
        return self.tracker.total > self.max_cost_per_run


__all__ = ["Provider", "ProviderRouter"]
