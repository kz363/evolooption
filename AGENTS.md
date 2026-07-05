# Repository Agent Rules

This repository contains the reusable `evolooption` framework and starter template.

## Non-negotiable rules

- Keep the framework domain-agnostic.
- Do not ship real-world action tools in the base package.
- Preserve protected-surface enforcement for metrics, guardrails, approval code, and baseline tests.
- Replace executable dynamic configuration with safe declarative formats.
- Keep tests fully offline by default.
- Update `docs/PROJECT_HISTORY.md` for every implementation change.
