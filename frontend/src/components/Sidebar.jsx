import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { hasPageAccess } from "../utils/permissions";

import krusNaLigasLogo from "../assets/krus-na-ligas-logo.jpg";


const NAV_ITEMS = [
  {
    key: "dashboard",
    path: "/dashboard",
    label: "Dashboard",
  },
  {
    key: "patients",
    path: "/patients",
    label: "Patients",
  },
  {
    key: "consultations",
    path: "/consultations",
    label: "Consultations",
  },
  {
    key: "surveillance",
    path: "/surveillance",
    label: "Disease Surveillance",
  },
  {
    key: "inventory",
    path: "/inventory",
    label: "Medicine Inventory",
  },
  {
    key: "forecasts",
    path: "/forecasts",
    label: "Forecasts",
  },
  {
    key: "reports",
    path: "/reports",
    label: "Reports",
  },
  {
    key: "users",
    path: "/users",
    label: "User Management",
  },
  {
    key: "auditLogs",
    path: "/audit-logs",
    label: "Audit Logs",
  },
  {
    key: "backupRecovery",
    path: "/backup-recovery",
    label: "Backup & Recovery",
  },
];


function Sidebar() {
  const { user } = useAuth();

  const roles = Array.isArray(
    user?.roles
  )
    ? user.roles
    : [];

  const visibleItems = NAV_ITEMS.filter(
    (item) =>
      hasPageAccess(
        roles,
        item.key
      )
  );

  const getLinkClass = ({
    isActive,
  }) =>
    `sidebar-link${
      isActive ? " active" : ""
    }`;

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-logo">
          <img
            src={krusNaLigasLogo}
            alt="Barangay Krus na Ligas Logo"
          />
        </div>

        <div className="sidebar-brand-text">
          <strong>
            Barangay Health
            <br />
            Center
          </strong>

          <span>
            Management System
          </span>
        </div>
      </div>

      <nav
        className="sidebar-nav"
        aria-label="Main navigation"
      >
        {visibleItems.map((item) => (
          <NavLink
            key={item.key}
            to={item.path}
            className={getLinkClass}
          >
            <span className="sidebar-link-label">
              {item.label}
            </span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span>
          Krus na Ligas Health Center
        </span>

        <small>
          Health Information System
        </small>
      </div>
    </aside>
  );
}


export default Sidebar;
