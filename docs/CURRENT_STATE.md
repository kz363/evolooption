# Current state

`evolooption` is retired and frozen. The historical Phase 0-4 framework surface remains in the
repository for audit, but it is not an active product-runtime dependency and accepts no new
consumers or features. Generic evaluation, promotion, mutation, scaffolding, and dynamic
registry entry points fail closed.

The test suite is fully offline by default. See `PROJECT_HISTORY.md` for the chronological
implementation log and `README.md` for historical examples only. The generated-validator
tests in `tests/test_ai_assets_validation.py` still expect an unavailable `validate_manifest`
API; the non-validator suite passes and this pre-existing mismatch is not part of the
retirement change.

## Recent changes (2026-07-06)

- Global Kilo config at `~/.config/kilo/` now provides shared agents, skills, and commands for all repos.
- Added `project-memory` skill to global config for durable cross-session documentation patterns.
- Cleaned up redundant skills from alpacagents that now use global equivalents.
