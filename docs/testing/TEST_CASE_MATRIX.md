# Test Case Matrix

| ID | Validation Area | Representative Requirement | Automated Evidence | Expected Result | Status Basis |
|---|---|---|---|---|---|
| AUTH-01 | Authentication | ACTIVE user with correct credentials can authenticate | `test_auth_service.py`, `test_auth_endpoints.py` | Allow | Automated |
| AUTH-02 | Authentication | PENDING/INACTIVE accounts cannot authenticate | `test_auth_service.py` | Deny | Automated |
| RBAC-01 | RBAC | Permissions are enforced by backend role/permission checks | `test_dependencies.py`, `test_rbac_policy.py` | Allow/Deny per policy | Automated |
| LIFE-01 | Account lifecycle | PENDING → ACTIVE → INACTIVE lifecycle rules are enforced | `test_user_lifecycle.py` | Valid transitions only | Automated |
| LIFE-02 | Admin safety | Last active SYSTEM_ADMIN cannot be deactivated | `test_user_endpoint_guards.py` | Block | Automated |
| CLIN-01 | Consultation | Consultation transaction creates required audit evidence | `test_consultation_transactions.py` | Commit + audit | Automated |
| DISP-01 | Dispensing | Medicine stock deduction and dispensing records are atomic | `test_consultation_dispensing_transactions.py`, `test_medicine_dispensing_transactions.py` | All-or-nothing | Automated |
| DISP-02 | Dispensing | Insufficient/unverified medicine is rejected | `test_medicine_dispensing_transactions.py` | Reject, no partial mutation | Automated |
| PRIV-01 | Sensitive disease | Unauthorized sensitive surveillance access returns denial | `test_sensitive_surveillance_access.py` | 403/Deny | Automated |
| PRIV-02 | Sensitive disease | Sensitive surveillance is aggregate-only | `test_sensitive_privacy_contracts.py` | No patient/location leakage | Automated |
| PRIV-03 | Sensitive disease | Sensitive street/hotspot mapping is blocked | `test_sensitive_surveillance_access.py` | Block | Automated |
| FORE-01 | Disease forecast | Supported models return 12-week forecast contract | `test_disease_forecast_runtime.py`, `test_runtime_forecast_periods.py` | 12 completed-week-aligned periods | Automated |
| FORE-02 | Disease catalog | Unsupported diseases remain `MODEL_PENDING` | `test_forecast_catalog_contracts.py` | No fake model forecast | Automated |
| DSS-01 | Medicine DSS | Recommendation uses forecast + safety stock − usable stock with zero floor | `test_medicine_forecast_dss.py` | Correct formula | Automated |
| DSS-02 | Medicine DSS | Forecasting does not mutate inventory or create procurement | `test_medicine_forecast_dss.py` | Advisory only | Automated |
| BACK-01 | Backup access | SYSTEM_ADMIN can run manual backup/restore verification | `test_backup_recovery_access.py` | Allow | Automated |
| BACK-02 | Backup access | HEALTH_CENTER_ADMIN is view-only; other roles denied | `test_backup_recovery_access.py` | View-only/Deny | Automated |
| BACK-03 | Restore safety | Restore verification uses temporary DB and does not overwrite live DB | `test_backup_recovery_safety_contracts.py` | Temporary verify DB only | Automated + operational design |
| DEPLOY-01 | Deployment | MySQL/backend/frontend recover after Windows startup | `scripts/deployment/*` operational test | Healthy/owned | Manual operational evidence |
| RECOV-01 | Recovery | Managed backend/frontend self-heal after process stop | `Test-AutoRecovery.ps1` | Services recover | Manual operational evidence |

## Notes

- The matrix summarizes representative requirements; the full automated suite contains 161 test cases.
- Manual operational rows should be supported by dated screenshots or generated validation logs.
- UAT rows should only be marked complete after actual authorized end-user evaluation.
