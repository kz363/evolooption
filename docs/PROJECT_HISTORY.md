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
