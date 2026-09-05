# Role-Based UAT Checklist

Use synthetic/mock accounts representing each role.

## SYSTEM_ADMIN

- [ ] Can sign in when ACTIVE
- [ ] Can manage eligible user lifecycle actions
- [ ] Cannot deactivate own account
- [ ] Cannot deactivate the last active SYSTEM_ADMIN
- [ ] Can view Backup & Recovery status
- [ ] Can run manual backup
- [ ] Can run restore verification
- [ ] Cannot gain clinical permissions that are intentionally excluded by RBAC

## HEALTH_CENTER_ADMIN

- [ ] Can sign in when ACTIVE
- [ ] Can access authorized operational/admin views
- [ ] Can view Backup & Recovery status
- [ ] Cannot run manual backup or restore verification
- [ ] Medicine-dispensing behavior matches configured RBAC
- [ ] Sensitive-disease access matches permission assignment

## DOCTOR

- [ ] Can access authorized patient/consultation functions
- [ ] Can create/update consultations
- [ ] Can dispense medicine when permitted
- [ ] Can validate eligible disease cases
- [ ] Can access forecast features when permitted
- [ ] Sensitive-disease access is denied unless permission exists

## NURSE

- [ ] Can access authorized patient/consultation functions
- [ ] Can dispense medicine when permitted
- [ ] Cannot perform DOCTOR-only disease validation
- [ ] Cannot access restricted administration functions
- [ ] Sensitive-disease access follows permission assignment

## MIDWIFE

- [ ] Can access permitted patient/consultation functions
- [ ] Can dispense medicine when permitted
- [ ] Cannot perform DOCTOR-only disease validation
- [ ] Cannot access restricted administration functions
- [ ] Sensitive-disease access follows permission assignment

## BHW

- [ ] Can access only intended community/clinical functions
- [ ] Can dispense medicine when permitted
- [ ] Cannot perform DOCTOR-only disease validation
- [ ] Cannot access restricted administration functions
- [ ] Sensitive-disease access follows permission assignment

## Cross-role privacy checks

- [ ] Unauthorized users cannot retrieve sensitive disease cases through direct navigation/API
- [ ] Sensitive surveillance remains aggregate-only
- [ ] No sensitive street/hotspot/patient-location output is exposed
- [ ] General surveillance does not leak sensitive-disease rows
