# Phase 14.1 — User Acceptance Testing (UAT) Readiness

This folder contains the manual acceptance-test materials for the Barangay Krus na Ligas Health Center Management System.

## Goal

Phase 14.1 validates the system from the perspective of intended health-center roles after automated regression testing has passed.

This phase does **not** replace the automated test suite. It complements it with role-based, end-to-end user acceptance scenarios that require actual UI interaction and observable behavior.

## Files

- `UAT_TEST_MATRIX.md` — master acceptance-test matrix
- `ROLE_BASED_UAT_CHECKLIST.md` — role-by-role execution checklist
- `UAT_SIGNOFF_TEMPLATE.md` — sign-off form for evaluator/reviewer use
- `DEFENSE_DEMO_FLOW.md` — recommended defense/demo sequence

## Evidence policy

Use synthetic/mock records for screenshots and demonstrations unless the health center has explicitly authorized use of real operational data.

Safe wording for development data:

> Synthetic/mock dataset informed by publicly available DOH and Quezon City LGU health reports and surveillance statistics.

Do not describe synthetic data as LGU-provided data.

## UAT result states

- `PASS` — behavior matches the expected result
- `FAIL` — behavior does not match the expected result
- `BLOCKED` — test cannot be completed because of an external dependency or unavailable setup
- `N/A` — scenario does not apply to the current environment
