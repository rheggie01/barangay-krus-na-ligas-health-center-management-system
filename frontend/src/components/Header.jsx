import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";


function Header() {
  const navigate = useNavigate();

  const {
    user,
    logout,
  } = useAuth();


  const handleLogout = () => {
    logout();
    navigate("/login");
  };


  const initials = [
    user?.first_name?.[0],
    user?.last_name?.[0],
  ]
    .filter(Boolean)
    .join("")
    .toUpperCase();


  return (
    <header className="topbar">

      <div className="topbar-left">

        <div>
          <span className="topbar-kicker">
            Barangay Health Center
          </span>

          <strong className="topbar-title">
            Health Management System
          </strong>
        </div>

      </div>


      <div className="topbar-right">

        <div className="topbar-user">

          <div className="topbar-avatar">
            {initials || "U"}
          </div>


          <div className="topbar-user-info">

            <strong>
              {user?.first_name}{" "}
              {user?.last_name}
            </strong>

            <span>
              {user?.roles?.join(", ")}
            </span>

          </div>

        </div>


        <button
          type="button"
          className="topbar-logout"
          onClick={handleLogout}
        >
          Logout
        </button>

      </div>

    </header>
  );
}


export default Header;