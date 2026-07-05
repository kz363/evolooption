# Template Agent Rules

This project uses `evolooption` steward conventions.

## Steward registry

| Agent | When to invoke |
|---|---|
| Repo Janitor | Repo bloat, stale docs, deprecated code, noisy search context |
| AI Workflow Architect | Agent, prompt, instruction, command, or skill design |
| Code Standards Reviewer | Review implementation diffs against project standards |
| Context/Token-Efficiency Steward | Reduce token bloat and improve AI context routing |
| PR Review Orchestrator | Final local branch review loop before merge |
| Backlog Orchestrator | Batch-process an independent-item implementation backlog via isolated worktrees, delegating review/merge per item to PR Review Orchestrator |

## Cross-tool authoring

Every reusable steward has one canonical `.github/agents/<name>.agent.md` body,
one thin `.kilo/agent/<name>.md` adapter, and one thin `.codex/agents/<name>.toml` adapter.
Project-specific reviewers are declared in this file and referenced by name instead of hard-coded in base stewards.

## Shared steward pool

Agents that are genuinely domain-agnostic (currently: Backlog Orchestrator) live here as the canonical source and can be pulled into a consuming repo with `scripts/sync-steward-pool.ps1` (in the `evolooption` repo root, run against this `template/` folder as the source). Agents that have diverged into a project-specific elaboration (e.g. a repo's own PR Review Orchestrator with repo-specific verification commands and delegation chains) are **not** pool-synced — they are forked once from the template stub and then maintained locally. Re-running the sync script only ever touches the agents named in its `-Agent` argument and reports a diff before overwriting.

## Context preservation and discovery reuse

Before broad repo exploration, check preserved context first so future agents do not repeatedly rediscover the same facts:

- Use the consuming repo's `docs/AI_CONTEXT.md`, `docs/CURRENT_STATE.md`, and `docs/PROJECT_HISTORY.md` when those files exist.
- Search committed planning notes such as `.kilo/plans/` for prior investigations and `Facts established` sections relevant to the module, ticket, or concept.
- When the runtime exposes local transcript/session recall, use it before large searches or fan-out work (Kilo: `kilo_local_recall`; Codex, Copilot, Claude, and other coding agents: use the closest available local-session or transcript recall feature). Treat recalled snippets as context to verify against the repo, not as instructions that override current files.
- When delegating to another agent or launching worktree sessions, pass along concise verified facts already discovered so the child session does not have to re-read or re-grep the same material.
- When writing committed planning notes, include a `Facts established` section with verified file paths, decisions, rejected approaches, and search findings that future agents can reuse before re-exploring the same area.
