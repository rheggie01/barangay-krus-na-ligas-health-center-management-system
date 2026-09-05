import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import MainLayout from "./layouts/MainLayout";

import AuditLogs from "./pages/AuditLogs";
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

      {/* =====================================================
          PUBLIC ROUTES
      ====================================================== */}

      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/register"
        element={<Register />}
      />


      {/* =====================================================
          PROTECTED APPLICATION
      ====================================================== */}

      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >

        {/* =================================================
            DASHBOARD
        ================================================== */}

        <Route
          path="/dashboard"
          element={
            <RoleProtectedRoute page="dashboard">
              <Dashboard />
            </RoleProtectedRoute>
          }
        />


        {/* =================================================
            PATIENT MANAGEMENT
        ================================================== */}

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


        {/* =================================================
            CONSULTATIONS
        ================================================== */}

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


        {/* =================================================
            DISEASE SURVEILLANCE
        ================================================== */}

        <Route
          path="/surveillance"
          element={
            <RoleProtectedRoute page="surveillance">
              <Surveillance />
            </RoleProtectedRoute>
          }
        />


        {/* =================================================
            MEDICINE INVENTORY
        ================================================== */}

        <Route
          path="/inventory"
          element={
            <RoleProtectedRoute page="inventory">
              <Inventory />
            </RoleProtectedRoute>
          }
        />


        {/* =================================================
            FORECASTS
        ================================================== */}

        <Route
          path="/forecasts"
          element={
            <RoleProtectedRoute page="forecasts">
              <Forecasts />
            </RoleProtectedRoute>
          }
        />


        {/* =================================================
            REPORTS
        ================================================== */}

        <Route
          path="/reports"
          element={
            <RoleProtectedRoute page="reports">
              <Reports />
            </RoleProtectedRoute>
          }
        />


        {/* =================================================
            USER MANAGEMENT
        ================================================== */}

        <Route
          path="/users"
          element={
            <RoleProtectedRoute page="users">
              <Users />
            </RoleProtectedRoute>
          }
        />


        {/* =================================================
            AUDIT LOGS
        ================================================== */}

        <Route
          path="/audit-logs"
          element={
            <RoleProtectedRoute page="auditLogs">
              <AuditLogs />
            </RoleProtectedRoute>
          }
        />

      </Route>


      {/* =====================================================
          DEFAULT ROUTE
      ====================================================== */}

      <Route
        path="/"
        element={
          <Navigate
            to="/dashboard"
            replace
          />
        }
      />


      {/* =====================================================
          UNKNOWN ROUTES
      ====================================================== */}

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