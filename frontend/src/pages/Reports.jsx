import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getDashboardSummary } from "../api/dashboardApi";
import { getMedicines } from "../api/medicineApi";
import { getPatients } from "../api/patientApi";
import { getWeeklyDiseaseComparison } from "../api/surveillanceApi";

import "../styles/Reports.css";


/* =========================================================
   CONSTANTS
========================================================= */

const REPORT_DATE_FORMAT = {
  dateStyle: "medium",
  timeStyle: "short",
};


const CONSULTATION_DAYS = 7;


const SEX_COLORS = {
  Male: "#3976a8",
  Female: "#c5658c",
};


const CHART_COLORS = {
  primary: "#3c906d",
  secondary: "#3976a8",
  warning: "#b87518",
  muted: "#8b98a8",
};


/* =========================================================
   REPORTS PAGE
========================================================= */

function Reports() {
  /* =======================================================
     DATA
  ======================================================= */

  const [
    dashboard,
    setDashboard,
  ] = useState(null);

  const [
    medicines,
    setMedicines,
  ] = useState([]);

  const [
    patients,
    setPatients,
  ] = useState([]);

  const [
    weeklyDiseases,
    setWeeklyDiseases,
  ] = useState([]);


  /* =======================================================
     PAGE STATE
  ======================================================= */

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    refreshing,
    setRefreshing,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    generatedAt,
    setGeneratedAt,
  ] = useState(null);


  /* =======================================================
     LOAD REPORT DATA
  ======================================================= */

  const loadReports =
    useCallback(
      async (
        isRefresh = false
      ) => {
        try {
          if (isRefresh) {
            setRefreshing(true);
          } else {
            setLoading(true);
          }

          setError("");


          const [
            dashboardData,
            medicineData,
            patientData,
            weeklyDiseaseData,
          ] = await Promise.all([
            getDashboardSummary(),

            getMedicines(
              "",
              false
            ),

            getPatients(),

            getWeeklyDiseaseComparison(),
          ]);


          setDashboard(
            dashboardData ?? null
          );


          setMedicines(
            Array.isArray(
              medicineData
            )
              ? medicineData
              : []
          );


          setPatients(
            Array.isArray(
              patientData
            )
              ? patientData
              : []
          );


          setWeeklyDiseases(
            Array.isArray(
              weeklyDiseaseData
            )
              ? weeklyDiseaseData
              : []
          );


          setGeneratedAt(
            new Date()
          );

        } catch (err) {
          console.error(
            "Failed to load reports:",
            err
          );

          setError(
            getApiErrorMessage(
              err,
              "Unable to load reports."
            )
          );

        } finally {
          setLoading(false);
          setRefreshing(false);
        }
      },
      []
    );


  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {
    loadReports();
  }, [
    loadReports,
  ]);


  /* =======================================================
     INVENTORY REPORT
  ======================================================= */

  const inventoryReport =
    useMemo(() => {
      const activeMedicines =
        medicines.filter(
          (medicine) =>
            medicine.is_active
        );


      const lowStock = [];
      const outOfStock = [];


      medicines.forEach(
        (medicine) => {
          const status =
            getStockStatus(
              medicine
            );


          if (
            status ===
            "LOW STOCK"
          ) {
            lowStock.push(
              medicine
            );
          }


          if (
            status ===
            "OUT OF STOCK"
          ) {
            outOfStock.push(
              medicine
            );
          }
        }
      );


      return {
        activeCount:
          activeMedicines.length,

        lowStock,

        outOfStock,

        atRisk: [
          ...outOfStock,
          ...lowStock,
        ],
      };
    }, [
      medicines,
    ]);


  /* =======================================================
     RISING DISEASES
  ======================================================= */

  const risingDiseases =
    useMemo(() => {
      return [
        ...weeklyDiseases,
      ]
        .filter(
          (item) =>
            Number(
              item?.difference ??
                0
            ) > 0
        )
        .sort(
          (a, b) =>
            Number(
              b?.difference ??
                0
            ) -
            Number(
              a?.difference ??
                0
            )
        );
    }, [
      weeklyDiseases,
    ]);


  /* =======================================================
     CONSULTATION TREND
  ======================================================= */

  const consultationTrend =
    useMemo(() => {
      const days =
        createRecentDays(
          CONSULTATION_DAYS
        );


      const countByDate =
        Object.fromEntries(
          days.map(
            (day) => [
              day.key,
              0,
            ]
          )
        );


      const recentConsultations =
        Array.isArray(
          dashboard
            ?.recent_consultations
        )
          ? dashboard
              .recent_consultations
          : [];


      recentConsultations.forEach(
        (consultation) => {
          const dateValue =
            getConsultationDate(
              consultation
            );

          const key =
            toLocalDateKey(
              dateValue
            );


          if (
            key &&
            Object.prototype.hasOwnProperty.call(
              countByDate,
              key
            )
          ) {
            countByDate[key] += 1;
          }
        }
      );


      return days.map(
        (day) => ({
          date: day.label,

          consultations:
            countByDate[
              day.key
            ] ?? 0,
        })
      );
    }, [
      dashboard,
    ]);


  /* =======================================================
     TOP DISEASE CASES
  ======================================================= */

  const topDiseaseCases =
    useMemo(() => {
      return [
        ...weeklyDiseases,
      ]
        .map(
          (item) => ({
            name:
              item?.name ||
              "Unknown",

            cases:
              Number(
                item
                  ?.current_week_cases ??
                  0
              ),
          })
        )
        .sort(
          (a, b) =>
            b.cases -
            a.cases
        )
        .slice(
          0,
          5
        );
    }, [
      weeklyDiseases,
    ]);


  /* =======================================================
     SEX DISTRIBUTION
  ======================================================= */

  const sexDistribution =
    useMemo(() => {
      let male = 0;
      let female = 0;


      patients.forEach(
        (patient) => {
          const sex =
            String(
              patient?.sex || ""
            )
              .trim()
              .toLowerCase();


          if (sex === "male") {
            male += 1;
          }


          if (
            sex === "female"
          ) {
            female += 1;
          }
        }
      );


      return [
        {
          name: "Male",
          value: male,
        },
        {
          name: "Female",
          value: female,
        },
      ];
    }, [
      patients,
    ]);


  /* =======================================================
     AGE GROUP DISTRIBUTION
  ======================================================= */

  const ageDistribution =
    useMemo(() => {
      const groups = {
        Toddler: 0,
        Minor: 0,
        Adult: 0,
        Senior: 0,
      };


      patients.forEach(
        (patient) => {
          const age =
            calculateAge(
              patient
                ?.date_of_birth
            );


          if (age == null) {
            return;
          }


          if (
            age >= 0 &&
            age <= 4
          ) {
            groups.Toddler += 1;
            return;
          }


          if (
            age >= 5 &&
            age <= 17
          ) {
            groups.Minor += 1;
            return;
          }


          if (
            age >= 18 &&
            age <= 59
          ) {
            groups.Adult += 1;
            return;
          }


          if (age >= 60) {
            groups.Senior += 1;
          }
        }
      );


      return [
        {
          name: "Toddler",
          ageRange: "0–4",
          patients:
            groups.Toddler,
        },
        {
          name: "Minor",
          ageRange: "5–17",
          patients:
            groups.Minor,
        },
        {
          name: "Adult",
          ageRange: "18–59",
          patients:
            groups.Adult,
        },
        {
          name: "Senior",
          ageRange: "60+",
          patients:
            groups.Senior,
        },
      ];
    }, [
      patients,
    ]);


  /* =======================================================
     CHART STATUS
  ======================================================= */

  const sexTotal =
    useMemo(
      () =>
        sexDistribution.reduce(
          (
            total,
            item
          ) =>
            total +
            item.value,
          0
        ),
      [
        sexDistribution,
      ]
    );


  const ageTotal =
    useMemo(
      () =>
        ageDistribution.reduce(
          (
            total,
            item
          ) =>
            total +
            item.patients,
          0
        ),
      [
        ageDistribution,
      ]
    );


  const diseaseCasesTotal =
    useMemo(
      () =>
        topDiseaseCases.reduce(
          (
            total,
            item
          ) =>
            total +
            item.cases,
          0
        ),
      [
        topDiseaseCases,
      ]
    );


  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {
    return (
      <div className="reports-state">
        Loading reports...
      </div>
    );
  }


  /* =======================================================
     ERROR
  ======================================================= */

  if (error) {
    return (
      <div className="reports-state">

        <p>
          {error}
        </p>


        <button
          type="button"
          className="reports-button"
          onClick={() =>
            loadReports()
          }
        >
          Retry
        </button>

      </div>
    );
  }


  /* =======================================================
     PAGE
  ======================================================= */

  return (
    <div className="reports-page">

      {/* =================================================
          HEADER
      ================================================== */}

      <section className="reports-header">

        <div>

          <h1>
            Reports
          </h1>

          <p>
            Operational summary and statistical
            health center analysis.
          </p>

        </div>


        <div className="reports-header-actions">

          {generatedAt && (
            <span>
              Generated{" "}

              {generatedAt.toLocaleString(
                undefined,
                REPORT_DATE_FORMAT
              )}
            </span>
          )}


          <button
            type="button"
            className="reports-button"
            disabled={
              refreshing
            }
            onClick={() =>
              loadReports(
                true
              )
            }
          >
            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </button>

        </div>

      </section>


      {/* =================================================
          SUMMARY METRICS
      ================================================== */}

      <section className="reports-grid">

        <ReportMetric
          label="Total Patients"
          value={
            dashboard
              ?.total_patients ??
            patients.length
          }
        />


        <ReportMetric
          label="Consultations Today"
          value={
            dashboard
              ?.consultations_today ??
            0
          }
        />


        <ReportMetric
          label="Weekly Consultations"
          value={
            dashboard
              ?.consultations_this_week ??
            0
          }
        />


        <ReportMetric
          label="Active Medicines"
          value={
            inventoryReport
              .activeCount
          }
        />

      </section>


      {/* =================================================
          STATISTICAL OVERVIEW
      ================================================== */}

      <section className="reports-statistics-section">

        <div className="reports-section-title">

          <div>

            <h2>
              Statistical Overview
            </h2>

            <p>
              Visual summary of consultations,
              patient demographics, and disease cases.
            </p>

          </div>

        </div>


        <div className="reports-chart-grid">

          {/* ===============================================
              CONSULTATION TREND
          ================================================ */}

          <section className="reports-card reports-chart-card reports-chart-wide">

            <ReportHeader
              title="Consultation Trend"
              description={
                "Recent consultation activity for the last 7 days."
              }
            />


            <div className="reports-chart-body">

              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart
                  data={
                    consultationTrend
                  }
                  margin={{
                    top: 10,
                    right: 20,
                    left: -12,
                    bottom: 5,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                  />


                  <XAxis
                    dataKey="date"
                    tickLine={false}
                    axisLine={false}
                  />


                  <YAxis
                    allowDecimals={false}
                    tickLine={false}
                    axisLine={false}
                  />


                  <Tooltip
                    formatter={(
                      value
                    ) => [
                      value,
                      "Consultations",
                    ]}
                  />


                  <Legend />


                  <Line
                    type="monotone"
                    dataKey="consultations"
                    name="Consultations"
                    stroke={
                      CHART_COLORS.primary
                    }
                    strokeWidth={3}
                    activeDot={{
                      r: 5,
                    }}
                  />

                </LineChart>
              </ResponsiveContainer>

            </div>

          </section>


          {/* ===============================================
              TOP DISEASE CASES
          ================================================ */}

          <section className="reports-card reports-chart-card">

            <ReportHeader
              title="Top Disease Cases"
              description={
                "Highest case counts recorded for the current week."
              }
            />


            {topDiseaseCases.length === 0 ? (

              <EmptyReport>
                No disease data available.
              </EmptyReport>

            ) : (

              <div className="reports-chart-body">

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <BarChart
                    data={
                      topDiseaseCases
                    }
                    layout="vertical"
                    margin={{
                      top: 8,
                      right: 20,
                      left: 28,
                      bottom: 5,
                    }}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      horizontal={false}
                    />


                    <XAxis
                      type="number"
                      allowDecimals={false}
                      tickLine={false}
                      axisLine={false}
                    />


                    <YAxis
                      type="category"
                      dataKey="name"
                      width={135}
                      tickLine={false}
                      axisLine={false}
                    />


                    <Tooltip
                      formatter={(
                        value
                      ) => [
                        value,
                        "Cases",
                      ]}
                    />


                    <Bar
                      dataKey="cases"
                      name="Cases"
                      fill={
                        CHART_COLORS.warning
                      }
                      radius={[
                        0,
                        6,
                        6,
                        0,
                      ]}
                    />

                  </BarChart>
                </ResponsiveContainer>

              </div>

            )}


            <ChartFooter>
              Current-week cases shown:{" "}
              <strong>
                {diseaseCasesTotal}
              </strong>
            </ChartFooter>

          </section>


          {/* ===============================================
              SEX DISTRIBUTION
          ================================================ */}

          <section className="reports-card reports-chart-card">

            <ReportHeader
              title="Patient Sex Distribution"
              description={
                "Registered patients grouped by recorded sex."
              }
            />


            {sexTotal === 0 ? (

              <EmptyReport>
                No patient sex data available.
              </EmptyReport>

            ) : (

              <div className="reports-chart-body">

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <PieChart>

                    <Tooltip
                      formatter={(
                        value
                      ) => [
                        value,
                        "Patients",
                      ]}
                    />


                    <Legend
                      verticalAlign="bottom"
                    />


                    <Pie
                      data={
                        sexDistribution
                      }
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="46%"
                      innerRadius={65}
                      outerRadius={100}
                      paddingAngle={3}
                    >

                      {sexDistribution.map(
                        (entry) => (
                          <Cell
                            key={
                              entry.name
                            }
                            fill={
                              SEX_COLORS[
                                entry.name
                              ]
                            }
                          />
                        )
                      )}

                    </Pie>

                  </PieChart>
                </ResponsiveContainer>

              </div>

            )}


            <ChartFooter>
              Total categorized patients:{" "}

              <strong>
                {sexTotal}
              </strong>
            </ChartFooter>

          </section>


          {/* ===============================================
              AGE GROUP DISTRIBUTION
          ================================================ */}

          <section className="reports-card reports-chart-card reports-chart-wide">

            <ReportHeader
              title="Patient Age Group Distribution"
              description={
                "Registered patients grouped by age calculated from date of birth."
              }
            />


            {ageTotal === 0 ? (

              <EmptyReport>
                No patient age data available.
              </EmptyReport>

            ) : (

              <div className="reports-chart-body reports-chart-body-short">

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <BarChart
                    data={
                      ageDistribution
                    }
                    margin={{
                      top: 10,
                      right: 20,
                      left: -10,
                      bottom: 5,
                    }}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                    />


                    <XAxis
                      dataKey="name"
                      tickLine={false}
                      axisLine={false}
                    />


                    <YAxis
                      allowDecimals={false}
                      tickLine={false}
                      axisLine={false}
                    />


                    <Tooltip
                      formatter={(
                        value
                      ) => [
                        value,
                        "Patients",
                      ]}
                      labelFormatter={(
                        label
                      ) => {
                        const group =
                          ageDistribution.find(
                            (
                              item
                            ) =>
                              item.name ===
                              label
                          );

                        return group
                          ? `${label} (${group.ageRange})`
                          : label;
                      }}
                    />


                    <Bar
                      dataKey="patients"
                      name="Patients"
                      fill={
                        CHART_COLORS.secondary
                      }
                      radius={[
                        6,
                        6,
                        0,
                        0,
                      ]}
                    />

                  </BarChart>
                </ResponsiveContainer>

              </div>

            )}


            <div className="reports-age-legend">

              <span>
                Toddler: 0–4
              </span>

              <span>
                Minor: 5–17
              </span>

              <span>
                Adult: 18–59
              </span>

              <span>
                Senior: 60+
              </span>

            </div>

          </section>

        </div>

      </section>


      {/* =================================================
          MAIN OPERATIONAL REPORTS
      ================================================== */}

      <div className="reports-two-column">

        {/* ===============================================
            DISEASE TREND REPORT
        ================================================ */}

        <section className="reports-card">

          <ReportHeader
            title="Disease Trend Report"
            description={
              "Current week compared with the previous week."
            }
          />


          {weeklyDiseases.length ===
          0 ? (

            <EmptyReport>
              No weekly disease data available.
            </EmptyReport>

          ) : (

            <div className="reports-table-wrap">

              <table className="reports-table">

                <thead>

                  <tr>
                    <th>
                      Disease
                    </th>

                    <th>
                      Current
                    </th>

                    <th>
                      Previous
                    </th>

                    <th>
                      Change
                    </th>

                    <th>
                      Trend
                    </th>
                  </tr>

                </thead>


                <tbody>

                  {weeklyDiseases.map(
                    (item) => (

                      <tr
                        key={
                          item.disease_id
                        }
                      >

                        <td>

                          <strong>
                            {item.name}
                          </strong>

                        </td>


                        <td>
                          {
                            item
                              .current_week_cases
                          }
                        </td>


                        <td>
                          {
                            item
                              .previous_week_cases
                          }
                        </td>


                        <td>
                          {formatSignedNumber(
                            item.difference
                          )}
                        </td>


                        <td>

                          <TrendBadge
                            trend={
                              item.trend
                            }
                          />

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>


        {/* ===============================================
            INVENTORY RISK REPORT
        ================================================ */}

        <section className="reports-card">

          <ReportHeader
            title="Inventory Risk Report"
            description={
              "Medicines that need restocking or review."
            }
          />


          <div className="reports-risk-grid">

            <ReportMetric
              label="Low Stock"
              value={
                inventoryReport
                  .lowStock
                  .length
              }
              tone="warning"
            />


            <ReportMetric
              label="Out of Stock"
              value={
                inventoryReport
                  .outOfStock
                  .length
              }
              tone="danger"
            />

          </div>


          {inventoryReport.atRisk
            .length === 0 ? (

            <EmptyReport>
              No medicines currently need restocking.
            </EmptyReport>

          ) : (

            <div className="reports-table-wrap">

              <table className="reports-table">

                <thead>

                  <tr>
                    <th>
                      Code
                    </th>

                    <th>
                      Medicine
                    </th>

                    <th>
                      Stock
                    </th>

                    <th>
                      Status
                    </th>
                  </tr>

                </thead>


                <tbody>

                  {inventoryReport.atRisk.map(
                    (
                      medicine
                    ) => {
                      const status =
                        getStockStatus(
                          medicine
                        );


                      return (

                        <tr
                          key={
                            medicine.id
                          }
                        >

                          <td>

                            <span className="reports-code">
                              {medicine.code}
                            </span>

                          </td>


                          <td>

                            <strong>
                              {medicine.name}
                            </strong>

                          </td>


                          <td>
                            {getStockDisplay(
                              medicine
                            )}
                          </td>


                          <td>

                            <span
                              className={
                                status ===
                                "OUT OF STOCK"
                                  ? "reports-status reports-status-danger"
                                  : "reports-status reports-status-warning"
                              }
                            >
                              {status}
                            </span>

                          </td>

                        </tr>

                      );
                    }
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>

      </div>


      {/* =================================================
          PRIORITY REVIEW
      ================================================== */}

      <section className="reports-card">

        <ReportHeader
          title="Priority Review"
          description={
            "Items that may need staff attention this week."
          }
        />


        <div className="reports-review-list">

          <ReviewItem
            label="Rising disease trends"
            value={
              risingDiseases.length
            }
            detail={
              risingDiseases.length >
              0
                ? risingDiseases
                    .map(
                      (item) =>
                        item.name
                    )
                    .join(", ")
                : "No rising weekly trend detected."
            }
          />


          <ReviewItem
            label="Medicine stock risks"
            value={
              inventoryReport
                .lowStock
                .length +
              inventoryReport
                .outOfStock
                .length
            }
            detail={
              "Review purchasing, deliveries, and dispensing activity."
            }
          />


          <ReviewItem
            label="Recent consultations"
            value={
              dashboard
                ?.recent_consultations
                ?.length ??
              0
            }
            detail={
              "Use patient consultation records for clinical follow-up."
            }
          />

        </div>

      </section>

    </div>
  );
}


/* =========================================================
   REPORT METRIC
========================================================= */

function ReportMetric({
  label,
  value,
  tone = "default",
}) {
  return (
    <div
      className={
        `reports-metric reports-metric-${tone}`
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


/* =========================================================
   REPORT HEADER
========================================================= */

function ReportHeader({
  title,
  description,
}) {
  return (
    <div className="reports-card-header">

      <div>

        <h2>
          {title}
        </h2>

        <p>
          {description}
        </p>

      </div>

    </div>
  );
}


/* =========================================================
   REVIEW ITEM
========================================================= */

function ReviewItem({
  label,
  value,
  detail,
}) {
  return (
    <div className="reports-review-item">

      <span>
        {label}
      </span>


      <strong>
        {value}
      </strong>


      <p>
        {detail}
      </p>

    </div>
  );
}


/* =========================================================
   CHART FOOTER
========================================================= */

function ChartFooter({
  children,
}) {
  return (
    <div className="reports-chart-footer">
      {children}
    </div>
  );
}


/* =========================================================
   EMPTY REPORT
========================================================= */

function EmptyReport({
  children,
}) {
  return (
    <div className="reports-empty">
      {children}
    </div>
  );
}


/* =========================================================
   TREND BADGE
========================================================= */

function TrendBadge({
  trend,
}) {
  const normalized =
    String(
      trend || "NO_CHANGE"
    ).toUpperCase();


  let className =
    "reports-trend reports-trend-neutral";


  if (
    normalized === "RISING" ||
    normalized === "INCREASING"
  ) {
    className =
      "reports-trend reports-trend-up";
  }


  if (
    normalized === "FALLING" ||
    normalized === "DECREASING"
  ) {
    className =
      "reports-trend reports-trend-down";
  }


  return (
    <span className={className}>
      {normalized
        .replaceAll(
          "_",
          " "
        )}
    </span>
  );
}


/* =========================================================
   STOCK STATUS
========================================================= */

function getStockStatus(
  medicine
) {
  const stock =
    getStockQuantity(
      medicine
    );


  const reorderLevel =
    Number(
      medicine
        ?.reorder_level ??
        0
    );


  if (stock <= 0) {
    return "OUT OF STOCK";
  }


  if (
    stock <=
    reorderLevel
  ) {
    return "LOW STOCK";
  }


  return "IN STOCK";
}


/* =========================================================
   STOCK QUANTITY
========================================================= */

function getStockQuantity(
  medicine
) {
  const packageStock =
    Number(
      medicine
        ?.package_stock ??
        0
    );


  const looseStock =
    Number(
      medicine
        ?.loose_stock ??
        0
    );


  const unitsPerPackage =
    Number(
      medicine
        ?.units_per_package ??
        0
    );


  if (
    unitsPerPackage >
    0
  ) {
    return (
      packageStock *
        unitsPerPackage +
      looseStock
    );
  }


  return (
    packageStock +
    looseStock
  );
}


/* =========================================================
   STOCK DISPLAY
========================================================= */

function getStockDisplay(
  medicine
) {
  const parts = [];


  const packageStock =
    Number(
      medicine
        ?.package_stock ??
        0
    );


  const looseStock =
    Number(
      medicine
        ?.loose_stock ??
        0
    );


  if (
    packageStock >
    0
  ) {
    parts.push(
      medicine
        ?.package_unit
        ? `${packageStock} ${medicine.package_unit}`
        : `${packageStock} package(s)`
    );
  }


  if (
    looseStock >
    0
  ) {
    parts.push(
      `${looseStock} ${
        medicine
          ?.dispensing_unit ||
        "piece(s)"
      }`
    );
  }


  if (
    parts.length ===
    0
  ) {
    return (
      `0 ${
        medicine
          ?.dispensing_unit ||
        "piece(s)"
      }`
    );
  }


  return parts.join(
    " + "
  );
}


/* =========================================================
   AGE
========================================================= */

function calculateAge(
  dateOfBirth
) {
  if (!dateOfBirth) {
    return null;
  }


  const [
    birthYear,
    birthMonth,
    birthDay,
  ] = String(
    dateOfBirth
  )
    .split("-")
    .map(Number);


  if (
    !birthYear ||
    !birthMonth ||
    !birthDay
  ) {
    return null;
  }


  const today =
    new Date();


  let age =
    today.getFullYear() -
    birthYear;


  const currentMonth =
    today.getMonth() + 1;


  const currentDay =
    today.getDate();


  if (
    currentMonth <
      birthMonth ||
    (
      currentMonth ===
        birthMonth &&
      currentDay <
        birthDay
    )
  ) {
    age -= 1;
  }


  return age >= 0
    ? age
    : null;
}


/* =========================================================
   RECENT DAYS
========================================================= */

function createRecentDays(
  numberOfDays
) {
  const days = [];


  for (
    let offset =
      numberOfDays - 1;
    offset >= 0;
    offset -= 1
  ) {
    const date =
      new Date();

    date.setHours(
      0,
      0,
      0,
      0
    );

    date.setDate(
      date.getDate() -
        offset
    );


    days.push({
      key:
        toLocalDateKey(
          date
        ),

      label:
        date.toLocaleDateString(
          undefined,
          {
            month:
              "short",

            day:
              "numeric",
          }
        ),
    });
  }


  return days;
}


/* =========================================================
   CONSULTATION DATE
========================================================= */

function getConsultationDate(
  consultation
) {
  return (
    consultation
      ?.consultation_date ||
    consultation
      ?.created_at ||
    consultation
      ?.date ||
    null
  );
}


/* =========================================================
   LOCAL DATE KEY
========================================================= */

function toLocalDateKey(
  value
) {
  if (!value) {
    return null;
  }


  const date =
    value instanceof Date
      ? value
      : new Date(value);


  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return null;
  }


  const year =
    date.getFullYear();


  const month =
    String(
      date.getMonth() +
        1
    ).padStart(
      2,
      "0"
    );


  const day =
    String(
      date.getDate()
    ).padStart(
      2,
      "0"
    );


  return (
    `${year}-${month}-${day}`
  );
}


/* =========================================================
   SIGNED NUMBER
========================================================= */

function formatSignedNumber(
  value
) {
  const number =
    Number(
      value ?? 0
    );


  return number > 0
    ? `+${number}`
    : String(
        number
      );
}


/* =========================================================
   API ERROR
========================================================= */

function getApiErrorMessage(
  error,
  fallback
) {
  const detail =
    error
      ?.response
      ?.data
      ?.detail;


  if (
    typeof detail ===
    "string"
  ) {
    return detail;
  }


  if (
    Array.isArray(
      detail
    )
  ) {
    return detail
      .map(
        (item) =>
          item?.msg ||
          "Invalid request."
      )
      .join(", ");
  }


  return fallback;
}


export default Reports;