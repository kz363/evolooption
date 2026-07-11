---
name: context-token-efficiency
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

Use canonical instructions from `../.github/agents/context-token-efficiency.agent.md`. Focus on context routing and token efficiency.
