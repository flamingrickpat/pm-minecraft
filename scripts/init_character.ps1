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
    [int]$McpPort = 8765,
    [int]$McpRequestTimeoutMs = 200000
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$root = [System.IO.Path]::GetFullPath($AgentRoot)
$artifacts = [System.IO.Path]::GetFullPath($ArtifactRoot)
$sdk = Join-Path $repoRoot "mcp\sdk\minecraft.ts"
if (-not (Test-Path -LiteralPath $sdk -PathType Leaf)) { throw "Minecraft SDK is missing: $sdk" }
$draftSource = Join-Path $repoRoot "deploy\drafts"
if (-not (Test-Path -LiteralPath $draftSource -PathType Container)) { throw "Example drafts are missing: $draftSource" }
$exampleDrafts = @(Get-ChildItem -LiteralPath $draftSource -Filter "*.ts" -File)
if ($exampleDrafts.Count -eq 0) { throw "Example drafts are missing: $draftSource" }
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
# Deployed as working examples: they run as-is against this workspace's lib/minecraft.ts
# and are the starting point for new drafts.
foreach ($draft in $exampleDrafts) {
    Copy-Item -LiteralPath $draft.FullName -Destination (Join-Path $root "drafts\$($draft.Name)")
}

$draftList = ($exampleDrafts | ForEach-Object { "  - drafts/$($_.Name)" }) -join "`n"
$agentInstructions = @"
# Minecraft character workspace

This directory is the agent's writable Minecraft workspace.

- Connect to the minecraft MCP server configured in .mcp.json. Start with minecraft_observe; use minecraft_find_block, minecraft_walk_to, minecraft_mine_block, minecraft_craft_item, minecraft_equip, and minecraft_call for normal survival actions.
- Returned state is compact: coordinates, distances, and angles carry one decimal, and a nearbyBlocks entry only reports harvest eligibility when the held item cannot harvest it. Read the full uncompacted snapshot under artifacts/minecraft/state when a detail is missing.
- Fresh structured state is returned by every tool call. Durable state snapshots and screenshots are under artifacts/minecraft/state and artifacts/minecraft/screenshots. Use those files and the live Web UI to navigate and verify progress.
- For complex behavior, write a short TypeScript draft in drafts/. Import types and helpers from lib/minecraft.ts, export one async default function, then call minecraft_execute_typescript with its path and a mandatory deterministic postcondition. Inspect the fresh after-state; move a proven draft to skills/ only after it passes.
- These drafts ship with the workspace and already run against lib/minecraft.ts. Read one before writing a new draft, execute it directly where it fits the situation, and copy its guard-and-verify shape otherwise. Some carry world-specific constants (coordinates, tool names) that must be checked against fresh state first.
$draftList

Practical gameplay tips:
- Coordinate args are FLAT for the wrapper tools: minecraft_walk_to(x,y,z,tolerance,profile) and minecraft_mine_block(x,y,z,walk_into_range) take separate x, y, z numbers, NOT a position/block object. To inspect/place/use/rotate/look, use minecraft_call with the nested action schemas from minecraft_info (e.g. {"action":"place_block","parameters":{"referenceBlock":{"x":..,"y":..,"z":..},"face":{"x":0,"y":1,"z":0}}}).
- Probe before you dig: read the `hazards` array (water/lava) and use inspect on the next cell before tunneling. Mining drafts stop on a hazard; a direct mine_block into water/lava strands the bot.
- minecraft_find_block is anti-x-ray (line-of-sight only) by design: walled-off/underground targets return block_not_found. Explore or get a better viewpoint first; mining reveals ores on exposed faces.
- Check your .mcp.json: the minecraft server entry has requestTimeoutMs (the character default is 200000). When you set the server's skill timeout with minecraft_set_skill_timeout, keep it BELOW your client's requestTimeoutMs — subtract ~10s for safety (e.g. requestTimeoutMs 200000 => skillTimeoutSeconds <= 190). If a long skill still runs past your client window it will be cut off cleanly; track it with minecraft_observe and halt with minecraft_stop/minecraft_kill_skill.
- Long skills (minecraft_execute_typescript / collect_blocks / minecraft_smelt_item) run in a separate subprocess and are killed server-side at minecraft_set_skill_timeout. Prefer several short skills over one huge one; each needs a deterministic postcondition. Costs: skills run fine for 100s+ now that the client window is large.
- Walk behavior: adaptive is the default (it may dig/place/tower/parkour/drop up to four blocks) and can now travel LONG distances (walkToMaxDistance is 512) by streaming chunks as it goes. Pass profile=walk_only to forbid changing blocks. tolerance defaults to 1 so you get adjacent — needed for pickups and placements; raise it only for long noisy hops.
- Every skill needs a deterministic postcondition (ONLY evaluated on the after-state). Pick ONE kind: inventory_min{item,count}, inventory_delta_min{item,count}, held_item{item}, y_min/y_max/health_min/position_changed_min{value}, distance_max{target:{x,y,z},value}. To combine several, send a single object with only an `all` array, e.g. {"all":[{"kind":"inventory_min","item":"iron_pickaxe","count":1}]} (do NOT set kind when using all).
- Drops: mine_block with walk_into_range:true puts the body adjacent so the (generous) pickup collects the drop; if you see an uncollected item entity, walk to it.
- Held-tool drift: a climb-y mine_block or pillar can leave a placeable block (dirt/cobblestone) in hand instead of your tool. ALWAYS re-equip your tool right before using it, and verify the swap (equip can report ok while the old item stays in hand).
- minecraft_info reports the full admin/state map: action schemas, postcondition schemas, and skill policy. Re-read it whenever a tool's parameter shape is unclear.
- Store durable world notes in memory/minecraft/. Use normal survival mechanics only: never use creative mode, /give, teleportation, or operator commands.
"@
$agentInstructions.Trim() + "`n" | Set-Content -LiteralPath (Join-Path $root "AGENTS.md") -Encoding UTF8

foreach ($memoryName in @("WORLD", "PLACES", "ROUTES", "CHESTS", "FAILURES", "JOURNAL")) {
    "# $memoryName`n" | Set-Content -LiteralPath (Join-Path $root "memory\minecraft\$memoryName.md") -Encoding UTF8
}
$mcpConfig = @{ mcpServers = @{ minecraft = @{ url = "http://127.0.0.1:$McpPort/mcp"; requestTimeoutMs = $McpRequestTimeoutMs } } } | ConvertTo-Json -Depth 4
# Write pure UTF-8 (no BOM): Set-Content -Encoding UTF8 on Windows PowerShell 5.1
# emits a leading BOM that breaks Pi's .mcp.json parser, so use the .NET writer.
$mcpJsonPath = Join-Path $root ".mcp.json"
[System.IO.File]::WriteAllText($mcpJsonPath, ($mcpConfig + "`n"), (New-Object System.Text.UTF8Encoding($false)))
@{ schema = "pm.minecraft-character.v1"; name = $Name; minecraft = @{ host = $MinecraftHost; port = $MinecraftPort }; ports = @{ web = $WebPort; viewer = $ViewerPort; mcp = $McpPort }; paths = @{ agent_root = $root; artifact_root = $artifacts } } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $root "minecraft-character.json") -Encoding UTF8
Write-Host "Character workspace initialized: $root"
Write-Host "Example drafts deployed: $(($exampleDrafts | ForEach-Object { $_.Name }) -join ', ')"
Write-Host "Artifact root: $artifacts"
Write-Host "MCP configuration: $(Join-Path $root '.mcp.json')"
