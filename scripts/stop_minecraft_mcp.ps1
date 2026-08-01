param(
    [Parameter(Mandatory = $true)]
    [string]$ArtifactRoot
)

$ErrorActionPreference = "Stop"
$resolvedArtifactRoot = [System.IO.Path]::GetFullPath($ArtifactRoot)
$processFile = Join-Path $resolvedArtifactRoot "service-process.yaml"
if (-not (Test-Path -LiteralPath $processFile -PathType Leaf)) {
    throw "Service process receipt not found: $processFile"
}
function Read-ReceiptPid([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }
    $pidLine = Get-Content -LiteralPath $Path |
        Where-Object { $_ -match "^pid:\s+\d+$" } |
        Select-Object -First 1
    if (-not $pidLine) {
        throw "Process receipt has no valid pid: $Path"
    }
    return [int](($pidLine -split ":", 2)[1].Trim())
}

$bodyPid = Read-ReceiptPid (
    Join-Path $resolvedArtifactRoot "body-process.yaml"
)
$servicePid = Read-ReceiptPid $processFile
$stopped = @()
foreach ($ownedPid in @($bodyPid, $servicePid)) {
    if (-not $ownedPid) {
        continue
    }
    $process = Get-Process -Id $ownedPid -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $ownedPid -Force -ErrorAction Stop
        $stopped += $ownedPid
    }
}
if ($stopped.Count -eq 0) {
    Write-Host "Minecraft embodiment is already stopped."
}
else {
    Write-Host "Stopped Minecraft embodiment processes: $($stopped -join ', ')"
}
