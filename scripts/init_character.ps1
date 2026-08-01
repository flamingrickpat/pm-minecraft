param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Za-z0-9_]{1,16}$")]
    [string]$Name,
    [Parameter(Mandatory = $true)]
    [string]$AgentRoot,
    [Parameter(Mandatory = $true)]
    [string]$ArtifactRoot,
    [string]$MinecraftHost = "127.0.0.1",
    [int]$MinecraftPort = 12345,
    [int]$WebPort = 3000,
    [int]$ViewerPort = 3007,
    [int]$McpPort = 8765
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$root = [System.IO.Path]::GetFullPath($AgentRoot)
$artifacts = [System.IO.Path]::GetFullPath($ArtifactRoot)
$sdk = Join-Path $repoRoot "mcp\sdk\minecraft.ts"
if (-not (Test-Path -LiteralPath $sdk -PathType Leaf)) { throw "Minecraft SDK is missing: $sdk" }
$ports = @($MinecraftPort, $WebPort, $ViewerPort, $McpPort)
if (($ports | Select-Object -Unique).Count -ne 4) { throw "Minecraft, web, viewer, and MCP ports must be distinct." }
if (Test-Path -LiteralPath $root) {
    $existing = Get-ChildItem -LiteralPath $root -Force -ErrorAction Stop
    if ($existing.Count -gt 0) { throw "AgentRoot must be empty or not exist: $root" }
}
foreach ($relative in @("drafts", "skills", "lib", "memory\minecraft", "artifacts\minecraft\actions", "artifacts\minecraft\executions", "artifacts\minecraft\screenshots", "artifacts\minecraft\state")) {
    New-Item -ItemType Directory -Path (Join-Path $root $relative) -Force | Out-Null
}
New-Item -ItemType Directory -Path $artifacts -Force | Out-Null
Copy-Item -LiteralPath $sdk -Destination (Join-Path $root "lib\minecraft.ts")

$agentInstructions = @'
# Minecraft character workspace

This directory is the agent's writable Minecraft workspace.

- Connect to the minecraft MCP server configured in .mcp.json. Start with minecraft_observe; use minecraft_find_block, minecraft_walk_to, minecraft_mine_block, minecraft_craft_item, minecraft_equip, and minecraft_call for normal survival actions.
- Fresh structured state is returned by every tool call. Durable state snapshots and screenshots are under artifacts/minecraft/state and artifacts/minecraft/screenshots. Use those files and the live Web UI to navigate and verify progress.
- For complex behavior, write a short TypeScript draft in drafts/. Import types and helpers from lib/minecraft.ts, export one async default function, then call minecraft_execute_typescript with its path and a mandatory deterministic postcondition. Inspect the fresh after-state; move a proven draft to skills/ only after it passes.
- Store durable world notes in memory/minecraft/. Use normal survival mechanics only: never use creative mode, /give, teleportation, or operator commands.
'@
$agentInstructions.Trim() + "`n" | Set-Content -LiteralPath (Join-Path $root "AGENTS.md") -Encoding UTF8

foreach ($memoryName in @("WORLD", "PLACES", "ROUTES", "CHESTS", "FAILURES", "JOURNAL")) {
    "# $memoryName`n" | Set-Content -LiteralPath (Join-Path $root "memory\minecraft\$memoryName.md") -Encoding UTF8
}
$mcpConfig = @{ mcpServers = @{ minecraft = @{ url = "http://127.0.0.1:$McpPort/mcp" } } } | ConvertTo-Json -Depth 4
$mcpConfig + "`n" | Set-Content -LiteralPath (Join-Path $root ".mcp.json") -Encoding UTF8
@{ schema = "pm.minecraft-character.v1"; name = $Name; minecraft = @{ host = $MinecraftHost; port = $MinecraftPort }; ports = @{ web = $WebPort; viewer = $ViewerPort; mcp = $McpPort }; paths = @{ agent_root = $root; artifact_root = $artifacts } } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root "minecraft-character.json") -Encoding UTF8
Write-Host "Character workspace initialized: $root"
Write-Host "Artifact root: $artifacts"
Write-Host "MCP configuration: $(Join-Path $root '.mcp.json')"
