# Technical design

## Critical rules for implementers

- Do not use `eval` or executable strings for dynamic gating rules.
- Keep the base package domain-agnostic.
- Keep metrics and policy enforcement on the protected surface.
- Tests must be offline unless explicitly marked otherwise.

## Module guide

See `docs/AI_CONTEXT.md` for the package map.
