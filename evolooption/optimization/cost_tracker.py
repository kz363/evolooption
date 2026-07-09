"""Cost tracking for LLM/API providers.

Provider-agnostic: accepts token counts extracted from any ``LLMResponse.raw`` dict
(Ollama ``prompt_eval_count`` / ``eval_count``; OpenAI-compatible ``usage.prompt_tokens`` /
``usage.completion_tokens``; etc.) and computes cost using a per-provider price table.

This module is intentionally minimal. It does not perform I/O, does not read the network,
and does not mutate provider configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TokenUsage:
    """Token counts for a single call.

    Either ``input_tokens`` or ``output_tokens`` may be ``None`` if a provider did not
    report it; cost calculation treats ``None`` as zero for the missing side.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class ProviderPricing:
    """Per-million-token pricing for one provider.

    Prices are in USD per 1M tokens. ``None`` on a side means that side is free (e.g.
    a local Ollama model) or has no configured price; cost on that side is zero.
    """

    input_per_million: float | None = None
    output_per_million: float | None = None


def extract_ollama_usage(raw: dict | None) -> TokenUsage:
    """Extract token counts from an Ollama ``/api/chat`` raw response."""
    if not isinstance(raw, dict):
        return TokenUsage()
    return TokenUsage(
        input_tokens=_coerce_int(raw.get("prompt_eval_count")),
        output_tokens=_coerce_int(raw.get("eval_count")),
    )


def extract_openai_usage(raw: dict | None) -> TokenUsage:
    """Extract token counts from an OpenAI-compatible chat-completions raw response."""
    if not isinstance(raw, dict):
        return TokenUsage()
    usage = raw.get("usage")
    if not isinstance(usage, dict):
        return TokenUsage()
    return TokenUsage(
        input_tokens=_coerce_int(usage.get("prompt_tokens")),
        output_tokens=_coerce_int(usage.get("completion_tokens")),
    )


def extract_usage(raw: dict | None, *, provider: str) -> TokenUsage:
    """Dispatch to the right extractor based on the provider name."""
    if provider == "ollama":
        return extract_ollama_usage(raw)
    if provider == "openai-compatible":
        return extract_openai_usage(raw)
    return TokenUsage()


def cost_for_usage(usage: TokenUsage, pricing: ProviderPricing) -> float:
    """Compute USD cost for a single call given a token count and pricing row."""
    total = 0.0
    if pricing.input_per_million is not None and usage.input_tokens:
        total += (usage.input_tokens / 1_000_000.0) * pricing.input_per_million
    if pricing.output_per_million is not None and usage.output_tokens:
        total += (usage.output_tokens / 1_000_000.0) * pricing.output_per_million
    return total


@dataclass
class CostTracker:
    """Rolling cost aggregator for one run or session.

    Call :meth:`record` after each call to accumulate spend. ``total`` is the cumulative
    USD cost recorded so far. ``calls`` is the number of recorded calls.
    """

    pricing: dict[str, ProviderPricing] = field(default_factory=dict)
    total: float = 0.0
    calls: int = 0
    _per_provider: dict[str, float] = field(default_factory=dict)

    def record(self, provider: str, usage: TokenUsage) -> float:
        """Record one call and return the cost it added."""
        pricing = self.pricing.get(provider, ProviderPricing())
        added = cost_for_usage(usage, pricing)
        self.total += added
        self.calls += 1
        self._per_provider[provider] = self._per_provider.get(provider, 0.0) + added
        return added

    def per_provider(self) -> dict[str, float]:
        """Return a copy of the per-provider spend map."""
        return dict(self._per_provider)

    def within_budget(self, budget_usd: float) -> bool:
        return self.total <= budget_usd


def _coerce_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


__all__ = [
    "CostTracker",
    "ProviderPricing",
    "TokenUsage",
    "cost_for_usage",
    "extract_ollama_usage",
    "extract_openai_usage",
    "extract_usage",
]
