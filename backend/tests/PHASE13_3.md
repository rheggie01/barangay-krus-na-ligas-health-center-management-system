# Phase 13.3 — Sensitive Disease Privacy & Surveillance Access Tests

Phase 13.3 adds regression tests around the system's sensitive/program disease
privacy boundary.

## Protected behavior

The tests verify that:

- `GENERAL` surveillance never opts into sensitive disease rows.
- `SENSITIVE` surveillance requires `SENSITIVE_DISEASE_VIEW`.
- Sensitive surveillance is exposed only through aggregate disease-count and
  weekly-trend endpoints.
- Street-level mapping is blocked for sensitive/program surveillance even for
  an otherwise authorized sensitive-disease viewer.
- General street-level surveillance explicitly excludes sensitive rows.
- Consultation disease-case lists hide sensitive records from users who do not
  hold `SENSITIVE_DISEASE_VIEW`.
- Read, create, edit, and validation flows enforce the sensitive-disease check
  before returning or mutating a sensitive disease record.
- Sensitive forecast catalog/detail and disease-to-medicine mapping access
  requires the explicit sensitive-disease permission.
- Aggregate surveillance response contracts do not expose patient identity,
  address, coordinates, or street fields.

## Test isolation

These are unit/policy regression tests. They do not connect to or mutate the
live `barangay_health_db`. Existing test-only environment configuration in
`backend/tests/conftest.py` remains authoritative.

## Run

From the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest .\backend\tests -q
```

Then run the repository quality check:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\repo-quality-check.ps1
```
