## Summary

Describe what this pull request changes.

## Module

- [ ] Authentication / RBAC
- [ ] Patients / EHR
- [ ] Consultations
- [ ] Disease surveillance
- [ ] Forecasting / ML
- [ ] Medicines / inventory
- [ ] Reports
- [ ] Audit / administration
- [ ] Documentation / infrastructure
- [ ] Other

## Safety and Data Checks

- [ ] No `.env`, password, JWT secret, private key, or credential was committed.
- [ ] No real patient PII or confidential LGU/health-center export was committed.
- [ ] Sensitive-disease access remains enforced by the backend.
- [ ] Inventory changes remain transactional where applicable.
- [ ] Synthetic data is not described as official LGU-provided data.

## Database

- [ ] No schema change.
- [ ] Schema change included with a reviewed hand-written Alembic migration.
- [ ] I did **not** use Alembic autogenerate.

## Verification

- [ ] Backend Python syntax check passed.
- [ ] Frontend production build passed.
- [ ] Relevant manual smoke tests passed.
