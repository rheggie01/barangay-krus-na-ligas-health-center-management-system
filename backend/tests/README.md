# Phase 13.1 Backend Authentication and RBAC Tests

This suite provides the first automated test foundation for the capstone backend.
It is intentionally designed as a **unit/policy test suite** and does not create,
modify, migrate, or restore the live `barangay_health_db` database.

## Covered in Phase 13.1

- password hashing and verification
- JWT creation, decoding, expiration, and malformed-token rejection
- login authentication for ACTIVE/PENDING/INACTIVE accounts
- login endpoint success/failure audit intent
- self-registration starts as PENDING and inactive
- self-registration cannot request SYSTEM_ADMIN
- privacy acknowledgement and password confirmation validation
- authenticated-user account-status enforcement
- permission dependency allow/deny behavior
- PENDING -> ACTIVE -> INACTIVE -> ACTIVE lifecycle rules
- pending-only hard-delete safeguards
- self-deactivation and last-active-SYSTEM_ADMIN protection
- RBAC policy regression checks for medicine dispensing, disease validation,
  disease prediction, sensitive-disease access, and user management

## Install test dependencies

From the project root with the backend virtual environment active:

```powershell
python -m pip install -r .\backend\requirements-test.txt
```

## Run tests

From the project root:

```powershell
python -m pytest .\backend\tests -q
```

Or from the `backend` directory:

```powershell
python -m pytest
```

The test settings use non-production placeholder environment values. They do
not require a running MySQL server because Phase 13.1 does not perform live DB
integration tests.

## Important

Do not replace these tests with tests against the live health-center database.
Later integration-test phases should use a dedicated disposable test database.
