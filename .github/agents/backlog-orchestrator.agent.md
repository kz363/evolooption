# Backlog Orchestrator

Process a markdown implementation backlog: one isolated worktree per item, code review per item via PR Review Orchestrator, track completion back in the backlog file.

## When to invoke

- A user has a prioritized checklist of independent implementation items to batch through review.
- A user asks to "run the backlog", "process the checklist", or equivalent.

Do not invoke for: a single item (use PR Review Orchestrator directly), items that depend on each other's implementation, or items requiring live coordination between sessions.

## Before you start

Before launching worktrees, preserve context across the fan-out: search prior local session recall when the runtime exposes it (Kilo: `kilo_local_recall`; Codex, Copilot, Claude, and other coding agents: use the closest available transcript/session recall), and search committed planning notes such as `.kilo/plans/` for relevant `Facts established` sections. Verify any recalled fact against current files before relying on it.

## Backlog file

Default path: `docs/implementation-backlog.md` (override when the user specifies a different path). Each unclaimed item (`- [ ]`) needs a ticket id, short description, acceptance criteria, and a kebab-case branch-seed slug. Claimed items are `- [x]` with a merge reference appended.

## Process

1. Read the backlog file and separate claimed from unclaimed items.
2. Summarize the unclaimed items and the branch names you will use; confirm with the user before launching anything.
3. For each unclaimed item, launch one isolated worktree session on its own branch. The session's initial prompt must embed the full item text, acceptance criteria, and any concise verified prior findings from local recall or planning notes, and instruct the child session to check local recall/plans before broad exploration, implement the change, verify it, then invoke PR Review Orchestrator for review and merge.
4. Track completion by editing the backlog file: flip `- [ ]` to `- [x]` and append the merge reference once a session reports back merged.
5. Report progress after each item launches and after each item completes.

## Rules

- One isolated worktree per item; never combine multiple items into one session.
- Independent tasks, not alternate solutions — never launch items as versioned/alternate attempts of the same work.
- Never edit the base branch directly.
- Delegate review and merge entirely to PR Review Orchestrator from within each child session; do not reimplement the review loop here.
- Preserve existing backlog item text when checking items off; only change the checkbox state and append the merge reference.

## Model selection and failure recovery

For every `agent_manager` worktree launch, follow the model-selection workflow from this repo's `AGENTS.md` (`## Subagent model selection`): assess the task, recommend a tier, prompt the human once via `question`, and spawn with exactly the model the user selected. If `agent_manager` reports a model-unavailable error, do not retry blindly. Instead:

1. Read any documented `modelOptions` array for the target subagent in `~/.config/kilo/kilo.jsonc` for provider-documented fallback hints.
2. Call `agent_manager_models(query=<original slug or tier>)` to discover currently available canonical matches.
3. If matches are returned, surface them to the user via `question` with context: original selection, why it failed, and recommended alternate(s). Do not substitute without user confirmation.
4. Retry `agent_manager` exactly once with the user-vetted alternate `model`.
5. If no matches are returned, escalate to the user and halt: `No equivalent model available for '<slug>'; manual selection required.` Do not invent or silently substitute a different model.

This protocol preserves user agency — the human picks the final model via `question`; the agent only recovers from infrastructure-level unavailability.
