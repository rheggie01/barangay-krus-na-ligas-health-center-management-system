# Phase 12.3 — Deployment & Power-Recovery Hardening

This folder adds a Windows startup/recovery layer for the local health-center
deployment. It does **not** change the database schema.

## What it does

At Windows startup, a Task Scheduler job runs as `SYSTEM` after a short delay.

The long-running deployment monitor:

1. checks that MySQL is reachable;
2. starts MySQL when possible;
3. starts the FastAPI backend without development `--reload`;
4. serves the already-built React `dist` folder using a small SPA-aware Python
   HTTP server;
5. checks backend/database and frontend health;
6. restarts the backend or frontend if either managed process stops;
7. writes local runtime status/logs under `runtime/deployment/`.

The repository's existing backend already exposes `/api/v1/health` and checks a
real database connection. The frontend already uses `VITE_API_BASE_URL`, so its
production build continues to use the configured API URL.

## Files

- `Common-DeploymentFunctions.ps1`
- `Initialize-DeploymentSettings.ps1`
- `Ensure-MySqlReady.ps1`
- `Start-ProductionStack.ps1`
- `Stop-ProductionStack.ps1`
- `Restart-ProductionStack.ps1`
- `Get-DeploymentStatus.ps1`
- `Test-DeploymentHealth.ps1`
- `Test-AutoRecovery.ps1`
- `Install-StartupTask.ps1`
- `Uninstall-StartupTask.ps1`
- `serve_spa.py`
- `deployment-settings.example.json`

`deployment-settings.local.json` is machine-specific and ignored by Git.

## Installation

Open **PowerShell as Administrator**:

```powershell
cd C:\Users\PC\Desktop\barangay-health-system
Set-ExecutionPolicy -Scope Process Bypass

.\scripts\deployment\Initialize-DeploymentSettings.ps1
.\scripts\deployment\Install-StartupTask.ps1
```

The installer runs a production frontend build, makes sure MySQL is available,
registers the startup task, starts it immediately, and waits for a full health
check.

Expected:

```text
[PASS] MySQL
[PASS] Backend
[PASS] Frontend

APPLICATION HEALTHY
AUTO-START INSTALLATION VERIFIED
```

## Status

```powershell
.\scripts\deployment\Get-DeploymentStatus.ps1
```

## Health check

```powershell
.\scripts\deployment\Test-DeploymentHealth.ps1
```

## Restart managed application

Administrator PowerShell:

```powershell
.\scripts\deployment\Restart-ProductionStack.ps1
```

## Controlled self-healing test

This temporarily stops only the **managed backend/frontend processes** and waits
for the monitor to restore them. It does not stop MySQL and does not change the
database.

```powershell
.\scripts\deployment\Test-AutoRecovery.ps1
```

Run this only after the startup task owns both app processes.

## Final reboot test

After all checks pass:

1. close development `npm run dev` / `uvicorn --reload` terminals;
2. restart Windows normally;
3. wait about 1–2 minutes;
4. open the application;
5. run:

```powershell
.\scripts\deployment\Get-DeploymentStatus.ps1
.\scripts\deployment\Test-DeploymentHealth.ps1
```

The application should recover without manually starting backend/frontend.

## MySQL behavior

Preferred: MySQL/MariaDB is installed as a Windows service.

If no service is found and the system is using the common XAMPP paths, the
startup layer can start `C:\xampp\mysql\bin\mysqld.exe` with XAMPP's `my.ini`.

If your MySQL installation differs, edit the ignored
`deployment-settings.local.json`.

## Power interruption / UPS

Automatic restart does not replace a UPS.

Recommended deployment behavior:

- Put the application computer/server, router, and required network switch on a
  UPS.
- Use the UPS manufacturer's supported Windows shutdown software.
- Configure graceful Windows shutdown before the battery is exhausted.
- In BIOS/UEFI, consider **Restore on AC Power Loss = Power On** if approved by
  the health center.
- Test the exact UPS shutdown/restart procedure before real patient-data use.

Do not guess UPS-specific shutdown commands; configure them from the exact UPS
vendor/model documentation.

## Security

Default listeners are bound to `127.0.0.1`, not the whole LAN. That is safer for
a single-computer deployment.

If LAN access is later required, change host bindings and Windows Firewall rules
deliberately, and review CORS/TLS/network access before using real patient data.

## Logs

Local runtime logs are written under:

```text
runtime/deployment/logs/
```

The entire `runtime/` folder is ignored by Git.
