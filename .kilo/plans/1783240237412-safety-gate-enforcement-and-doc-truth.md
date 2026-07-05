# Plan: Make evolooption's advertised safety gates real, and align docs with code

## Goal

The framework's README/docs advertise a layered safety posture (human approval,
spend limit, rate limit, protected-surface enforcement, autonomy tiers). Empirical
verification shows several of these gates are declared but **inert at runtime**.
This plan makes the safety gates actually enforced by `EvolutionLoop` (per the
user's chosen direction: "enforce in code"), corrects genuinely-future claims in
the docs, and adds tests that prove each gate blocks a bad action.

Scope is the `evolooption/` framework and `docs/`. No `template/` behavior changes.

## Verification results (claim vs. code) — confirmed by reading + grep + running tests

All 18 tests currently pass (`python -m pytest -q -n auto` → `18 passed`), matching
`docs/PROJECT_HISTORY.md`. The gaps below are between the **documented safety story**
and the **runtime code path**, not test failures.

1. **Human approval is not enforced.** `ActionPolicy.require_human_approval` defaults
   `True` (`evolooption/execution/policy.py:8`) but is read nowhere. `EvolutionLoop._execute_allowed_action`
   only calls `action_policy.allows()` (`evolooption/loop/engine.py:51`). README claims
   `require_human_approval` "defaults to True" as a gate (`README.md:207`). Dead gate.
2. **Spend & rate limits are inert inside the loop.** `ActionPolicy.spent` / `_timestamps`
   only change via `ActionPolicy.record()` (`evolooption/execution/policy.py:25-27`).
   `record()` is never called by the loop (grep: only `tests/test_loop_phase3.py:71`).
   The loop calls `allows(tool_name)` with no `estimated_cost` and never records
   (`evolooption/loop/engine.py:51`), so `spent` stays `0.0` and `_timestamps` stays
   empty across a real run — the spend/rate gates advertised at `README.md:206` can
   never trip during loop execution.
3. **Protected surface is never validated by the loop.** `ProtectedSurface.validate_changed_paths()`
   (`evolooption/policy/autonomy.py:22`) is only called directly in a test
   (`tests/test_loop_phase3.py:66`); the loop never calls it. README implies the loop
   "may never modify" protected paths (`README.md:316-321`).
4. **`AutonomyTier` is dead.** Only imported/exported in `evolooption/policy/__init__.py:1,6`;
   never consumed. README documents per-tier behavior (`README.md:289-298`) that no code enforces.
5. **`ProtectedSurface.modules` / `baseline_tests` are dead fields** — declared
   (`evolooption/policy/autonomy.py:15-16`) but only `.globs` is read by `protects()`.
6. **`docs/CURRENT_STATE.md` is stale** — says "Provider adapters, evolution logic, and
   orchestration are planned for later phases" (`docs/CURRENT_STATE.md:3-4`) though all
   are implemented (contradicts README + `PROJECT_HISTORY.md`).
7. **Accurate claims (no change):** README quickstart runs and is test-covered; no
   `eval`/`exec`/`importlib`; subprocess usage is safe; secrets stored by env-var name only.

## Decision

**Enforce in code.** Wire human approval, spend/rate recording, and protected-surface
validation into `EvolutionLoop` so the documented posture is real and fail-closed.
Correct docs only where a feature is genuinely future (`AutonomyTier`, `modules`,
`baseline_tests`).

---

## Remediation task list (ordered)

### A. Critical safety-gate enforcement (do before production)

**A1. Enforce human approval in the loop (fail closed).**
- Files: `evolooption/loop/engine.py`, `evolooption/execution/policy.py`.
- Add an optional approval hook to `EvolutionLoop`, e.g.
  `approval_callback: Callable[[str, dict[str, Any]], bool] | None = None`.
- In `_execute_allowed_action`, after `allows()` passes: if
  `action_policy.require_human_approval` is `True`, execution proceeds only if
  `approval_callback` is provided AND returns `True`; otherwise raise
  `PermissionError(f"human approval required for tool: {tool_name}")`. No callback +
  approval required = denied (fail closed).
- Do not silently honor an `action["approved"]` flag from LLM-controlled state; approval
  must come from the operator-supplied callback, not from the `state` dict.

**A2. Make spend/rate limits effective during loop execution.**
- Files: `evolooption/loop/engine.py` (and confirm `execution/policy.py` API).
- Read `estimated_cost = float(action.get("cost", 0.0))` from the action.
- Call `action_policy.allows(tool_name, estimated_cost=estimated_cost)`.
- After a successful `action_executor.execute(...)`, call
  `action_policy.record(cost=estimated_cost)` so `spent` and `_timestamps` advance and
  the gates can actually trip on subsequent iterations/actions.
- Decide and document ordering: check `allows()` BEFORE execute; `record()` AFTER a
  successful execute (so failed executions do not consume budget). State this in a
  code comment.

**A3. Wire protected-surface validation into the loop (fail closed).**
- Files: `evolooption/loop/engine.py`.
- Add optional `changed_paths_provider: Callable[[], list[str]] | None = None`
  (a `WorktreeRunner.changed_paths` is the intended provider).
- After executing an action, if a provider is set, call
  `protected_surface.validate_changed_paths(changed_paths_provider())`; let the raised
  `PermissionError` propagate (it is the reward-hacking guard).
- If no provider is set, document clearly (docstring + README) that protected-surface
  enforcement is inactive and the consumer must supply a provider.

**A4. Add a defined failure/escalation outcome instead of bare exceptions.**
- Files: `evolooption/loop/engine.py`, `evolooption/loop/contracts.py`.
- Today a denied action raises `PermissionError` mid-run and no ledger entry is written
  for that iteration. Decide behavior: either (a) record a failed `IterationResult`
  (with a `reason`) before/while raising, or (b) convert policy denials into a terminal
  `IterationResult(success=False, metadata={"blocked": ...})` and stop the loop cleanly.
  Recommended: record a failed iteration with a machine-readable `reason` in metadata,
  then stop — so denials are observable in the ledger rather than only via a traceback.

### B. Correct dead/aspirational claims (do before production)

**B1. Resolve `AutonomyTier`.** Either implement tier-to-gate mapping in the loop
(conservative ⇒ `require_human_approval=True` for all; assisted ⇒ approval only for
non-allowlisted; full-auto ⇒ policy limits only), OR mark it explicitly unimplemented.
Given "enforce in code", prefer a minimal implementation: a helper that derives an
`ActionPolicy`/approval posture from a tier, plus a test. If deferred, add a docstring
and a README note "not yet enforced" and a `# TODO(autonomy-tier)` marker.
- Files: `evolooption/policy/autonomy.py`, `README.md:289-298`.

**B2. Resolve `ProtectedSurface.modules` / `baseline_tests`.** Either implement checks
(e.g. `modules` matched against dotted module paths, `baseline_tests` verified present/passing
via the verification runner) or remove the unused fields and their README references.
Recommended: remove the dead fields now; reintroduce with tests when a real need exists.
- Files: `evolooption/policy/autonomy.py:15-16`, README/`docs` references.

**B3. Fix `docs/CURRENT_STATE.md`** to reflect implemented Phases 0–4 (or delete it and
point to `PROJECT_HISTORY.md`). Cross-check `docs/AI_CONTEXT.md` for the same drift.

### C. Reliability & correctness hardening (do next)

**C1. Validate LLM JSON output against the requested schema.** Both clients do bare
`json.loads()` with no schema check (`evolooption/llm/ollama.py:41`,
`evolooption/llm/openai_compatible.py:46`). Add minimal validation in `structured()`
(required keys + top-level type at least; optional `jsonschema` dev dep for full checks)
and raise a typed error on mismatch so callers can retry/fallback.

**C2. Add bounded retry with backoff to LLM HTTP calls.** No retries today
(`evolooption/llm/ollama.py:50`, `evolooption/llm/openai_compatible.py:59`). Make retry
count/backoff configurable and default conservative.

**C3. Persist `IterationLedger`.** It is in-memory only (`evolooption/loop/orchestrator.py:20-27`).
Add an optional JSONL sink under `state/` (already gitignored) so task success rate and
denials are auditable after the process exits.

**C4. `JSONLessonStore` growth/locking.** Full-file read-modify-write, unbounded, no lock
(`evolooption/learning/json_store.py:12-29`). Add a max-lessons cap or JSONL append, and
document single-writer or add a lock.

### D. Process & coverage (do next / nice to have)

**D1. Add CI.** No `.github/workflows/` exists. Add a workflow running the finalization
gate: `ruff check .`, `pytest -q -n auto`, `python -m compileall -q -x "(\.venv|\.venv-win)" .`,
`git diff --check`. Matrix across supported Python (3.10–3.13) to catch D3.

**D2. Add tests for the newly enforced gates and untested modules:** human-approval
denial, spend-limit trip across iterations, rate-limit trip, protected-surface denial via
loop, plus existing gaps (`OllamaClient`, `structured()`, `VerificationRunner`,
`WorktreeRunner`).

**D3. Pin `ProtectedSurface` glob semantics.** `PurePath.match()` differs 3.10/3.11 vs
3.12+ (`evolooption/policy/autonomy.py:20`). Add a cross-version test or switch to a
version-stable matcher and document the glob dialect.

**D4. Minor cleanups (nice to have):** remove or clearly mark unused
`evolooption/agents/collaboration.py` (`Collaborator`/`DebateRound`, zero call sites);
simplify `AgentSelector`'s dual `specs`/`optional_agents` dicts; add file locking to
`evolution/registry.py` writes; add `Proposal.dependencies` before concurrent scaffolding.

---

## Validation plan (tiered, per AGENTS.md)

- Per changed module: `ruff check <files>` + targeted test file
  (e.g. `pytest tests/test_loop_phase3.py -q`).
- Each new/changed gate must ship with a test that asserts a bad action is **blocked**
  (denied approval, exceeded spend, exceeded rate, protected path touched) and a matching
  test that a good action still passes.
- Fast loop when a unit of work is done: `python -m pytest -q -n auto` (expect >18 passing).
- Finalization gate once before commit: `python -m ruff check .`,
  `python -m pytest -q -n auto`, `python -m compileall -q -x "(\.venv|\.venv-win)" .`,
  `git diff --check` (or `scripts/verify.ps1`).

## Failure modes / risks to watch

- **Backward compatibility:** adding required-approval enforcement flips the effective
  default from "executes" to "denied unless approved" for consumers relying on
  `require_human_approval=True` default. This is the correct secure default but is a
  behavior change — call it out prominently in `README.md` and `PROJECT_HISTORY.md`, and
  ensure the offline quickstart still works (it sets `require_human_approval=False`).
- **Fail-closed vs. usability:** A3/A1 must fail closed but must not break the documented
  offline quickstart (no `changed_paths_provider`, approval disabled). Verify the README
  quickstart still runs after changes.
- **Do not weaken the protected surface** to make tests pass; the reward-hacking test
  (`tests/test_loop_phase3.py`) is a baseline guard.

## Out of scope

- No new real-world action tools (framework stays domain-agnostic per `AGENTS.md`).
- No `template/` steward behavior changes (only docs there if a claim is wrong).
- No new runtime dependencies unless C1 opts into `jsonschema` as a dev/optional extra.

---

## Handoff to implementation agent

This plan was produced in plan mode. Implementation requires source edits, so hand off to
an implementation-capable agent (e.g. Kilo Code) on a feature branch.

**Handoff notes:**
1. Read this plan and the cited files first; re-run `python -m pytest -q -n auto` to
   confirm the 18-test baseline before changing anything.
2. Implement in order: A1 → A2 → A3 → A4, then B, then C, then D. A-block is the
   before-production safety work and should land first as a reviewable unit.
3. For every gate change, add the paired block/allow tests (D2) in the same change.
4. Editing `evolooption/execution/policy.py`, `evolooption/loop/engine.py`, and
   `evolooption/policy/autonomy.py` is the intended work here — this is *strengthening*
   approval/guardrail/protected-surface code, consistent with the repo rule to preserve
   that enforcement. Do not modify `MetricEvaluator` semantics or loosen protected-surface
   checks.
5. Per `AGENTS.md`, **update `docs/PROJECT_HISTORY.md`** with each implementation change,
   and keep tests fully offline.
6. Run the finalization gate once before commit. Only commit/push if the user explicitly
   asks.

**Suggested branch:** `safety-gate-enforcement`.

## Open questions (none blocking)

- A4 exact behavior (record-failed-iteration-then-stop vs. terminal result): recommended
  record-then-stop; confirm during implementation if the ledger consumer needs per-denial
  entries.
- B1 (AutonomyTier): minimal implementation vs. explicit deferral — recommended minimal
  implementation given the "enforce in code" direction; acceptable to defer with clear
  markers if it balloons scope.
