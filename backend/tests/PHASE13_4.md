# Phase 13.4 - Forecast and Decision-Support Validation Tests

This phase adds regression tests for the disease and medicine forecasting layer without connecting to the live `barangay_health_db`.

Coverage includes:

- the four configured disease forecast aliases (Dengue, ARI, ILI, Diarrhea/Gastroenteritis);
- `MODEL_PENDING` behavior for active Disease Master conditions without a validated time-series model;
- 12-week disease forecast output and Monday-aligned forecast dates;
- completed-week cutoffs so the currently open disease-surveillance week is not treated as complete;
- non-negative forecast/confidence output clipping;
- forecast endpoint 404/503 error translation;
- six-month medicine forecast output aligned to the actual next calendar month;
- completed-month medicine-demand cutoffs;
- inventory package-to-dispensing-unit conversion;
- recommendation availability/withholding safety gates;
- `max(0, Forecast Demand + Safety Stock - Usable Current Stock)` and whole-unit ceiling behavior;
- DSS-only behavior: forecast reads do not create stock transactions or purchase orders.

These tests use mocks/fake sessions and deterministic dates. They do not decrement real medicine stock, create consultations, or write forecast recommendations to the production database.
