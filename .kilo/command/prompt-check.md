---
description: "Scan agent/system prompts for prompt-as-spec gaps: missing version/changelog, undefined output schema, and no fallback for out-of-scope input. Use when: reviewing or adding a prompt, agent body, or AgentSpec."
agent: plan
model: kilo-auto/balanced
---

You are running a prompt-as-spec audit (see `_ai-context/skills/prompt-as-spec/SKILL.md`).

Goal: flag prompts that violate "a prompt is a spec."

Inspect the repo's prompts:
- evolooption: `evolooption/evolooption/agents/spec.py` `AgentSpec.prompt` string fields, and any `.agent.md` / `.md` prompt bodies.
- alpacagents: `agents/*.md` (loaded whole-file as system prompts) + `state/evolution_agents.json` sidecar (check for a `version` field per agent).
- llama_router: `router/app/*.py` prompt strings + any `.md` agent bodies.

For each prompt, report (do not edit):
1. **Version / changelog** — is there a `v1/v2` + changelog, or a `version` field in the sidecar? (Not inline in `agents/*.md` — that bloats the prompt; register in the sidecar instead.)
2. **Output schema** — is the expected output format/schema defined (JSON schema, Markdown template, or prose spec)?
3. **Fallback / out-of-scope** — does it define behavior for inputs outside its scope (refusal or redirect)?
4. **Injection defense** — does it isolate untrusted external content from instructions and validate outputs?

Output a compact table: `file | prompt | version? | schema? | fallback? | injection? | note`.
End with a verdict: pass, or list the specific prompts to fix. Do not modify files.
