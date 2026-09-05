// =========================================================
// PAGE ACCESS BY ROLE
// =========================================================

export const ROLE_ACCESS = {
  SYSTEM_ADMIN: [
    "landing",
    "dashboard",
    "patients",
    "consultations",
    "surveillance",
    "inventory",
    "forecasts",
    "reports",
    "users",
    "auditLogs",
    "backupRecovery",
  ],

  HEALTH_CENTER_ADMIN: [
    "landing",
    "dashboard",
    "patients",
    "consultations",
    "surveillance",
    "inventory",
    "forecasts",
    "reports",
    "users",
    "auditLogs",
    "backupRecovery",
  ],

  DOCTOR: [
    "landing",
    "dashboard",
    "patients",
    "consultations",
    "surveillance",
    "inventory",
    "forecasts",
    "reports",
  ],

  NURSE: [
    "landing",
    "dashboard",
    "patients",
    "consultations",
    "surveillance",
    "inventory",
    "forecasts",
    "reports",
  ],

  MIDWIFE: [
    "landing",
    "dashboard",
    "patients",
    "consultations",
    "surveillance",
    "inventory",
    "forecasts",
    "reports",
  ],

  BHW: [
    "landing",
    "dashboard",
    "patients",
    "surveillance",
    "inventory",
  ],
};


// =========================================================
// PAGE ACCESS
// =========================================================

export const hasPageAccess = (
  roles = [],
  page
) => {
  if (!page) {
    return false;
  }

  if (!Array.isArray(roles)) {
    return false;
  }

  return roles.some(
    (role) =>
      ROLE_ACCESS[role]?.includes(
        page
      )
  );
};


// =========================================================
// SINGLE PERMISSION
// =========================================================

export const hasPermission = (
  permissions = [],
  permission
) => {
  if (!permission) {
    return true;
  }

  if (!Array.isArray(permissions)) {
    return false;
  }

  return permissions.includes(
    permission
  );
};


// =========================================================
// ANY PERMISSION
// =========================================================

export const hasAnyPermission = (
  permissions = [],
  requiredPermissions = []
) => {
  if (
    !Array.isArray(
      requiredPermissions
    )
    || requiredPermissions.length === 0
  ) {
    return true;
  }

  return requiredPermissions.some(
    (permission) =>
      hasPermission(
        permissions,
        permission
      )
  );
};


// =========================================================
// ALL PERMISSIONS
// =========================================================

export const hasAllPermissions = (
  permissions = [],
  requiredPermissions = []
) => {
  if (
    !Array.isArray(
      requiredPermissions
    )
    || requiredPermissions.length === 0
  ) {
    return true;
  }

  return requiredPermissions.every(
    (permission) =>
      hasPermission(
        permissions,
        permission
      )
  );
};
