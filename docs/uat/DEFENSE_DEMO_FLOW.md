# Recommended Defense Demo Flow

Keep the live demonstration short, role-aware, and evidence-based.

## 1. Readiness proof

1. Show managed deployment status: MySQL, backend, frontend HEALTHY.
2. Show latest final validation result: 161 automated tests passed.
3. State that demo records are synthetic/mock unless authorized operational data is being used.

## 2. Authentication and RBAC

1. Sign in using an ACTIVE clinical account.
2. Briefly show that restricted administration functions are not available to the role.
3. If needed, show SYSTEM_ADMIN user lifecycle controls separately.

## 3. Patient and consultation workflow

1. Open a synthetic patient.
2. Create or open a consultation.
3. Add medicine and perform a permitted dispensing action.
4. Show the resulting inventory movement/audit evidence.

## 4. Disease surveillance and privacy

1. Show general surveillance.
2. Demonstrate sensitive surveillance only with an authorized account.
3. Emphasize aggregate-only sensitive reporting and absence of sensitive street/hotspot/patient-location output.

## 5. Predictive analytics and DSS

1. Show one validated disease forecast (for example Dengue).
2. Explain that the runtime horizon is 12 weeks.
3. Show a disease without a validated model and the `MODEL_PENDING` behavior.
4. Show medicine demand forecast and recommended additional stock.
5. Emphasize that recommendations are decision support only and do not automatically mutate inventory or create procurement orders.

## 6. Backup, recovery, and deployment resilience

1. Show Backup & Recovery status page.
2. Explain SYSTEM_ADMIN action authorization versus HEALTH_CENTER_ADMIN view-only behavior.
3. Show successful restore-verification evidence.
4. Mention verified Windows auto-start and application self-healing.

## 7. Close with validation scope

State that the system has passed the current automated regression baseline and UAT is used to validate actual user-facing workflows before final acceptance.
