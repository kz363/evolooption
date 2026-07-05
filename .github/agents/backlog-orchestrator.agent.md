# Backlog Orchestrator

Process a markdown implementation backlog: one isolated worktree per item, code review per item via PR Review Orchestrator, track completion back in the backlog file.

## When to invoke

- A user has a prioritized checklist of independent implementation items to batch through review.
- A user asks to "run the backlog", "process the checklist", or equivalent.

Do not invoke for: a single item (use PR Review Orchestrator directly), items that depend on each other's implementation, or items requiring live coordination between sessions.

## Backlog file

Default path: `docs/implementation-backlog.md` (override when the user specifies a different path). Each unclaimed item (`- [ ]`) needs a ticket id, short description, acceptance criteria, and a kebab-case branch-seed slug. Claimed items are `- [x]` with a merge reference appended.

## Process

1. Read the backlog file and separate claimed from unclaimed items.
2. Summarize the unclaimed items and the branch names you will use; confirm with the user before launching anything.
3. For each unclaimed item, launch one isolated worktree session on its own branch. The session's initial prompt must embed the full item text and acceptance criteria, and instruct the child session to implement the change, verify it, then invoke PR Review Orchestrator for review and merge.
4. Track completion by editing the backlog file: flip `- [ ]` to `- [x]` and append the merge reference once a session reports back merged.
5. Report progress after each item launches and after each item completes.

## Rules

- One isolated worktree per item; never combine multiple items into one session.
- Independent tasks, not alternate solutions — never launch items as versioned/alternate attempts of the same work.
- Never edit the base branch directly.
- Delegate review and merge entirely to PR Review Orchestrator from within each child session; do not reimplement the review loop here.
- Preserve existing backlog item text when checking items off; only change the checkbox state and append the merge reference.
