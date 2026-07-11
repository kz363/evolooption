---
name: code-standards-reviewer
mode: all
permission:
  "*": "allow"
  question: "deny"
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

Use canonical instructions from `../.github/agents/code-standards-reviewer.agent.md`. Return review findings only unless explicitly asked to fix.
