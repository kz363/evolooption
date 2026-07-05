# Repository Agent Rules

This repository contains the reusable `evolooption` framework and starter template.

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
