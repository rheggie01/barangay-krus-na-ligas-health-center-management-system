import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "../styles/SurveillanceMap.css";


// =========================================================
// KRUS NA LIGAS MAP BOUNDS
// =========================================================
//
// These bounds are intentionally a little wider so the
// complete street network can be seen on initial load.
//

const KRUS_NA_LIGAS_BOUNDS = [
  [
    14.6398,
    121.0578,
  ],
  [
    14.6502,
    121.0702,
  ],
];


// =========================================================
// STREET REFERENCE COORDINATES
// =========================================================
//
// Street-level reference points only.
// These are NOT patient/home coordinates.
//

const STREET_COORDINATES = {
  "Angeles St.": [
    14.64490,
    121.06270,
  ],

  "Baluyot St.": [
    14.64610,
    121.06300,
  ],

  "C.P. Garcia": [
    14.64770,
    121.06480,
  ],

  "E. Ramos St.": [
    14.64365,
    121.06475,
  ],

  "Eugenio St.": [
    14.64555,
    121.06330,
  ],

  "Fernando St.": [
    14.64415,
    121.06465,
  ],

  "Flores St.": [
    14.64360,
    121.06420,
  ],

  "Gonzales St.": [
    14.64455,
    121.06535,
  ],

  "Kabaitan": [
    14.64565,
    121.06295,
  ],

  "Maginhawa": [
    14.64510,
    121.06610,
  ],

  "M. Dela Cruz St.": [
    14.64395,
    121.06385,
  ],

  "Manansala St.": [
    14.64475,
    121.06425,
  ],

  "P. Francisco St.": [
    14.64465,
    121.06480,
  ],

  "Panginiban": [
    14.64580,
    121.06430,
  ],

  "Salvador St.": [
    14.64515,
    121.06320,
  ],

  "Santos St.": [
    14.64495,
    121.06365,
  ],

  "T. Fulgencio St.": [
    14.64375,
    121.06445,
  ],

  "Tiburcio St.": [
    14.64425,
    121.06510,
  ],

  "Tiburcio Ext.": [
    14.64390,
    121.06550,
  ],

  "V. Francisco St.": [
    14.64465,
    121.06290,
  ],
};


// =========================================================
// STREET ALIASES
// =========================================================

const STREET_ALIASES = {
  angeles: "Angeles St.",
  "angeles st": "Angeles St.",
  "angeles st.": "Angeles St.",

  baluyot: "Baluyot St.",
  "baluyot st": "Baluyot St.",
  "baluyot st.": "Baluyot St.",

  "cp garcia": "C.P. Garcia",
  "c.p. garcia": "C.P. Garcia",

  "e ramos": "E. Ramos St.",
  "e. ramos": "E. Ramos St.",
  "e ramos st": "E. Ramos St.",
  "e. ramos st.": "E. Ramos St.",

  eugenio: "Eugenio St.",
  "eugenio st": "Eugenio St.",
  "eugenio st.": "Eugenio St.",

  fernando: "Fernando St.",
  "fernando st": "Fernando St.",
  "fernando st.": "Fernando St.",

  flores: "Flores St.",
  "flores st": "Flores St.",
  "flores st.": "Flores St.",

  gonzales: "Gonzales St.",
  "gonzales st": "Gonzales St.",
  "gonzales st.": "Gonzales St.",

  kabaitan: "Kabaitan",

  maginhawa: "Maginhawa",
  "maginhawa st": "Maginhawa",
  "maginhawa st.": "Maginhawa",

  "m dela cruz": "M. Dela Cruz St.",
  "m. dela cruz": "M. Dela Cruz St.",
  "m dela cruz st": "M. Dela Cruz St.",
  "m. dela cruz st.": "M. Dela Cruz St.",

  manansala: "Manansala St.",
  "manansala st": "Manansala St.",
  "manansala st.": "Manansala St.",

  "p francisco": "P. Francisco St.",
  "p. francisco": "P. Francisco St.",
  "p francisco st": "P. Francisco St.",
  "p. francisco st.": "P. Francisco St.",

  panginiban: "Panginiban",

  salvador: "Salvador St.",
  "salvador st": "Salvador St.",
  "salvador st.": "Salvador St.",

  santos: "Santos St.",
  "santos st": "Santos St.",
  "santos st.": "Santos St.",

  "t fulgencio": "T. Fulgencio St.",
  "t. fulgencio": "T. Fulgencio St.",
  "t fulgencio st": "T. Fulgencio St.",
  "t. fulgencio st.": "T. Fulgencio St.",

  tiburcio: "Tiburcio St.",
  "tiburcio st": "Tiburcio St.",
  "tiburcio st.": "Tiburcio St.",

  "tiburcio ext": "Tiburcio Ext.",
  "tiburcio ext.": "Tiburcio Ext.",

  "v francisco": "V. Francisco St.",
  "v. francisco": "V. Francisco St.",
  "v francisco st": "V. Francisco St.",
  "v. francisco st.": "V. Francisco St.",
};


// =========================================================
// STREET NORMALIZATION
// =========================================================

function normalizeStreet(
  value = ""
) {
  const raw =
    value.trim();

  if (!raw) {
    return "";
  }

  const key =
    raw
      .toLowerCase()
      .replace(
        /\s+/g,
        " "
      );

  return (
    STREET_ALIASES[key] ||
    raw
  );
}


// =========================================================
// AGGREGATE CASES BY STREET
// =========================================================

function aggregateStreetCases(
  streetCases = []
) {
  const grouped =
    new Map();


  streetCases.forEach(
    (item) => {

      const street =
        normalizeStreet(
          item.street || ""
        );


      if (
        !street ||
        street.toLowerCase() ===
          "unknown"
      ) {
        return;
      }


      const count =
        Number(
          item.case_count || 0
        );


      if (
        !grouped.has(street)
      ) {
        grouped.set(
          street,
          {
            street,
            totalCases: 0,
            diseases:
              new Map(),
          }
        );
      }


      const hotspot =
        grouped.get(street);

      hotspot.totalCases +=
        count;


      const diseaseKey =
        item.disease_id ??
        item.code ??
        item.name;


      const existing =
        hotspot.diseases.get(
          diseaseKey
        ) || {
          diseaseId:
            item.disease_id,

          code:
            item.code,

          name:
            item.name,

          count: 0,
        };


      existing.count +=
        count;


      hotspot.diseases.set(
        diseaseKey,
        existing
      );

    }
  );


  return Array.from(
    grouped.values()
  )
    .map(
      (item) => ({
        ...item,

        diseases:
          Array.from(
            item.diseases.values()
          ).sort(
            (a, b) =>
              b.count -
              a.count
          ),
      })
    )
    .sort(
      (a, b) =>
        b.totalCases -
        a.totalCases
    );
}


// =========================================================
// HOTSPOT LEVEL
// =========================================================

function getHotspotStyle(
  caseCount
) {
  if (
    caseCount >= 10
  ) {
    return {
      label: "Critical",
      color: "#b91c1c",
      fillColor: "#ef4444",
    };
  }


  if (
    caseCount >= 6
  ) {
    return {
      label: "High",
      color: "#c2410c",
      fillColor: "#f97316",
    };
  }


  if (
    caseCount >= 3
  ) {
    return {
      label: "Moderate",
      color: "#a16207",
      fillColor: "#eab308",
    };
  }


  return {
    label: "Low",
    color: "#15803d",
    fillColor: "#22c55e",
  };
}


// =========================================================
// SURVEILLANCE MAP
// =========================================================

function SurveillanceMap({
  streetCases = [],
}) {

  const hotspots =
    aggregateStreetCases(
      streetCases
    );


  const mappedHotspots =
    hotspots.filter(
      (item) =>
        STREET_COORDINATES[
          item.street
        ]
    );


  const unmappedHotspots =
    hotspots.filter(
      (item) =>
        !STREET_COORDINATES[
          item.street
        ]
    );


  return (
    <div className="surveillance-map-shell">


      {/* =================================================
          KRUS NA LIGAS MAP
      ================================================= */}

      <MapContainer

        bounds={
          KRUS_NA_LIGAS_BOUNDS
        }

        maxBounds={
          KRUS_NA_LIGAS_BOUNDS
        }

        maxBoundsViscosity={
          0.9
        }

        minZoom={15}

        maxZoom={20}

        scrollWheelZoom

        className="surveillance-map"

      >


        {/* BASE MAP */}

        <TileLayer

          attribution={
            "&copy; OpenStreetMap contributors"
          }

          url={
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          }

        />


        {/* HOTSPOT MARKERS */}

        {mappedHotspots.map(
          (hotspot) => {

            const level =
              getHotspotStyle(
                hotspot.totalCases
              );


            const radius =
              Math.min(
                10 +
                  hotspot.totalCases *
                    1.5,
                30
              );


            return (

              <CircleMarker

                key={
                  hotspot.street
                }

                center={
                  STREET_COORDINATES[
                    hotspot.street
                  ]
                }

                radius={
                  radius
                }

                pathOptions={{
                  color:
                    level.color,

                  fillColor:
                    level.fillColor,

                  fillOpacity:
                    0.62,

                  weight:
                    2,
                }}

              >


                <Popup>

                  <div className="hotspot-popup">


                    <strong className="hotspot-popup-title">
                      {
                        hotspot.street
                      }
                    </strong>


                    <p>

                      Total validated
                      cases:{" "}

                      <strong>
                        {
                          hotspot.totalCases
                        }
                      </strong>

                    </p>


                    <p>

                      Hotspot level:{" "}

                      <strong>
                        {
                          level.label
                        }
                      </strong>

                    </p>


                    <div className="hotspot-popup-divider" />


                    {hotspot.diseases.map(
                      (disease) => (

                        <div
                          key={
                            disease.diseaseId ??
                            disease.code ??
                            disease.name
                          }
                          className="hotspot-popup-row"
                        >

                          <span>
                            {
                              disease.name
                            }
                          </span>


                          <strong>
                            {
                              disease.count
                            }
                          </strong>

                        </div>

                      )
                    )}


                  </div>

                </Popup>


              </CircleMarker>

            );

          }
        )}


      </MapContainer>


      {/* =================================================
          LEGEND
      ================================================= */}

      <div className="surveillance-map-legend">


        <strong>
          Hotspot Level
        </strong>


        <LegendItem
          className="legend-low"
          label="Low (1-2)"
        />


        <LegendItem
          className="legend-moderate"
          label="Moderate (3-5)"
        />


        <LegendItem
          className="legend-high"
          label="High (6-9)"
        />


        <LegendItem
          className="legend-critical"
          label="Critical (10+)"
        />


      </div>


      {/* =================================================
          UNMAPPED STREET WARNING
      ================================================= */}

      {unmappedHotspots.length >
        0 && (

        <div className="surveillance-map-notice">

          <strong>
            Unmapped street names:
          </strong>{" "}


          {unmappedHotspots
            .map(
              (item) =>
                item.street
            )
            .join(", ")}
          .


          <br />


          These records are still
          included in surveillance
          totals but need a matching
          Krus na Ligas street name to
          appear on the map.

        </div>

      )}


    </div>
  );
}


// =========================================================
// LEGEND ITEM
// =========================================================

function LegendItem({
  className,
  label,
}) {
  return (
    <span className="surveillance-map-legend-item">

      <span
        className={
          `surveillance-map-legend-dot ${className}`
        }
      />

      {label}

    </span>
  );
}


export default SurveillanceMap;