# Phase 13.6 — Final Regression & Capstone Validation Summary

## Objective

Provide a repeatable final regression process and an evidence structure suitable for capstone documentation and defense preparation.

## Current automated coverage

The backend regression suite contains 161 automated tests across five validation groups:

1. Authentication, account lifecycle, and RBAC — 45 tests
2. Clinical transactions and medicine dispensing — 17 tests
3. Sensitive-disease privacy and access controls — 32 tests
4. Disease forecasting and medicine decision-support validation — 35 tests
5. Backup/recovery authorization and operational safety — 32 tests

## Final regression procedure

Run from the repository root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\testing\Invoke-FinalValidation.ps1
```

This records:

- Git working-tree status,
- the full backend pytest suite,
- the repository quality check,
- and optionally the managed deployment health check.

For deployment evidence:

```powershell
.\scripts\testing\Invoke-FinalValidation.ps1 -IncludeDeploymentHealth
```

## PASS criteria

A release/defense regression run is considered PASS only when:

- all backend tests pass,
- backend Python syntax validation passes,
- no obvious tracked environment/key/database-backup files are detected,
- the frontend production build passes,
- and, when deployment evidence is included, MySQL/backend/frontend health checks pass.

## Evidence handling

Generated evidence is stored under `runtime/testing/`, which is intentionally ignored by Git. Use sanitized copies or screenshots for the manuscript/appendices. Avoid including credentials, raw health records, database dumps, secret keys, or personal cloud paths in capstone artifacts.

## Interpretation

Automated tests demonstrate that the implemented software behavior matches the tested contracts. They do not by themselves prove clinical effectiveness, real-world epidemiological accuracy, usability acceptance, or LGU operational approval. Those require separate authorized validation/UAT.
