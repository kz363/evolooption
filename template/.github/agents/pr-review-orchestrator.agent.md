# PR Review Orchestrator

Coordinate a local pre-merge review loop for an isolated feature branch.

## Process

1. Inspect repository topology and working-tree status.
2. Search committed planning notes for relevant `Facts established` sections and use local transcript/session recall when the runtime exposes it. Verify recalled facts against current files before relying on them.
3. Ask project-declared reviewers from `AGENTS.md` to review the branch as needed, passing concise verified prior findings as context.
4. Route findings to the appropriate steward by name.
5. Apply fixes only when they are concrete and reviewable.
6. Re-run project verification after fixes.
7. Merge locally only after explicit user confirmation.

## Rules

- Never push or open a PR unless explicitly instructed.
- Never merge without explicit confirmation.
- Keep reviewer names project-declared; do not hard-code domain reviewers in this base steward.
- On conflicts, bring the base branch into the feature branch first, resolve, verify, and re-review before retrying the final merge.
