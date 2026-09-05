import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../context/AuthContext";

import krusNaLigasLogo
  from "../assets/krus-na-ligas-logo.jpg";

import healthCenterBackground
  from "../assets/health-center-background.png";

import "../styles/Login.css";


/* =========================================================
   HELPERS
========================================================= */

function getLoginErrorMessage(error) {
  const detail =
    error?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map(
        (item) =>
          item?.msg ||
          "Invalid login information."
      )
      .join(" ");
  }

  return (
    "Invalid username or password, or your " +
    "account is still awaiting approval."
  );
}


/* =========================================================
   LOGIN PAGE
========================================================= */

function Login() {
  const {
    login,
    isAuthenticated,
  } = useAuth();

  const location =
    useLocation();

  const navigate =
    useNavigate();


  /* =======================================================
     FORM STATE
  ======================================================= */

  const [
    username,
    setUsername,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    privacyAccepted,
    setPrivacyAccepted,
  ] = useState(false);


  /* =======================================================
     UI STATE
  ======================================================= */

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");


  /* =======================================================
     REGISTRATION SUCCESS MESSAGE
  ======================================================= */

  useEffect(() => {
    if (
      location.state?.registrationSuccess
    ) {
      setSuccessMessage(
        "Registration submitted successfully. " +
        "Your account is awaiting administrator approval."
      );

      /*
       * Remove navigation state after reading it
       * so the message does not reappear forever.
       */
      navigate(
        location.pathname,
        {
          replace: true,
          state: null,
        }
      );
    }
  }, [
    location.pathname,
    location.state,
    navigate,
  ]);


  /* =======================================================
     REDIRECT AUTHENTICATED USER
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
     LOGIN
  ======================================================= */

  const handleSubmit =
    async (event) => {
      event.preventDefault();

      setError("");
      setSuccessMessage("");

      const normalizedUsername =
        username.trim();

      if (!normalizedUsername) {
        setError(
          "Please enter your username or email."
        );

        return;
      }

      if (password.length < 8) {
        setError(
          "Password must contain at least 8 characters."
        );

        return;
      }

      if (!privacyAccepted) {
        setError(
          "Please acknowledge the Data Privacy Act before signing in."
        );

        return;
      }

      try {
        setLoading(true);

        await login(
          normalizedUsername,
          password
        );

      } catch (err) {
        console.error(
          "Login failed:",
          err
        );

        setError(
          getLoginErrorMessage(err)
        );

      } finally {
        setLoading(false);
      }
    };


  /* =======================================================
     PAGE
  ======================================================= */

  return (
    <main
      className="login-page"
      style={{
        backgroundImage:
          `url(${healthCenterBackground})`,
      }}
    >
      <div className="login-background-overlay" />

      <section className="login-card">

        {/* BRANDING */}

        <div className="login-brand">

          <div className="login-logo">
            <img
              src={krusNaLigasLogo}
              alt="Barangay Krus na Ligas Logo"
            />
          </div>

          <h1>
            Krus na Ligas
            <br />
            Health Center
          </h1>

          <p>
            Health Management System
          </p>

        </div>


        {/* LOGIN HEADER */}

        <div className="login-heading">

          <h2>
            Welcome Back
          </h2>

          <p>
            Sign in to your account
            to continue.
          </p>

        </div>


        {/* SUCCESS MESSAGE */}

        {successMessage && (
          <div
            className="login-success"
            role="status"
          >
            {successMessage}
          </div>
        )}


        {/* LOGIN FORM */}

        <form
          className="login-form"
          onSubmit={handleSubmit}
        >

          <div className="login-field">

            <label htmlFor="username">
              Username or Email
            </label>

            <input
              id="username"
              name="username"
              type="text"
              value={username}
              onChange={(event) => {
                setUsername(
                  event.target.value
                );

                if (error) {
                  setError("");
                }
              }}
              autoComplete="username"
              disabled={loading}
              required
            />

          </div>


          <div className="login-field">

            <label htmlFor="password">
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              value={password}
              onChange={(event) => {
                setPassword(
                  event.target.value
                );

                if (error) {
                  setError("");
                }
              }}
              autoComplete="current-password"
              minLength={8}
              disabled={loading}
              required
            />

          </div>


          {/* PRIVACY */}

          <label className="login-privacy">

            <input
              type="checkbox"
              checked={privacyAccepted}
              onChange={(event) => {
                setPrivacyAccepted(
                  event.target.checked
                );

                if (error) {
                  setError("");
                }
              }}
              disabled={loading}
            />

            <span>
              I acknowledge the{" "}

              <strong>
                Data Privacy Act of 2012
                (Republic Act No. 10173).
              </strong>
            </span>

          </label>


          {/* ERROR */}

          {error && (
            <div
              className="login-error"
              role="alert"
            >
              {error}
            </div>
          )}


          {/* SUBMIT */}

          <button
            type="submit"
            className="login-button"
            disabled={
              loading ||
              !privacyAccepted
            }
          >
            {loading
              ? "Signing In..."
              : "Sign In"}
          </button>

        </form>


        {/* REGISTER */}

        <div className="login-register">

          <span>
            Don't have an account?
          </span>

          <Link to="/register">
            Register New User
          </Link>

        </div>


        {/* FOOTER */}

        <div className="login-footer">
          Krus na Ligas Health Center
        </div>

      </section>

    </main>
  );
}


export default Login;