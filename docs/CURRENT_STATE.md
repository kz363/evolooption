# Current state

`evolooption` includes the implemented Phase 0-4 framework surface: typed package interfaces,
LLM provider adapters, declarative agent selection, evolution proposals and registries,
iteration orchestration, action-policy enforcement, protected-surface helpers, worktree and
verification runners, lesson persistence, and the starter steward template.

The test suite is fully offline by default. See `PROJECT_HISTORY.md` for the chronological
implementation log and `README.md` for the supported public examples.

## Recent changes (2026-07-06)

- Global Kilo config at `~/.config/kilo/` now provides shared agents, skills, and commands for all repos.
- Added `project-memory` skill to global config for durable cross-session documentation patterns.
- Cleaned up redundant skills from alpacagents that now use global equivalents.
