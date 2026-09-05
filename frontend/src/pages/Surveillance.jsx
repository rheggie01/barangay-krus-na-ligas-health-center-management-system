import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getDiseaseCaseCounts,
  getDiseaseCasesByStreet,
  getWeeklyDiseaseComparison,
} from "../api/surveillanceApi";

import {
  getActiveDiseases,
} from "../api/diseaseApi";

import SurveillanceMap from "../components/SurveillanceMap";

import {
  useAuth,
} from "../context/AuthContext";

import {
  hasPermission,
} from "../utils/permissions";

import "../styles/Surveillance.css";


// =========================================================
// FILTER CONSTANTS
// =========================================================

const FILTERS = {
  ALL: "ALL",
  TODAY: "TODAY",
  WEEK: "WEEK",
  MONTH: "MONTH",
  CUSTOM: "CUSTOM",
};


const SURVEILLANCE_SCOPES = {
  GENERAL: "GENERAL",
  SENSITIVE: "SENSITIVE",
};


// =========================================================
// QUICK FILTERS
// =========================================================

const QUICK_FILTERS = [
  {
    id: FILTERS.ALL,
    label: "All Time",
  },
  {
    id: FILTERS.TODAY,
    label: "Today",
  },
  {
    id: FILTERS.WEEK,
    label: "This Week",
  },
  {
    id: FILTERS.MONTH,
    label: "This Month",
  },
];


// =========================================================
// DATE HELPERS
// =========================================================

function toDateInput(
  value
) {
  const year =
    value.getFullYear();

  const month =
    String(
      value.getMonth() + 1
    ).padStart(
      2,
      "0"
    );

  const day =
    String(
      value.getDate()
    ).padStart(
      2,
      "0"
    );

  return `${year}-${month}-${day}`;
}


function getQuickFilterDates(
  filter
) {
  const today =
    new Date();


  // TODAY

  if (
    filter ===
    FILTERS.TODAY
  ) {
    const date =
      toDateInput(
        today
      );

    return {
      startDate: date,
      endDate: date,
    };
  }


  // THIS WEEK

  if (
    filter ===
    FILTERS.WEEK
  ) {
    const start =
      new Date(
        today
      );

    const weekday =
      start.getDay();

    const mondayOffset =
      weekday === 0
        ? -6
        : 1 - weekday;

    start.setDate(
      start.getDate() +
        mondayOffset
    );


    const end =
      new Date(
        start
      );

    end.setDate(
      end.getDate() + 6
    );


    return {
      startDate:
        toDateInput(
          start
        ),

      endDate:
        toDateInput(
          end
        ),
    };
  }


  // THIS MONTH

  if (
    filter ===
    FILTERS.MONTH
  ) {
    const start =
      new Date(
        today.getFullYear(),
        today.getMonth(),
        1
      );

    const end =
      new Date(
        today.getFullYear(),
        today.getMonth() + 1,
        0
      );


    return {
      startDate:
        toDateInput(
          start
        ),

      endDate:
        toDateInput(
          end
        ),
    };
  }


  // ALL TIME

  return {
    startDate: "",
    endDate: "",
  };
}


// =========================================================
// GENERAL HELPERS
// =========================================================

function safeArray(
  value
) {
  return Array.isArray(
    value
  )
    ? value
    : [];
}


function getApiErrorMessage(
  error,
  fallback
) {
  const detail =
    error.response?.data?.detail;


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
          item.msg ||
          String(
            item
          )
      )
      .join(
        ", "
      );
  }


  return fallback;
}


// =========================================================
// SURVEILLANCE PAGE
// =========================================================

function Surveillance() {

  const {
    user,
  } = useAuth();


  const canViewSensitiveDiseases =
    hasPermission(
      user?.permissions || [],
      "SENSITIVE_DISEASE_VIEW"
    );


  const [
    surveillanceScope,
    setSurveillanceScope,
  ] = useState(
    SURVEILLANCE_SCOPES.GENERAL
  );


  // =======================================================
  // MASTER DATA
  // =======================================================

  const [
    diseases,
    setDiseases,
  ] = useState([]);


  // =======================================================
  // SURVEILLANCE DATA
  // =======================================================

  const [
    diseaseCases,
    setDiseaseCases,
  ] = useState([]);


  const [
    streetCases,
    setStreetCases,
  ] = useState([]);


  const [
    weeklyComparison,
    setWeeklyComparison,
  ] = useState([]);


  // =======================================================
  // FILTER STATE
  // =======================================================

  const [
    startDate,
    setStartDate,
  ] = useState("");


  const [
    endDate,
    setEndDate,
  ] = useState("");


  const [
    activeFilter,
    setActiveFilter,
  ] = useState(
    FILTERS.ALL
  );


  const [
    selectedDiseaseId,
    setSelectedDiseaseId,
  ] = useState("");


  // =======================================================
  // UI STATE
  // =======================================================

  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    refreshing,
    setRefreshing,
  ] = useState(false);


  const [
    diseasesLoading,
    setDiseasesLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  // =======================================================
  // LOAD ACTIVE DISEASE MASTER LIST
  // =======================================================

  const loadDiseases =
    async () => {

      try {

        setDiseasesLoading(
          true
        );


        const data =
          await getActiveDiseases();


        setDiseases(
          safeArray(
            data
          )
        );


      } catch (err) {

        console.error(
          "Unable to load diseases:",
          err
        );


        setError(
          getApiErrorMessage(
            err,
            "Unable to load the disease list."
          )
        );


      } finally {

        setDiseasesLoading(
          false
        );

      }
    };


  // =======================================================
  // LOAD SURVEILLANCE DATA
  // =======================================================

  const loadSurveillance =
    async (
      from = "",
      to = "",
      diseaseId = "",
      scope = SURVEILLANCE_SCOPES.GENERAL,
      preserveCurrentData = true
    ) => {

      try {

        if (
          preserveCurrentData
        ) {
          setRefreshing(
            true
          );

        } else {
          setLoading(
            true
          );
        }


        setError(
          ""
        );


        const [
          diseaseData,
          streetData,
          weeklyData,
        ] =
          await Promise.all([

            getDiseaseCaseCounts(
              from,
              to,
              scope
            ),

            scope ===
              SURVEILLANCE_SCOPES.SENSITIVE
              ? Promise.resolve([])
              : getDiseaseCasesByStreet(
                  from,
                  to,
                  diseaseId || null,
                  scope
                ),

            getWeeklyDiseaseComparison(
              scope
            ),

          ]);


        setDiseaseCases(
          safeArray(
            diseaseData
          )
        );


        setStreetCases(
          safeArray(
            streetData
          )
        );


        setWeeklyComparison(
          safeArray(
            weeklyData
          )
        );


      } catch (err) {

        console.error(
          "Unable to load surveillance data:",
          err
        );


        setError(
          getApiErrorMessage(
            err,
            "Unable to load surveillance data."
          )
        );


      } finally {

        setLoading(
          false
        );

        setRefreshing(
          false
        );

      }
    };


  // =======================================================
  // INITIAL LOAD
  // =======================================================

  useEffect(
    () => {

      loadDiseases();

      loadSurveillance(
        "",
        "",
        "",
        SURVEILLANCE_SCOPES.GENERAL,
        false
      );

    },
    [
      canViewSensitiveDiseases,
    ]
  );


  // =======================================================
  // QUICK DATE FILTER
  // =======================================================

  const handleQuickFilter =
    async (
      filter
    ) => {

      const dates =
        getQuickFilterDates(
          filter
        );


      setActiveFilter(
        filter
      );


      setStartDate(
        dates.startDate
      );


      setEndDate(
        dates.endDate
      );


      await loadSurveillance(
        dates.startDate,
        dates.endDate,
        selectedDiseaseId,
        surveillanceScope
      );
    };


  // =======================================================
  // CUSTOM DATE FILTER
  // =======================================================

  const handleApplyFilter =
    async (
      event
    ) => {

      event.preventDefault();


      setError(
        ""
      );


      if (
        startDate &&
        endDate &&
        startDate >
          endDate
      ) {

        setError(
          "The From date cannot be later than the To date."
        );

        return;
      }


      setActiveFilter(
        FILTERS.CUSTOM
      );


      await loadSurveillance(
        startDate,
        endDate,
        selectedDiseaseId,
        surveillanceScope
      );
    };


  // =======================================================
  // CLEAR DATE FILTER
  // =======================================================

  const handleClearFilter =
    async () => {

      setStartDate(
        ""
      );

      setEndDate(
        ""
      );

      setActiveFilter(
        FILTERS.ALL
      );


      await loadSurveillance(
        "",
        "",
        selectedDiseaseId,
        surveillanceScope
      );
    };


  // =======================================================
  // DISEASE OPTIONS
  // =======================================================

  const diseaseOptions =
    useMemo(
      () =>
        diseases
          .map(
            (
              disease
            ) => ({
              id:
                disease.id,

              code:
                disease.code,

              name:
                disease.name,

              isSensitive:
                Boolean(
                  disease.is_sensitive
                ),

              privacyCategory:
                disease.privacy_category ||
                "STANDARD",
            })
          )
          .filter(
            (
              disease
            ) =>
              disease.id != null
          )
          .sort(
            (
              a,
              b
            ) =>
              a.name.localeCompare(
                b.name
              )
          ),
      [
        diseases,
      ]
    );


  // =======================================================
  // STANDARD DISEASES
  // =======================================================

  const standardDiseases =
    useMemo(
      () =>
        diseaseOptions.filter(
          (
            disease
          ) =>
            !disease.isSensitive
        ),
      [
        diseaseOptions,
      ]
    );


  // =======================================================
  // SENSITIVE DISEASES
  // =======================================================

  const sensitiveDiseases =
    useMemo(
      () =>
        diseaseOptions.filter(
          (
            disease
          ) =>
            disease.isSensitive
        ),
      [
        diseaseOptions,
      ]
    );


  // =======================================================
  // VISIBLE DISEASE OPTIONS
  // =======================================================

  const visibleDiseaseOptions =
    useMemo(
      () =>
        surveillanceScope ===
          SURVEILLANCE_SCOPES.SENSITIVE
          ? sensitiveDiseases
          : standardDiseases,
      [
        surveillanceScope,
        sensitiveDiseases,
        standardDiseases,
      ]
    );


  // =======================================================
  // SELECTED DISEASE
  // =======================================================

  const selectedDisease =
    useMemo(
      () =>
        diseaseOptions.find(
          (
            disease
          ) =>
            String(
              disease.id
            ) ===
            String(
              selectedDiseaseId
            )
        ) || null,
      [
        diseaseOptions,
        selectedDiseaseId,
      ]
    );


  // =======================================================
  // DISEASE FILTER
  // =======================================================

  const handleDiseaseChange =
    async (
      event
    ) => {

      const value =
        event.target.value;


      setSelectedDiseaseId(
        value
      );


      await loadSurveillance(
        startDate,
        endDate,
        value,
        surveillanceScope
      );
    };


  // =======================================================
  // SURVEILLANCE SCOPE
  // =======================================================

  const handleScopeChange =
    async (
      nextScope
    ) => {

      if (
        nextScope ===
          surveillanceScope
      ) {
        return;
      }


      if (
        nextScope ===
          SURVEILLANCE_SCOPES.SENSITIVE &&
        !canViewSensitiveDiseases
      ) {
        return;
      }


      setSurveillanceScope(
        nextScope
      );

      setSelectedDiseaseId(
        ""
      );


      await loadSurveillance(
        startDate,
        endDate,
        "",
        nextScope,
        false
      );
    };


  // =======================================================
  // TOTAL CASES
  // =======================================================

  const totalCases =
    useMemo(
      () =>
        diseaseCases.reduce(
          (
            total,
            disease
          ) =>
            total +
            Number(
              disease.case_count ||
                0
            ),
          0
        ),
      [
        diseaseCases,
      ]
    );


  // =======================================================
  // DISEASES WITH CASES
  // =======================================================

  const diseasesWithCases =
    useMemo(
      () =>
        diseaseCases.filter(
          (
            disease
          ) =>
            Number(
              disease.case_count ||
                0
            ) > 0
        ).length,
      [
        diseaseCases,
      ]
    );


  // =======================================================
  // HIGHEST CASE DISEASE
  // =======================================================

  const highestCaseDisease =
    useMemo(
      () =>
        diseaseCases.reduce(
          (
            highest,
            current
          ) => {

            if (
              !highest
            ) {
              return current;
            }


            return Number(
              current.case_count ||
                0
            ) >
              Number(
                highest.case_count ||
                  0
              )
              ? current
              : highest;

          },
          null
        ),
      [
        diseaseCases,
      ]
    );


  // =======================================================
  // UNIQUE STREETS
  // =======================================================

  const uniqueStreets =
    useMemo(
      () => {

        const streets =
          streetCases
            .map(
              (
                item
              ) =>
                item.street?.trim()
            )
            .filter(
              (
                street
              ) =>
                street &&
                street
                  .toLowerCase() !==
                  "unknown"
            );


        return new Set(
          streets
        ).size;

      },
      [
        streetCases,
      ]
    );


  // =======================================================
  // STREET HOTSPOTS
  // =======================================================

  const streetHotspots =
    useMemo(
      () => {

        const grouped =
          new Map();


        for (
          const item
          of streetCases
        ) {

          const street =
            item.street?.trim();


          if (
            !street ||
            street
              .toLowerCase() ===
              "unknown"
          ) {
            continue;
          }


          const count =
            Number(
              item.case_count ||
                0
            );


          if (
            !grouped.has(
              street
            )
          ) {

            grouped.set(
              street,
              {
                street,
                caseCount: 0,
                diseases: [],
              }
            );

          }


          const hotspot =
            grouped.get(
              street
            );


          hotspot.caseCount +=
            count;


          hotspot.diseases.push(
            {
              name:
                item.name,

              code:
                item.code,

              count,
            }
          );

        }


        return Array.from(
          grouped.values()
        )
          .sort(
            (
              a,
              b
            ) =>
              b.caseCount -
              a.caseCount
          )
          .slice(
            0,
            5
          );

      },
      [
        streetCases,
      ]
    );


  // =======================================================
  // PERIOD LABEL
  // =======================================================

  const periodLabel =
    useMemo(
      () => {

        if (
          activeFilter ===
          FILTERS.TODAY
        ) {
          return "Today";
        }


        if (
          activeFilter ===
          FILTERS.WEEK
        ) {
          return "This Week";
        }


        if (
          activeFilter ===
          FILTERS.MONTH
        ) {
          return "This Month";
        }


        if (
          activeFilter ===
          FILTERS.CUSTOM
        ) {

          if (
            startDate &&
            endDate
          ) {
            return (
              `${startDate} to ${endDate}`
            );
          }


          if (
            startDate
          ) {
            return (
              `From ${startDate}`
            );
          }


          if (
            endDate
          ) {
            return (
              `Until ${endDate}`
            );
          }

        }


        return "All Time";

      },
      [
        activeFilter,
        startDate,
        endDate,
      ]
    );


  const isBusy =
    loading ||
    refreshing;


  // =======================================================
  // PAGE
  // =======================================================

  return (
    <div className="surveillance-page">


      {/* ===================================================
          HEADER
      ==================================================== */}

      <header className="surveillance-page-header">

        <div>

          <h1>
            Disease Surveillance
          </h1>

          <p>
            Monitor validated disease
            cases, geographic distribution,
            street hotspots, and weekly
            trends.
          </p>

        </div>

      </header>


      {/* ===================================================
          ERROR
      ==================================================== */}

      {error && (
        <div className="app-message app-message-error surveillance-message">

          {error}

        </div>
      )}


      {refreshing && (

        <div
          className="surveillance-refresh-indicator"
          role="status"
          aria-live="polite"
        >

          <span className="surveillance-refresh-dot" />

          Updating surveillance data...

        </div>

      )}


      {/* ===================================================
          SURVEILLANCE SCOPE
      ==================================================== */}

      <section className="surveillance-card surveillance-scope-card">

        <CardHeader
          title="Surveillance View"
          description="General disease monitoring is separated from restricted sensitive/program surveillance."
        />


        <div className="surveillance-scope-switch">

          <button
            type="button"
            aria-pressed={
              surveillanceScope ===
              SURVEILLANCE_SCOPES.GENERAL
            }
            title={
              surveillanceScope ===
                SURVEILLANCE_SCOPES.GENERAL
                ? "General Surveillance is already selected"
                : "Open General Surveillance"
            }
            className={
              surveillanceScope ===
                SURVEILLANCE_SCOPES.GENERAL
                ? "surveillance-scope-button active"
                : "surveillance-scope-button"
            }
            onClick={
              () =>
                handleScopeChange(
                  SURVEILLANCE_SCOPES.GENERAL
                )
            }
            disabled={
              isBusy
            }
          >
            <strong>
              General Surveillance
            </strong>

            <span>
              Standard validated disease counts,
              maps, streets, and hotspots.
            </span>
          </button>


          {canViewSensitiveDiseases && (

            <button
              type="button"
              aria-pressed={
                surveillanceScope ===
                SURVEILLANCE_SCOPES.SENSITIVE
              }
              title={
                surveillanceScope ===
                  SURVEILLANCE_SCOPES.SENSITIVE
                  ? "Sensitive / Program Surveillance is already selected"
                  : "Open Sensitive / Program Surveillance"
              }
              className={
                surveillanceScope ===
                  SURVEILLANCE_SCOPES.SENSITIVE
                  ? "surveillance-scope-button surveillance-scope-button-sensitive active"
                  : "surveillance-scope-button surveillance-scope-button-sensitive"
              }
              onClick={
                () =>
                  handleScopeChange(
                    SURVEILLANCE_SCOPES.SENSITIVE
                  )
              }
              disabled={
                isBusy
              }
            >
              <strong>
                Sensitive / Program Surveillance
              </strong>

              <span>
                Restricted aggregate TB, HIV,
                and STI surveillance.
              </span>
            </button>

          )}

        </div>


        {surveillanceScope ===
          SURVEILLANCE_SCOPES.SENSITIVE && (

          <div className="surveillance-sensitive-mode-notice">

            <strong>
              Restricted aggregate view
            </strong>

            <span>
              Street-level maps, patient locations,
              and hotspot tables are intentionally
              disabled for sensitive/program disease data.
            </span>

          </div>

        )}

      </section>


      {/* ===================================================
          QUICK FILTERS
      ==================================================== */}

      <section className="surveillance-card">

        <CardHeader
          title="Quick Filters"
          description="Select a predefined period to review recorded cases."
        />


        <div className="quick-filter-grid">

          {QUICK_FILTERS.map(
            (
              filter
            ) => (

              <button
                key={
                  filter.id
                }
                type="button"
                className={
                  activeFilter ===
                  filter.id
                    ? "quick-filter-button active"
                    : "quick-filter-button"
                }
                onClick={
                  () =>
                    handleQuickFilter(
                      filter.id
                    )
                }
                disabled={
                  loading
                }
              >

                {
                  filter.label
                }

              </button>

            )
          )}

        </div>

      </section>


      {/* ===================================================
          CUSTOM DATE RANGE
      ==================================================== */}

      <section className="surveillance-card">

        <CardHeader
          title="Custom Date Range"
          description="Select a specific period for the surveillance report."
        />


        <form
          className="surveillance-filter-form"
          onSubmit={
            handleApplyFilter
          }
        >

          <div className="surveillance-date-grid">


            <DateField
              id="start_date"
              label="From"
              value={
                startDate
              }
              onChange={
                (
                  value
                ) => {

                  setStartDate(
                    value
                  );

                  setActiveFilter(
                    FILTERS.CUSTOM
                  );

                }
              }
            />


            <DateField
              id="end_date"
              label="To"
              value={
                endDate
              }
              onChange={
                (
                  value
                ) => {

                  setEndDate(
                    value
                  );

                  setActiveFilter(
                    FILTERS.CUSTOM
                  );

                }
              }
            />


          </div>


          <div className="app-button-group surveillance-filter-actions">

            <button
              type="submit"
              className="app-button app-button-primary"
              disabled={
                isBusy
              }
            >

              {isBusy
                ? "Applying..."
                : "Apply Filter"}

            </button>


            <button
              type="button"
              className="app-button app-button-secondary"
              onClick={
                handleClearFilter
              }
              disabled={
                isBusy
              }
            >

              Clear

            </button>

          </div>

        </form>

      </section>


      {/* ===================================================
          SUMMARY
      ==================================================== */}

      <section className="surveillance-card">

        <CardHeader
          title="Surveillance Summary"
          description={
            `Period: ${periodLabel}`
          }
        />


        <div className="surveillance-summary-grid">


          <SummaryCard
            label="Total Validated Cases"
            value={
              totalCases
            }
          />


          <SummaryCard
            label="Diseases With Cases"
            value={
              diseasesWithCases
            }
          />


          <SummaryCard
            label={
              surveillanceScope ===
                SURVEILLANCE_SCOPES.SENSITIVE
                ? "Location Detail"
                : "Streets With Cases"
            }
            value={
              surveillanceScope ===
                SURVEILLANCE_SCOPES.SENSITIVE
                ? "Restricted"
                : uniqueStreets
            }
            subtitle={
              surveillanceScope ===
                SURVEILLANCE_SCOPES.SENSITIVE
                ? "Street-level mapping disabled"
                : undefined
            }
          />


          <SummaryCard
            label="Highest Case Count"
            value={
              highestCaseDisease
                ? highestCaseDisease
                    .case_count
                : 0
            }
            subtitle={
              highestCaseDisease &&
              Number(
                highestCaseDisease
                  .case_count ||
                  0
              ) > 0
                ? highestCaseDisease
                    .name
                : "No recorded cases"
            }
          />


        </div>

      </section>


      {/* ===================================================
          DISEASE FILTER
      ==================================================== */}

      <section className="surveillance-card">

        <CardHeader
          title="Disease Filter"
          description={
            surveillanceScope ===
              SURVEILLANCE_SCOPES.SENSITIVE
              ? "Select a restricted disease to review aggregate validated counts and weekly trends."
              : "Select a disease to focus the outbreak map, street distribution, and hotspot analysis."
          }
        />


        <div className="surveillance-disease-filter">


          <div className="surveillance-field">

            <label htmlFor="disease_filter">
              Disease
            </label>


            <select
              id="disease_filter"
              value={
                selectedDiseaseId
              }
              onChange={
                handleDiseaseChange
              }
              disabled={
                isBusy ||
                diseasesLoading
              }
            >

              <option value="">
                {surveillanceScope ===
                  SURVEILLANCE_SCOPES.SENSITIVE
                  ? "All Sensitive / Program Diseases"
                  : "All General Diseases"}
              </option>


              {visibleDiseaseOptions.map(
                (
                  disease
                ) => (

                  <option
                    key={
                      disease.id
                    }
                    value={
                      disease.id
                    }
                  >
                    {disease.code}
                    {" - "}
                    {disease.name}
                  </option>

                )
              )}


            </select>

          </div>


          <div className="surveillance-filter-status">

            <span>
              Showing
            </span>

            <strong>

              {selectedDisease
                ? `${selectedDisease.code} - ${selectedDisease.name}`
                : surveillanceScope ===
                    SURVEILLANCE_SCOPES.SENSITIVE
                  ? "All Sensitive / Program Diseases"
                  : "All General Diseases"}

            </strong>


            {selectedDisease
              ?.isSensitive && (

              <small>
                Sensitive health information
              </small>

            )}

          </div>


        </div>

      </section>


      {/* ===================================================
          OUTBREAK MAP / SENSITIVE PRIVACY GUARD
      ==================================================== */}

      <section className="surveillance-card">

        {surveillanceScope ===
          SURVEILLANCE_SCOPES.SENSITIVE ? (

          <>
            <CardHeader
              title="Sensitive Location Privacy"
              description="Geographic drill-down is intentionally unavailable for restricted program surveillance."
            />

            <div className="surveillance-sensitive-location-guard">

              <div className="surveillance-sensitive-location-icon">
                🔒
              </div>

              <div>
                <strong>
                  Street-level mapping is disabled
                </strong>

                <p>
                  Sensitive TB, HIV, and STI records are
                  shown only as authorized aggregate disease
                  counts and weekly trends. No street hotspot
                  or patient-location visualization is rendered.
                </p>
              </div>

            </div>
          </>

        ) : (

          <>
            <CardHeader
              title="Disease Outbreak Map"
              description={
                selectedDisease
                  ? `Street-level distribution of ${selectedDisease.name} cases in Krus na Ligas.`
                  : "Street-level distribution of validated disease cases in Krus na Ligas."
              }
            />

            <div className="surveillance-map-privacy-note">
              Map markers represent aggregated
              street-level disease cases and
              do not show individual patient
              home locations.
            </div>

            {loading ? (
              <EmptyState>
                Loading outbreak map...
              </EmptyState>
            ) : streetCases.length === 0 ? (
              <EmptyState>
                No street-level disease data
                available for the selected filters.
              </EmptyState>
            ) : (
              <SurveillanceMap
                streetCases={streetCases}
              />
            )}
          </>

        )}

      </section>


      {/* ===================================================
          DISEASE CASES
      ==================================================== */}

      <section className="surveillance-card">

        <CardHeader
          title="Disease Cases"
          description="Validated surveillance cases grouped by disease."
        />


        {loading ? (

          <EmptyState>
            Loading surveillance data...
          </EmptyState>

        ) : diseaseCases.length ===
          0 ? (

          <EmptyState>
            No disease data available.
          </EmptyState>

        ) : (

          <div className="surveillance-table-wrap">

            <table className="surveillance-table">

              <thead>

                <tr>
                  <th>
                    Code
                  </th>

                  <th>
                    Disease
                  </th>

                  <th>
                    Cases
                  </th>

                  <th>
                    Status
                  </th>
                </tr>

              </thead>


              <tbody>

                {diseaseCases.map(
                  (
                    disease
                  ) => {

                    const caseCount =
                      Number(
                        disease.case_count ||
                          0
                      );


                    return (

                      <tr
                        key={
                          disease.disease_id
                        }
                      >

                        <td>

                          <span className="surveillance-code">

                            {
                              disease.code
                            }

                          </span>

                        </td>


                        <td>

                          <strong>

                            {
                              disease.name
                            }

                          </strong>

                        </td>


                        <td>

                          <span className="surveillance-case-count">

                            {
                              caseCount
                            }

                          </span>

                        </td>


                        <td>

                          <span
                            className={
                              caseCount > 0
                                ? "surveillance-status surveillance-status-recorded"
                                : "surveillance-status surveillance-status-none"
                            }
                          >

                            {caseCount > 0
                              ? "VALIDATED"
                              : "NO CASES"}

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


      {/* ===================================================
          WEEKLY DISEASE TREND
      ==================================================== */}

      <section className="surveillance-card">

        <CardHeader
          title="Weekly Disease Trend"
          description="Current week compared with the previous week."
        />


        {loading ? (

          <EmptyState>
            Loading weekly trend...
          </EmptyState>

        ) : weeklyComparison.length ===
          0 ? (

          <EmptyState>
            No weekly comparison data
            available.
          </EmptyState>

        ) : (

          <div className="surveillance-table-wrap">

            <table className="surveillance-table">

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
                    Difference
                  </th>

                  <th>
                    Trend
                  </th>

                </tr>

              </thead>


              <tbody>

                {weeklyComparison.map(
                  (
                    item
                  ) => (

                    <tr
                      key={
                        item.disease_id
                      }
                    >

                      <td>

                        <strong>

                          {
                            item.name
                          }

                        </strong>

                      </td>


                      <td>

                        {
                          item.current_week_cases
                        }

                      </td>


                      <td>

                        {
                          item.previous_week_cases
                        }

                      </td>


                      <td>

                        {Number(
                          item.difference
                        ) > 0
                          ? "+"
                          : ""}

                        {
                          item.difference
                        }

                      </td>


                      <td>

                        {
                          item.trend
                        }

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>


      {/* ===================================================
          CASES BY STREET
      ==================================================== */}

      {surveillanceScope ===
        SURVEILLANCE_SCOPES.GENERAL && (

      <section className="surveillance-card">

        <CardHeader
          title="Cases by Street"
          description={
            selectedDisease
              ? `${selectedDisease.name} cases grouped by patient street.`
              : "Validated disease cases grouped by patient street."
          }
        />


        {loading ? (

          <EmptyState>
            Loading street surveillance
            data...
          </EmptyState>

        ) : streetCases.length ===
          0 ? (

          <EmptyState>
            No street-level disease data
            available for the selected
            filters.
          </EmptyState>

        ) : (

          <div className="surveillance-table-wrap">

            <table className="surveillance-table">

              <thead>

                <tr>

                  <th>
                    Street
                  </th>

                  <th>
                    Code
                  </th>

                  <th>
                    Disease
                  </th>

                  <th>
                    Cases
                  </th>

                </tr>

              </thead>


              <tbody>

                {streetCases.map(
                  (
                    item
                  ) => (

                    <tr
                      key={
                        `${item.street}-${item.disease_id}`
                      }
                    >

                      <td>

                        <strong>

                          {
                            item.street ||
                            "Unknown"
                          }

                        </strong>

                      </td>


                      <td>

                        <span className="surveillance-code">

                          {
                            item.code
                          }

                        </span>

                      </td>


                      <td>

                        {
                          item.name
                        }

                      </td>


                      <td>

                        <span className="surveillance-case-count">

                          {
                            Number(
                              item.case_count ||
                                0
                            )
                          }

                        </span>

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>

      )}


      {/* ===================================================
          STREET HOTSPOTS
      ==================================================== */}

      {surveillanceScope ===
        SURVEILLANCE_SCOPES.GENERAL && (

      <section className="surveillance-card">

        <CardHeader
          title="Street Hotspots"
          description={
            selectedDisease
              ? `Streets with the highest number of ${selectedDisease.name} cases.`
              : "Streets with the highest number of validated disease cases."
          }
        />


        {loading ? (

          <EmptyState>
            Loading hotspot data...
          </EmptyState>

        ) : streetHotspots.length ===
          0 ? (

          <EmptyState>
            No mapped street hotspot data
            is available for the selected
            filters.
          </EmptyState>

        ) : (

          <div className="surveillance-hotspot-list">

            {streetHotspots.map(
              (
                hotspot,
                index
              ) => (

                <div
                  key={
                    hotspot.street
                  }
                  className="surveillance-hotspot-item"
                >


                  <div className="surveillance-hotspot-rank">

                    {
                      index + 1
                    }

                  </div>


                  <div className="surveillance-hotspot-info">

                    <strong>

                      {
                        hotspot.street
                      }

                    </strong>


                    <span>

                      {hotspot.diseases
                        .map(
                          (
                            disease
                          ) =>
                            disease.name
                        )
                        .join(
                          ", "
                        )}

                    </span>

                  </div>


                  <div className="surveillance-hotspot-count">

                    {
                      hotspot.caseCount
                    }

                  </div>


                </div>

              )
            )}

          </div>

        )}

      </section>

      )}


    </div>
  );
}


// =========================================================
// CARD HEADER
// =========================================================

function CardHeader({
  title,
  description,
}) {
  return (
    <div className="surveillance-card-header">

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


// =========================================================
// SUMMARY CARD
// =========================================================

function SummaryCard({
  label,
  value,
  subtitle = "",
}) {
  return (
    <div className="surveillance-summary-card">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      {subtitle && (

        <small>
          {subtitle}
        </small>

      )}

    </div>
  );
}


// =========================================================
// DATE FIELD
// =========================================================

function DateField({
  id,
  label,
  value,
  onChange,
}) {
  return (
    <div className="surveillance-field">

      <label
        htmlFor={
          id
        }
      >
        {label}
      </label>


      <input
        id={
          id
        }
        type="date"
        value={
          value
        }
        onChange={
          (
            event
          ) =>
            onChange(
              event.target.value
            )
        }
      />

    </div>
  );
}


// =========================================================
// EMPTY STATE
// =========================================================

function EmptyState({
  children,
}) {
  return (
    <div className="surveillance-empty">

      {children}

    </div>
  );
}


export default Surveillance;