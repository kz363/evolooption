# Architecture

`evolooption` owns the domain-agnostic harness. Projects provide goals, metrics, tools,
action executors, signal extractors, and domain-specific steward agents.

## Ownership boundary

- Python validates, routes, persists state, enforces policies, and executes actions.
- LLMs may propose agents, lessons, plans, and explanations.
- Projects own all real-world action tools.
- Metric evaluators and protected-surface declarations are not writable by the loop.

## Subpackages

- `evolooption.llm`: provider-agnostic LLM interfaces, role registry, Ollama and OpenAI-compatible adapters with structured-output validation and bounded retries.
- `evolooption.agents`: agent specifications, declarative activation, selection, and collaboration primitives.
- `evolooption.evolution`: signals, proposals, declarative registries, scaffolding, and postmortems.
- `evolooption.loop`: goal intake, iteration orchestration, policy denial ledger entries, and optional JSONL audit persistence.
- `evolooption.execution`: action executor and action policy interfaces, including allowlist, spend, rate, and approval gates.
- `evolooption.metrics`: protected metric evaluator interface.
- `evolooption.policy`: autonomy tiers, tier-derived action policies, protected path surfaces, worktree runner, and verification runner.
- `evolooption.learning`: in-memory and JSON lesson persistence with optional retention caps.
- `evolooption.optimization`: provider circuit breaker, cost tracker, weight-based router, LLM-as-a-Judge grading, shadow-traffic runner, optimization policy, and signal/proposal wiring.
- `evolooption.cli`: setup command entry points.

## Optimization subpackage — trust boundary

`evolooption.optimization` wraps LLM calls and proposes routing changes. It is
**advisory** and obeys the same ownership boundary as the rest of the framework:

- It wraps LLM calls (breaker, cost tracking, routing) — it does not call the network
  on its own; it only wraps existing `LLMClient` implementations.
- It emits `Signal` records of kind `high-llm-cost`, `provider-degraded`, and
  `shadow-win`.
- `OptimizationProposalRule` turns those signals into `Proposal(kind="config-change")`
  objects that flow through the existing `ProposalEngine`. Routing-weight and
  policy changes pass through `ActionPolicy`, `ProtectedSurface`, and any
  configured `VerificationRunner` before they take effect — the optimization
  layer never mutates routing state directly.
- It must not: modify `MetricEvaluator` or `ProtectedSurface` declarations; bypass
  `ActionPolicy` approval gates; mutate broker/order/execution paths.
