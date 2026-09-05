# Barangay Krus na Ligas Health Center Management System

A predictive analytics-driven barangay health center management system for disease surveillance, consultation management, medicine inventory, forecasting, and medicine-based resource allocation.

## Capstone Title

**A Predictive Analytics-Driven Barangay Health Center Management System Using Machine Learning for Disease Surveillance and Medicine-Based Resource Allocation for Barangay Krus na Ligas**

## Project Scope

The system is designed as a barangay health-center management platform with:

- Patient registration and electronic health records
- Consultations and structured symptom capture
- Disease case recording and validation
- Disease surveillance and geographic visualization
- Sensitive-disease access controls
- Medicine formulary and inventory management
- Consultation-based medicine dispensing
- Disease trend forecasting
- Medicine-demand forecasting and advisory resource allocation
- Role-based access control
- Application audit trails
- Administrative reports

## Technology Stack

### Frontend
- React
- Vite
- Axios
- React Router
- Leaflet / React Leaflet
- Recharts

### Backend
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- JWT authentication
- PyMySQL

### Database
- MySQL

### Analytics / Machine Learning
- Python
- pandas
- NumPy
- scikit-learn
- statistical forecasting modules used by the project

## User Roles

The application supports the following staff roles:

- SYSTEM_ADMIN
- HEALTH_CENTER_ADMIN
- DOCTOR
- NURSE
- MIDWIFE
- BHW

Authorization is enforced by the backend through permissions. Frontend visibility is not treated as the authoritative security boundary.

## Privacy and Sensitive Health Information

Sensitive illnesses are subject to additional access controls. Sensitive surveillance is intentionally restricted to aggregate views and must not expose patient-level exact locations or street-level sensitive disease mapping.

The project is intended to follow data-minimization principles and should not store unnecessary exact patient location data.

## Development Dataset Disclosure

Current development and demonstration datasets are **synthetic/mock data** informed by publicly available Department of Health and Quezon City LGU health reports and surveillance statistics.

They are **not official patient records supplied by the LGU or health center**.

Development metrics produced from synthetic datasets are technical/developmental results only and must not be presented as evidence of real-world clinical predictive accuracy.

Before operational deployment, models and decision-support outputs should be validated using authorized data and reviewed by qualified health professionals or designated health-center personnel.

## Predictive Analytics

The current development disease-forecasting catalog includes validated model-capable diseases such as:

- Dengue
- Acute Respiratory Infection (ARI)
- Influenza-Like Illness (ILI)
- Diarrhea / Gastroenteritis

Other active diseases may be displayed as `MODEL_PENDING` rather than receiving a fabricated or unvalidated forecast.

Medicine-demand forecasting is advisory. Forecast outputs must not automatically mutate inventory or create procurement orders.

A resource-allocation recommendation may follow the general decision-support relationship:

```text
Recommended Additional Stock
= max(0, Forecast Demand + Safety Stock - Usable Current Stock)
```

This is decision support, not an automatic procurement action.

## Repository Structure

```text
barangay-health-system/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── seed/
│   │   └── services/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── .env.example
│   └── package.json
├── .github/
│   └── workflows/
├── .gitattributes
├── .gitignore
└── start-local.ps1
```

## Local Development Setup

### Prerequisites

Install:

- Git
- Python
- Node.js
- MySQL Server or a compatible local MySQL installation

### 1. Clone

```powershell
git clone https://github.com/rheggie01/barangay-krus-na-ligas-health-center-management-system.git
cd barangay-krus-na-ligas-health-center-management-system
```

### 2. Backend

```powershell
cd backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install additional project analytics requirements when needed:

```powershell
python -m pip install -r requirements-ml.txt
python -m pip install -r requirements-forecast.txt
python -m pip install -r requirements-medicine-forecast.txt
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and provide local credentials and a unique JWT secret.

Generate a strong development JWT secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Never commit the actual `.env`.

### 3. Database

The default development database name documented by the project is:

```text
barangay_health_db
```

Create it if necessary, then apply existing migrations:

```powershell
python -m alembic current
python -m alembic heads
python -m alembic upgrade head
```

**Do not use Alembic autogenerate for this project.** Existing migration/model drift is known, so project migrations should be reviewed and written explicitly.

### 4. Backend Server

```powershell
python -m uvicorn app.main:app --reload
```

Typical development URL:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 5. Frontend

Open another PowerShell window:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Typical Vite URL:

```text
http://localhost:5173
```

## Git Team Workflow

Use feature branches instead of editing `main` directly.

```powershell
git pull
git checkout -b feature/short-description
```

After changes:

```powershell
git status
git add .
git commit -m "Describe the change"
git push -u origin feature/short-description
```

Then open a Pull Request and review it before merging into `main`.

## Quality Checks

Run the local repository quality script:

```powershell
.\scripts\repo-quality-check.ps1
```

GitHub Actions also checks backend Python syntax and the frontend production build on pushes and pull requests.

## Backup and Recovery

Source code is protected through local Git history and the GitHub repository.

The MySQL database is **not** backed up by Git. Database backup and recovery should be implemented separately using automated MySQL dumps, retention, encryption, off-device storage, and periodic restore verification.

Do not commit:

- real patient exports
- database backups
- `.env`
- passwords
- API/JWT secrets
- private keys
- confidential LGU or health-center datasets

## Deployment Status

This repository represents a capstone/development system and should not be treated as production-ready healthcare infrastructure without additional operational validation, backup/recovery automation, security hardening, user acceptance testing, and authorized data governance.

## License

No open-source license is currently declared. Unless a license is explicitly added, repository visibility does not automatically grant reuse rights.
