# Capstone Defense Evidence Checklist

Use this checklist before final manuscript submission or defense.

## Automated regression

- [ ] Run `Invoke-FinalValidation.ps1`.
- [ ] Confirm all 161 backend tests pass.
- [ ] Confirm repository quality check passes.
- [ ] Capture a dated screenshot or sanitized text output.

## Security and privacy

- [ ] Capture evidence of ACTIVE/PENDING/INACTIVE account behavior.
- [ ] Capture representative RBAC deny/allow behavior.
- [ ] Capture sensitive-disease unauthorized access denial.
- [ ] Capture aggregate-only sensitive surveillance output.
- [ ] Confirm no patient/street/hotspot details are shown for sensitive surveillance.

## Clinical transactions

- [ ] Capture a successful consultation/dispensing workflow using synthetic/mock data.
- [ ] Capture inventory decrement and corresponding transaction/audit evidence.
- [ ] Capture a rejected/rollback scenario such as insufficient stock.

## Forecasting and DSS

- [ ] Capture disease forecast output for at least one validated model disease.
- [ ] Capture `MODEL_PENDING` behavior for an unsupported disease.
- [ ] Capture medicine forecast recommendation and explain the formula.
- [ ] State clearly that recommendations are decision support only and do not automatically procure or mutate stock.
- [ ] State that development data is synthetic/mock and technical metrics are not real clinical accuracy claims.

## Backup, recovery, and deployment

- [ ] Capture successful encrypted backup status.
- [ ] Capture successful restore verification status.
- [ ] Capture SYSTEM_ADMIN vs HEALTH_CENTER_ADMIN backup UI authorization behavior.
- [ ] Capture managed deployment health after actual Windows reboot.
- [ ] Capture auto-recovery/self-healing PASS evidence.

## Final documentation integrity

- [ ] Do not include `.env`, passwords, keys, raw database dumps, or personal cloud credentials.
- [ ] Do not describe synthetic/mock data as LGU-provided.
- [ ] Do not claim professional/LGU validation unless it actually occurred and permission exists to state it.
- [ ] Separate automated software validation from future UAT/clinical validation.
