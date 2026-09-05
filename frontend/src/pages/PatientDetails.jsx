import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  getPatient,
  updatePatient,
} from "../api/patientApi";

import {
  createPatientHistory,
  getPatientHistory,
} from "../api/patientHistoryApi";

import {
  createConsultation,
  getPatientConsultations,
} from "../api/consultationApi";

import {
  getActiveDiseases,
} from "../api/diseaseApi";

import { useAuth } from "../context/AuthContext";
import { hasPermission } from "../utils/permissions";

import "../styles/PatientDetails.css";


/* =========================================================
   FORM DEFAULTS
========================================================= */

const EMPTY_HISTORY_FORM = {
  history_type: "",
  description: "",
};


const EMPTY_CONSULTATION_FORM = {
  disease_id: "",
  chief_complaint: "",
  symptoms: "",
  temperature: "",
  systolic_bp: "",
  diastolic_bp: "",
  heart_rate: "",
  respiratory_rate: "",
  oxygen_saturation: "",
  weight_kg: "",
  height_cm: "",
  assessment: "",
  treatment_plan: "",
  notes: "",
};


/* =========================================================
   PATIENT OPTIONS
========================================================= */

const SEX_OPTIONS = [
  {
    value: "Male",
    label: "Male",
  },
  {
    value: "Female",
    label: "Female",
  },
];


const CIVIL_STATUS_OPTIONS = [
  {
    value: "Single",
    label: "Single",
  },
  {
    value: "Married",
    label: "Married",
  },
  {
    value: "Widowed",
    label: "Widowed",
  },
  {
    value: "Separated",
    label: "Separated",
  },
];


const SUFFIX_OPTIONS = [
  {
    value: "Jr.",
    label: "Jr.",
  },
  {
    value: "Sr.",
    label: "Sr.",
  },
  {
    value: "II",
    label: "II",
  },
  {
    value: "III",
    label: "III",
  },
  {
    value: "IV",
    label: "IV",
  },
  {
    value: "V",
    label: "V",
  },
];


const RECORD_STATUS_OPTIONS = [
  {
    value: "ACTIVE",
    label: "Active",
  },
  {
    value: "INACTIVE",
    label: "Inactive",
  },
];


/* =========================================================
   KRUS NA LIGAS STREETS
========================================================= */

const KRUS_NA_LIGAS_STREETS = [
  "Angeles St.",
  "Baluyot St.",
  "C.P. Garcia",
  "E. Ramos St.",
  "Eugenio St.",
  "Fernando St.",
  "Flores St.",
  "Gonzales St.",
  "Kabalitang St.",
  "M. Dela Cruz St.",
  "Manansala St.",
  "P. Francisco St.",
  "Panginiban St.",
  "Salvador St.",
  "Santos St.",
  "T. Fulgencio St.",
  "Tiburcio St.",
  "Tiburcio Ext.",
  "V. Francisco St.",
];


/* =========================================================
   HELPERS
========================================================= */

function textOrNull(value) {
  if (typeof value !== "string") {
    return null;
  }

  const cleaned = value.trim();

  return cleaned || null;
}


function numberOrNull(value) {
  if (
    value === "" ||
    value === null ||
    value === undefined
  ) {
    return null;
  }

  const parsed = Number(value);

  return Number.isNaN(parsed)
    ? null
    : parsed;
}


function getApiErrorMessage(
  error,
  fallback = "An unexpected error occurred."
) {
  const detail =
    error?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map(
        (item) =>
          item?.msg ||
          "Invalid information."
      )
      .join(", ");
  }

  return fallback;
}


function calculateAge(dateOfBirth) {
  if (!dateOfBirth) {
    return null;
  }

  const [
    birthYear,
    birthMonth,
    birthDay,
  ] = String(dateOfBirth)
    .split("-")
    .map(Number);

  if (
    !birthYear ||
    !birthMonth ||
    !birthDay
  ) {
    return null;
  }

  const today = new Date();

  let age =
    today.getFullYear() -
    birthYear;

  const currentMonth =
    today.getMonth() + 1;

  const currentDay =
    today.getDate();

  if (
    currentMonth < birthMonth ||
    (
      currentMonth === birthMonth &&
      currentDay < birthDay
    )
  ) {
    age -= 1;
  }

  return age >= 0
    ? age
    : null;
}


function buildPatientFormData(data) {
  return {
    first_name:
      data?.first_name || "",

    middle_name:
      data?.middle_name || "",

    last_name:
      data?.last_name || "",

    suffix:
      data?.suffix || "",

    date_of_birth:
      data?.date_of_birth || "",

    sex:
      data?.sex || "",

    civil_status:
      data?.civil_status || "",

    street:
      data?.street || "",

    address:
      data?.address || "",

    contact_number:
      data?.contact_number || "",

    emergency_contact_name:
      data?.emergency_contact_name || "",

    emergency_contact_number:
      data?.emergency_contact_number || "",

    record_status:
      data?.record_status || "ACTIVE",
  };
}


function formatPatientName(patient) {
  if (!patient) {
    return "Patient";
  }

  const lastName =
    patient.last_name || "";

  const firstName =
    patient.first_name || "";

  const middleName =
    patient.middle_name || "";

  const suffix =
    patient.suffix || "";

  const givenNames = [
    firstName,
    middleName,
  ]
    .filter(Boolean)
    .join(" ");

  if (lastName) {
    return [
      `${lastName},`,
      givenNames,
      suffix,
    ]
      .filter(Boolean)
      .join(" ");
  }

  return [
    firstName,
    middleName,
    suffix,
  ]
    .filter(Boolean)
    .join(" ") || "Patient";
}


function formatDiagnosis(diagnosis) {
  if (
    diagnosis ===
    "Restricted Sensitive Record"
  ) {
    return "🔒 Restricted Sensitive Record";
  }

  return (
    diagnosis ||
    "No diagnosis recorded"
  );
}


function isRestrictedDiagnosis(
  diagnosis
) {
  return (
    diagnosis ===
    "Restricted Sensitive Record"
  );
}


function formatHistoryType(type) {
  if (!type) {
    return "-";
  }

  return type
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    );
}


function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  return new Date(
    value
  ).toLocaleString();
}


/* =========================================================
   PATIENT DETAILS
========================================================= */

function PatientDetails() {
  const { patientId } =
    useParams();

  const { user } =
    useAuth();


  /* =======================================================
     PERMISSIONS
  ======================================================= */

  const permissions =
    user?.permissions ?? [];

  const canViewSensitiveDisease =
    hasPermission(
      permissions,
      "SENSITIVE_DISEASE_VIEW"
    );


  /* =======================================================
     STATE
  ======================================================= */

  const [
    patient,
    setPatient,
  ] = useState(null);

  const [
    formData,
    setFormData,
  ] = useState(null);

  const [
    histories,
    setHistories,
  ] = useState([]);

  const [
    consultations,
    setConsultations,
  ] = useState([]);

  const [
    diseases,
    setDiseases,
  ] = useState([]);


  const [
    editing,
    setEditing,
  ] = useState(false);

  const [
    showHistoryForm,
    setShowHistoryForm,
  ] = useState(false);

  const [
    showConsultationForm,
    setShowConsultationForm,
  ] = useState(false);


  const [
    historyForm,
    setHistoryForm,
  ] = useState({
    ...EMPTY_HISTORY_FORM,
  });

  const [
    consultationForm,
    setConsultationForm,
  ] = useState({
    ...EMPTY_CONSULTATION_FORM,
  });


  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    historySaving,
    setHistorySaving,
  ] = useState(false);

  const [
    consultationSaving,
    setConsultationSaving,
  ] = useState(false);

  const [
    diseaseLoading,
    setDiseaseLoading,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");

  const [
    success,
    setSuccess,
  ] = useState("");


  /* =======================================================
     MESSAGES
  ======================================================= */

  const clearMessages = () => {
    setError("");
    setSuccess("");
  };


  /* =======================================================
     LOAD PATIENT
  ======================================================= */

  const loadPatient =
    useCallback(async () => {
      try {
        setLoading(true);
        setError("");

        const data =
          await getPatient(
            patientId
          );

        setPatient(data);

        setFormData(
          buildPatientFormData(
            data
          )
        );

        return data;
      } catch (err) {
        console.error(
          "Unable to load patient:",
          err
        );

        setError(
          getApiErrorMessage(
            err,
            "Unable to load patient record."
          )
        );

        return null;
      } finally {
        setLoading(false);
      }
    }, [
      patientId,
    ]);


  /* =======================================================
     LOAD MEDICAL HISTORY
  ======================================================= */

  const loadHistory =
    useCallback(async () => {
      try {
        const data =
          await getPatientHistory(
            patientId
          );

        setHistories(
          Array.isArray(data)
            ? data
            : []
        );
      } catch (err) {
        console.error(
          "Unable to load medical history:",
          err
        );
      }
    }, [
      patientId,
    ]);


  /* =======================================================
     LOAD CONSULTATIONS
  ======================================================= */

  const loadConsultations =
    useCallback(async () => {
      try {
        const data =
          await getPatientConsultations(
            patientId
          );

        setConsultations(
          Array.isArray(data)
            ? data
            : []
        );
      } catch (err) {
        console.error(
          "Unable to load consultations:",
          err
        );
      }
    }, [
      patientId,
    ]);


  /* =======================================================
     LOAD DISEASES
  ======================================================= */

  const loadDiseases =
    useCallback(async () => {
      try {
        setDiseaseLoading(true);

        const data =
          await getActiveDiseases();

        const list =
          Array.isArray(data)
            ? data
            : [];

        setDiseases(
          canViewSensitiveDisease
            ? list
            : list.filter(
                (disease) =>
                  !disease.is_sensitive
              )
        );
      } catch (err) {
        console.error(
          "Unable to load diseases:",
          err
        );

        setDiseases([]);
      } finally {
        setDiseaseLoading(false);
      }
    }, [
      canViewSensitiveDisease,
    ]);


  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {
    loadPatient();
    loadHistory();
    loadConsultations();
    loadDiseases();
  }, [
    loadPatient,
    loadHistory,
    loadConsultations,
    loadDiseases,
  ]);


  /* =======================================================
     PATIENT EDIT
  ======================================================= */

  const handlePatientChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setFormData(
      (current) => ({
        ...current,
        [name]: value,
      })
    );

    if (error) {
      setError("");
    }
  };


  const handlePatientSave =
    async (event) => {
      event.preventDefault();

      clearMessages();


      /* Validate date of birth */

      if (
        formData.date_of_birth
      ) {
        const birthDate =
          new Date(
            `${formData.date_of_birth}T00:00:00`
          );

        const today =
          new Date();

        if (birthDate > today) {
          setError(
            "Date of birth cannot be in the future."
          );

          return;
        }
      }


      const payload = {
        first_name:
          formData
            .first_name
            .trim(),

        middle_name:
          textOrNull(
            formData.middle_name
          ),

        last_name:
          formData
            .last_name
            .trim(),

        suffix:
          textOrNull(
            formData.suffix
          ),

        date_of_birth:
          formData.date_of_birth,

        sex:
          formData.sex,

        civil_status:
          textOrNull(
            formData.civil_status
          ),

        street:
          textOrNull(
            formData.street
          ),

        address:
          formData
            .address
            .trim(),

        contact_number:
          textOrNull(
            formData.contact_number
          ),

        emergency_contact_name:
          textOrNull(
            formData
              .emergency_contact_name
          ),

        emergency_contact_number:
          textOrNull(
            formData
              .emergency_contact_number
          ),

        record_status:
          formData.record_status,
      };


      try {
        setSaving(true);

        await updatePatient(
          patientId,
          payload
        );

        /*
         * Reload from FastAPI after update.
         * This confirms that the database actually
         * stored the suffix and other changes.
         */
        await loadPatient();

        setEditing(false);

        setSuccess(
          "Patient record updated successfully."
        );
      } catch (err) {
        console.error(
          "Unable to update patient:",
          err
        );

        setError(
          getApiErrorMessage(
            err,
            "Unable to update patient record."
          )
        );
      } finally {
        setSaving(false);
      }
    };


  const startPatientEdit = () => {
    clearMessages();

    setFormData(
      buildPatientFormData(
        patient
      )
    );

    setEditing(true);
  };


  const cancelPatientEdit = () => {
    clearMessages();

    setFormData(
      buildPatientFormData(
        patient
      )
    );

    setEditing(false);
  };


  /* =======================================================
     MEDICAL HISTORY
  ======================================================= */

  const handleHistoryChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setHistoryForm(
      (current) => ({
        ...current,
        [name]: value,
      })
    );
  };


  const handleHistorySubmit =
    async (event) => {
      event.preventDefault();

      try {
        setHistorySaving(true);
        clearMessages();

        await createPatientHistory(
          patientId,
          {
            history_type:
              historyForm
                .history_type,

            description:
              historyForm
                .description
                .trim(),
          }
        );

        setHistoryForm({
          ...EMPTY_HISTORY_FORM,
        });

        setShowHistoryForm(false);

        await loadHistory();

        setSuccess(
          "Medical history added successfully."
        );
      } catch (err) {
        console.error(
          "Unable to add medical history:",
          err
        );

        setError(
          getApiErrorMessage(
            err,
            "Unable to add medical history."
          )
        );
      } finally {
        setHistorySaving(false);
      }
    };


  /* =======================================================
     CONSULTATION
  ======================================================= */

  const handleConsultationChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setConsultationForm(
      (current) => ({
        ...current,
        [name]: value,
      })
    );
  };


  const handleConsultationSubmit =
    async (event) => {
      event.preventDefault();

      clearMessages();

      try {
        setConsultationSaving(
          true
        );

        const selectedDisease =
          diseases.find(
            (disease) =>
              disease.id ===
              Number(
                consultationForm
                  .disease_id
              )
          );

        if (!selectedDisease) {
          setError(
            "Please select a diagnosis."
          );

          return;
        }


        const payload = {
          disease_id:
            selectedDisease.id,

          chief_complaint:
            consultationForm
              .chief_complaint
              .trim(),

          symptoms:
            textOrNull(
              consultationForm.symptoms
            ),

          temperature:
            numberOrNull(
              consultationForm.temperature
            ),

          systolic_bp:
            numberOrNull(
              consultationForm.systolic_bp
            ),

          diastolic_bp:
            numberOrNull(
              consultationForm.diastolic_bp
            ),

          heart_rate:
            numberOrNull(
              consultationForm.heart_rate
            ),

          respiratory_rate:
            numberOrNull(
              consultationForm
                .respiratory_rate
            ),

          oxygen_saturation:
            numberOrNull(
              consultationForm
                .oxygen_saturation
            ),

          weight_kg:
            numberOrNull(
              consultationForm.weight_kg
            ),

          height_cm:
            numberOrNull(
              consultationForm.height_cm
            ),

          assessment:
            textOrNull(
              consultationForm.assessment
            ),

          diagnosis:
            selectedDisease.name,

          treatment_plan:
            textOrNull(
              consultationForm
                .treatment_plan
            ),

          notes:
            textOrNull(
              consultationForm.notes
            ),
        };


        await createConsultation(
          patientId,
          payload
        );

        setConsultationForm({
          ...EMPTY_CONSULTATION_FORM,
        });

        setShowConsultationForm(
          false
        );

        await loadConsultations();

        setSuccess(
          "Consultation recorded successfully."
        );
      } catch (err) {
        console.error(
          "Unable to save consultation:",
          err
        );

        setError(
          getApiErrorMessage(
            err,
            "Unable to save consultation."
          )
        );
      } finally {
        setConsultationSaving(
          false
        );
      }
    };


  /* =======================================================
     COMPUTED VALUES
  ======================================================= */

  const age = useMemo(
    () =>
      calculateAge(
        patient?.date_of_birth
      ),
    [
      patient?.date_of_birth,
    ]
  );


  const patientInitials =
    useMemo(() => {
      if (!patient) {
        return "PT";
      }

      return [
        patient.first_name?.[0],
        patient.last_name?.[0],
      ]
        .filter(Boolean)
        .join("")
        .toUpperCase();
    }, [
      patient,
    ]);


  const patientFullName =
    useMemo(
      () =>
        formatPatientName(
          patient
        ),
      [
        patient,
      ]
    );


  const latestConsultation =
    useMemo(() => {
      if (
        consultations.length ===
        0
      ) {
        return null;
      }

      return [
        ...consultations,
      ].sort(
        (a, b) =>
          new Date(
            b.consultation_date
          ) -
          new Date(
            a.consultation_date
          )
      )[0];
    }, [
      consultations,
    ]);


  const previousDiagnoses =
    useMemo(
      () =>
        consultations.filter(
          (consultation) =>
            consultation.diagnosis
        ),
      [
        consultations,
      ]
    );


  /* =======================================================
     LOADING / ERROR
  ======================================================= */

  if (loading) {
    return (
      <div className="patient-record-state">
        Loading patient record...
      </div>
    );
  }


  if (
    error &&
    !patient
  ) {
    return (
      <div className="patient-record-state">

        <p>
          {error}
        </p>

        <Link to="/patients">
          Back to Patients
        </Link>

      </div>
    );
  }


  if (
    !patient ||
    !formData
  ) {
    return (
      <div className="patient-record-state">
        Patient not found.
      </div>
    );
  }


  /* =======================================================
     PAGE
  ======================================================= */

  return (
    <div className="patient-record-page">

      {/* TOP ACTIONS */}

      <div className="patient-record-top">

        <Link
          to="/patients"
          className="patient-record-back"
        >
          ← Back to Patients
        </Link>


        {!editing && (
          <button
            type="button"
            className="patient-record-secondary-button"
            onClick={
              startPatientEdit
            }
          >
            Edit Patient
          </button>
        )}

      </div>


      {/* MESSAGES */}

      {error && (
        <div
          className="patient-record-message patient-record-error"
          role="alert"
        >
          {error}
        </div>
      )}


      {success && (
        <div
          className="patient-record-message patient-record-success"
          role="status"
        >
          {success}
        </div>
      )}


      {/* =================================================
          PROFILE HEADER
      ================================================== */}

      <section className="patient-profile-card">

        <div className="patient-profile-avatar">
          {patientInitials}
        </div>


        <div className="patient-profile-main">

          <div className="patient-profile-name-row">

            <div>

              <h1>
                {patientFullName}
              </h1>

              <p>
                Patient Code:{" "}

                <strong>
                  {patient.patient_code}
                </strong>
              </p>

            </div>


            <span
              className={
                patient.record_status ===
                "ACTIVE"
                  ? "patient-status patient-status-active"
                  : "patient-status patient-status-inactive"
              }
            >
              {patient.record_status}
            </span>

          </div>


          <div className="patient-profile-meta">

            <span>
              {age != null
                ? `${age} years old`
                : "Age unavailable"}
            </span>

            <span>
              {patient.sex || "-"}
            </span>

            <span>
              {patient.civil_status ||
                "Civil status not set"}
            </span>

          </div>


          <div className="patient-profile-contact">

            <span>
              {patient.street
                ? `${patient.street}, `
                : ""}

              {patient.address || ""}
            </span>

            <span>
              {patient.contact_number ||
                "No contact number"}
            </span>

          </div>

        </div>

      </section>


      {/* =================================================
          SUMMARY
      ================================================== */}

      <div className="patient-summary-grid">

        <SummaryCard
          label="Latest Diagnosis"
          value={
            formatDiagnosis(
              latestConsultation
                ?.diagnosis
            )
          }
        />


        <SummaryCard
          label="Last Consultation"
          value={
            latestConsultation
              ? formatDateTime(
                  latestConsultation
                    .consultation_date
                )
              : "No consultation yet"
          }
        />


        <SummaryCard
          label="Medical History Entries"
          value={histories.length}
        />


        <SummaryCard
          label="Total Consultations"
          value={consultations.length}
        />

      </div>


      {/* =================================================
          PATIENT INFORMATION
      ================================================== */}

      <section className="patient-record-card">

        <div className="patient-record-section-header">

          <div>
            <h2>
              Patient Information
            </h2>

            <p>
              Personal and contact details.
            </p>
          </div>

        </div>


        {!editing ? (

          /* ===============================================
             VIEW MODE
          ================================================ */

          <div className="patient-info-grid">

            <InfoItem
              label="Last Name"
              value={
                patient.last_name ||
                "-"
              }
            />


            <InfoItem
              label="First Name"
              value={
                patient.first_name ||
                "-"
              }
            />


            <InfoItem
              label="Middle Name"
              value={
                patient.middle_name ||
                "-"
              }
            />


            <InfoItem
              label="Suffix"
              value={
                patient.suffix ||
                "-"
              }
            />


            <InfoItem
              label="Date of Birth"
              value={
                patient.date_of_birth ||
                "-"
              }
            />


            <InfoItem
              label="Sex"
              value={
                patient.sex ||
                "-"
              }
            />


            <InfoItem
              label="Civil Status"
              value={
                patient.civil_status ||
                "-"
              }
            />


            <InfoItem
              label="Street"
              value={
                patient.street ||
                "-"
              }
            />


            <InfoItem
              label="Complete Address"
              value={
                patient.address ||
                "-"
              }
            />


            <InfoItem
              label="Contact Number"
              value={
                patient.contact_number ||
                "-"
              }
            />


            <InfoItem
              label="Emergency Contact"
              value={
                patient
                  .emergency_contact_name ||
                "-"
              }
            />


            <InfoItem
              label="Emergency Contact Number"
              value={
                patient
                  .emergency_contact_number ||
                "-"
              }
            />

          </div>

        ) : (

          /* ===============================================
             EDIT MODE
          ================================================ */

          <form
            className="patient-edit-form"
            onSubmit={
              handlePatientSave
            }
          >

            <EditField
              label="Last Name"
              name="last_name"
              value={
                formData.last_name
              }
              onChange={
                handlePatientChange
              }
              disabled={saving}
              required
            />


            <EditField
              label="First Name"
              name="first_name"
              value={
                formData.first_name
              }
              onChange={
                handlePatientChange
              }
              disabled={saving}
              required
            />


            <EditField
              label="Middle Name"
              name="middle_name"
              value={
                formData.middle_name
              }
              onChange={
                handlePatientChange
              }
              disabled={saving}
            />


            <EditSelect
              label="Suffix"
              name="suffix"
              value={
                formData.suffix
              }
              onChange={
                handlePatientChange
              }
              options={
                SUFFIX_OPTIONS
              }
              placeholder="No suffix"
              disabled={saving}
            />


            <EditField
              label="Date of Birth"
              name="date_of_birth"
              type="date"
              value={
                formData.date_of_birth
              }
              onChange={
                handlePatientChange
              }
              disabled={saving}
              required
            />


            <EditSelect
              label="Sex"
              name="sex"
              value={
                formData.sex
              }
              onChange={
                handlePatientChange
              }
              options={
                SEX_OPTIONS
              }
              placeholder="Select Sex"
              disabled={saving}
              required
            />


            <EditSelect
              label="Civil Status"
              name="civil_status"
              value={
                formData.civil_status
              }
              onChange={
                handlePatientChange
              }
              options={
                CIVIL_STATUS_OPTIONS
              }
              placeholder="Select Civil Status"
              disabled={saving}
            />


            <StreetSelect
              value={
                formData.street
              }
              onChange={
                handlePatientChange
              }
              disabled={saving}
            />


            <EditSelect
              label="Record Status"
              name="record_status"
              value={
                formData.record_status
              }
              onChange={
                handlePatientChange
              }
              options={
                RECORD_STATUS_OPTIONS
              }
              disabled={saving}
            />


            <div className="patient-edit-field patient-edit-field-full">

              <label htmlFor="address">
                Complete Address
              </label>

              <textarea
                id="address"
                name="address"
                value={
                  formData.address
                }
                onChange={
                  handlePatientChange
                }
                disabled={saving}
                required
              />

            </div>


            <EditField
              label="Contact Number"
              name="contact_number"
              type="tel"
              value={
                formData.contact_number
              }
              onChange={
                handlePatientChange
              }
              disabled={saving}
            />


            <EditField
              label="Emergency Contact Name"
              name="emergency_contact_name"
              value={
                formData
                  .emergency_contact_name
              }
              onChange={
                handlePatientChange
              }
              disabled={saving}
            />


            <EditField
              label="Emergency Contact Number"
              name="emergency_contact_number"
              type="tel"
              value={
                formData
                  .emergency_contact_number
              }
              onChange={
                handlePatientChange
              }
              disabled={saving}
            />


            <div className="patient-edit-actions">

              <button
                type="submit"
                className="patient-record-primary-button"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : "Save Changes"}
              </button>


              <button
                type="button"
                className="patient-record-secondary-button"
                onClick={
                  cancelPatientEdit
                }
                disabled={saving}
              >
                Cancel
              </button>

            </div>

          </form>
        )}

      </section>


      {/* =================================================
          MEDICAL HISTORY
      ================================================== */}

      <section className="patient-record-card">

        <div className="patient-record-section-header">

          <div>

            <h2>
              Medical History
            </h2>

            <p>
              Allergies, conditions,
              illnesses, surgeries, and
              family history.
            </p>

          </div>


          <button
            type="button"
            className="patient-record-primary-button"
            onClick={() => {
              setShowHistoryForm(
                (current) =>
                  !current
              );

              clearMessages();
            }}
          >
            {showHistoryForm
              ? "Cancel"
              : "+ Add Medical History"}
          </button>

        </div>


        {showHistoryForm && (

          <form
            className="patient-history-form"
            onSubmit={
              handleHistorySubmit
            }
          >

            <div className="patient-edit-field">

              <label htmlFor="history_type">
                History Type
              </label>

              <select
                id="history_type"
                name="history_type"
                value={
                  historyForm
                    .history_type
                }
                onChange={
                  handleHistoryChange
                }
                required
              >

                <option value="">
                  Select Type
                </option>

                <option value="ALLERGY">
                  Allergy
                </option>

                <option value="EXISTING_CONDITION">
                  Existing Condition
                </option>

                <option value="PAST_ILLNESS">
                  Past Illness
                </option>

                <option value="SURGERY">
                  Surgery
                </option>

                <option value="FAMILY_HISTORY">
                  Family History
                </option>

              </select>

            </div>


            <div className="patient-edit-field patient-edit-field-full">

              <label htmlFor="description">
                Description
              </label>

              <textarea
                id="description"
                name="description"
                value={
                  historyForm.description
                }
                onChange={
                  handleHistoryChange
                }
                required
              />

            </div>


            <div className="patient-edit-actions">

              <button
                type="submit"
                className="patient-record-primary-button"
                disabled={
                  historySaving
                }
              >
                {historySaving
                  ? "Saving..."
                  : "Save Medical History"}
              </button>

            </div>

          </form>
        )}


        {histories.length === 0 ? (

          <div className="patient-record-empty">
            No medical history recorded.
          </div>

        ) : (

          <div className="patient-record-table-wrap">

            <table className="patient-record-table">

              <thead>
                <tr>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Date Recorded</th>
                </tr>
              </thead>


              <tbody>

                {histories.map(
                  (history) => (

                    <tr key={history.id}>

                      <td>
                        <span className="patient-history-type">
                          {formatHistoryType(
                            history
                              .history_type
                          )}
                        </span>
                      </td>

                      <td>
                        {history.description}
                      </td>

                      <td>
                        {formatDateTime(
                          history.recorded_at
                        )}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>
        )}

      </section>


      {/* =================================================
          PREVIOUS DIAGNOSES
      ================================================== */}

      <section className="patient-record-card">

        <div className="patient-record-section-header">

          <div>

            <h2>
              Previous Diagnoses
            </h2>

            <p>
              Diagnoses from previous
              consultations.
            </p>

          </div>

        </div>


        {previousDiagnoses.length === 0 ? (

          <div className="patient-record-empty">
            No previous diagnoses recorded.
          </div>

        ) : (

          <div className="patient-record-table-wrap">

            <table className="patient-record-table">

              <thead>
                <tr>
                  <th>Date</th>
                  <th>Diagnosis</th>
                  <th>Chief Complaint</th>
                  <th>Action</th>
                </tr>
              </thead>


              <tbody>

                {previousDiagnoses.map(
                  (consultation) => (

                    <tr
                      key={
                        consultation.id
                      }
                    >

                      <td>
                        {formatDateTime(
                          consultation
                            .consultation_date
                        )}
                      </td>


                      <td>
                        <strong>
                          {formatDiagnosis(
                            consultation
                              .diagnosis
                          )}
                        </strong>
                      </td>


                      <td>
                        {
                          consultation
                            .chief_complaint
                        }
                      </td>


                      <td>

                        {isRestrictedDiagnosis(
                          consultation
                            .diagnosis
                        ) ? (

                          <span className="patient-record-restricted">
                            Restricted
                          </span>

                        ) : (

                          <Link
                            className="patient-record-link"
                            to={
                              `/consultations/${consultation.id}`
                            }
                          >
                            View
                          </Link>

                        )}

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>
        )}

      </section>


      {/* =================================================
          CONSULTATIONS
      ================================================== */}

      <section className="patient-record-card">

        <div className="patient-record-section-header">

          <div>

            <h2>
              Consultation History
            </h2>

            <p>
              Complete consultation records
              for this patient.
            </p>

          </div>


          <button
            type="button"
            className="patient-record-primary-button"
            onClick={() => {
              setShowConsultationForm(
                (current) =>
                  !current
              );

              clearMessages();
            }}
          >
            {showConsultationForm
              ? "Cancel"
              : "+ New Consultation"}
          </button>

        </div>


        {showConsultationForm && (

          <ConsultationForm
            formData={
              consultationForm
            }
            diseases={
              diseases
            }
            diseaseLoading={
              diseaseLoading
            }
            saving={
              consultationSaving
            }
            onChange={
              handleConsultationChange
            }
            onSubmit={
              handleConsultationSubmit
            }
          />

        )}


        {consultations.length === 0 ? (

          <div className="patient-record-empty">
            No consultations recorded.
          </div>

        ) : (

          <div className="patient-record-table-wrap">

            <table className="patient-record-table">

              <thead>
                <tr>
                  <th>Date</th>
                  <th>Chief Complaint</th>
                  <th>Diagnosis</th>
                  <th>Temperature</th>
                  <th>Blood Pressure</th>
                  <th>Action</th>
                </tr>
              </thead>


              <tbody>

                {consultations.map(
                  (consultation) => (

                    <tr
                      key={
                        consultation.id
                      }
                    >

                      <td>
                        {formatDateTime(
                          consultation
                            .consultation_date
                        )}
                      </td>


                      <td>
                        {
                          consultation
                            .chief_complaint
                        }
                      </td>


                      <td>
                        {formatDiagnosis(
                          consultation
                            .diagnosis
                        )}
                      </td>


                      <td>
                        {consultation
                          .temperature != null
                          ? `${consultation.temperature} °C`
                          : "-"}
                      </td>


                      <td>
                        {consultation
                          .systolic_bp != null &&
                        consultation
                          .diastolic_bp != null
                          ? `${consultation.systolic_bp}/${consultation.diastolic_bp}`
                          : "-"}
                      </td>


                      <td>

                        {isRestrictedDiagnosis(
                          consultation
                            .diagnosis
                        ) ? (

                          <span className="patient-record-restricted">
                            Restricted
                          </span>

                        ) : (

                          <Link
                            className="patient-record-link"
                            to={
                              `/consultations/${consultation.id}`
                            }
                          >
                            View
                          </Link>

                        )}

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>
        )}

      </section>

    </div>
  );
}


/* =========================================================
   SMALL COMPONENTS
========================================================= */

function SummaryCard({
  label,
  value,
}) {
  return (
    <div className="patient-summary-card">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


function InfoItem({
  label,
  value,
}) {
  return (
    <div className="patient-info-item">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


function EditField({
  label,
  name,
  value,
  onChange,
  type = "text",
  required = false,
  disabled = false,
}) {
  return (
    <div className="patient-edit-field">

      <label htmlFor={name}>
        {label}
      </label>

      <input
        id={name}
        name={name}
        type={type}
        value={
          value ?? ""
        }
        onChange={
          onChange
        }
        required={
          required
        }
        disabled={
          disabled
        }
      />

    </div>
  );
}


function EditSelect({
  label,
  name,
  value,
  onChange,
  options,
  placeholder = "",
  required = false,
  disabled = false,
}) {
  return (
    <div className="patient-edit-field">

      <label htmlFor={name}>
        {label}
      </label>

      <select
        id={name}
        name={name}
        value={
          value ?? ""
        }
        onChange={
          onChange
        }
        required={
          required
        }
        disabled={
          disabled
        }
      >

        {placeholder && (
          <option value="">
            {placeholder}
          </option>
        )}


        {options.map(
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
        )}

      </select>

    </div>
  );
}


function StreetSelect({
  value,
  onChange,
  disabled,
}) {
  return (
    <div className="patient-edit-field">

      <label htmlFor="street">
        Street
      </label>

      <select
        id="street"
        name="street"
        value={
          value || ""
        }
        onChange={
          onChange
        }
        disabled={
          disabled
        }
        required
      >

        <option value="">
          Select Street
        </option>


        {value &&
          !KRUS_NA_LIGAS_STREETS.includes(
            value
          ) && (

            <option value={value}>
              {value} (Current)
            </option>

          )}


        {KRUS_NA_LIGAS_STREETS.map(
          (street) => (

            <option
              key={street}
              value={street}
            >
              {street}
            </option>

          )
        )}

      </select>

    </div>
  );
}


/* =========================================================
   CONSULTATION FORM
========================================================= */

function ConsultationForm({
  formData,
  diseases,
  diseaseLoading,
  saving,
  onChange,
  onSubmit,
}) {
  return (
    <form
      className="patient-consultation-form"
      onSubmit={
        onSubmit
      }
    >

      <div className="patient-form-section-title">
        Complaint & Symptoms
      </div>


      <div className="patient-edit-field patient-edit-field-full">

        <label htmlFor="chief_complaint">
          Chief Complaint
        </label>

        <textarea
          id="chief_complaint"
          name="chief_complaint"
          value={
            formData.chief_complaint
          }
          onChange={
            onChange
          }
          required
        />

      </div>


      <div className="patient-edit-field patient-edit-field-full">

        <label htmlFor="symptoms">
          Symptoms
        </label>

        <textarea
          id="symptoms"
          name="symptoms"
          value={
            formData.symptoms
          }
          onChange={
            onChange
          }
        />

      </div>


      <div className="patient-form-section-title">
        Vital Signs
      </div>


      <EditField
        label="Temperature (°C)"
        name="temperature"
        type="number"
        value={formData.temperature}
        onChange={onChange}
      />

      <EditField
        label="Systolic BP"
        name="systolic_bp"
        type="number"
        value={formData.systolic_bp}
        onChange={onChange}
      />

      <EditField
        label="Diastolic BP"
        name="diastolic_bp"
        type="number"
        value={formData.diastolic_bp}
        onChange={onChange}
      />

      <EditField
        label="Heart Rate"
        name="heart_rate"
        type="number"
        value={formData.heart_rate}
        onChange={onChange}
      />

      <EditField
        label="Respiratory Rate"
        name="respiratory_rate"
        type="number"
        value={
          formData.respiratory_rate
        }
        onChange={onChange}
      />

      <EditField
        label="Oxygen Saturation (%)"
        name="oxygen_saturation"
        type="number"
        value={
          formData.oxygen_saturation
        }
        onChange={onChange}
      />

      <EditField
        label="Weight (kg)"
        name="weight_kg"
        type="number"
        value={formData.weight_kg}
        onChange={onChange}
      />

      <EditField
        label="Height (cm)"
        name="height_cm"
        type="number"
        value={formData.height_cm}
        onChange={onChange}
      />


      <div className="patient-form-section-title">
        Clinical Information
      </div>


      <div className="patient-edit-field patient-edit-field-full">

        <label htmlFor="assessment">
          Assessment
        </label>

        <textarea
          id="assessment"
          name="assessment"
          value={formData.assessment}
          onChange={onChange}
        />

      </div>


      <div className="patient-edit-field">

        <label htmlFor="disease_id">
          Diagnosis
        </label>

        <select
          id="disease_id"
          name="disease_id"
          value={
            formData.disease_id
          }
          onChange={
            onChange
          }
          required
          disabled={
            diseaseLoading
          }
        >

          <option value="">
            {diseaseLoading
              ? "Loading diagnoses..."
              : "Select Diagnosis"}
          </option>


          {diseases.map(
            (disease) => (

              <option
                key={disease.id}
                value={disease.id}
              >
                {disease.code}
                {" - "}
                {disease.name}

                {disease.is_sensitive
                  ? " 🔒 Sensitive"
                  : ""}
              </option>

            )
          )}

        </select>

      </div>


      <div className="patient-edit-field patient-edit-field-full">

        <label htmlFor="treatment_plan">
          Treatment Plan
        </label>

        <textarea
          id="treatment_plan"
          name="treatment_plan"
          value={
            formData.treatment_plan
          }
          onChange={
            onChange
          }
        />

      </div>


      <div className="patient-edit-field patient-edit-field-full">

        <label htmlFor="notes">
          Notes
        </label>

        <textarea
          id="notes"
          name="notes"
          value={formData.notes}
          onChange={onChange}
        />

      </div>


      <div className="patient-edit-actions">

        <button
          type="submit"
          className="patient-record-primary-button"
          disabled={
            saving ||
            diseaseLoading ||
            diseases.length === 0
          }
        >
          {saving
            ? "Saving..."
            : "Save Consultation"}
        </button>

      </div>

    </form>
  );
}


export default PatientDetails;