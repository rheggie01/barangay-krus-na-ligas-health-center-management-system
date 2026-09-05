import { useState } from "react";
import {
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";

import { registerUser } from "../api/registrationApi";
import { useAuth } from "../context/AuthContext";

import krusNaLigasLogo from "../assets/krus-na-ligas-logo.jpg";
import healthCenterBackground from "../assets/health-center-background.png";

import "../styles/Register.css";


/* =========================================================
   CONSTANTS
========================================================= */

const ROLE_OPTIONS = [
  {
    value: "HEALTH_CENTER_ADMIN",
    label: "Health Center Administrator",
  },
  {
    value: "DOCTOR",
    label: "Doctor",
  },
  {
    value: "NURSE",
    label: "Nurse",
  },
  {
    value: "MIDWIFE",
    label: "Midwife",
  },
  {
    value: "BHW",
    label: "Barangay Health Worker",
  },
];


/* =========================================================
   INITIAL FORM
========================================================= */

const INITIAL_FORM = {
  first_name: "",
  last_name: "",
  username: "",
  email: "",
  password: "",
  confirm_password: "",
  role_name: "BHW",
  privacy_accepted: false,
};


/* =========================================================
   ERROR HELPER
========================================================= */

function getApiErrorMessage(error) {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = item?.loc?.at(-1);
        const message = item?.msg || "Invalid information.";

        if (field) {
          return `${field}: ${message}`;
        }

        return message;
      })
      .join(" | ");
  }

  return (
    "Unable to submit your registration. " +
    "Please check your information and try again."
  );
}


/* =========================================================
   REGISTER PAGE
========================================================= */

function Register() {
  const navigate = useNavigate();

  const {
    isAuthenticated,
  } = useAuth();

  const [form, setForm] =
    useState(INITIAL_FORM);

  const [submitting, setSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");


  /* =======================================================
     AUTHENTICATED USER
  ======================================================= */

  if (isAuthenticated) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }


  /* =======================================================
     INPUT CHANGE
  ======================================================= */

  const handleChange = (event) => {
    const {
      name,
      value,
      type,
      checked,
    } = event.target;

    setForm((current) => ({
      ...current,

      [name]:
        type === "checkbox"
          ? checked
          : value,
    }));

    if (error) {
      setError("");
    }
  };


  /* =======================================================
     VALIDATION
  ======================================================= */

  const validateForm = () => {
    if (!form.first_name.trim()) {
      return "First name is required.";
    }

    if (!form.last_name.trim()) {
      return "Last name is required.";
    }

    if (!form.username.trim()) {
      return "Username is required.";
    }

    if (!form.email.trim()) {
      return "Email address is required.";
    }

    if (form.password.length < 8) {
      return "Password must contain at least 8 characters.";
    }

    if (
      form.password !==
      form.confirm_password
    ) {
      return "Passwords do not match.";
    }

    if (!form.role_name) {
      return "Requested role is required.";
    }

    if (!form.privacy_accepted) {
      return (
        "Please acknowledge the Data Privacy Act " +
        "before submitting your registration."
      );
    }

    return "";
  };


  /* =======================================================
     SUBMIT REGISTRATION
  ======================================================= */

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    const validationError =
      validateForm();

    if (validationError) {
      setError(validationError);
      return;
    }

    /*
      IMPORTANT:
      These keys must match the FastAPI RegisterRequest schema:
      first_name
      last_name
      username
      email
      password
      confirm_password
      role_name
      privacy_accepted
    */
    const payload = {
      first_name:
        form.first_name.trim(),

      last_name:
        form.last_name.trim(),

      username:
        form.username.trim(),

      email:
        form.email
          .trim()
          .toLowerCase(),

      password:
        form.password,

      confirm_password:
        form.confirm_password,

      role_name:
        form.role_name,

      privacy_accepted:
        form.privacy_accepted,
    };

    try {
      setSubmitting(true);

      await registerUser(payload);

      navigate(
        "/login",
        {
          replace: true,

          state: {
            registrationSuccess: true,
          },
        }
      );
    } catch (err) {
      console.error(
        "Registration failed:",
        err
      );

      setError(
        getApiErrorMessage(err)
      );
    } finally {
      setSubmitting(false);
    }
  };


  /* =========================================================
     PAGE
  ========================================================= */

  return (
    <main
      className="register-page"
      style={{
        backgroundImage:
          `url(${healthCenterBackground})`,
      }}
    >
      <div className="register-background-overlay" />

      <section className="register-card">

        {/* BRAND */}

        <div className="register-brand">
          <img
            src={krusNaLigasLogo}
            alt="Barangay Krus na Ligas Logo"
          />

          <div>
            <h1>
              Krus na Ligas Health Center
            </h1>

            <p>
              Health Management System
            </p>
          </div>
        </div>


        {/* HEADER */}

        <div className="register-heading">
          <h2>
            Register New User
          </h2>

          <p>
            Submit your information for
            administrator approval.
          </p>
        </div>


        {/* ERROR */}

        {error && (
          <div
            className="register-error"
            role="alert"
          >
            {error}
          </div>
        )}


        {/* FORM */}

        <form
          className="register-form"
          onSubmit={handleSubmit}
        >

          <div className="register-grid">

            <FormField
              label="First Name"
              name="first_name"
              value={form.first_name}
              onChange={handleChange}
              disabled={submitting}
              required
            />

            <FormField
              label="Last Name"
              name="last_name"
              value={form.last_name}
              onChange={handleChange}
              disabled={submitting}
              required
            />

            <FormField
              label="Username"
              name="username"
              value={form.username}
              onChange={handleChange}
              autoComplete="username"
              disabled={submitting}
              required
            />

            <FormField
              label="Email Address"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
              disabled={submitting}
              required
            />

            <FormField
              label="Password"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              minLength={8}
              autoComplete="new-password"
              disabled={submitting}
              required
            />

            <FormField
              label="Confirm Password"
              name="confirm_password"
              type="password"
              value={form.confirm_password}
              onChange={handleChange}
              minLength={8}
              autoComplete="new-password"
              disabled={submitting}
              required
            />

          </div>


          {/* REQUESTED ROLE */}

          <label className="register-field">
            <span>
              Requested Role
            </span>

            <select
              name="role_name"
              value={form.role_name}
              onChange={handleChange}
              disabled={submitting}
              required
            >
              {ROLE_OPTIONS.map(
                (role) => (
                  <option
                    key={role.value}
                    value={role.value}
                  >
                    {role.label}
                  </option>
                )
              )}
            </select>
          </label>


          <p className="register-help">
            Your account will remain pending
            until approved by an authorized
            Health Center administrator.
          </p>


          {/* PRIVACY */}

          <label className="register-privacy">
            <input
              type="checkbox"
              name="privacy_accepted"
              checked={
                form.privacy_accepted
              }
              onChange={handleChange}
              disabled={submitting}
              required
            />

            <span>
              I acknowledge the{" "}

              <strong>
                Data Privacy Act of 2012
                (Republic Act No. 10173).
              </strong>
            </span>
          </label>


          {/* ACTION */}

          <button
            type="submit"
            className="register-button"
            disabled={submitting}
          >
            {submitting
              ? "Submitting Registration..."
              : "Submit Registration"}
          </button>

        </form>


        {/* LOGIN LINK */}

        <div className="register-login">
          <span>
            Already have an account?
          </span>

          <Link to="/login">
            Sign In
          </Link>
        </div>

      </section>
    </main>
  );
}


/* =========================================================
   FORM FIELD
========================================================= */

function FormField({
  label,
  name,
  type = "text",
  ...props
}) {
  return (
    <label className="register-field">
      <span>
        {label}
      </span>

      <input
        type={type}
        name={name}
        {...props}
      />
    </label>
  );
}


export default Register;
