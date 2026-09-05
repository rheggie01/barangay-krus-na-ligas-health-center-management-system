# Phase 13.2 Clinical Transaction and Medicine Dispensing Tests

Phase 13.2 extends the Phase 13.1 backend unit/policy suite with clinical
transaction regression tests. These tests use fake sessions and test-only model
objects; they do **not** connect to, modify, migrate, or restore the live
`barangay_health_db` database.

## Added coverage

- consultation creation writes actor snapshots and `CONSULTATION_CREATE` audit intent
- consultation update writes `CONSULTATION_UPDATE` audit intent
- consultation create/update rollback paths are exercised on transaction failure
- `commit=False` consultation creation remains controlled by the outer transaction
- consultation-linked medicine dispensing deducts PACKAGE or LOOSE stock correctly
- consultation dispensing writes `ConsultationMedicine` and `InventoryTransaction`
  records with immutable actor snapshots
- consultation dispensing records `CONSULTATION_MEDICINE_DISPENSE` audit intent
- unverified medicine and insufficient stock are rejected before commit
- dispensing commit failures invoke database rollback
- free medicine dispensing creates patient/medicine/staff snapshots
- free medicine dispensing creates a DISPENSE inventory ledger entry and audit log
- loose-unit dispensing can open whole packages and preserve remainder stock
- package dispensing only reduces package stock
- insufficient stock does not mutate stock in the validation path
- a consultation used for dispensing must belong to the selected patient
- inactive patient records cannot receive medicine

## Important transaction note

These are unit-level transaction tests. They verify service behavior, emitted
records, stock calculations, commit calls, and rollback calls without touching a
real database. A later disposable-database integration phase should verify that
MySQL itself restores persisted state after an intentionally failed transaction.

## Run

From the project root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest .\backend\tests -q
```

The Phase 13.1 suite contains 45 tests. Phase 13.2 adds 17 tests, so the expected
combined total is **62 tests** when all tests pass.
