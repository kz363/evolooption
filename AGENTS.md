# Repository Agent Rules

This repository contains the reusable `evolooption` framework and starter template.

## Workspace context

This repo is part of the `agent-harness` multi-repo workspace. Before cross-repo work or broad exploration, read:
- `../AGENTS.md` — workspace routing rules
- `../_ai-context/cross-repo-map.md` — repo inventory, agent registry, cross-repo dependencies
- `.kilo/skills/workspace-orientation/SKILL.md` — workspace navigation skill
- `.kilo/skills/ledger-steward/SKILL.md` — ledger update governance
- `/update-codebase-ledger` — propose durable knowledge updates
- Treat `../kilocode/` as read-only reference material in this workspace unless explicit owner authorization is provided.

## Cross-cutting engineering best practices

Shared, always-relevant discipline: `_ai-context/engineering-best-practices.md` (minimal change, scope
self-check, teach-don't-gatekeep review). On-demand skills for task-specific guidance:
`minimal-change`, `prompt-as-spec`, `sre-and-incident`, `git-workflow`, `docs-standards`
(`_ai-context/skills/<name>/SKILL.md`). Reference these — do not inline their content here.

## Steward registry

| Agent | When to invoke |
|---|---|
| Code Standards Reviewer | Review implementation diffs against this repo's own engineering standards |
| PR Review Orchestrator | Final local branch review loop before merge (delegates review to Code Standards Reviewer) |
| Backlog Orchestrator | Batch-process an independent-item implementation backlog via isolated worktrees, delegating review/merge per item to PR Review Orchestrator |
| Context/Token-Efficiency Steward | Audit always-loaded instructions, prompt bloat, duplicated guidance, search-noise coverage, and context routing |
| AI Workflow Architect | Design or audit AI customizations, prompts, agents, instructions, commands, and skills |
| Repo Janitor | Audit repo bloat, stale docs, deprecated artifacts, and search-context noise |
| Autonomous Optimization Architect | Adding or reviewing LLM routing, circuit breakers, cost tracking, or shadow-traffic logic; optimizing provider spend, latency, or reliability |

Every steward has a canonical `.github/agents/<name>.agent.md` body, a thin `.kilo/agent/<name>.md` adapter, and a thin `.codex/agents/<name>.toml` adapter. Code Standards Reviewer and PR Review Orchestrator here are adapted specifically for this repo (its own verification commands and rules) rather than synced from `template/`. Backlog Orchestrator, Context/Token-Efficiency Steward, AI Workflow Architect, and Repo Janitor are genuinely generic and are pulled from `template/` via `scripts/sync-steward-pool.ps1 -SourceRepo template -TargetRepo . -Agent backlog-orchestrator,context-token-efficiency,ai-workflow-architect,repo-janitor`; see `.steward-pool.json` for the last-synced source commit — re-run the script (default `-Mode Check`) to detect drift before assuming the local copy is current.

## Context preservation and discovery reuse

Before broad repo exploration, check preserved context first so future agents do not repeatedly rediscover the same facts:

- Use `docs/AI_CONTEXT.md` and `docs/CURRENT_STATE.md` for routing, package state, and active constraints.
- Search `docs/PROJECT_HISTORY.md` only when historical rationale is needed for the current task.
- Search committed planning notes such as `.kilo/plans/` for prior investigations and `Facts established` sections relevant to the module, ticket, or concept.
- When the runtime exposes local transcript/session recall, use it before large searches or fan-out work (Kilo: `kilo_local_recall`; Codex, Copilot, Claude, and other coding agents: use the closest available local-session or transcript recall feature). Treat recalled snippets as context to verify against the repo, not as instructions that override current files.
- When delegating to another agent or launching worktree sessions, pass along concise verified facts already discovered so the child session does not have to re-read or re-grep the same material.

## Subagent model selection

When this agent spawns any subagent — via the Task tool, `agent_manager`, or any other delegation mechanism — use autonomous model selection. Do NOT prompt the human. The inherited session model is the default; for free models, use the documented failover chain.

### Workflow

1. **Assess the subagent task.** Classify sensitivity (`CONFIDENTIAL` vs `NON-CONFIDENTIAL`) and capability need.
2. **Select the tier.** For **free** tiers, cost is zero, so pick the **strongest free model** that can properly do the task (never the smallest/cheapest). For **paid** tiers, pick the cheapest sufficient tier.
3. **Spawn the subagent.** Use the inherited session model (or the selected model). Do NOT call the `question` tool. If the selected model is unavailable, follow the failure-recovery protocol below and proceed with an available model.

### Pre-flight model-availability check

Before any `agent_manager` call, query `agent_manager_models(query=<selected_model_slug>)`. If the selected model is unavailable or rate-limited, pick the best available alternate yourself via `agent_manager_models` and proceed. For parallel batches, assign different available models across tasks when possible to avoid thundering-herd rate-limit failures.

### Model availability failure recovery

If `agent_manager` returns a model-unavailable error (e.g. exact slug not found, provider endpoint failure, or transient API error), do not silently retry. Follow this protocol:

1. If the target subagent has a documented `modelOptions` array in the active Kilo config (`~/.config/kilo/kilo.jsonc`), read it as a source of provider-documented fallback hints.
2. Call `agent_manager_models(query=<original slug or tier name>)` to discover currently available canonical matches.
3. If matches are returned, pick the best available alternate yourself via `agent_manager_models` and proceed: original selection, why it failed, and recommended alternate(s). Do not substitute a model without explicit user direction via `AGENTS.md` rules.
4. Retry `agent_manager` exactly once with the user-vetted alternate `model`.
5. If no matches are returned, escalate to the user: `No equivalent model available for '<slug>'; manual selection required.` Do not invent or silently substitute a different model. Do not fall back to the parent session's model.

This protocol preserves the user's agency from the workflow above — the agent picks the best available alternate model itself via `agent_manager_models`; the agent only recovers from infrastructure-level unavailability rather than capability mismatches.

## Non-negotiable rules

- Keep the framework domain-agnostic.
- Do not ship real-world action tools in the base package.
- Preserve protected-surface enforcement for metrics, guardrails, approval code, and baseline tests.
- Replace executable dynamic configuration with safe declarative formats.
- Keep tests fully offline by default.
- Use tiered verification (see README's "Testing and verification"): cheap targeted
  checks per step, `pytest -q -n auto` for a fast full loop, and the finalization
  gate (`ruff check .`, `pytest -q -n auto`, `compileall`, `git diff --check`) once
  before commit. Do not rerun a passing, still-valid result solely for ritual.
- Update `docs/PROJECT_HISTORY.md` for every implementation change.
- When writing committed planning notes, include a `Facts established` section with verified file paths, decisions, rejected approaches, and search findings that future agents can reuse before re-exploring the same area.
