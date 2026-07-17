# template_sync

Status: retired
Last audited: 2026-07-08
Audited by: source-code exploration + plan implementation

## Purpose

`evolooption/template/` is a frozen historical steward pool. It is not a canonical source,
is not synchronized into consumers, and must not receive new framework features. Generic
engineering semantics are owned by the root `_ai-context/agentic-ai/` foundation.

## Entrypoints
- `scripts/sync-steward-pool.ps1` — PowerShell sync script (cross-platform)
- `.steward-pool.json` — tracks last-synced source commit

## Key files
- `template/.github/agents/*.agent.md` — canonical steward bodies (source)
- `template/.kilo/agent/*.md` — canonical Kilo adapters (source)
- `template/.codex/agents/*.toml` — canonical Codex adapters (source)
- `<root>/.github/agents/*.agent.md` — pulled destinations
- `<root>/.kilo/agent/*.md` — pulled destinations
- `<root>/.codex/agents/*.toml` — pulled destinations

## Invariants

- Stewards are either **generic/stewards** (synced from template) or **local-architect** or **local-reviewer** (repo-specific).
- Generic stewards pulled from template: Backlog Orchestrator, Context/Token-Efficiency Steward, AI Workflow Architect, Repo Janitor, PR Review Orchestrator, Merge Orchestrator, Serial Backlog Runner, Code Standards Reviewer.
- Sync script modes:
  - `Check` — detect drift between template and target, do not modify
  - `Sync` — copy template files to target, overwrite destination

## Historical workflow

The former detect/review/sync workflow is retained only to explain historical files. Do not
run it for new work; use the root foundation generator and repo-local ownership instead.

## Known pitfalls

- **Drift detection is path-based**, not content-hash-based. Renames/moves can cause false positives.
- **Sync wipes local elaborations** — if you've added `.kilo/agent/<name>.md` with batch-state logic, `-Mode Sync` will overwrite it.
- **Only pull generic stewards** — never pull local-architect or local-reviewer agents from template; those are repo-specific by design.
- **Template doesn't have `.kilo/skills/`** — skills are repo-specific and not synced.

## Historical cross-repo references

- Existing sync scripts and `.steward-pool.json` remain for audit and history only.

## Related notes
- `../../alpacagents/docs/ai/subsystems/steward_pattern.md` — the triad pattern that steward sync ships
- `../../alpacagents/docs/ai/subsystems/pr_review_orchestrator.md` — example of pulled + elaborated steward
