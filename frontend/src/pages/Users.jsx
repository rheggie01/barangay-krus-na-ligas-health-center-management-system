import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  approveUser,
  deactivateUser,
  deleteInactiveUser,
  deletePendingUser,
  getUsers,
  reactivateUser,
} from "../api/userApi";

import {
  useAuth,
} from "../context/AuthContext";

import "../styles/Users.css";
import "../styles/UsersLifecycle.css";


const ROLE_LABELS = {
  SYSTEM_ADMIN:
    "System Administrator",

  HEALTH_CENTER_ADMIN:
    "Health Center Administrator",

  DOCTOR:
    "Doctor",

  NURSE:
    "Nurse",

  MIDWIFE:
    "Midwife",

  BHW:
    "Barangay Health Worker",
};


function Users() {
  const {
    user: currentUser,
  } = useAuth();

  const [
    users,
    setUsers,
  ] = useState([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    updatingUserId,
    setUpdatingUserId,
  ] = useState(null);

  const [
    deletingUser,
    setDeletingUser,
  ] = useState(null);

  const [
    deleteMode,
    setDeleteMode,
  ] = useState(null);

  const [
    error,
    setError,
  ] = useState("");

  const [
    success,
    setSuccess,
  ] = useState("");


  const clearMessages = () => {
    setError("");
    setSuccess("");
  };


  const getRoleLabel = (
    role
  ) => {
    return (
      ROLE_LABELS[role]
      ||
      role
        ?.replaceAll(
          "_",
          " "
        )
        .toLowerCase()
        .replace(
          /\b\w/g,
          (letter) =>
            letter.toUpperCase()
        )
      ||
      "-"
    );
  };


  const getAccountStatus = (
    user
  ) => {
    if (
      user?.account_status
    ) {
      return user.account_status;
    }

    return (
      user?.is_active
        ? "ACTIVE"
        : "PENDING"
    );
  };


  const loadUsers =
    async () => {
      try {
        setLoading(true);
        setError("");

        const data =
          await getUsers();

        setUsers(
          Array.isArray(data)
            ? data
            : []
        );

      } catch (err) {
        console.error(err);

        setError(
          err.response
            ?.data
            ?.detail
          ||
          "Unable to load user accounts."
        );

      } finally {
        setLoading(false);
      }
    };


  useEffect(() => {
    loadUsers();
  }, []);


  useEffect(
    () => {
      if (
        !deletingUser
      ) {
        return undefined;
      }

      const previousOverflow =
        document.body.style.overflow;

      document.body.style.overflow =
        "hidden";

      const onKeyDown = (
        event
      ) => {
        if (
          event.key ===
            "Escape"
          &&
          updatingUserId
            == null
        ) {
          setDeletingUser(
            null
          );

          setDeleteMode(
            null
          );
        }
      };

      document.addEventListener(
        "keydown",
        onKeyDown
      );

      return () => {
        document.body.style.overflow =
          previousOverflow;

        document.removeEventListener(
          "keydown",
          onKeyDown
        );
      };
    },
    [
      deletingUser,
      updatingUserId,
    ]
  );


  const openDeleteDialog = (
    targetUser,
    mode
  ) => {
    clearMessages();

    setDeletingUser(
      targetUser
    );

    setDeleteMode(
      mode
    );
  };


  const closeDeleteDialog = () => {
    if (
      updatingUserId
        != null
    ) {
      return;
    }

    setDeletingUser(
      null
    );

    setDeleteMode(
      null
    );
  };


  const replaceUpdatedUser = (
    updatedUser
  ) => {
    setUsers(
      (current) =>
        current.map(
          (user) =>
            user.id ===
              updatedUser.id
              ? updatedUser
              : user
        )
    );
  };


  const runLifecycleAction =
    async (
      targetUser,
      action
    ) => {
      clearMessages();

      try {
        setUpdatingUserId(
          targetUser.id
        );

        let updatedUser = null;

        if (
          action ===
          "APPROVE"
        ) {
          updatedUser =
            await approveUser(
              targetUser.id
            );
        }

        if (
          action ===
          "DEACTIVATE"
        ) {
          if (
            targetUser.id ===
              currentUser?.id
          ) {
            setError(
              "You cannot deactivate your own account."
            );

            return;
          }

          updatedUser =
            await deactivateUser(
              targetUser.id
            );
        }

        if (
          action ===
          "REACTIVATE"
        ) {
          updatedUser =
            await reactivateUser(
              targetUser.id
            );
        }

        if (
          !updatedUser
        ) {
          return;
        }

        replaceUpdatedUser(
          updatedUser
        );

        const displayName =
          `${updatedUser.first_name} ${updatedUser.last_name}`
            .trim();

        if (
          action ===
          "APPROVE"
        ) {
          setSuccess(
            `${displayName}'s account has been approved.`
          );
        }

        if (
          action ===
          "DEACTIVATE"
        ) {
          setSuccess(
            `${displayName}'s login access has been deactivated. Historical records remain preserved.`
          );
        }

        if (
          action ===
          "REACTIVATE"
        ) {
          setSuccess(
            `${displayName}'s account has been reactivated.`
          );
        }

      } catch (err) {
        console.error(err);

        setError(
          err.response
            ?.data
            ?.detail
          ||
          "Unable to update account lifecycle."
        );

      } finally {
        setUpdatingUserId(null);
      }
    };


  const confirmDelete =
    async () => {
      if (
        !deletingUser
        ||
        !deleteMode
      ) {
        return;
      }

      clearMessages();

      try {
        setUpdatingUserId(
          deletingUser.id
        );

        if (
          deleteMode ===
          "PENDING"
        ) {
          await deletePendingUser(
            deletingUser.id
          );
        }

        if (
          deleteMode ===
          "INACTIVE"
        ) {
          await deleteInactiveUser(
            deletingUser.id
          );
        }

        const displayName =
          `${deletingUser.first_name} ${deletingUser.last_name}`
            .trim();

        setUsers(
          (current) =>
            current.filter(
              (user) =>
                user.id !==
                deletingUser.id
            )
        );

        if (
          deleteMode ===
          "PENDING"
        ) {
          setSuccess(
            `${displayName}'s never-approved account request was permanently deleted.`
          );
        }

        if (
          deleteMode ===
          "INACTIVE"
        ) {
          setSuccess(
            `${displayName}'s inactive account was archived. Login access remains disabled and historical records were preserved.`
          );
        }

        setDeletingUser(
          null
        );

        setDeleteMode(
          null
        );

      } catch (err) {
        console.error(err);

        setError(
          err.response
            ?.data
            ?.detail
          ||
          (
            deleteMode ===
              "INACTIVE"
              ? "Unable to archive inactive staff account."
              : "Unable to delete pending account request."
          )
        );

      } finally {
        setUpdatingUserId(
          null
        );
      }
    };

  const pendingUsers =
    useMemo(
      () =>
        users.filter(
          (user) =>
            getAccountStatus(
              user
            )
            === "PENDING"
        ),
      [
        users,
      ]
    );


  const activeUsers =
    useMemo(
      () =>
        users.filter(
          (user) =>
            getAccountStatus(
              user
            )
            === "ACTIVE"
        ),
      [
        users,
      ]
    );


  const inactiveUsers =
    useMemo(
      () =>
        users.filter(
          (user) =>
            getAccountStatus(
              user
            )
            === "INACTIVE"
        ),
      [
        users,
      ]
    );


  const totalSystemAdmins =
    useMemo(
      () =>
        users.filter(
          (user) =>
            user.roles?.includes(
              "SYSTEM_ADMIN"
            )
        ).length,
      [
        users,
      ]
    );


  return (
    <div className="users-page">

      <header className="users-page-header">

        <div>
          <h1>
            User Management
          </h1>

          <p>
            Review account requests,
            preserve staff accountability,
            and manage Health Center access.
          </p>
        </div>


        <button
          type="button"
          className="app-button app-button-secondary"
          onClick={
            loadUsers
          }
          disabled={
            loading
          }
        >
          {
            loading
              ? "Refreshing..."
              : "Refresh Users"
          }
        </button>

      </header>


      {error && (
        <div className="app-message app-message-error users-message">
          {error}
        </div>
      )}


      {success && (
        <div className="app-message app-message-success users-message">
          {success}
        </div>
      )}


      <div className="users-summary-grid users-summary-grid-lifecycle">

        <SummaryCard
          label="Total Users"
          value={users.length}
        />

        <SummaryCard
          label="Pending Approval"
          value={pendingUsers.length}
          type={
            pendingUsers.length > 0
              ? "warning"
              : "default"
          }
        />

        <SummaryCard
          label="Active Accounts"
          value={activeUsers.length}
        />

        <SummaryCard
          label="Inactive Accounts"
          value={inactiveUsers.length}
        />

        <SummaryCard
          label="System Administrators"
          value={totalSystemAdmins}
        />

      </div>


      <UserSection
        title="Pending Account Requests"
        subtitle="Never-approved registrations. Approve legitimate staff or permanently remove invalid requests."
        users={pendingUsers}
        loading={loading}
        emptyTitle="No pending registrations"
        emptyText="New account requests will appear here."
        status="PENDING"
        currentUser={currentUser}
        getRoleLabel={getRoleLabel}
        updatingUserId={updatingUserId}
        onApprove={
          (user) =>
            runLifecycleAction(
              user,
              "APPROVE"
            )
        }
        onDeleteRequest={
          (user) =>
            openDeleteDialog(
              user,
              "PENDING"
            )
        }
      />


      <UserSection
        title="Active User Accounts"
        subtitle="Current approved staff with login access to the system."
        users={activeUsers}
        loading={loading}
        emptyTitle="No active user accounts"
        emptyText=""
        status="ACTIVE"
        currentUser={currentUser}
        getRoleLabel={getRoleLabel}
        updatingUserId={updatingUserId}
        onDeactivate={
          (user) =>
            runLifecycleAction(
              user,
              "DEACTIVATE"
            )
        }
      />


      <UserSection
        title="Inactive Staff Accounts"
        subtitle="Previously approved staff whose login access is disabled. Historical transactions remain intact."
        users={inactiveUsers}
        loading={loading}
        emptyTitle="No inactive staff accounts"
        emptyText="Deactivated staff remain here for audit history."
        status="INACTIVE"
        currentUser={currentUser}
        getRoleLabel={getRoleLabel}
        updatingUserId={updatingUserId}
        onReactivate={
          (user) =>
            runLifecycleAction(
              user,
              "REACTIVATE"
            )
        }
        onDeleteInactive={
          (user) =>
            openDeleteDialog(
              user,
              "INACTIVE"
            )
        }
      />


      {
        deletingUser
        && (
          <div
            className="users-modal-backdrop"
            role="presentation"
            onMouseDown={
              (event) => {
                if (
                  event.target ===
                    event.currentTarget
                  &&
                  updatingUserId
                    == null
                ) {
                  setDeletingUser(
                    null
                  );

                  setDeleteMode(
                    null
                  );
                }
              }
            }
          >

            <section
              className="users-confirm-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-account-request-title"
            >

              <h2 id="delete-account-request-title">
                {
                  deleteMode ===
                    "INACTIVE"
                    ? "Delete Inactive Staff Account?"
                    : "Delete Pending Account Request?"
                }
              </h2>

              <p>
                {
                  deleteMode ===
                    "INACTIVE"
                    ? (
                      <>
                        This will archive the inactive
                        account for{" "}
                        <strong>
                          @{deletingUser.username}
                        </strong>.
                      </>
                    )
                    : (
                      <>
                        This permanently removes
                        the never-approved request for{" "}
                        <strong>
                          @{deletingUser.username}
                        </strong>.
                      </>
                    )
                }
              </p>

              <div className="users-confirm-warning">
                {
                  deleteMode ===
                    "INACTIVE"
                    ? (
                      <>
                        This is a soft delete. The account
                        will disappear from normal user
                        management and cannot be reactivated
                        through the standard workflow.
                        Historical clinical, dispensing,
                        inventory, and audit records remain
                        preserved and attributable.
                      </>
                    )
                    : (
                      <>
                        This hard-delete workflow is only
                        for never-approved PENDING account
                        requests with no linked operational
                        or audit actor records.
                      </>
                    )
                }
              </div>

              <div className="users-confirm-actions">

                <button
                  type="button"
                  className="app-button app-button-secondary"
                  onClick={
                    closeDeleteDialog
                  }
                  disabled={
                    updatingUserId ===
                      deletingUser.id
                  }
                >
                  Cancel
                </button>


                <button
                  type="button"
                  className="app-button app-button-danger"
                  onClick={
                    confirmDelete
                  }
                  disabled={
                    updatingUserId ===
                      deletingUser.id
                  }
                >
                  {
                    updatingUserId ===
                      deletingUser.id
                      ? "Deleting..."
                      : (
                        deleteMode ===
                          "INACTIVE"
                          ? "Delete Account"
                          : "Delete Request"
                      )
                  }
                </button>

              </div>

            </section>

          </div>
        )
      }

    </div>
  );
}


function UserSection({
  title,
  subtitle,
  users,
  loading,
  emptyTitle,
  emptyText,
  status,
  currentUser,
  getRoleLabel,
  updatingUserId,
  onApprove,
  onDeleteRequest,
  onDeactivate,
  onReactivate,
  onDeleteInactive,
}) {
  return (
    <section className="users-card">

      <div className="users-card-header">

        <div>
          <h2>
            {title}
          </h2>

          <p>
            {subtitle}
          </p>
        </div>


        <span className="users-count-badge">
          {users.length}
        </span>

      </div>


      {
        loading
          ? (
            <div className="users-empty">
              Loading users...
            </div>
          )
          : users.length === 0
            ? (
              <div className="users-empty">

                <strong>
                  {emptyTitle}
                </strong>

                {
                  emptyText
                  && (
                    <span>
                      {emptyText}
                    </span>
                  )
                }

              </div>
            )
            : (
              <UserTable
                users={users}
                currentUser={currentUser}
                getRoleLabel={getRoleLabel}
                updatingUserId={updatingUserId}
                status={status}
                onApprove={onApprove}
                onDeleteRequest={onDeleteRequest}
                onDeactivate={onDeactivate}
                onReactivate={onReactivate}
                onDeleteInactive={onDeleteInactive}
              />
            )
      }

    </section>
  );
}


function UserTable({
  users,
  currentUser,
  getRoleLabel,
  updatingUserId,
  status,
  onApprove,
  onDeleteRequest,
  onDeactivate,
  onReactivate,
  onDeleteInactive,
}) {
  return (
    <div className="users-table-wrap">

      <table className="users-table">

        <thead>
          <tr>
            <th>User</th>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>


        <tbody>

          {
            users.map(
              (user) => {
                const isCurrentUser =
                  user.id ===
                    currentUser?.id;

                return (
                  <tr key={user.id}>

                    <td>
                      <UserIdentity
                        user={user}
                        current={isCurrentUser}
                      />
                    </td>

                    <td>
                      <span className="users-username">
                        @{user.username}
                      </span>
                    </td>

                    <td>
                      {user.email}
                    </td>

                    <td>
                      <RoleBadges
                        roles={user.roles}
                        getRoleLabel={getRoleLabel}
                      />
                    </td>

                    <td>
                      <span
                        className={
                          status === "ACTIVE"
                            ? "users-status users-status-active"
                            : status === "INACTIVE"
                              ? "users-status users-status-inactive"
                              : "users-status users-status-pending"
                        }
                      >
                        {status}
                      </span>
                    </td>

                    <td>
                      <div className="users-actions">

                        {
                          status === "PENDING"
                          && (
                            <>
                              <button
                                type="button"
                                className="app-button app-button-primary app-button-small"
                                disabled={
                                  updatingUserId ===
                                    user.id
                                }
                                onClick={
                                  () =>
                                    onApprove(
                                      user
                                    )
                                }
                              >
                                {
                                  updatingUserId ===
                                    user.id
                                    ? "Approving..."
                                    : "Approve"
                                }
                              </button>

                              <button
                                type="button"
                                className="app-button app-button-danger app-button-small"
                                disabled={
                                  updatingUserId ===
                                    user.id
                                }
                                onClick={
                                  () =>
                                    onDeleteRequest(
                                      user
                                    )
                                }
                              >
                                Delete Request
                              </button>
                            </>
                          )
                        }


                        {
                          status === "ACTIVE"
                          && (
                            isCurrentUser
                              ? (
                                <span className="users-current-account">
                                  Current Account
                                </span>
                              )
                              : (
                                <button
                                  type="button"
                                  className="app-button app-button-danger app-button-small"
                                  disabled={
                                    updatingUserId ===
                                      user.id
                                  }
                                  onClick={
                                    () =>
                                      onDeactivate(
                                        user
                                      )
                                  }
                                >
                                  {
                                    updatingUserId ===
                                      user.id
                                      ? "Deactivating..."
                                      : "Deactivate"
                                  }
                                </button>
                              )
                          )
                        }


                        {
                          status === "INACTIVE"
                          && (
                            <>
                              <button
                                type="button"
                                className="app-button app-button-primary app-button-small"
                                disabled={
                                  updatingUserId ===
                                    user.id
                                }
                                onClick={
                                  () =>
                                    onReactivate(
                                      user
                                    )
                                }
                              >
                                {
                                  updatingUserId ===
                                    user.id
                                    ? "Updating..."
                                    : "Reactivate"
                                }
                              </button>

                              <button
                                type="button"
                                className="app-button app-button-danger app-button-small"
                                disabled={
                                  updatingUserId ===
                                    user.id
                                }
                                onClick={
                                  () =>
                                    onDeleteInactive(
                                      user
                                    )
                                }
                              >
                                Delete Account
                              </button>
                            </>
                          )
                        }

                      </div>
                    </td>

                  </tr>
                );
              }
            )
          }

        </tbody>

      </table>

    </div>
  );
}


function SummaryCard({
  label,
  value,
  type = "default",
}) {
  return (
    <div
      className={
        `users-summary-card ` +
        `users-summary-${type}`
      }
    >
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>
    </div>
  );
}


function UserIdentity({
  user,
  current = false,
}) {
  const initials = [
    user.first_name?.[0],
    user.last_name?.[0],
  ]
    .filter(Boolean)
    .join("")
    .toUpperCase();

  return (
    <div className="users-identity">

      <div className="users-avatar">
        {initials || "U"}
      </div>

      <div>
        <strong>
          {user.first_name}{" "}
          {user.last_name}
        </strong>

        {current && (
          <span>
            You
          </span>
        )}
      </div>

    </div>
  );
}


function RoleBadges({
  roles = [],
  getRoleLabel,
}) {
  if (
    roles.length === 0
  ) {
    return (
      <span>
        -
      </span>
    );
  }

  return (
    <div className="users-role-list">

      {
        roles.map(
          (role) => (
            <span
              key={role}
              className="users-role"
            >
              {
                getRoleLabel(
                  role
                )
              }
            </span>
          )
        )
      }

    </div>
  );
}


export default Users;
