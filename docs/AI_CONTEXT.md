# AI context

`evolooption` is a Python package plus starter template for self-learning multi-agent projects.

## Global agent config

Generic agents, skills, and commands are now available in the global Kilo config at `~/.config/kilo/`. These are domain-agnostic:

- **Agents**: `ai-workflow-architect`, `backlog-orchestrator`, `code-standards-reviewer`, `context-token-efficiency`, `pr-review-orchestrator`, `repo-janitor`
- **Skills**: `context-token-efficiency`, `project-memory`, `tests-offline`
- **Commands**: `recommend-ai-customizations`, `repo-hygiene-audit`, `run-implementation-backlog`, `verify`

These global agents follow the canonical-body-plus-adapter pattern used by this repo, but are self-contained.

## Package map

- `evolooption.llm`: provider-agnostic LLM interfaces, role registry, Ollama and OpenAI-compatible adapters with structured-output validation and bounded retries.
- `evolooption.agents`: agent specifications, declarative activation, selection, and collaboration primitives.
- `evolooption.evolution`: signals, proposals, declarative registries, scaffolding, and postmortems.
- `evolooption.loop`: goal intake, iteration orchestration, policy denial ledger entries, and optional JSONL audit persistence.
- `evolooption.execution`: action executor and action policy interfaces, including allowlist, spend, rate, and approval gates.
- `evolooption.metrics`: protected metric evaluator interface.
- `evolooption.policy`: autonomy tiers, tier-derived action policies, protected path surfaces, worktree runner, and verification runner.
- `evolooption.learning`: in-memory and JSON lesson persistence with optional retention caps.
- `evolooption.optimization`: provider circuit breaker, cost tracker, weight-based router, LLM-as-a-Judge grading, shadow-traffic runner, optimization policy, and signal/proposal wiring. Advisory only — proposals still pass through `ActionPolicy` / `ProtectedSurface`.
- `evolooption.cli`: setup command entry points.
