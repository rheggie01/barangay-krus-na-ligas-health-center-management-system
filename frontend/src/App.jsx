import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import MainLayout from "./layouts/MainLayout";
import AuditLogs from "./pages/AuditLogs";
import BackupRecovery from "./pages/BackupRecovery";
import ConsultationDetails from "./pages/ConsultationDetails";
import Consultations from "./pages/Consultations";
import Dashboard from "./pages/Dashboard";
import Forecasts from "./pages/Forecasts";
import Inventory from "./pages/Inventory";
import Login from "./pages/Login";
import PatientDetails from "./pages/PatientDetails";
import Patients from "./pages/Patients";
import Register from "./pages/Register";
import Reports from "./pages/Reports";
import Surveillance from "./pages/Surveillance";
import Users from "./pages/Users";
import ProtectedRoute from "./routes/ProtectedRoute";
import RoleProtectedRoute from "./routes/RoleProtectedRoute";

import "./App.css";


function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/register"
        element={<Register />}
      />

      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route
          path="/dashboard"
          element={
            <RoleProtectedRoute page="dashboard">
              <Dashboard />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/patients"
          element={
            <RoleProtectedRoute page="patients">
              <Patients />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/patients/:patientId"
          element={
            <RoleProtectedRoute page="patients">
              <PatientDetails />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/consultations"
          element={
            <RoleProtectedRoute page="consultations">
              <Consultations />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/consultations/:consultationId"
          element={
            <RoleProtectedRoute page="consultations">
              <ConsultationDetails />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/surveillance"
          element={
            <RoleProtectedRoute page="surveillance">
              <Surveillance />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/inventory"
          element={
            <RoleProtectedRoute page="inventory">
              <Inventory />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/forecasts"
          element={
            <RoleProtectedRoute page="forecasts">
              <Forecasts />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/reports"
          element={
            <RoleProtectedRoute page="reports">
              <Reports />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/users"
          element={
            <RoleProtectedRoute page="users">
              <Users />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/audit-logs"
          element={
            <RoleProtectedRoute page="auditLogs">
              <AuditLogs />
            </RoleProtectedRoute>
          }
        />

        <Route
          path="/backup-recovery"
          element={
            <RoleProtectedRoute page="backupRecovery">
              <BackupRecovery />
            </RoleProtectedRoute>
          }
        />
      </Route>

      <Route
        path="/"
        element={
          <Navigate
            to="/dashboard"
            replace
          />
        }
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/dashboard"
            replace
          />
        }
      />
    </Routes>
  );
}


export default App;
