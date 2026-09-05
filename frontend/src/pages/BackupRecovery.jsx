import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getBackupRecoveryStatus,
  runBackupNow,
  runRestoreTest,
} from "../api/backupRecoveryApi";
import { useAuth } from "../context/AuthContext";

import "../styles/BackupRecovery.css";


const formatDateTime = (value) => {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
};


const formatBytes = (value) => {
  const bytes = Number(value || 0);

  if (bytes <= 0) {
    return "0 B";
  }

  const units = [
    "B",
    "KB",
    "MB",
    "GB",
  ];

  const index = Math.min(
    Math.floor(
      Math.log(bytes) / Math.log(1024)
    ),
    units.length - 1
  );

  const amount = (
    bytes / 1024 ** index
  ).toFixed(index === 0 ? 0 : 2);

  return `${amount} ${units[index]}`;
};


const StatusPill = ({
  good,
  goodLabel,
  badLabel,
}) => (
  <span
    className={
      good
        ? "backup-status-pill good"
        : "backup-status-pill bad"
    }
  >
    {good ? goodLabel : badLabel}
  </span>
);


function BackupRecovery() {
  const { user } = useAuth();

  const [
    statusData,
    setStatusData,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    refreshing,
    setRefreshing,
  ] = useState(false);

  const [
    actionLoading,
    setActionLoading,
  ] = useState("");

  const [
    message,
    setMessage,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState("");

  const roles = useMemo(
    () => (
      Array.isArray(user?.roles)
        ? user.roles
        : []
    ),
    [user]
  );

  const isSystemAdmin =
    roles.includes("SYSTEM_ADMIN");

  const loadStatus = useCallback(
    async (showFeedback = false) => {
      try {
        if (showFeedback) {
          setRefreshing(true);
          setMessage("");
        }

        setError("");

        const data =
          await getBackupRecoveryStatus();

        setStatusData(data);

        if (showFeedback) {
          setMessage(
            "Backup status refreshed."
          );
        }
      } catch (err) {
        setError(
          err?.response?.data?.detail
          || "Unable to load backup status."
        );
      } finally {
        setLoading(false);

        if (showFeedback) {
          setRefreshing(false);
        }
      }
    },
    []
  );

  useEffect(() => {
    loadStatus();

    const interval = setInterval(
      () => loadStatus(false),
      30000
    );

    return () => clearInterval(
      interval
    );
  }, [loadStatus]);

  const handleBackupNow = async () => {
    const confirmed = window.confirm(
      "Run a database backup now?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setActionLoading("backup");
      setError("");
      setMessage("");

      await runBackupNow();

      setMessage(
        "Manual database backup completed."
      );

      await loadStatus(false);
    } catch (err) {
      setError(
        err?.response?.data?.detail
        || "Manual backup failed."
      );
    } finally {
      setActionLoading("");
    }
  };

  const handleRestoreTest = async () => {
    const confirmed = window.confirm(
      "Run a restore verification test? "
      + "This creates a temporary database "
      + "and does not overwrite the live database."
    );

    if (!confirmed) {
      return;
    }

    try {
      setActionLoading("restore");
      setError("");
      setMessage("");

      await runRestoreTest();

      setMessage(
        "Backup restore verification passed."
      );

      await loadStatus(false);
    } catch (err) {
      setError(
        err?.response?.data?.detail
        || "Restore verification failed."
      );
    } finally {
      setActionLoading("");
    }
  };

  if (loading) {
    return (
      <div className="backup-page">
        <div className="backup-loading">
          Loading backup status...
        </div>
      </div>
    );
  }

  const backupSuccess =
    statusData?.backup_success === true;

  const taskHealthy =
    statusData?.scheduled_task?.healthy
    === true;

  const encrypted =
    statusData?.encryption_enabled
    === true;

  const cloudCopied =
    !statusData?.cloud_enabled
    || statusData?.cloud_status === "COPIED";

  const restorePassed =
    statusData?.restore_test?.success
    === true;

  return (
    <div className="backup-page">
      <div className="backup-page-header">
        <div>
          <p className="backup-eyebrow">
            Administration
          </p>

          <h1>
            Backup &amp; Recovery
          </h1>

          <p className="backup-subtitle">
            Monitor automated database
            protection, encryption, cloud copy,
            and restore verification.
          </p>
        </div>

        <button
          type="button"
          className="backup-refresh-button"
          disabled={refreshing}
          onClick={() => loadStatus(true)}
          aria-busy={refreshing}
        >
          {
            refreshing
              ? "Refreshing..."
              : "Refresh Status"
          }
        </button>
      </div>

      {message && (
        <div className="backup-alert success">
          {message}
        </div>
      )}

      {error && (
        <div className="backup-alert error">
          {error}
        </div>
      )}

      <section className="backup-summary-grid">
        <article className="backup-card">
          <span className="backup-card-label">
            Latest Backup
          </span>

          <StatusPill
            good={backupSuccess}
            goodLabel="Successful"
            badLabel="Needs Attention"
          />

          <strong>
            {formatDateTime(
              statusData?.finished_at
            )}
          </strong>

          <small>
            {
              statusData?.latest_backup
                ?.file_name
              || "No backup file recorded"
            }
          </small>
        </article>

        <article className="backup-card">
          <span className="backup-card-label">
            Encryption
          </span>

          <StatusPill
            good={encrypted}
            goodLabel="Enabled"
            badLabel="Disabled"
          />

          <strong>
            {
              encrypted
                ? "Encrypted archive"
                : "Raw logical backup"
            }
          </strong>

          <small>
            Latest size:{" "}
            {formatBytes(
              statusData?.latest_backup
                ?.size_bytes
            )}
          </small>
        </article>

        <article className="backup-card">
          <span className="backup-card-label">
            Off-device / Cloud Copy
          </span>

          <StatusPill
            good={cloudCopied}
            goodLabel={
              statusData?.cloud_enabled
                ? "Copied"
                : "Disabled"
            }
            badLabel="Copy Failed"
          />

          <strong>
            {
              statusData?.cloud_enabled
                ? statusData?.cloud_status
                : "Not configured"
            }
          </strong>

          <small>
            Use only authorized storage for
            operational health-center data.
          </small>
        </article>

        <article className="backup-card">
          <span className="backup-card-label">
            Scheduled Task
          </span>

          <StatusPill
            good={taskHealthy}
            goodLabel="Healthy"
            badLabel="Needs Attention"
          />

          <strong>
            Next:{" "}
            {formatDateTime(
              statusData?.scheduled_task
                ?.next_run_time
            )}
          </strong>

          <small>
            Last task result:{" "}
            {
              statusData?.scheduled_task
                ?.last_task_result
              ?? "N/A"
            }
          </small>
        </article>
      </section>

      <section className="backup-details-grid">
        <article className="backup-panel">
          <div className="backup-panel-heading">
            <div>
              <h2>
                Backup Retention
              </h2>
              <p>
                Automatic local retention policy.
              </p>
            </div>
          </div>

          <div className="backup-retention-grid">
            <div>
              <strong>
                {
                  statusData?.retention
                    ?.daily_count
                  ?? 0
                }
              </strong>
              <span>Daily stored</span>
              <small>
                Keep{" "}
                {
                  statusData?.retention
                    ?.daily_keep
                  ?? 0
                }
              </small>
            </div>

            <div>
              <strong>
                {
                  statusData?.retention
                    ?.weekly_count
                  ?? 0
                }
              </strong>
              <span>Weekly stored</span>
              <small>
                Keep{" "}
                {
                  statusData?.retention
                    ?.weekly_keep
                  ?? 0
                }
              </small>
            </div>

            <div>
              <strong>
                {
                  statusData?.retention
                    ?.monthly_count
                  ?? 0
                }
              </strong>
              <span>Monthly stored</span>
              <small>
                Keep{" "}
                {
                  statusData?.retention
                    ?.monthly_keep
                  ?? 0
                }
              </small>
            </div>
          </div>
        </article>

        <article className="backup-panel">
          <div className="backup-panel-heading">
            <div>
              <h2>
                Restore Verification
              </h2>

              <p>
                Restores the newest backup into a
                temporary database for verification.
              </p>
            </div>

            <StatusPill
              good={restorePassed}
              goodLabel="Passed"
              badLabel={
                statusData?.restore_test
                  ?.available
                  ? "Failed / Pending"
                  : "Not Recorded"
              }
            />
          </div>

          <dl className="backup-detail-list">
            <div>
              <dt>Last test</dt>
              <dd>
                {formatDateTime(
                  statusData?.restore_test
                    ?.finished_at
                )}
              </dd>
            </div>

            <div>
              <dt>Result</dt>
              <dd>
                {
                  statusData?.restore_test
                    ?.message
                  || "Run a restore test to record status."
                }
              </dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="backup-panel">
        <div className="backup-panel-heading">
          <div>
            <h2>
              Administrative Actions
            </h2>

            <p>
              Health Center Administrators can
              monitor status. Manual operations are
              restricted by the backend to the
              System Administrator.
            </p>
          </div>
        </div>

        {isSystemAdmin ? (
          <div className="backup-actions">
            <button
              type="button"
              className="backup-primary-button"
              disabled={Boolean(actionLoading)}
              onClick={handleBackupNow}
            >
              {
                actionLoading === "backup"
                  ? "Running Backup..."
                  : "Run Backup Now"
              }
            </button>

            <button
              type="button"
              className="backup-secondary-button"
              disabled={Boolean(actionLoading)}
              onClick={handleRestoreTest}
            >
              {
                actionLoading === "restore"
                  ? "Testing Restore..."
                  : "Run Restore Test"
              }
            </button>
          </div>
        ) : (
          <div className="backup-view-only">
            View-only access. Contact the System
            Administrator when a manual operation
            is required.
          </div>
        )}
      </section>

      <section className="backup-note">
        <strong>
          Power-loss protection:
        </strong>{" "}
        backups reduce data-loss risk, but a UPS
        and clean MySQL shutdown remain recommended.
      </section>
    </div>
  );
}


export default BackupRecovery;
