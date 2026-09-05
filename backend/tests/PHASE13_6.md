# Phase 13.6 — Final Regression & Capstone Testing Evidence

Phase 13.6 consolidates the automated testing work completed in Phases 13.1–13.5 and provides a repeatable final-validation workflow for capstone evidence.

## Automated regression baseline

| Phase | Coverage | Tests |
|---|---|---:|
| 13.1 | Authentication, account lifecycle, RBAC | 45 |
| 13.2 | Clinical transactions and medicine dispensing | 17 |
| 13.3 | Sensitive-disease privacy and surveillance access | 32 |
| 13.4 | Disease forecasting and medicine DSS validation | 35 |
| 13.5 | Backup/recovery authorization and operational safety | 32 |
| **Total** | **Backend automated regression suite** | **161** |

## Final validation command

From the project root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\testing\Invoke-FinalValidation.ps1
```

Optional managed deployment health evidence:

```powershell
.\scripts\testing\Invoke-FinalValidation.ps1 -IncludeDeploymentHealth
```

The generated evidence file is stored under the ignored runtime path:

```text
runtime/testing/final-validation-YYYYMMDD_HHMMSS.txt
```

Do not commit generated runtime evidence if it contains machine-specific paths or operational details. Keep sanitized copies for thesis appendices when appropriate.
