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
- Installed the PR Review Orchestrator as an active project Kilo agent and updated its template
  adapter with selectable agent metadata and inline instructions.
- Ported the tiered verification convention validated in the `agents` consumer repo (commit
  `2071d163`): added `pytest-xdist` to the `dev` extra, declared a `slow` marker in
  `pyproject.toml`, and documented per-step / fast-loop (`pytest -q -n auto`) / finalization-gate
  tiers in `AGENTS.md` and the README. `scripts/verify.ps1` now runs the finalization gate with
  `-n auto`. The current suite (18 tests, ~0.4s) has no test slow enough to warrant
  `@pytest.mark.slow` yet; the marker and `-m "not slow"` convention are wired in ahead of need so
  this template and its consumers can adopt it without further setup as suites grow. Validated with
  `pytest -q -n auto` (18 passed) and `ruff check .` (clean) after the change.
- Enforced the advertised safety gates in `EvolutionLoop`: human approval now fails closed without
  an operator callback, spend/rate policy state is recorded after successful execution, protected
  surfaces are checked through an optional changed-path provider, and blocked actions are recorded
  as terminal failed ledger entries instead of uncaptured exceptions.
- Added JSONL audit persistence for iteration ledgers, a tier-to-policy helper for `AutonomyTier`,
  version-stable protected-surface glob matching, and removed unused `ProtectedSurface` fields.
- Hardened LLM clients with typed structured-output validation and bounded HTTP retries, capped and
  atomically persisted JSON lesson storage, and atomic dynamic registry writes.
- Added CI for the finalization gate across Python 3.10-3.13, broadened offline coverage for loop
  gate blocking/allowing behavior, LLM structured output, worktree and verification runners, lesson
  caps, selector lookup, autonomy policy derivation, and proposal dependencies. The suite now has
  36 offline tests.
- Updated `README.md`, `docs/CURRENT_STATE.md`, and `docs/AI_CONTEXT.md` so documented safety and
  package-state claims match runtime behavior.
