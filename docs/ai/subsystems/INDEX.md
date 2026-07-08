# Subsystem index

## evolooption

| Subsystem | Status | Entrypoints | Key gotchas | Used by |
|---|---|---|---|---|
| template_sync | maintained | `scripts/sync-steward-pool.ps1` | pull once, elaborate locally, diverge by design; `-Mode Check` detects drift, `-Mode Sync` overwrites | Pulling generic stewards into alpacagents and evolooption (root) |
