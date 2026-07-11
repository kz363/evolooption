---
name: repo-janitor
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

Use canonical instructions from `../.github/agents/repo-janitor.agent.md`. Translate Kilo tool names as needed. Read-only by default.
