# Template Agent Rules

This project uses `evolooption` steward conventions.

## Steward registry

| Agent | When to invoke |
|---|---|
| Repo Janitor | Repo bloat, stale docs, deprecated code, noisy search context |
| AI Workflow Architect | Agent, prompt, instruction, command, or skill design |
| Code Standards Reviewer | Review implementation diffs against project standards |
| Context/Token-Efficiency Steward | Reduce token bloat and improve AI context routing |
| PR Review Orchestrator | Final local branch review loop before merge |

## Cross-tool authoring

Every reusable steward has one canonical `.github/agents/<name>.agent.md` body,
one thin `.kilo/agent/<name>.md` adapter, and one thin `.codex/agents/<name>.toml` adapter.
Project-specific reviewers are declared in this file and referenced by name instead of hard-coded in base stewards.
