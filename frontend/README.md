# Frontend

React/Vite frontend for the Barangay Krus na Ligas Health Center Management System.

## Main Responsibilities

The frontend provides authorized interfaces for:

- Authentication
- Patient management
- Consultations
- Disease surveillance
- Forecasting
- Medicine inventory and dispensing
- Reports
- User administration
- Audit-related views

Security-sensitive authorization is enforced by the backend. Hiding a button or page in the frontend is not considered sufficient access control.

## Development

Run these commands inside the frontend folder:

npm install
Copy-Item .env.example .env
npm run dev

Typical development URL: http://localhost:5173

## Production Build

npm run build

The repository quality checks and GitHub Actions verify that the frontend can build successfully.

## Environment Variables

Use frontend/.env.example as the template for local configuration.
Do not commit the real frontend/.env file.
