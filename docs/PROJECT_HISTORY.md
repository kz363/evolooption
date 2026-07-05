# Project history

## 2026-07-05

- Created the initial Phase 0 scaffold for `evolooption`: package metadata, package tree,
  typed extension stubs, docs skeleton, and offline verification harness.
- Added Phase 1 LLM abstractions: `LLMClient`, role registry, Ollama and OpenAI-compatible clients,
  provider config persistence, and setup CLI tests.
- Added Phase 2 evolution primitives: SQLite signal store, threshold proposal engine, safe declarative
  dynamic registry, multi-artifact scaffolder, postmortem lesson persistence, and offline tests.
- Added Phase 3 loop/policy primitives: fake-domain orchestration loop, action policy spend/rate gates,
  protected-surface checks, worktree/verification helpers, and reward-hacking tests.
- Added Phase 4 template steward system with canonical `.github/agents` bodies, thin Kilo/Codex
  adapters, skills, and starter `AGENTS.md` registry conventions.
- Ported the tiered verification convention validated in the `agents` consumer repo (commit
  `2071d163`): added `pytest-xdist` to the `dev` extra, declared a `slow` marker in
  `pyproject.toml`, and documented per-step / fast-loop (`pytest -q -n auto`) / finalization-gate
  tiers in `AGENTS.md` and the README. `scripts/verify.ps1` now runs the finalization gate with
  `-n auto`. The current suite (18 tests, ~0.4s) has no test slow enough to warrant
  `@pytest.mark.slow` yet; the marker and `-m "not slow"` convention are wired in ahead of need so
  this template and its consumers can adopt it without further setup as suites grow. Validated with
  `pytest -q -n auto` (18 passed) and `ruff check .` (clean) after the change.
