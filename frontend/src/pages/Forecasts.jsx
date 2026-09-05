import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getDiseaseForecast,
  getDiseaseForecastCatalog,
  getMedicineForecast,
  getMedicineForecasts,
  getDiseaseMedicineMappings,
} from "../api/forecastApi";

import "../styles/Forecasts.css";
import "../styles/ForecastsDisease.css";
import "../styles/ForecastsMedicine.css";
import "../styles/ForecastsRuntime.css";
import "../styles/ForecastsMapping.css";
import "../styles/ForecastsCatalog.css";


const SVG_WIDTH = 1000;
const SVG_HEIGHT = 360;
const PADDING = 38;


function getApiErrorMessage(
  error,
  fallback
) {
  return (
    error?.response?.data?.detail ||
    fallback
  );
}


function formatMetric(
  value,
  decimals = 2
) {
  if (
    value === null ||
    value === undefined
  ) {
    return "-";
  }

  return Number(value).toFixed(
    decimals
  );
}


function formatWhole(
  value
) {
  if (
    value === null ||
    value === undefined
  ) {
    return "-";
  }

  return Math.round(
    Number(value)
  ).toLocaleString();
}


function ForecastChart({
  historicalPoints,
  forecastPoints,
  dateKey,
  historicalValueKey,
  forecastValueKey,
  lowerKey,
  upperKey,
  yUnitLabel,
  ariaLabel,
}) {
  const chart = useMemo(() => {
    const historical =
      historicalPoints || [];

    const forecast =
      forecastPoints || [];

    if (
      historical.length === 0 &&
      forecast.length === 0
    ) {
      return null;
    }

    const numericHistorical =
      historical.filter(
        (item) =>
          item[
            historicalValueKey
          ] !== null
          && item[
            historicalValueKey
          ] !== undefined
      );

    const values = [
      ...numericHistorical.map(
        (item) =>
          Number(
            item[
              historicalValueKey
            ]
          )
      ),
      ...forecast.map(
        (item) =>
          Number(
            item[
              forecastValueKey
            ]
          )
      ),
      ...forecast.map(
        (item) =>
          Number(
            item[
              upperKey
            ]
          )
      ),
    ];

    const maxValue = Math.max(
      1,
      ...values.filter(
        (value) =>
          Number.isFinite(
            value
          )
      )
    );

    const count =
      historical.length +
      forecast.length;

    const xForIndex =
      (index) =>
        PADDING +
        (
          (
            SVG_WIDTH -
            PADDING * 2
          )
          * index
        )
        / Math.max(
          1,
          count - 1
        );

    const yForValue =
      (value) =>
        SVG_HEIGHT -
        PADDING -
        (
          (
            SVG_HEIGHT -
            PADDING * 2
          )
          * Number(value)
        )
        / maxValue;

    const historicalSegments = [];

    let activeSegment = [];

    historical.forEach(
      (item, index) => {
        const value =
          item[
            historicalValueKey
          ];

        if (
          value === null ||
          value === undefined
        ) {
          if (
            activeSegment.length > 0
          ) {
            historicalSegments.push(
              activeSegment
            );

            activeSegment = [];
          }

          return;
        }

        activeSegment.push({
          x: xForIndex(index),
          y: yForValue(value),
        });
      }
    );

    if (
      activeSegment.length > 0
    ) {
      historicalSegments.push(
        activeSegment
      );
    }

    const historicalPaths =
      historicalSegments.map(
        (segment) =>
          segment
            .map(
              (point, index) =>
                `${
                  index === 0
                    ? "M"
                    : "L"
                } ${point.x} ${point.y}`
            )
            .join(" ")
      );

    const forecastPathPoints = [];

    const lastKnownIndex =
      [...historical]
        .map(
          (item, index) => ({
            item,
            index,
          })
        )
        .reverse()
        .find(
          ({ item }) =>
            item[
              historicalValueKey
            ] !== null
            && item[
              historicalValueKey
            ] !== undefined
        );

    if (
      lastKnownIndex &&
      forecast.length > 0
    ) {
      forecastPathPoints.push({
        x: xForIndex(
          lastKnownIndex.index
        ),
        y: yForValue(
          lastKnownIndex.item[
            historicalValueKey
          ]
        ),
      });
    }

    forecast.forEach(
      (item, index) => {
        forecastPathPoints.push({
          x: xForIndex(
            historical.length +
            index
          ),
          y: yForValue(
            item[
              forecastValueKey
            ]
          ),
        });
      }
    );

    const forecastPath =
      forecastPathPoints
        .map(
          (point, index) =>
            `${
              index === 0
                ? "M"
                : "L"
            } ${point.x} ${point.y}`
        )
        .join(" ");

    const upperPoints =
      forecast.map(
        (item, index) => ({
          x: xForIndex(
            historical.length +
            index
          ),
          y: yForValue(
            item[
              upperKey
            ]
          ),
        })
      );

    const lowerPoints =
      [...forecast]
        .reverse()
        .map(
          (
            item,
            reversedIndex
          ) => {
            const originalIndex =
              forecast.length -
              1 -
              reversedIndex;

            return {
              x: xForIndex(
                historical.length +
                originalIndex
              ),
              y: yForValue(
                item[
                  lowerKey
                ]
              ),
            };
          }
        );

    const confidencePolygon = [
      ...upperPoints,
      ...lowerPoints,
    ]
      .map(
        (point) =>
          `${point.x},${point.y}`
      )
      .join(" ");

    const allDates = [
      ...historical.map(
        (item) =>
          item[
            dateKey
          ]
      ),
      ...forecast.map(
        (item) =>
          item[
            dateKey
          ]
      ),
    ];

    return {
      historicalPaths,
      forecastPath,
      confidencePolygon,
      maxValue,
      splitX:
        historical.length > 0
          ? xForIndex(
              historical.length - 1
            )
          : null,
      firstDate:
        allDates[0],
      lastDate:
        allDates[
          allDates.length - 1
        ],
    };
  }, [
    dateKey,
    forecastPoints,
    forecastValueKey,
    historicalPoints,
    historicalValueKey,
    lowerKey,
    upperKey,
  ]);


  if (!chart) {
    return (
      <div className="forecast-placeholder">
        No chart data available.
      </div>
    );
  }


  return (
    <div className="disease-forecast-chart">

      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        role="img"
        aria-label={ariaLabel}
      >

        <line
          x1={PADDING}
          y1={
            SVG_HEIGHT -
            PADDING
          }
          x2={
            SVG_WIDTH -
            PADDING
          }
          y2={
            SVG_HEIGHT -
            PADDING
          }
          className="forecast-axis"
        />

        <line
          x1={PADDING}
          y1={PADDING}
          x2={PADDING}
          y2={
            SVG_HEIGHT -
            PADDING
          }
          className="forecast-axis"
        />

        {chart.confidencePolygon && (
          <polygon
            points={
              chart.confidencePolygon
            }
            className="forecast-confidence-band"
          />
        )}

        {chart.splitX !== null && (
          <line
            x1={chart.splitX}
            y1={PADDING}
            x2={chart.splitX}
            y2={
              SVG_HEIGHT -
              PADDING
            }
            className="forecast-split-line"
          />
        )}

        {
          chart.historicalPaths.map(
            (
              path,
              index
            ) => (
              <path
                key={index}
                d={path}
                className="forecast-history-line"
              />
            )
          )
        }

        {chart.forecastPath && (
          <path
            d={
              chart.forecastPath
            }
            className="forecast-future-line"
          />
        )}

        <text
          x={PADDING}
          y={PADDING - 10}
          className="forecast-axis-label"
        >
          {
            Math.ceil(
              chart.maxValue
            )
          }{" "}
          {yUnitLabel}
        </text>

        <text
          x={PADDING}
          y={
            SVG_HEIGHT - 10
          }
          className="forecast-axis-label"
        >
          {chart.firstDate}
        </text>

        <text
          x={
            SVG_WIDTH -
            PADDING
          }
          y={
            SVG_HEIGHT - 10
          }
          textAnchor="end"
          className="forecast-axis-label"
        >
          {chart.lastDate}
        </text>

      </svg>


      <div className="forecast-chart-legend">

        <span>
          <i className="legend-history" />
          Stored / baseline history
        </span>

        <span>
          <i className="legend-forecast" />
          Runtime forecast
        </span>

        <span>
          <i className="legend-confidence" />
          95% confidence interval
        </span>

      </div>

    </div>
  );
}


function MetricCards({
  detail,
  mapeLabel,
}) {
  return (
    <div className="disease-forecast-metrics">

      <div>
        <span>
          Model
        </span>
        <strong>
          {detail.model_family}
        </strong>
      </div>

      <div>
        <span>
          RMSE
        </span>
        <strong>
          {formatMetric(detail.rmse)}
        </strong>
      </div>

      <div>
        <span>
          MAE
        </span>
        <strong>
          {formatMetric(detail.mae)}
        </strong>
      </div>

      <div>
        <span>
          MAPE
        </span>
        <strong>
          {
            detail
              .mape_nonzero_pct
              != null
              ? `${formatMetric(
                  detail
                    .mape_nonzero_pct
                )}%`
              : "-"
          }
        </strong>
        <small>
          {mapeLabel}
        </small>
      </div>

    </div>
  );
}


function ModelSpecification({
  detail,
}) {
  return (
    <div className="disease-forecast-model-detail">
      <span>
        Runtime model specification:
      </span>

      <strong>
        {detail.model_family}{" "}
        ({detail.order.join(", ")})
        {
          detail
            .seasonal_order
            ? ` × (${detail.seasonal_order.join(", ")})`
            : ""
        }
      </strong>
    </div>
  );
}


function RuntimeDataPanel({
  runtimeData,
  periodLabel,
}) {
  return (
    <div
      className={
        runtimeData
          .freshness_status
          === "LIVE_CURRENT"
          ? "runtime-data-panel runtime-data-current"
          : "runtime-data-panel runtime-data-limited"
      }
    >

      <div className="runtime-data-panel-header">

        <div>
          <strong>
            Automatic Runtime Data Refresh
          </strong>

          <span>
            {
              runtimeData
                .data_mode
            }
          </span>
        </div>

        <span className="runtime-data-badge">
          {
            runtimeData
              .freshness_status
          }
        </span>

      </div>


      <p>
        {runtimeData.message}
      </p>


      <div className="runtime-data-grid">

        <div>
          <span>
            Development baseline ends
          </span>
          <strong>
            {
              runtimeData
                .baseline_end
            }
          </strong>
        </div>

        <div>
          <span>
            Latest completed {periodLabel}
          </span>
          <strong>
            {
              runtimeData
                .latest_completed_period
            }
          </strong>
        </div>

        <div>
          <span>
            Database coverage begins
          </span>
          <strong>
            {
              runtimeData
                .system_coverage_start
                || "Not yet available"
            }
          </strong>
        </div>

        <div>
          <span>
            Live {periodLabel}s used
          </span>
          <strong>
            {
              runtimeData
                .live_periods_used
            }
          </strong>
        </div>

      </div>


      {
        runtimeData
          .missing_bridge_periods
          > 0
        && (
          <div className="runtime-data-note">
            {
              runtimeData
                .missing_bridge_periods
            } historical {periodLabel}
            {
              runtimeData
                .missing_bridge_periods
                === 1
                ? ""
                : "s"
            } between the development
            baseline and live system
            coverage are treated as
            missing data, not zero.
          </div>
        )
      }


      <small>
        Generated:{" "}
        {
          runtimeData
            .forecast_generated_at
        }
      </small>

    </div>
  );
}


function DiseaseMedicineMappingPanel({
  rows,
  loading,
  error,
}) {
  const [
    selectedDisease,
    setSelectedDisease,
  ] = useState("ALL");

  const [
    search,
    setSearch,
  ] = useState("");


  const diseaseOptions =
    useMemo(
      () => [
        {
          value: "ALL",
          label: "All Diseases",
        },
        ...rows.map(
          (row) => ({
            value:
              String(
                row.disease_id
              ),
            label:
              row.disease_name,
          })
        ),
      ],
      [
        rows,
      ]
    );


  const visibleRows =
    useMemo(
      () => {
        const normalizedSearch =
          search
            .trim()
            .toLowerCase();

        return rows.filter(
          (row) => {
            if (
              selectedDisease !==
                "ALL"
              &&
              String(
                row.disease_id
              ) !== selectedDisease
            ) {
              return false;
            }

            if (!normalizedSearch) {
              return true;
            }

            const medicineText =
              (
                row
                  .mapped_medicines
                || []
              )
                .map(
                  (item) =>
                    [
                      item.target_label,
                      item.medicine_name,
                      item.medicine_code,
                    ]
                      .filter(
                        Boolean
                      )
                      .join(" ")
                )
                .join(" ");

            return [
              row.disease_code,
              row.disease_name,
              row.disease_category,
              row.mapping_group,
              row.mapping_status,
              medicineText,
            ]
              .filter(
                Boolean
              )
              .join(" ")
              .toLowerCase()
              .includes(
                normalizedSearch
              );
          }
        );
      },
      [
        rows,
        selectedDisease,
        search,
      ]
    );


  return (
    <div className="forecast-mapping-panel">

      <div className="forecast-mapping-heading">

        <div>
          <h3>
            Disease → Medicine Development Mapping
          </h3>

          <p>
            Browse all active disease /
            condition master entries.
            The default filter is
            <strong> All Diseases</strong>.
            Only exact active,
            stock-verified formulations
            can receive synthetic demand.
          </p>
        </div>

        <span className="forecast-mapping-development-badge">
          Synthetic Development Data
        </span>

      </div>


      <div className="forecast-mapping-controls">

        <label>
          <span>
            Disease
          </span>

          <select
            value={
              selectedDisease
            }
            onChange={
              (event) =>
                setSelectedDisease(
                  event
                    .target
                    .value
                )
            }
            disabled={
              loading
            }
          >
            {
              diseaseOptions.map(
                (option) => (
                  <option
                    key={
                      option.value
                    }
                    value={
                      option.value
                    }
                  >
                    {option.label}
                  </option>
                )
              )
            }
          </select>
        </label>


        <label className="forecast-mapping-search">
          <span>
            Search
          </span>

          <input
            type="search"
            value={
              search
            }
            onChange={
              (event) =>
                setSearch(
                  event
                    .target
                    .value
                )
            }
            placeholder="Disease, condition, medicine, code..."
          />
        </label>


        <div className="forecast-mapping-result-count">
          <span>
            Showing
          </span>

          <strong>
            {
              visibleRows.length
            } / {
              rows.length
            }
          </strong>
        </div>

      </div>


      {error && (
        <div className="app-message app-message-error forecast-section-message">
          {error}
        </div>
      )}


      {
        loading
          ? (
            <div className="forecast-placeholder">
              Loading complete disease-medicine mapping...
            </div>
          )
          : rows.length === 0
            ? (
              <div className="forecast-placeholder">
                No active disease mapping rows are available.
              </div>
            )
            : visibleRows.length === 0
              ? (
                <div className="forecast-placeholder">
                  No mapping matches the selected filter/search.
                </div>
              )
              : (
                <div className="forecast-mapping-table-wrap">

                  <table className="forecast-mapping-table">

                    <thead>
                      <tr>
                        <th>
                          Disease / Condition
                        </th>

                        <th>
                          Group
                        </th>

                        <th>
                          Mapped Medicine
                        </th>

                        <th>
                          Exact DB Match
                        </th>

                        <th>
                          Mock Demand
                        </th>
                      </tr>
                    </thead>


                    <tbody>

                      {
                        visibleRows.flatMap(
                          (row) => {
                            const medicines =
                              (
                                row
                                  .mapped_medicines
                                || []
                              );

                            if (
                              medicines.length
                              === 0
                            ) {
                              return [
                                <tr
                                  key={
                                    `disease-${row.disease_id}`
                                  }
                                >
                                  <td>
                                    <strong>
                                      {row.disease_name}
                                    </strong>

                                    <small>
                                      {row.disease_code}
                                    </small>
                                  </td>

                                  <td>
                                    {row.mapping_group}
                                  </td>

                                  <td>
                                    No development mapping configured
                                  </td>

                                  <td>
                                    <span className="forecast-mapping-status forecast-mapping-status-waiting">
                                      UNMAPPED
                                    </span>
                                  </td>

                                  <td>
                                    -
                                  </td>
                                </tr>,
                              ];
                            }

                            return medicines.map(
                              (
                                medicine,
                                index
                              ) => (
                                <tr
                                  key={
                                    `${row.disease_id}-${medicine.mapping_key}`
                                  }
                                >
                                  <td>
                                    {
                                      index === 0
                                        ? (
                                          <>
                                            <strong>
                                              {row.disease_name}
                                            </strong>

                                            <small>
                                              {row.disease_code}

                                              {
                                                row.is_sensitive
                                                && (
                                                  <>
                                                    {" · "}Restricted
                                                  </>
                                                )
                                              }
                                            </small>
                                          </>
                                        )
                                        : (
                                          <span className="forecast-mapping-repeat">
                                            ↳
                                          </span>
                                        )
                                    }
                                  </td>

                                  <td>
                                    {
                                      index === 0
                                        ? row.mapping_group
                                        : ""
                                    }
                                  </td>

                                  <td>
                                    <strong>
                                      {medicine.target_label}
                                    </strong>

                                    <small>
                                      {
                                        medicine
                                          .medicine_name
                                          || "Awaiting verified formulation"
                                      }
                                    </small>
                                  </td>

                                  <td>
                                    <span
                                      className={
                                        medicine
                                          .medicine_id
                                          ? "forecast-mapping-status forecast-mapping-status-ready"
                                          : "forecast-mapping-status forecast-mapping-status-waiting"
                                      }
                                    >
                                      {
                                        medicine
                                          .medicine_id
                                          ? "EXACT VERIFIED"
                                          : "NOT MATCHED"
                                      }
                                    </span>

                                    {
                                      medicine
                                        .medicine_code
                                      && (
                                        <small>
                                          {
                                            medicine
                                              .medicine_code
                                          }
                                        </small>
                                      )
                                    }
                                  </td>

                                  <td>
                                    <strong>
                                      {
                                        Number(
                                          medicine
                                            .synthetic_dispensed_units
                                          || 0
                                        )
                                          .toLocaleString()
                                      }
                                    </strong>

                                    <small>
                                      synthetic units ·{" "}
                                      {
                                        Number(
                                          medicine
                                            .synthetic_dispensing_records
                                          || 0
                                        )
                                          .toLocaleString()
                                      } rows
                                    </small>
                                  </td>
                                </tr>
                              )
                            );
                          }
                        )
                      }

                    </tbody>

                  </table>

                </div>
              )
      }


      <div className="forecast-mapping-note">
        Medicine mappings and quantities are
        synthetic development inputs for
        technical testing only. They are not
        prescribing instructions and do not
        establish real-world clinical accuracy.
        Candidate formulary records are never
        auto-verified by this workflow.
      </div>

    </div>
  );
}


function getDiseaseCatalogValue(
  item
) {
  if (
    item?.forecast_status ===
      "AVAILABLE"
    && item?.forecast_code
  ) {
    return (
      `MODEL:${item.forecast_code}`
    );
  }

  return (
    `DISEASE:${item?.disease_id}`
  );
}


function formatDiseaseCategory(
  value
) {
  if (!value) {
    return "Unclassified";
  }

  return String(value)
    .replaceAll(
      "_",
      " "
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );
}


function DiseaseForecastCatalogOverview({
  rows,
}) {
  return (
    <div className="forecast-catalog-overview">

      <div className="forecast-catalog-overview-header">

        <div>
          <h3>
            All Diseases Forecast Overview
          </h3>

          <p>
            All active diseases and conditions
            visible to your role are listed here.
            A forecast is generated only when a
            validated time-series model is available.
          </p>
        </div>

        <span className="forecast-catalog-count">
          {rows.length} diseases
        </span>

      </div>


      <div className="forecast-catalog-table-wrap">

        <table className="forecast-catalog-table">

          <thead>
            <tr>
              <th>
                Disease / Condition
              </th>

              <th>
                Category
              </th>

              <th>
                Access
              </th>

              <th>
                Forecast Status
              </th>

              <th>
                Model
              </th>
            </tr>
          </thead>


          <tbody>

            {rows.map(
              (item) => (

                <tr
                  key={
                    item.disease_id
                  }
                >
                  <td>
                    <strong>
                      {item.disease_name}
                    </strong>

                    <small>
                      {item.disease_code}
                    </small>
                  </td>


                  <td>
                    {
                      formatDiseaseCategory(
                        item.category
                      )
                    }
                  </td>


                  <td>
                    {
                      item.is_sensitive
                        ? (
                          <span className="forecast-catalog-access forecast-catalog-access-sensitive">
                            Restricted
                          </span>
                        )
                        : (
                          <span className="forecast-catalog-access">
                            General
                          </span>
                        )
                    }
                  </td>


                  <td>
                    {
                      item.forecast_status ===
                        "AVAILABLE"
                        ? (
                          <span className="forecast-catalog-status forecast-catalog-status-ready">
                            Available
                          </span>
                        )
                        : (
                          <span className="forecast-catalog-status forecast-catalog-status-pending">
                            Model Pending
                          </span>
                        )
                    }
                  </td>


                  <td>
                    {
                      item.model_family
                      || "-"
                    }
                  </td>
                </tr>

              )
            )}

          </tbody>

        </table>

      </div>


      <div className="forecast-catalog-note">
        The current validated development
        forecasting configurations remain
        Dengue, ARI, ILI, and Diarrhea /
        Gastroenteritis. Other active conditions
        are visible but are not assigned an
        unvalidated model merely to produce a chart.
      </div>

    </div>
  );
}


function DiseaseForecastPending({
  disease,
}) {
  if (!disease) {
    return null;
  }

  return (
    <div className="forecast-catalog-pending">

      <div className="forecast-catalog-pending-icon">
        ⏳
      </div>

      <div>
        <h3>
          {disease.disease_name}
        </h3>

        <p>
          {
            disease.status_message
            || (
              "This disease/condition is active "
              + "in the Disease Master, but a "
              + "validated forecasting model is "
              + "not available yet."
            )
          }
        </p>

        <div className="forecast-catalog-pending-meta">
          <span>
            {
              formatDiseaseCategory(
                disease.category
              )
            }
          </span>

          {
            disease.is_sensitive
            && (
              <span>
                Restricted / sensitive
              </span>
            )
          }
        </div>
      </div>

    </div>
  );
}


function Forecasts() {
  const [
    diseaseCatalog,
    setDiseaseCatalog,
  ] = useState([]);

  const [
    selectedDisease,
    setSelectedDisease,
  ] = useState("ALL");

  const [
    diseaseDetail,
    setDiseaseDetail,
  ] = useState(null);

  const [
    diseaseLoading,
    setDiseaseLoading,
  ] = useState(true);

  const [
    diseaseDetailLoading,
    setDiseaseDetailLoading,
  ] = useState(false);

  const [
    diseaseError,
    setDiseaseError,
  ] = useState("");


  const [
    medicineSummaries,
    setMedicineSummaries,
  ] = useState([]);

  const [
    selectedMedicine,
    setSelectedMedicine,
  ] = useState("");

  const [
    medicineDetail,
    setMedicineDetail,
  ] = useState(null);

  const [
    medicineLoading,
    setMedicineLoading,
  ] = useState(true);

  const [
    medicineDetailLoading,
    setMedicineDetailLoading,
  ] = useState(false);

  const [
    medicineError,
    setMedicineError,
  ] = useState("");


  const [
    mappingRows,
    setMappingRows,
  ] = useState([]);

  const [
    mappingLoading,
    setMappingLoading,
  ] = useState(true);

  const [
    mappingError,
    setMappingError,
  ] = useState("");


  const loadDiseaseCatalog =
    useCallback(async () => {
      try {
        setDiseaseLoading(true);
        setDiseaseError("");

        const data =
          await getDiseaseForecastCatalog();

        const rows =
          Array.isArray(data)
            ? data
            : [];

        setDiseaseCatalog(
          rows
        );

        setSelectedDisease(
          (current) =>
            current || "ALL"
        );

      } catch (error) {
        console.error(error);

        setDiseaseError(
          getApiErrorMessage(
            error,
            "Unable to load disease forecast catalog."
          )
        );

      } finally {
        setDiseaseLoading(false);
      }
    }, []);



  const loadDiseaseDetail =
    useCallback(
      async (
        diseaseCode
      ) => {
        if (!diseaseCode) {
          return;
        }

        try {
          setDiseaseDetailLoading(true);
          setDiseaseError("");

          const data =
            await getDiseaseForecast(
              diseaseCode
            );

          setDiseaseDetail(data);

        } catch (error) {
          console.error(error);

          setDiseaseError(
            getApiErrorMessage(
              error,
              "Unable to load disease forecast detail."
            )
          );

          setDiseaseDetail(null);

        } finally {
          setDiseaseDetailLoading(false);
        }
      },
      []
    );


  const loadMedicineSummaries =
    useCallback(async () => {
      try {
        setMedicineLoading(true);
        setMedicineError("");

        const data =
          await getMedicineForecasts();

        const rows =
          Array.isArray(data)
            ? data
            : [];

        setMedicineSummaries(rows);

        if (rows.length > 0) {
          setSelectedMedicine(
            (current) =>
              current ||
              rows[0]
                .medicine_code
          );
        }

      } catch (error) {
        console.error(error);

        setMedicineError(
          getApiErrorMessage(
            error,
            "Unable to load medicine forecasts."
          )
        );

      } finally {
        setMedicineLoading(false);
      }
    }, []);


  const loadMedicineDetail =
    useCallback(
      async (
        medicineCode
      ) => {
        if (!medicineCode) {
          return;
        }

        try {
          setMedicineDetailLoading(true);
          setMedicineError("");

          const data =
            await getMedicineForecast(
              medicineCode
            );

          setMedicineDetail(data);

        } catch (error) {
          console.error(error);

          setMedicineError(
            getApiErrorMessage(
              error,
              "Unable to load medicine forecast detail."
            )
          );

          setMedicineDetail(null);

        } finally {
          setMedicineDetailLoading(false);
        }
      },
      []
    );


  const loadDiseaseMedicineMappings =
    useCallback(
      async () => {
        try {
          setMappingLoading(
            true
          );

          setMappingError(
            ""
          );

          const data =
            await getDiseaseMedicineMappings();

          setMappingRows(
            Array.isArray(
              data
            )
              ? data
              : []
          );

        } catch (error) {
          console.error(
            error
          );

          setMappingError(
            getApiErrorMessage(
              error,
              "Unable to load disease-medicine development mapping."
            )
          );

        } finally {
          setMappingLoading(
            false
          );
        }
      },
      []
    );


  useEffect(() => {
    loadDiseaseCatalog();
    loadMedicineSummaries();
    loadDiseaseMedicineMappings();
  }, [
    loadDiseaseCatalog,
    loadMedicineSummaries,
    loadDiseaseMedicineMappings,
  ]);


  useEffect(() => {
    if (
      !selectedDisease
      || selectedDisease ===
        "ALL"
    ) {
      setDiseaseDetail(
        null
      );

      return;
    }

    if (
      selectedDisease.startsWith(
        "MODEL:"
      )
    ) {
      loadDiseaseDetail(
        selectedDisease.replace(
          "MODEL:",
          ""
        )
      );

      return;
    }

    setDiseaseDetail(
      null
    );
  }, [
    loadDiseaseDetail,
    selectedDisease,
  ]);


  useEffect(() => {
    if (selectedMedicine) {
      loadMedicineDetail(
        selectedMedicine
      );
    }
  }, [
    loadMedicineDetail,
    selectedMedicine,
  ]);


  const selectedDiseaseCatalogRow =
    useMemo(
      () => {
        if (
          selectedDisease ===
          "ALL"
        ) {
          return null;
        }

        return (
          diseaseCatalog.find(
            (item) =>
              getDiseaseCatalogValue(
                item
              )
              === selectedDisease
          )
          || null
        );
      },
      [
        diseaseCatalog,
        selectedDisease,
      ]
    );


  const generalDiseaseCatalog =
    useMemo(
      () =>
        diseaseCatalog.filter(
          (item) =>
            !item.is_sensitive
        ),
      [
        diseaseCatalog,
      ]
    );


  const sensitiveDiseaseCatalog =
    useMemo(
      () =>
        diseaseCatalog.filter(
          (item) =>
            item.is_sensitive
        ),
      [
        diseaseCatalog,
      ]
    );


  return (
    <div className="forecasts-page">

      <header className="forecasts-header">
        <div>
          <h1>
            Forecasts
          </h1>

          <p>
            Dynamic predictive analytics
            using the development baseline
            plus qualifying health-center
            records stored in the database.
          </p>
        </div>
      </header>


      <section className="forecast-card disease-forecast-workspace">

        <div className="disease-forecast-toolbar">

          <div>
            <h2>
              Disease Trend Forecast
            </h2>

            <p>
              Browse all active diseases and
              conditions visible to your role.
              Validated runtime forecasts are
              generated only for diseases with
              an established forecasting model.
            </p>
          </div>


          <label className="disease-forecast-select">
            <span>
              Disease
            </span>

            <select
              value={selectedDisease}
              onChange={
                (event) =>
                  setSelectedDisease(
                    event.target.value
                  )
              }
              disabled={
                diseaseLoading ||
                diseaseCatalog
                  .length === 0
              }
            >

              <option value="ALL">
                All Diseases
              </option>


              {
                generalDiseaseCatalog
                  .length > 0
                && (
                  <optgroup label="General / Standard">

                    {
                      generalDiseaseCatalog.map(
                        (item) => (

                          <option
                            key={
                              item
                                .disease_id
                            }
                            value={
                              getDiseaseCatalogValue(
                                item
                              )
                            }
                          >
                            {
                              item
                                .disease_code
                            }{" - "}
                            {
                              item
                                .disease_name
                            }
                            {
                              item
                                .forecast_status
                                !== "AVAILABLE"
                                ? " · Model Pending"
                                : ""
                            }
                          </option>

                        )
                      )
                    }

                  </optgroup>
                )
              }


              {
                sensitiveDiseaseCatalog
                  .length > 0
                && (
                  <optgroup label="Sensitive / Program (Restricted)">

                    {
                      sensitiveDiseaseCatalog.map(
                        (item) => (

                          <option
                            key={
                              item
                                .disease_id
                            }
                            value={
                              getDiseaseCatalogValue(
                                item
                              )
                            }
                          >
                            {
                              item
                                .disease_code
                            }{" - "}
                            {
                              item
                                .disease_name
                            }{" · Restricted"}
                            {
                              item
                                .forecast_status
                                !== "AVAILABLE"
                                ? " · Model Pending"
                                : ""
                            }
                          </option>

                        )
                      )
                    }

                  </optgroup>
                )
              }

            </select>
          </label>

        </div>


        {diseaseError && (
          <div className="app-message app-message-error forecast-section-message">
            {diseaseError}
          </div>
        )}


        {
          diseaseLoading
            ? (
              <div className="forecast-placeholder">
                Loading disease catalog...
              </div>
            )
            : selectedDisease ===
                "ALL"
              ? (
                <DiseaseForecastCatalogOverview
                  rows={
                    diseaseCatalog
                  }
                />
              )
              : selectedDiseaseCatalogRow
                  ?.forecast_status
                  !== "AVAILABLE"
                ? (
                  <DiseaseForecastPending
                    disease={
                      selectedDiseaseCatalogRow
                    }
                  />
                )
                : diseaseDetailLoading
                  ? (
                    <div className="forecast-placeholder">
                      Rebuilding runtime disease forecast...
                    </div>
                  )
                  : diseaseDetail
                ? (
                  <>

                    <div className="disease-forecast-warning">
                      {diseaseDetail.warning}
                    </div>


                    <RuntimeDataPanel
                      runtimeData={
                        diseaseDetail
                          .runtime_data
                      }
                      periodLabel="week"
                    />


                    <MetricCards
                      detail={diseaseDetail}
                      mapeLabel="development test metric"
                    />


                    <ModelSpecification
                      detail={diseaseDetail}
                    />


                    <ForecastChart
                      historicalPoints={
                        diseaseDetail
                          .historical_points
                      }
                      forecastPoints={
                        diseaseDetail
                          .forecast_points
                      }
                      dateKey="week_start"
                      historicalValueKey="case_count"
                      forecastValueKey="forecast_case_count"
                      lowerKey="lower_95"
                      upperKey="upper_95"
                      yUnitLabel="cases"
                      ariaLabel="Dynamic historical and forecast disease cases"
                    />


                    <div className="disease-forecast-table-wrap">
                      <table className="disease-forecast-table">
                        <thead>
                          <tr>
                            <th>Forecast Week</th>
                            <th>Cases</th>
                            <th>Lower 95%</th>
                            <th>Upper 95%</th>
                          </tr>
                        </thead>

                        <tbody>
                          {
                            diseaseDetail
                              .forecast_points
                              .map(
                                (item) => (
                                  <tr
                                    key={
                                      item
                                        .week_start
                                    }
                                  >
                                    <td>
                                      {item.week_start}
                                    </td>
                                    <td>
                                      {
                                        formatMetric(
                                          item
                                            .forecast_case_count,
                                          1
                                        )
                                      }
                                    </td>
                                    <td>
                                      {
                                        formatMetric(
                                          item.lower_95,
                                          1
                                        )
                                      }
                                    </td>
                                    <td>
                                      {
                                        formatMetric(
                                          item.upper_95,
                                          1
                                        )
                                      }
                                    </td>
                                  </tr>
                                )
                              )
                          }
                        </tbody>
                      </table>
                    </div>

                  </>
                )
                : (
                    <div className="forecast-placeholder">
                      No disease forecast data available.
                    </div>
                  )
        }

      </section>


      <section className="forecast-card medicine-forecast-workspace">

        <DiseaseMedicineMappingPanel
          rows={
            mappingRows
          }
          loading={
            mappingLoading
          }
          error={
            mappingError
          }
        />


        <div className="disease-forecast-toolbar">

          <div>
            <h2>
              Medicine Demand Forecast
            </h2>

            <p>
              Uses completed dispensing
              records stored in the database
              and always targets the actual
              next calendar month for resource
              planning.
            </p>
          </div>


          <label className="disease-forecast-select">
            <span>
              Medicine
            </span>

            <select
              value={selectedMedicine}
              onChange={
                (event) =>
                  setSelectedMedicine(
                    event.target.value
                  )
              }
              disabled={
                medicineLoading ||
                medicineSummaries
                  .length === 0
              }
            >
              {
                medicineSummaries.map(
                  (item) => (
                    <option
                      key={
                        item
                          .medicine_code
                      }
                      value={
                        item
                          .medicine_code
                      }
                    >
                      {
                        item
                          .medicine_name
                      }
                    </option>
                  )
                )
              }
            </select>
          </label>

        </div>


        {medicineError && (
          <div className="app-message app-message-error forecast-section-message">
            {medicineError}
          </div>
        )}


        {
          medicineLoading
            ? (
              <div className="forecast-placeholder">
                Loading medicine forecasts...
              </div>
            )
            : medicineDetailLoading
              ? (
                <div className="forecast-placeholder">
                  Rebuilding runtime medicine forecast...
                </div>
              )
              : medicineDetail
                ? (
                  <>

                    <div className="disease-forecast-warning">
                      {medicineDetail.warning}
                    </div>


                    <RuntimeDataPanel
                      runtimeData={
                        medicineDetail
                          .runtime_data
                      }
                      periodLabel="month"
                    />


                    <MetricCards
                      detail={medicineDetail}
                      mapeLabel="development test metric"
                    />


                    <ModelSpecification
                      detail={medicineDetail}
                    />


                    <ForecastChart
                      historicalPoints={
                        medicineDetail
                          .historical_points
                      }
                      forecastPoints={
                        medicineDetail
                          .forecast_points
                      }
                      dateKey="month_start"
                      historicalValueKey="quantity_dispensed"
                      forecastValueKey="forecast_quantity_dispensed"
                      lowerKey="lower_95"
                      upperKey="upper_95"
                      yUnitLabel="dispensed units"
                      ariaLabel="Dynamic historical and forecast medicine demand"
                    />


                    <div className="medicine-dss-heading">

                      <div>
                        <h3>
                          Resource Allocation
                          Decision Support
                        </h3>

                        <p>
                          The first displayed
                          forecast month is the
                          actual next calendar
                          month. Recommendation
                          requires current live
                          completed-month coverage
                          and an exact safe
                          inventory formulation
                          match.
                        </p>
                      </div>

                      <span
                        className={
                          medicineDetail
                            .recommendation
                            .status
                            === "AVAILABLE"
                            ? "medicine-dss-status medicine-dss-status-ready"
                            : "medicine-dss-status medicine-dss-status-withheld"
                        }
                      >
                        {
                          medicineDetail
                            .recommendation
                            .status
                            === "AVAILABLE"
                            ? "Recommendation Available"
                            : "Recommendation Withheld"
                        }
                      </span>

                    </div>


                    {
                      medicineDetail
                        .recommendation
                        .status
                        === "AVAILABLE"
                        ? (
                          <div className="medicine-dss-grid">

                            <div className="medicine-dss-card">
                              <span>
                                Forecast Month
                              </span>
                              <strong>
                                {
                                  medicineDetail
                                    .recommendation
                                    .forecast_month
                                }
                              </strong>
                            </div>

                            <div className="medicine-dss-card">
                              <span>
                                Forecast Demand
                              </span>
                              <strong>
                                {
                                  formatMetric(
                                    medicineDetail
                                      .recommendation
                                      .forecast_quantity,
                                    1
                                  )
                                }
                              </strong>
                              <small>
                                {
                                  medicineDetail
                                    .recommendation
                                    .dispensing_unit
                                    || "units"
                                }
                              </small>
                            </div>

                            <div className="medicine-dss-card">
                              <span>
                                Usable Current Stock
                              </span>
                              <strong>
                                {
                                  formatWhole(
                                    medicineDetail
                                      .recommendation
                                      .current_usable_stock
                                  )
                                }
                              </strong>
                            </div>

                            <div className="medicine-dss-card">
                              <span>
                                Safety Stock
                              </span>
                              <strong>
                                {
                                  formatWhole(
                                    medicineDetail
                                      .recommendation
                                      .safety_stock
                                  )
                                }
                              </strong>
                              <small>
                                reorder level
                              </small>
                            </div>

                            <div className="medicine-dss-card medicine-dss-card-primary">
                              <span>
                                Recommended Additional Stock
                              </span>
                              <strong>
                                {
                                  formatWhole(
                                    medicineDetail
                                      .recommendation
                                      .recommended_additional_stock
                                  )
                                }
                              </strong>
                              <small>
                                advisory whole units
                              </small>
                            </div>

                          </div>
                        )
                        : (
                          <div className="medicine-safety-guards">

                            {
                              medicineDetail
                                .recommendation
                                .withheld_reasons
                                .map(
                                  (
                                    reason,
                                    index
                                  ) => (
                                    <div
                                      className="medicine-inventory-match-warning"
                                      key={`${index}-${reason}`}
                                    >
                                      {reason}
                                    </div>
                                  )
                                )
                            }

                          </div>
                        )
                    }


                    <div className="medicine-dss-formula">
                      <span>
                        Advisory formula
                      </span>

                      <code>
                        {
                          medicineDetail
                            .recommendation
                            .formula
                        }
                      </code>

                      <p>
                        {
                          medicineDetail
                            .recommendation
                            .note
                        }
                      </p>
                    </div>


                    <div className="medicine-inventory-snapshot">

                      <div>
                        <span>
                          Inventory Match
                        </span>
                        <strong>
                          {
                            medicineDetail
                              .inventory
                              .matched
                              ? medicineDetail
                                  .inventory
                                  .inventory_name
                              : "No exact safe match"
                          }
                        </strong>
                      </div>

                      <div>
                        <span>
                          Match Strategy
                        </span>
                        <strong>
                          {
                            medicineDetail
                              .inventory
                              .match_strategy
                              || medicineDetail
                                .inventory
                                .match_status
                          }
                        </strong>
                      </div>

                      <div>
                        <span>
                          Inventory Code
                        </span>
                        <strong>
                          {
                            medicineDetail
                              .inventory
                              .inventory_code
                              || "-"
                          }
                        </strong>
                      </div>

                      <div>
                        <span>
                          Usable Current Stock
                        </span>
                        <strong>
                          {
                            formatWhole(
                              medicineDetail
                                .inventory
                                .usable_current_stock
                            )
                          }
                        </strong>
                      </div>

                    </div>


                    <div className="medicine-forecast-summary-row">
                      <span>
                        Dynamic 6-month horizon:
                      </span>

                      <strong>
                        {
                          medicineDetail
                            .forecast_points[0]
                            ?.month_start
                        }{" "}
                        to{" "}
                        {
                          medicineDetail
                            .forecast_points[
                              medicineDetail
                                .forecast_points
                                .length - 1
                            ]
                            ?.month_start
                        }
                        {" · "}
                        {
                          formatWhole(
                            medicineDetail
                              .cumulative_6_month_forecast
                          )
                        }{" "}
                        forecast units
                      </strong>
                    </div>


                    <div className="disease-forecast-table-wrap">
                      <table className="disease-forecast-table">
                        <thead>
                          <tr>
                            <th>Forecast Month</th>
                            <th>Demand</th>
                            <th>Lower 95%</th>
                            <th>Upper 95%</th>
                          </tr>
                        </thead>

                        <tbody>
                          {
                            medicineDetail
                              .forecast_points
                              .map(
                                (item) => (
                                  <tr
                                    key={
                                      item
                                        .month_start
                                    }
                                  >
                                    <td>
                                      {item.month_start}
                                    </td>
                                    <td>
                                      {
                                        formatMetric(
                                          item
                                            .forecast_quantity_dispensed,
                                          1
                                        )
                                      }
                                    </td>
                                    <td>
                                      {
                                        formatMetric(
                                          item.lower_95,
                                          1
                                        )
                                      }
                                    </td>
                                    <td>
                                      {
                                        formatMetric(
                                          item.upper_95,
                                          1
                                        )
                                      }
                                    </td>
                                  </tr>
                                )
                              )
                          }
                        </tbody>
                      </table>
                    </div>

                  </>
                )
                : (
                  <div className="forecast-placeholder">
                    No medicine forecast data available.
                  </div>
                )
        }

      </section>

    </div>
  );
}


export default Forecasts;
