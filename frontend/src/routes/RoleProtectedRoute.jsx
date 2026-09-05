import {
  Navigate,
} from "react-router-dom";

import {
  useAuth,
} from "../context/AuthContext";

import {
  hasPageAccess,
} from "../utils/permissions";


function RoleProtectedRoute({
  page,
  children,
}) {
  const {
    user,
    loading,
    isAuthenticated,
  } = useAuth();


  if (loading) {
    return (
      <div>
        Loading...
      </div>
    );
  }


  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  const allowed =
    hasPageAccess(
      user?.roles || [],
      page
    );


  if (!allowed) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }


  return children;
}


export default RoleProtectedRoute;