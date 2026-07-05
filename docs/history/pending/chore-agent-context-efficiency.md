# chore/agent-context-efficiency

**Date:** 2026-07-05

Fixed template skill frontmatter for `context-token-efficiency` and `tests-offline` skills so they register as triggerable skills in the evolooption working set. Adopted generic Context/Token-Efficiency Steward, AI Workflow Architect, and Repo Janitor stewards into the working set via `scripts/sync-steward-pool.ps1` (all four pool-synced stewards passed in one invocation). Copied the corresponding skills into `.agents/skills/`. Updated `.steward-pool.json` to track all four pool-synced stewards. Updated root `AGENTS.md` steward registry and the pool-sync paragraph, preserving the domain-agnostic frame. Fixed `scripts/sync-steward-pool.ps1` to read/write explicitly as UTF-8 to avoid Windows PowerShell mangling non-ASCII steward text during Apply, which also fixed mojibake em-dashes in previously-synced Backlog Orchestrator files.
