# AI context

`evolooption` is a Python package plus starter template for self-learning multi-agent projects.

## Package map

- `evolooption.llm`: provider-agnostic LLM interfaces, role registry, Ollama and OpenAI-compatible adapters with structured-output validation and bounded retries.
- `evolooption.agents`: agent specifications, declarative activation, selection, and collaboration primitives.
- `evolooption.evolution`: signals, proposals, declarative registries, scaffolding, and postmortems.
- `evolooption.loop`: goal intake, iteration orchestration, policy denial ledger entries, and optional JSONL audit persistence.
- `evolooption.execution`: action executor and action policy interfaces, including allowlist, spend, rate, and approval gates.
- `evolooption.metrics`: protected metric evaluator interface.
- `evolooption.policy`: autonomy tiers, tier-derived action policies, protected path surfaces, worktree runner, and verification runner.
- `evolooption.learning`: in-memory and JSON lesson persistence with optional retention caps.
- `evolooption.cli`: setup command entry points.
