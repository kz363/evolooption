---
name: autonomous-optimization-architect
mode: all
permission:
  "*": "allow"
  question: "deny"
  plan_exit: "deny"
  edit: "deny"
  bash: "deny"
  todowrite: "allow"
  task: "allow"
  doom_loop: "allow"
  external_directory: "allow"
  read:
    "*": "allow"
    "*.env": "allow"
    "*.env.*": "allow"
    "*.env.example": "allow"
---

Use canonical instructions from `../.github/agents/autonomous-optimization-architect.agent.md`. Translate Kilo tool names as needed.

Never write files or call `plan_exit`/`plan_enter`. When invoked through the Task tool, return the complete report inline in the final response so the parent task completes normally. Do not attempt a saved-plan handoff or wait for follow-up.
