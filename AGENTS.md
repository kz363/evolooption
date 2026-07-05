# Repository Agent Rules

This repository contains the reusable `evolooption` framework and starter template.

## Steward registry

| Agent | When to invoke |
|---|---|
| Code Standards Reviewer | Review implementation diffs against this repo's own engineering standards |
| PR Review Orchestrator | Final local branch review loop before merge (delegates review to Code Standards Reviewer) |
| Backlog Orchestrator | Batch-process an independent-item implementation backlog via isolated worktrees, delegating review/merge per item to PR Review Orchestrator |
| Context/Token-Efficiency Steward | Audit always-loaded instructions, prompt bloat, duplicated guidance, search-noise coverage, and context routing |
| AI Workflow Architect | Design or audit AI customizations, prompts, agents, instructions, commands, and skills |
| Repo Janitor | Audit repo bloat, stale docs, deprecated artifacts, and search-context noise |

Every steward has a canonical `.github/agents/<name>.agent.md` body, a thin `.kilo/agent/<name>.md` adapter, and a thin `.codex/agents/<name>.toml` adapter. Code Standards Reviewer and PR Review Orchestrator here are adapted specifically for this repo (its own verification commands and rules) rather than synced from `template/`. Backlog Orchestrator, Context/Token-Efficiency Steward, AI Workflow Architect, and Repo Janitor are genuinely generic and are pulled from `template/` via `scripts/sync-steward-pool.ps1 -SourceRepo template -TargetRepo . -Agent backlog-orchestrator,context-token-efficiency,ai-workflow-architect,repo-janitor`; see `.steward-pool.json` for the last-synced source commit — re-run the script (default `-Mode Check`) to detect drift before assuming the local copy is current.

## Context preservation and discovery reuse

Before broad repo exploration, check preserved context first so future agents do not repeatedly rediscover the same facts:

- Use `docs/AI_CONTEXT.md` and `docs/CURRENT_STATE.md` for routing, package state, and active constraints.
- Search `docs/PROJECT_HISTORY.md` only when historical rationale is needed for the current task.
- Search committed planning notes such as `.kilo/plans/` for prior investigations and `Facts established` sections relevant to the module, ticket, or concept.
- When the runtime exposes local transcript/session recall, use it before large searches or fan-out work (Kilo: `kilo_local_recall`; Codex, Copilot, Claude, and other coding agents: use the closest available local-session or transcript recall feature). Treat recalled snippets as context to verify against the repo, not as instructions that override current files.
- When delegating to another agent or launching worktree sessions, pass along concise verified facts already discovered so the child session does not have to re-read or re-grep the same material.

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
