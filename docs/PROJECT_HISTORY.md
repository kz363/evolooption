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
- Added a new generic **Backlog Orchestrator** steward to `template/` (canonical `.github/agents`
  body plus thin Kilo/Codex adapters and an `AGENTS.md` registry row): it batch-processes a
  markdown implementation backlog by launching one isolated worktree per item and delegating
  review/merge for each item to PR Review Orchestrator.
- Added `scripts/sync-steward-pool.ps1`, a Check/Apply copy tool that pulls genuinely
  domain-agnostic stewards (currently only Backlog Orchestrator) from `template/` into a
  consuming repo and records the source commit in `.steward-pool.json`, so drift can be detected
  before overwriting. Project-specific stewards (Code Standards Reviewer, PR Review Orchestrator)
  are intentionally excluded from this sync path — they are forked once from the template stub
  and maintained locally per repo.
- Installed **Code Standards Reviewer** and **PR Review Orchestrator** as active root-level agents
  (`.github/agents`, `.kilo/agent`, `.codex/agents`) for this repo's own development workflow,
  adapted to `evolooption`'s own rules (domain-agnosticism, protected-surface enforcement, offline
  tests) and its own verification commands (`ruff check .`, `pytest -q -n auto`, `compileall`,
  `git diff --check`) rather than copied verbatim from a trading-specific consumer repo. Also
  installed Backlog Orchestrator at the root via the new sync script. Added a "Steward registry"
  section to the root `AGENTS.md` documenting all three and the sync-vs-fork distinction.
- Added cross-agent discovery-reuse guidance to the root and template `AGENTS.md` files, plus the
  Backlog Orchestrator and PR Review Orchestrator bodies/adapters for `.github`, `.kilo`, and
  `.codex`: agents now check committed planning notes (`Facts established`), local transcript/session
  recall when available, and pass concise verified prior findings into child worktree sessions and
  reviewer subagents instead of rediscovering the same codebase facts.

## 2026-07-06 — Seed global Kilo agent config and add project-memory skill

### Problem

Generic agents, skills, and commands existed only inside `template/` as adapters pointing to canonical bodies, requiring repos to copy them or implement their own. No shared cross-repo foundation existed.

### Decisions and Implementation

- Added self-contained generic agents to `~/.config/kilo/agent/`: `ai-workflow-architect`, `backlog-orchestrator`, `code-standards-reviewer`, `context-token-efficiency`, `pr-review-orchestrator`, `repo-janitor`.
- Added generic skills to `~/.config/kilo/skill/`: `context-token-efficiency`, `tests-offline`, and a new `project-memory` skill distilled from alpacagents' doc-memory pattern (repo map + current-state doc + history log + pending-fragment reconciliation).
- Added generic commands to `~/.config/kilo/command/`: `recommend-ai-customizations`, `repo-hygiene-audit`, `run-implementation-backlog`, `verify`.
- Updated `llama_router/AGENTS.md` with context preservation section and created `docs/AI_CONTEXT.md` + `docs/CURRENT_STATE.md`.
- Updated `evolooption/docs/AI_CONTEXT.md` to note global agent config availability.
- Updated `evolooption/docs/CURRENT_STATE.md` with recent changes.
- Updated `alpacagents/docs/AI_CONTEXT.md` to clarify global config exists but repo uses customized versions.
- Removed redundant skills from `alpacagents/.agents/skills/context-efficiency` and `tests-offline` since global versions now provide equivalent coverage.
- Removed redundant skills from `evolooption/.agents/skills/` and `evolooption/template/.agents/skills/` since global versions provide the same coverage and are auto-discovered.

### Validation

- All 13 global agent/skill/command files validated (Kilo config auto-validation on write).
- Code review passed: no blocking issues, corrected all should-fix items (description lengths, permission contradictions, mode references).
- Kilo loads global config automatically; files discovered in agent/command/skill search paths.

An audit (mirrored from the sibling `../agents` repo, where PR Review Orchestrator is more heavily
elaborated) found the bounded review loop always ran the full verification suite and re-sent the
full branch diff to the reviewer on every iteration regardless of fix size. Updated this repo's
canonical `.github/agents/pr-review-orchestrator.agent.md`: Step 4 re-verify now uses the cheaper
tier by default, reserving the full suite for financially/structurally critical paths and the one
required Terminal-gate run; Step 1/5 review now sends the full diff only on iteration 1 and an
incremental diff plus prior findings on re-review iterations 2-3; peer-steward re-delegation on
re-review is now conditional on the finding category still being open rather than unconditional.
This repo has no merge-lock section, so the sibling repo's exponential-backoff polling change did
not apply here. Doc-only change; finalization gate reduced to `git diff --check` per `AGENTS.md`.

## 2026-07-06 — PR Review Orchestrator: adaptive iterations by risk tier

### Problem

The PR Review Orchestrator's bounded review loop used a fixed 3-iteration maximum for all changes,
causing unnecessary delays for simple non-risk-tier changes. Each iteration involved expensive
delegation to Code Standards Reviewer on the strongest reasoning model.

### Decisions and Implementation

- Changed max iterations from fixed 3 to adaptive: 3 for risk-tier changes (touches
  `backtesting/`, `trading/`, `portfolio/`, `calibration/`, `evolution/`, or any
  statistics/EV/Kelly/P&L logic), 1 for all others.
- On iteration 1, run the full delegation chain in parallel — Code Standards Reviewer
  + Quantitative Standards Guardian (if risk-tier) + Trust Boundary Enforcer (if
  LLM↔Python boundary / broker mutations / replay pipelines) + specialist-registration
  skill (if new/modified LLM specialist) + AI Workflow Architect / Repo Janitor /
  Context/Token-Efficiency Steward (if agent-context hygiene findings).
- Only iterate on risk-tier changes if reviewer explicitly requests re-review for
  specific unresolved findings.
- Incremental diffs are sent on iterations 2+ instead of full branch diffs.
- Updated output format to show adaptive max iterations: "N of M (max M: 1 for non-risk-tier,
  3 for risk-tier)".

### Validation

- `ruff check .` passed.
- `pytest -q -n auto` passed (18 tests).
- `git diff --check` passed.
- Documentation review returned PASS.

## 2026-07-09 — Autonomous Optimization Architect steward + optimization subpackage

### Problem

The framework had no domain-agnostic primitives for governing LLM/provider economics
(cost tracking, circuit breaking, weight-based routing, shadow testing, LLM-as-a-Judge
grading) and no steward persona for that concern. Consumers (e.g. the alpacagents
trading repo) would otherwise have to invent these per-domain and risk inconsistent
guardrails.

### Decisions and Implementation

- Added a new `Autonomous Optimization Architect` steward to both `template/` (seed)
  and the root `evolooption/` repo: canonical `.github/agents/*.agent.md` body plus
  thin `.kilo/agent/*.md` and `.codex/agents/*.toml` adapters, and an `AGENTS.md`
  registry row in both locations. The persona enforces propose-and-gate: it emits
  `Proposal(kind="config-change")` objects, never mutates routing state directly,
  and references existing `ActionPolicy` / `ProtectedSurface` rather than restating
  them. Body is ≤120 lines, stripped of emoji/`vibe`/redundant examples.
- Added a new `evolooption.optimization` subpackage (Phase 5) with domain-agnostic
  primitives: `ProviderCircuitBreaker` (provider-failure velocity with cooldown),
  `CostTracker` + `TokenUsage` + `ProviderPricing` (provider-agnostic cost extraction
  from `LLMResponse.raw` for Ollama `prompt_eval_count`/`eval_count` and OpenAI
  `usage.*`), `Provider` + `ProviderRouter` (weight-based selection, breaker-aware
  fallback, per-run cost cap), `LLMJudge` + `RubricCriterion` (declarative numeric
  rubric enforcement), `ShadowRunner` (paired baseline/candidate grading with
  signal emission), and `OptimizationPolicy` (wraps `ActionPolicy` with
  shadow-traffic %, breaker config, and role allowlist).
- Added `OptimizationSignalKind` constants (`high-llm-cost`, `provider-degraded`,
  `shadow-win`) and `OptimizationProposalRule` (implements `ProposalRule` from
  `evolooption.evolution.analyzer`) so the optimization layer maps signals into
  `config-change` proposals that flow through the existing `ProposalEngine`. A
  `build_default_optimization_rules()` helper composes the three rules.
- Updated `docs/ARCHITECTURE.md` with the new subpackage row and a trust-boundary
  note: optimization wraps LLM calls and proposes config changes; it must not
  modify metrics, protected surfaces, approval gates, or broker/execution paths.
- Added the agent row to `_ai-context/cross-repo-map.md` (repo `evolooption`,
  no alpacagents row yet — Phase 4 of the plan defers the alpacagents persona
  until the repo runs ≥2 LLM providers).
- Registered the steward in `evolooption/AGENTS.md` and `evolooption/template/AGENTS.md`.
- Added `tests/test_optimization_phase5.py` with 33 offline tests covering:
  cost extraction for both providers, per-provider cost aggregation, breaker
  trip/reset/cooldown, router weight preference and fallback, cost-cap enforcement,
  judge rubric enforcement and clamping, shadow emission at threshold, policy
  validation, signal/proposal rule threshold gating, and default rule set.

### Validation

- `pytest -q -n auto` passes (66 tests: 39 pre-existing + 27 new in the
  optimization suite, plus the 6 new signal/proposal tests added in this entry).
- `python -m ruff check .` is clean for all new files; the single remaining
  warning is a pre-existing `SIM102` in `evolooption/policy/autonomy.py` that is
  not part of this change.
- `python -m compileall -q -x '(\.venv|\.venv-win)' .` passes.
- `git diff --check` passes.
- No new dependencies introduced (the package remains dependency-free at runtime).

## 2026-07-10 — Architect subagents return reports without plan handoff

### Problem

A Kilo Task invocation of an architect agent called `plan_exit`, a parent-facing Plan-mode handoff, instead of returning its report. The parent received no useful payload and appeared stalled.

### Decisions and Implementation

- Made AI Workflow Architect and Autonomous Optimization Architect report-only in the root project and reusable template.
- Added explicit Kilo denials for `plan_exit`, file edits, and Bash after the wildcard allow so last-match permission evaluation cannot expose those tools.
- Required delegated architects to return complete inline reports and terminate normally.
- Set the corresponding Codex adapters to read-only sandboxes for cross-tool consistency.

### Validation

- Effective Kilo permissions and Task-return behavior are checked from the workspace harness; documentation-only validation uses `git diff --check`.
