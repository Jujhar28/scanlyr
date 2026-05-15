# Run backend pytest from backend/ (parent of this scripts folder).
# Optional: set TEST_DATABASE_URL first (see tests/env.test.example).
param(
    [string[]]$PytestArgs = @("tests", "-q", "--tb=short")
)

$ErrorActionPreference = "Stop"
$backend = Split-Path -Parent $PSScriptRoot
Set-Location $backend
$pytest = Join-Path $backend ".venv\Scripts\pytest.exe"
if (-not (Test-Path $pytest)) {
    Write-Error "Missing $pytest - create venv and: pip install -r requirements.txt"
}
Write-Host "pytest cwd: $backend"
& $pytest @PytestArgs
