import {
  useEffect,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  getDashboardSummary,
} from "../api/dashboardApi";
import "../styles/Dashboard.css";

function Dashboard() {
  const [dashboard, setDashboard] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const data =
        await getDashboardSummary();

      setDashboard(data);

    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to load dashboard."
      );

    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadDashboard();
  }, []);


  if (loading) {
    return (
      <div className="dashboard-state">
        Loading dashboard...
      </div>
    );
  }


  if (error) {
    return (
      <div className="dashboard-state">
        <p>{error}</p>

        <button
          type="button"
          onClick={loadDashboard}
          className="dashboard-button"
        >
          Retry
        </button>
      </div>
    );
  }


  if (!dashboard) {
    return (
      <div className="dashboard-state">
        Dashboard data unavailable.
      </div>
    );
  }


  const summaryCards = [
    {
      label: "Total Patients",
      value: dashboard.total_patients,
    },
    {
      label: "Consultations Today",
      value: dashboard.consultations_today,
    },
    {
      label: "Consultations This Week",
      value:
        dashboard.consultations_this_week,
    },
    {
      label: "Active Medicines",
      value: dashboard.active_medicines,
    },
    {
      label: "Low Stock",
      value:
        dashboard.low_stock_medicines,
    },
    {
      label: "Out of Stock",
      value:
        dashboard.out_of_stock_medicines,
    },
  ];


  return (
    <div className="dashboard-page">

      {/* HEADER */}

      <section className="dashboard-header">
        <div>
          <h1>Dashboard</h1>

          <p>
            Barangay Health Center overview
            and monitoring.
          </p>
        </div>

        <button
          type="button"
          onClick={loadDashboard}
          className="dashboard-button"
        >
          Refresh Dashboard
        </button>
      </section>


      {/* SUMMARY CARDS */}

      <section className="dashboard-section">

        <div className="dashboard-section-header">
          <div>
            <h2>
              Health Center Summary
            </h2>

            <p>
              Current operational overview.
            </p>
          </div>
        </div>


        <div className="dashboard-card-grid">

          {summaryCards.map((card) => (
            <div
              className="dashboard-card"
              key={card.label}
            >
              <span className="dashboard-card-label">
                {card.label}
              </span>

              <strong className="dashboard-card-value">
                {card.value}
              </strong>
            </div>
          ))}

        </div>

      </section>


      {/* TWO COLUMN AREA */}

      <div className="dashboard-two-column">

        {/* DISEASE CASES */}

        <section className="dashboard-panel">

          <div className="dashboard-panel-header">
            <div>
              <h2>
                Disease Cases This Week
              </h2>

              <p>
                Recorded cases by disease.
              </p>
            </div>

            <Link
              to="/surveillance"
              className="dashboard-link"
            >
              View Surveillance
            </Link>
          </div>


          {dashboard
            .disease_cases_this_week
            .length === 0 ? (
            <p className="dashboard-empty">
              No disease cases recorded
              this week.
            </p>

          ) : (

            <div className="dashboard-table-wrap">

              <table className="dashboard-table">

                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Disease</th>
                    <th>Cases</th>
                  </tr>
                </thead>


                <tbody>

                  {dashboard
                    .disease_cases_this_week
                    .map((disease) => (
                      <tr
                        key={
                          disease.disease_id
                        }
                      >

                        <td>
                          {disease.code}
                        </td>

                        <td>
                          {disease.name}
                        </td>

                        <td>
                          <strong>
                            {
                              disease.case_count
                            }
                          </strong>
                        </td>

                      </tr>
                    ))}

                </tbody>

              </table>

            </div>
          )}

        </section>


        {/* MEDICINE STOCK ALERTS */}

        <section className="dashboard-panel">

          <div className="dashboard-panel-header">
            <div>
              <h2>
                Medicine Stock Alerts
              </h2>

              <p>
                Low-stock and out-of-stock
                medicines.
              </p>
            </div>

            <Link
              to="/inventory"
              className="dashboard-link"
            >
              View Inventory
            </Link>
          </div>


          {dashboard
            .low_stock_list
            .length === 0 ? (
            <p className="dashboard-empty">
              No low-stock or out-of-stock
              medicines.
            </p>

          ) : (

            <div className="dashboard-table-wrap">

              <table className="dashboard-table">

                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Medicine</th>
                    <th>Stock</th>
                    <th>Status</th>
                  </tr>
                </thead>


                <tbody>

                  {dashboard
                    .low_stock_list
                    .map((medicine) => (
                      <tr
                        key={
                          medicine.medicine_id
                        }
                      >

                        <td>
                          {medicine.code}
                        </td>

                        <td>
                          {medicine.name}
                        </td>

                        <td>
                          {
                            medicine
                              .stock_display
                          }
                        </td>

                        <td>
                          <span
                            className={
                              medicine.status ===
                              "OUT OF STOCK"
                                ? "status-badge status-out"
                                : "status-badge status-low"
                            }
                          >
                            {medicine.status}
                          </span>
                        </td>

                      </tr>
                    ))}

                </tbody>

              </table>

            </div>
          )}

        </section>

      </div>


      {/* RECENT CONSULTATIONS */}

      <section className="dashboard-panel">

        <div className="dashboard-panel-header">
          <div>
            <h2>
              Recent Consultations
            </h2>

            <p>
              Latest patient consultation
              records.
            </p>
          </div>

          <Link
            to="/consultations"
            className="dashboard-link"
          >
            View Consultations
          </Link>
        </div>


        {dashboard
          .recent_consultations
          .length === 0 ? (
          <p className="dashboard-empty">
            No consultations recorded.
          </p>

        ) : (

          <div className="dashboard-table-wrap">

            <table className="dashboard-table">

              <thead>
                <tr>
                  <th>Date</th>
                  <th>Patient</th>
                  <th>Diagnosis</th>
                  <th>Action</th>
                </tr>
              </thead>


              <tbody>

                {dashboard
                  .recent_consultations
                  .map((item) => (
                    <tr
                      key={
                        item.consultation_id
                      }
                    >

                      <td>
                        {new Date(
                          item
                            .consultation_date
                        ).toLocaleString()}
                      </td>

                      <td>
                        {
                          item.patient_name
                        }
                      </td>

                      <td>
                        {item.diagnosis ||
                          "-"}
                      </td>

                      <td>
                        <Link
                          to={`/consultations/${item.consultation_id}`}
                          className="dashboard-link"
                        >
                          View
                        </Link>
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


export default Dashboard;