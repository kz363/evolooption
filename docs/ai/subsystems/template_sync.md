# template_sync

Status: maintained
Last audited: 2026-07-08
Audited by: source-code exploration + plan implementation

## Purpose

`evolooption/template/` is the seed source for generic "steward pool" agents. It provides canonical agent bodies that are pulled into alpacagents and evolooption (the root) using `scripts/sync-steward-pool.ps1`. The pattern is: **pull once, elaborate locally, diverge by design**.

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

## Workflow

1. **Detect drift**: `scripts/sync-steward-pool.ps1 -SourceRepo template -TargetRepo . -Agent <name> -Mode Check`
2. **Review diff**: if differences found, decide whether to keep local elaborations or revert to template
3. **Sync if approved**: `-Mode Sync` overwrites target with template source
4. **Local elaboration**: after pull, Kilo adapters and batch-state logic are added on top of the canonical body

## Known pitfalls

- **Drift detection is path-based**, not content-hash-based. Renames/moves can cause false positives.
- **Sync wipes local elaborations** — if you've added `.kilo/agent/<name>.md` with batch-state logic, `-Mode Sync` will overwrite it.
- **Only pull generic stewards** — never pull local-architect or local-reviewer agents from template; those are repo-specific by design.
- **Template doesn't have `.kilo/skills/`** — skills are repo-specific and not synced.

## Cross-repo references

- `alpacagents/scripts/sync-steward-pool.ps1` pulls from `../evolooption/template/`
- `evolooption/.steward-pool.json` records the last-synced source commit
- After sync, alpacagents localizes agents for the alpacagents trading domain

## Related notes
- `../../alpacagents/docs/ai/subsystems/steward_pattern.md` — the triad pattern that steward sync ships
- `../../alpacagents/docs/ai/subsystems/pr_review_orchestrator.md` — example of pulled + elaborated steward
