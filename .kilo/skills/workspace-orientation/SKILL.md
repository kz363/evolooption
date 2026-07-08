---
name: workspace-orientation
description: "Use when starting work in this repo to understand the multi-repo workspace layout, find the right repo for a task, and locate durable knowledge before exploring."
---

# Workspace orientation

You are working in a multi-repo workspace at `~/projects/ai/`.

## Repo inventory

| Repo | Role | When to touch it |
|---|---|---|
| `alpacagents/` | Algorithmic trading system (backtest, execution, calibration) | Trading, backtesting, execution, calibration, EV/Kelly, P&L questions |
| `evolooption/` | Domain-agnostic multi-agent framework | Framework evolution, agent synthesis, autonomy policy, template sync |
| `kilocode/` | Kilo CLI fork (OpenCode fork) — VS Code extension, Agent Manager, TUI | Kilo internals, Agent Manager, task tool, skill discovery, worktree sessions, Kilo-specific bugs |
| `llama_router/` | LAN-only OpenAI-compatible router for local Ollama | Ollama routing, model routing, provider config, local LLM serving |
| `_ai-context/` | Shared AI context docs, cross-repo map, workspace-level instructions | Cross-repo rules, shared context, ledger updates |

## Navigation rules

1. **Before searching broadly**, check the nearest repo's `AGENTS.md` and the workspace ledger (`_ai-context/cross-repo-map.md`).
2. **Do not scan all repos** unless the task explicitly requires cross-repo analysis.
3. **For subsystem knowledge**, read `docs/ai/subsystems/INDEX.md` in the relevant repo, then the specific subsystem note.

## Durable knowledge locations

| Type | Location | Cross-tool parity |
|---|---|---|
| Workspace routing rules | `~/projects/ai/AGENTS.md` | All tools |
| Cross-repo ledger | `~/projects/ai/_ai-context/cross-repo-map.md` | All tools |
| Per-repo rules | `<repo>/AGENTS.md` | All tools |
| Subsystem notes | `<repo>/docs/ai/subsystems/<name>.md` | All tools |
| Skills (Kilo native) | `<repo>/.kilo/skills/<name>/SKILL.md` | Canonical source |
| Skills (cross-tool) | `<repo>/.agents/skills/<name>/` (Codex), `<repo>/.claude/skills/<name>/` (Claude Code) | Symlinks to canonical |
| Commands (Kilo) | `<repo>/.kilo/command/<name>.md` | Canonical source |
| Commands (Copilot) | `<repo>/.github/prompts/<name>.prompt.md` | Same content, Copilot format |
| Commands (Claude Code) | `<repo>/.claude/commands/<name>.md` | Same content, Claude Code format |
| Plans | `<repo>/.kilo/plans/<timestamp>-<name>.md` | Git-tracked |

## This repo's key facts

- This repo is a domain-agnostic, self-learning multi-agent framework.
- Generic steward agents are synced from `template/` via `scripts/sync-steward-pool.ps1`.
- This repo's Backlog Orchestrator, Context/Token-Efficiency Steward, AI Workflow Architect, and Repo Janitor are synced from template.
- Code Standards Reviewer and PR Review Orchestrator are adapted specifically for this repo.
