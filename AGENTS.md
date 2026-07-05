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
