---
description: "Produce a fact-only, 3-level orientation map of this repo (1-line summary, 5-minute explanation, deep dive). Use when: onboarding to an unfamiliar repo or answering 'where do I start?'."
agent: plan
model: kilo-auto/balanced
---

Produce a repo orientation map by following the `workspace-orientation` skill
(`_ai-context/skills/workspace-orientation/SKILL.md`), scoped to THIS repo.

Rules (from the skill + `engineering-codebase-onboarding-engineer`):
- **Fact-only.** State only what the inspected code/mosts actually show. If you did not inspect a file, say so.
- **Three levels, in order:**
  1. One-line statement of what this repo is.
  2. Five-minute explanation: primary tasks, inputs, outputs, key files, main code paths.
  3. Deep dive: entry points, top-level structure, boundaries, responsibilities by file, traced flows.
- **Stay read-only.** Do not suggest refactors, fixes, or next steps. Onboarding only.

Return the map as Markdown. Cite file paths and concrete function/class/route names.
