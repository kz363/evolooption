# Architecture

`evolooption` owns the domain-agnostic harness. Projects provide goals, metrics, tools,
action executors, signal extractors, and domain-specific steward agents.

## Ownership boundary

- Python validates, routes, persists state, enforces policies, and executes actions.
- LLMs may propose agents, lessons, plans, and explanations.
- Projects own all real-world action tools.
- Metric evaluators and protected-surface declarations are not writable by the loop.
