import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getAuditLogs,
} from "../api/auditLogApi";

import "../styles/AuditLogs.css";


function AuditLogs() {
  const [
    logs,
    setLogs,
  ] = useState([]);
  const [
    module,
    setModule,
  ] = useState("");
  const [
    action,
    setAction,
  ] = useState("");
  const [
    loading,
    setLoading,
  ] = useState(true);
  const [
    error,
    setError,
  ] = useState("");

  const loadAuditLogs = useCallback(async ({
    moduleValue = module,
    actionValue = action,
  } = {}) => {
    try {
      setLoading(true);
      setError("");

      const data =
        await getAuditLogs({
          module: moduleValue,
          action: actionValue,
          limit: 100,
        });

      setLogs(
        Array.isArray(data)
          ? data
          : []
      );

    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to load audit logs."
      );

    } finally {
      setLoading(false);
    }
  }, [
    action,
    module,
  ]);

  useEffect(() => {
    loadAuditLogs({
      moduleValue: "",
      actionValue: "",
    });
  }, [
    loadAuditLogs,
  ]);

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();
    await loadAuditLogs();
  };

  const handleClear = async () => {
    setModule("");
    setAction("");

    await loadAuditLogs({
      moduleValue: "",
      actionValue: "",
    });
  };

  return (
    <div className="audit-page">
      <section className="audit-header">
        <div>
          <h1>Audit Logs</h1>
          <p>
            Review security and administrative
            activity recorded by the system.
          </p>
        </div>

        <button
          type="button"
          className="audit-button"
          onClick={() => loadAuditLogs()}
        >
          Refresh
        </button>
      </section>

      <form
        className="audit-filters"
        onSubmit={handleSubmit}
      >
        <div className="audit-field">
          <label htmlFor="module">
            Module
          </label>
          <input
            id="module"
            value={module}
            onChange={
              (event) =>
                setModule(
                  event.target.value
                )
            }
            placeholder="authentication"
          />
        </div>

        <div className="audit-field">
          <label htmlFor="action">
            Action
          </label>
          <input
            id="action"
            value={action}
            onChange={
              (event) =>
                setAction(
                  event.target.value
                )
            }
            placeholder="LOGIN_SUCCESS"
          />
        </div>

        <div className="audit-filter-actions">
          <button
            type="submit"
            className="audit-button"
          >
            Apply
          </button>
          <button
            type="button"
            className="audit-button audit-button-secondary"
            onClick={handleClear}
          >
            Clear
          </button>
        </div>
      </form>

      <section className="audit-card">
        <div className="audit-card-header">
          <div>
            <h2>Recent Activity</h2>
            <p>
              Latest recorded actions across
              protected modules.
            </p>
          </div>

          <span>
            {logs.length} records
          </span>
        </div>

        {error && (
          <div className="audit-error">
            {error}
          </div>
        )}

        {loading ? (
          <div className="audit-empty">
            Loading audit logs...
          </div>
        ) : logs.length === 0 ? (
          <div className="audit-empty">
            No audit logs found.
          </div>
        ) : (
          <div className="audit-table-wrap">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>User</th>
                  <th>Role</th>
                  <th>Module</th>
                  <th>Action</th>
                  <th>Record</th>
                  <th>IP Address</th>
                  <th>Description</th>
                </tr>
              </thead>

              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>
                      {new Date(
                        log.created_at
                      ).toLocaleString()}
                    </td>
                    <td>
                      {
                        log.actor_name_snapshot
                          ? (
                            <div>
                              <strong>
                                {
                                  log.actor_name_snapshot
                                }
                              </strong>

                              <div>
                                {
                                  log.username
                                    ? `@${log.username}`
                                    : "-"
                                }
                              </div>
                            </div>
                          )
                          : (
                            log.username
                              ? `@${log.username}`
                              : "-"
                          )
                      }
                    </td>
                    <td>
                      {log.role_names || "-"}
                    </td>
                    <td>
                      <span className="audit-chip">
                        {log.module}
                      </span>
                    </td>
                    <td>
                      <strong>
                        {log.action}
                      </strong>
                    </td>
                    <td>
                      {log.record_id || "-"}
                    </td>
                    <td>
                      {log.ip_address || "-"}
                    </td>
                    <td>
                      {log.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}


export default AuditLogs;
