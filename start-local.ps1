$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "Starting Barangay Health System locally..."
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://127.0.0.1:5173"

Start-Process powershell `
  -WindowStyle Normal `
  -WorkingDirectory $backend `
  -ArgumentList @(
    "-NoExit",
    "-Command",
    ".\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
  )

Start-Process powershell `
  -WindowStyle Normal `
  -WorkingDirectory $frontend `
  -ArgumentList @(
    "-NoExit",
    "-Command",
    "npm run dev -- --host 127.0.0.1"
  )

Write-Host "Both startup windows were opened."
