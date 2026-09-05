# UAT Test Matrix

## Environment

Record the following before execution:

- Test date:
- Tester/evaluator:
- Commit / release reference:
- Browser:
- Windows version:
- Backend health:
- Frontend health:
- MySQL status:
- Data classification: Synthetic / Authorized operational data

## Acceptance matrix

| ID | Area | Role | Scenario | Expected result | Result | Evidence |
|---|---|---|---|---|---|---|
| UAT-AUTH-01 | Authentication | Any active user | Sign in using valid credentials | User reaches authorized dashboard |  |  |
| UAT-AUTH-02 | Authentication | Any user | Sign in using incorrect password | Login is rejected without exposing sensitive details |  |  |
| UAT-AUTH-03 | Lifecycle | Pending user | Attempt to sign in | Access is denied until activation |  |  |
| UAT-AUTH-04 | Lifecycle | Inactive user | Attempt to sign in | Access is denied |  |  |
| UAT-RBAC-01 | User management | SYSTEM_ADMIN | Open user-management functions | Authorized management controls are available |  |  |
| UAT-RBAC-02 | User management | Non-admin clinical role | Attempt to access restricted user-management action | Backend/UI denies restricted action |  |  |
| UAT-RBAC-03 | Lifecycle | SYSTEM_ADMIN | Attempt to deactivate own account | Action is blocked |  |  |
| UAT-RBAC-04 | Lifecycle | SYSTEM_ADMIN | Attempt to deactivate last active SYSTEM_ADMIN | Action is blocked |  |  |
| UAT-PAT-01 | Patients | Authorized clinical role | Create a synthetic patient | Patient record saves successfully |  |  |
| UAT-PAT-02 | Patients | Authorized clinical role | Update a synthetic patient | Updated details persist |  |  |
| UAT-CON-01 | Consultation | DOCTOR | Create consultation for active synthetic patient | Consultation saves and is visible in patient history |  |  |
| UAT-CON-02 | Consultation | Authorized clinical role | Add consultation medicine | Medicine line is associated with the consultation |  |  |
| UAT-MED-01 | Dispensing | DOCTOR/NURSE/MIDWIFE/BHW/HCA as configured | Dispense available verified medicine | Stock decreases correctly and transaction is recorded |  |  |
| UAT-MED-02 | Dispensing | Authorized dispenser | Attempt to dispense more than usable stock | Action is rejected; stock is unchanged |  |  |
| UAT-MED-03 | Dispensing | Unauthorized role | Attempt medicine-dispensing action | Action is denied |  |  |
| UAT-DIS-01 | Disease case | Authorized role | Record general disease case | Case saves according to workflow |  |  |
| UAT-DIS-02 | Validation | DOCTOR | Validate eligible disease case | Status changes to validated |  |  |
| UAT-DIS-03 | Validation | Non-DOCTOR | Attempt disease-case validation | Action is denied |  |  |
| UAT-PRIV-01 | Sensitive surveillance | Authorized sensitive-data user | Open sensitive aggregate surveillance | Aggregate statistics are available |  |  |
| UAT-PRIV-02 | Sensitive surveillance | Unauthorized user | Attempt sensitive surveillance access | Access is denied |  |  |
| UAT-PRIV-03 | Sensitive privacy | Authorized sensitive-data user | Inspect sensitive surveillance view | No street/hotspot/patient-location output is exposed |  |  |
| UAT-PRIV-04 | General surveillance | Authorized user | Open general street-level view | Sensitive diseases are excluded |  |  |
| UAT-FCST-01 | Disease forecast | Forecast-authorized role | Request Dengue forecast | 12-week forecast renders successfully |  |  |
| UAT-FCST-02 | Disease forecast | Forecast-authorized role | Request ARI/ILI/Diarrhea forecast | Configured model forecast renders |  |  |
| UAT-FCST-03 | Disease forecast | Forecast-authorized role | Select disease without validated model | `MODEL_PENDING`/equivalent pending state is shown; no fake forecast is generated |  |  |
| UAT-FCST-04 | Sensitive forecast | Unauthorized user | Attempt sensitive forecast access | Access is denied |  |  |
| UAT-DSS-01 | Medicine DSS | Authorized role | View medicine demand forecast | Forecast and recommendation values render |  |  |
| UAT-DSS-02 | Medicine DSS | Authorized role | Inspect recommended additional stock | Value follows forecast + safety stock - usable stock with zero floor |  |  |
| UAT-DSS-03 | Medicine DSS | Authorized role | View recommendation | No inventory/procurement mutation occurs automatically |  |  |
| UAT-BKP-01 | Backup status | HEALTH_CENTER_ADMIN | Open Backup & Recovery page | Status is visible; action controls remain unavailable |  |  |
| UAT-BKP-02 | Backup action | SYSTEM_ADMIN | Run manual backup | Backup completes and status/audit updates |  |  |
| UAT-BKP-03 | Restore verification | SYSTEM_ADMIN | Run restore test | Temporary verification succeeds without overwriting live DB |  |  |
| UAT-BKP-04 | Backup authorization | Non-admin role | Attempt backup/recovery endpoint/action | Access is denied |  |  |
| UAT-DEP-01 | Deployment | Maintainer | Reboot Windows and wait for startup task | MySQL/backend/frontend return healthy automatically |  |  |
| UAT-DEP-02 | Recovery | Maintainer | Stop only managed app processes using recovery test | Monitor restores backend/frontend to healthy state |  |  |
| UAT-AUD-01 | Audit | Authorized reviewer | Inspect recent auditable operations | Relevant actor/action information is recorded |  |  |

## Completion rule

Phase 14.1 UAT is ready for sign-off when all mandatory scenarios are `PASS`, or when any `BLOCKED`/`N/A` item has a documented and accepted reason.
