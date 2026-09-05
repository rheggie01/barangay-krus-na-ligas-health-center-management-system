$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "Barangay Health System - Repository Quality Check"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/5] Git status"
git status --short
if ($LASTEXITCODE -ne 0) {
    throw "git status failed."
}

Write-Host ""
Write-Host "[2/5] Backend Python syntax"
python -m compileall -q backend\app backend\alembic
if ($LASTEXITCODE -ne 0) {
    throw "Backend Python syntax check failed."
}
Write-Host "PASS: Backend Python syntax"

Write-Host ""
Write-Host "[3/5] Backend authentication and RBAC tests"
python -m pytest backend\tests -q
if ($LASTEXITCODE -ne 0) {
    throw (
        "Backend tests failed. If pytest is not installed, run: " +
        "python -m pip install -r backend\requirements-test.txt"
    )
}
Write-Host "PASS: Backend authentication and RBAC tests"

Write-Host ""
Write-Host "[4/5] Check accidental secrets / database backups"
$TrackedSensitive = git ls-files | Select-String -Pattern `
    '(^|/)\.env$|\.pem$|\.key$|database_backups/|\.sql$'
if ($TrackedSensitive) {
    Write-Host "Potential sensitive tracked files found:"
    $TrackedSensitive
    throw "Review tracked sensitive files before committing."
}
Write-Host "PASS: No obvious tracked environment/key/backup files"

Write-Host ""
Write-Host "[5/5] Frontend production build"
Push-Location frontend
try {
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend production build failed."
    }
}
finally {
    Pop-Location
}
Write-Host "PASS: Frontend production build"
Write-Host ""
Write-Host "ALL REPOSITORY QUALITY CHECKS PASSED"
