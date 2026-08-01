[CmdletBinding()]
param(
    [string]$PythonVersion = "3.12",
    [switch]$Refresh
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path $PSScriptRoot).Path
$venvPath = Join-Path $repoRoot ".venv"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install it from https://docs.astral.sh/uv/"
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js 20 or newer is required. Install it from https://nodejs.org/"
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found with Node.js. Reinstall Node.js, then rerun setup."
}

if (-not (Test-Path -LiteralPath $pythonPath)) {
    Write-Host "==> Creating .venv with Python $PythonVersion"
    & uv venv --python $PythonVersion $venvPath
} else {
    $version = (& $pythonPath --version 2>&1 | Out-String).Trim()
    if ($version -notmatch "Python $([regex]::Escape($PythonVersion))(\.|$)") {
        throw ".venv uses '$version', but this project requires Python $PythonVersion. Remove .venv after checking it, then rerun."
    }
    Write-Host "==> Reusing $version"
}

Push-Location $repoRoot
try {
    if ($Refresh) { & uv lock --upgrade }
    & uv sync --python $pythonPath
    if ($LASTEXITCODE -ne 0) { throw "Could not install Python dependencies." }
    & npm ci
    if ($LASTEXITCODE -ne 0) { throw "Could not install Node dependencies." }
} finally {
    Pop-Location
}

& $pythonPath -c "import fastmcp, pydantic, requests, ruamel.yaml; print('Python MCP environment ready')"
if ($LASTEXITCODE -ne 0) { throw "The MCP Python environment could not import its dependencies." }
& node --version
Write-Host "Environment ready: $venvPath" -ForegroundColor Green
