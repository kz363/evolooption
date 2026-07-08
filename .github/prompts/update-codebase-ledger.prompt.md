---
description: "Propose durable repo knowledge updates after codebase exploration. Use when: you discovered entrypoints, invariants, gotchas, or cross-repo relationships that future agents should know without re-exploring."
---

You are updating durable AI-agent context for this repo.

Goal:
Capture only durable, verified knowledge that will help future agents navigate this repo faster.

First inspect:
- root `AGENTS.md`
- `docs/ai/subsystems/INDEX.md` and relevant `docs/ai/subsystems/<name>.md` (if any exist)
- relevant `.agents/skills/*/SKILL.md` and `.claude/skills/*/SKILL.md`
- `../_ai-context/cross-repo-map.md` for cross-repo facts

Rules:
- Do not dump conversation history.
- Do not add speculative facts.
- Do not add temporary task details.
- Do not add large code snippets.
- Prefer paths, ownership, invariants, entrypoints, test commands, and gotchas.
- Put subsystem details in `docs/ai/subsystems/<name>.md` or a skill.
- If information is uncertain, mark it as uncertain or do not add it.
- Before editing, present proposed updates grouped by target file.

Output:
1. Durable facts learned
2. Proposed target files
3. Proposed patch
4. Why each update belongs there
5. Risk of context bloat

Wait for human approval before writing any files.
