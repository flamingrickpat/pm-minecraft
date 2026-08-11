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
    [string]$WebHost = "127.0.0.1",
    [int]$WebPort = 3000,
    [int]$ViewerPort = 3007,
    [string]$McpHost = "127.0.0.1",
    [int]$McpPort = 8765,
    [int]$ViewDistance = 24,
    [int]$MaxSkillCharacters = 50000,
    [float]$MineVisibilityIgnoreDistance = 3.0,
    [float]$WalkToMaxDistance = 512.0,
    [float]$SkillTimeoutSeconds = 90.0,
    [switch]$EnableAntiStallGuard,
    [switch]$NoImages,
    [switch]$Foreground
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$agentHome = [System.IO.Path]::GetFullPath($AgentRoot)
$artifactRoot = [System.IO.Path]::GetFullPath($ArtifactRoot)
$module = "pm_minecraft_mcp"
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

function Test-TcpReachable([string]$HostName, [int]$Port, [int]$TimeoutMilliseconds = 2000) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $pending = $client.ConnectAsync($HostName, $Port)
        return $pending.Wait($TimeoutMilliseconds) -and $client.Connected
    }
    catch { return $false }
    finally { $client.Dispose() }
}

function Test-LocalPortAvailable([int]$Port) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start(); return $true }
    catch { return $false }
    finally { $listener.Stop() }
}

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "MCP virtual environment is missing. Run .\scripts\setup.ps1 first."
}
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot "pm_minecraft_mcp\minecraft_mcp.py") -PathType Leaf)) {
    throw "Minecraft MCP server not found: pm_minecraft_mcp/minecraft_mcp.py"
}
foreach ($required in @("AGENTS.md", ".mcp.json", "lib\minecraft.ts", "memory\minecraft", "drafts", "skills")) {
    if (-not (Test-Path -LiteralPath (Join-Path $agentHome $required))) {
        throw "Agent root was not initialized by init_character.ps1: $agentHome"
    }
}
if (-not (Test-TcpReachable $MinecraftHost $MinecraftPort)) {
    throw "Minecraft server is not reachable at ${MinecraftHost}:$MinecraftPort"
}
foreach ($port in @($WebPort, $ViewerPort, $McpPort)) {
    if (-not (Test-LocalPortAvailable $port)) {
        throw "Local service port $port is already owned by another process"
    }
}

$arguments = @(
    "-m", $module, "--mc-host", $MinecraftHost, "--mc-port", $MinecraftPort,
    "--username", $Name, "--agent-home", $agentHome,
    "--artifact-root", $artifactRoot, "--web-host", $WebHost,
    "--web-port", $WebPort, "--viewer-port", $ViewerPort,
    "--mcp-host", $McpHost, "--mcp-port", $McpPort,
    "--max-skill-characters", $MaxSkillCharacters, "--view-distance", $ViewDistance,
    "--mine-visibility-ignore-distance", $MineVisibilityIgnoreDistance,
    "--walk-to-max-distance", $WalkToMaxDistance,
    "--skill-timeout-seconds", $SkillTimeoutSeconds
)
if ($EnableAntiStallGuard) { $arguments += "--enable-anti-stall-guard" }
if ($NoImages) { $arguments += "--no-images" }

New-Item -ItemType Directory -Path $artifactRoot -Force | Out-Null
$process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $repoRoot `
    -WindowStyle Hidden -PassThru

$deadline = (Get-Date).AddSeconds(90)
$health = $null
do {
    if ($process.HasExited) { throw "Minecraft MCP process exited with code $($process.ExitCode)" }
    try { $health = Invoke-RestMethod -Uri "http://${WebHost}:$WebPort/api/health" -TimeoutSec 2 }
    catch { $health = $null }
    $mcpReady = Test-TcpReachable $McpHost $McpPort 500
    if ($health.ready -and $mcpReady) { break }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $deadline)

if (-not $health.ready -or -not $mcpReady) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw "Minecraft body and MCP did not become ready within 90 seconds"
}
if ($health.mineflayer.username -ne $Name) { throw "Mineflayer joined as $($health.mineflayer.username), not $Name" }
if ($health.mineflayer.version -notlike "1.19*") { throw "Negotiated Minecraft version is $($health.mineflayer.version), not 1.19.x" }
$observation = Invoke-RestMethod -Uri "http://${WebHost}:$WebPort/api/observation" -TimeoutSec 10
if ($observation.player.gameMode -ne "survival") { throw "Minecraft game mode is $($observation.player.gameMode), not survival" }

@(
    "schema: pm.minecraft-service-process.v1", "pid: $($process.Id)", "username: $Name",
    "minecraft_version: $($health.mineflayer.version)", "game_mode: $($observation.player.gameMode)",
    "body_url: http://${WebHost}:$WebPort", "viewer_url: http://127.0.0.1:$ViewerPort",
    "mcp_url: http://${McpHost}:$McpPort/mcp"
) | Set-Content -LiteralPath (Join-Path $artifactRoot "service-process.yaml") -Encoding UTF8

Write-Host "Minecraft MCP ready."
Write-Host "  Web UI: http://${WebHost}:$WebPort"
Write-Host "  Viewer: http://127.0.0.1:$ViewerPort"
Write-Host "  MCP: http://${McpHost}:$McpPort/mcp"
Write-Host "  PID: $($process.Id)"
if ($Foreground) { Wait-Process -Id $process.Id }
