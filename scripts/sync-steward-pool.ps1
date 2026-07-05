<#
.SYNOPSIS
  Copies a named set of domain-agnostic steward agent files from a pool source
  (typically evolooption/template) into a consuming repo, and records what was
  synced in a manifest file.

.DESCRIPTION
  Only intended for agents that are genuinely generic (see "Shared steward
  pool" in template/AGENTS.md). Project-specific stewards (e.g. a repo's own
  elaborated PR Review Orchestrator) are forked once and maintained locally,
  never overwritten by this script.

  For each -Agent name, copies (when present in the source):
    .github/agents/<name>.agent.md
    .kilo/agent/<name>.md
    .codex/agents/<name>.toml

  In -Mode Check (default), reports which target files would change but does
  not write anything. In -Mode Apply, writes the files and updates
  <TargetRepo>/.steward-pool.json with the source path, source commit, agent
  names, and sync timestamp.

.PARAMETER SourceRepo
  Path to the pool source (e.g. the evolooption/template folder).

.PARAMETER TargetRepo
  Path to the consuming repo root.

.PARAMETER Agent
  One or more agent base names (without extension), e.g. backlog-orchestrator.

.PARAMETER Mode
  Check (default, report only) or Apply (write files + manifest).

.EXAMPLE
  ./scripts/sync-steward-pool.ps1 -SourceRepo ../evolooption/template `
      -TargetRepo ../agents -Agent backlog-orchestrator -Mode Check

.EXAMPLE
  ./scripts/sync-steward-pool.ps1 -SourceRepo ./template `
      -TargetRepo . -Agent backlog-orchestrator -Mode Apply
#>

param(
    [Parameter(Mandatory = $true)][string]$SourceRepo,
    [Parameter(Mandatory = $true)][string]$TargetRepo,
    [Parameter(Mandatory = $true)][string[]]$Agent,
    [ValidateSet("Check", "Apply")][string]$Mode = "Check"
)

$ErrorActionPreference = "Stop"

$relPaths = @{
    "agent.md" = ".github/agents/{0}.agent.md"
    "kilo"     = ".kilo/agent/{0}.md"
    "codex"    = ".codex/agents/{0}.toml"
}

$changed = @()
$missingSource = @()
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

foreach ($name in $Agent) {
    foreach ($key in $relPaths.Keys) {
        $rel = [string]::Format($relPaths[$key], $name)
        $srcPath = Join-Path $SourceRepo $rel
        $dstPath = Join-Path $TargetRepo $rel

        if (-not (Test-Path -LiteralPath $srcPath)) {
            $missingSource += $rel
            continue
        }

        $srcContent = [System.IO.File]::ReadAllText($srcPath, [System.Text.Encoding]::UTF8)
        $dstExists = Test-Path -LiteralPath $dstPath
        $dstContent = if ($dstExists) { [System.IO.File]::ReadAllText($dstPath, [System.Text.Encoding]::UTF8) } else { $null }

        if (-not $dstExists -or $srcContent -ne $dstContent) {
            $changed += $rel
            if ($Mode -eq "Apply") {
                $dstDir = Split-Path -Parent $dstPath
                if (-not (Test-Path -LiteralPath $dstDir)) {
                    New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
                }
                # Write with LF line endings; never introduce CRLF.
                $normalized = $srcContent -replace "`r`n", "`n"
                [System.IO.File]::WriteAllText($dstPath, $normalized, $utf8NoBom)
            }
        }
    }
}

if ($missingSource.Count -gt 0) {
    Write-Warning "Not found in source pool (skipped): $($missingSource -join ', ')"
}

if ($changed.Count -eq 0) {
    Write-Output "No drift detected for: $($Agent -join ', ')"
    exit 0
}

if ($Mode -eq "Check") {
    Write-Output "Would sync (re-run with -Mode Apply to write):"
    $changed | ForEach-Object { Write-Output "  $_" }
    exit 0
}

# Mode -eq Apply: update the manifest.
$sourceCommit = $null
try {
    $sourceCommit = (git -C $SourceRepo rev-parse HEAD 2>$null)
} catch {
    $sourceCommit = $null
}

$manifestPath = Join-Path $TargetRepo ".steward-pool.json"
$manifest = [ordered]@{
    sourceRepo   = (Resolve-Path -LiteralPath $SourceRepo).Path
    sourceCommit = $sourceCommit
    agents       = $Agent
    syncedAt     = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    filesSynced  = $changed
}
$json = $manifest | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($manifestPath, ($json -replace "`r`n", "`n"), $utf8NoBom)

Write-Output "Synced:"
$changed | ForEach-Object { Write-Output "  $_" }
Write-Output "Manifest updated: $manifestPath"
