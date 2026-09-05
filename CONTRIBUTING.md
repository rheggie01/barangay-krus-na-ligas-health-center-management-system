# Contributing

This repository is developed as a team capstone project.

## Branching

Do not work directly on `main` for ordinary feature development.

Suggested branch names:

```text
feature/patient-search
feature/forecast-ui
fix/inventory-dispensing
docs/readme
```

Start from the latest `main`:

```powershell
git checkout main
git pull
git checkout -b feature/your-change
```

## Before Commit

Run:

```powershell
.\scripts\repo-quality-check.ps1
git status
```

Review the staged files before committing.

## Secrets and Health Data

Never commit:

- `.env`
- database passwords
- JWT secrets
- private keys
- real patient-identifiable information
- confidential health-center or LGU exports
- database backups

Synthetic datasets intentionally stored in the project must remain clearly identified as synthetic/mock.

## Migrations

For this project, do not run Alembic autogenerate.

Database schema migrations must be deliberately reviewed and hand-written because unrelated database/model drift is known to exist.

## Pull Requests

Use a Pull Request for team changes. The author should describe:

- what changed
- why it changed
- affected modules
- schema implications
- security/privacy implications
- manual tests performed

Avoid multiple team members editing the same large file at the same time when possible.
