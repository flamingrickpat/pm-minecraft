& (Join-Path (Split-Path -Parent $PSScriptRoot) "setup.ps1") @args
exit $LASTEXITCODE
