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
$sdk = Join-Path $repoRoot "pm_minecraft_mcp\sdk\minecraft.ts"
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
# Character instructions live in the package's character_instructions.txt (single source
# of truth, used by both the Python init_character path and this script). It is deployed
# verbatim as AGENTS.md, with a @@DRAFT_LIST@@ placeholder filled from the example drafts
# shipped above.
$instructionsTplPath = Join-Path $repoRoot "pm_minecraft_mcp\character_instructions.txt"
if (-not (Test-Path -LiteralPath $instructionsTplPath -PathType Leaf)) { throw "Instructions file is missing: $instructionsTplPath" }
$agentInstructions = (Get-Content -LiteralPath $instructionsTplPath -Raw -Encoding UTF8).Replace("@@DRAFT_LIST@@", $draftList)
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
