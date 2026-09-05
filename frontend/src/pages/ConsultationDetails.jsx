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
  getConsultation,
  updateConsultation,
} from "../api/consultationApi";

import {
  getActiveDiseases,
} from "../api/diseaseApi";

import {
  createDiseaseCase,
  getConsultationDiseaseCases,
  updateDiseaseCaseValidation,
} from "../api/diseaseCaseApi";

import {
  dispenseMedicine,
  getDispensedMedicines,
} from "../api/dispensingApi";

import {
  getMedicines,
} from "../api/medicineApi";

import {
  createConsultationPrediction,
  getConsultationPredictions,
} from "../api/predictionApi";

import {
  useAuth,
} from "../context/AuthContext";

import {
  hasPermission,
} from "../utils/permissions";

import "../styles/ConsultationDetails.css";
import "../styles/ConsultationPredictionHistory.css";


/* =========================================================
   DEFAULT FORMS
========================================================= */

const EMPTY_DISEASE_CASE_FORM = {
  disease_id: "",
  case_status: "SUSPECTED",
  onset_date: "",
  remarks: "",
};

const EMPTY_DISPENSING_FORM = {
  medicine_id: "",
  stock_unit: "LOOSE",
  quantity: "",
  dosage_instruction: "",
  remarks: "",
};


/* =========================================================
   CONSULTATION DETAILS PAGE
========================================================= */

function ConsultationDetails() {
  const {
    consultationId,
  } = useParams();

  const {
    user,
  } = useAuth();


    /* =======================================================
     PERMISSIONS
  ======================================================= */

  const permissions =
    user?.permissions ?? [];


  const canEditConsultation =
    hasPermission(
      permissions,
      "CONSULTATION_CREATE"
    );


  const canCreateDiagnosis =
    hasPermission(
      permissions,
      "DIAGNOSIS_CREATE"
    );


  const canViewInventory =
    hasPermission(
      permissions,
      "INVENTORY_VIEW"
    );


  const canDispenseMedicine =
    hasPermission(
      permissions,
      "MEDICINE_DISPENSE"
    );


  const canPredictDisease =
    hasPermission(
      permissions,
      "DISEASE_PREDICT"
    );


  const canRecordDiseaseCase =
    hasPermission(
      permissions,
      "DISEASE_CASE_CREATE"
    );


  const canValidateDiseaseCase =
    hasPermission(
      permissions,
      "DISEASE_CASE_VALIDATE"
    );


  /* =======================================================
     CONSULTATION STATE
  ======================================================= */

  const [
    consultation,
    setConsultation,
  ] = useState(null);

  const [
    formData,
    setFormData,
  ] = useState(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    editing,
    setEditing,
  ] = useState(false);

  const [
    saving,
    setSaving,
  ] = useState(false);


  /* =======================================================
     ML ANALYSIS HISTORY STATE
  ======================================================= */

  const [
    predictionHistory,
    setPredictionHistory,
  ] = useState([]);

  const [
    predictionHistoryLoading,
    setPredictionHistoryLoading,
  ] = useState(false);

  const [
    predictionHistorySaving,
    setPredictionHistorySaving,
  ] = useState(false);

  const [
    predictionHistoryError,
    setPredictionHistoryError,
  ] = useState("");


  /* =======================================================
     DISEASE CASE STATE
  ======================================================= */

  const [
    diseases,
    setDiseases,
  ] = useState([]);

  const [
    diseaseCases,
    setDiseaseCases,
  ] = useState([]);

  const [
    diseaseCaseForm,
    setDiseaseCaseForm,
  ] = useState({
    ...EMPTY_DISEASE_CASE_FORM,
  });

  const [
    diseaseCasesLoading,
    setDiseaseCasesLoading,
  ] = useState(false);

  const [
    diseaseCaseSaving,
    setDiseaseCaseSaving,
  ] = useState(false);

  const [
    validatingCaseId,
    setValidatingCaseId,
  ] = useState(null);


  /* =======================================================
     MEDICINE STATE
  ======================================================= */

  const [
    medicines,
    setMedicines,
  ] = useState([]);

  const [
    dispensedMedicines,
    setDispensedMedicines,
  ] = useState([]);

  const [
    medicineLoading,
    setMedicineLoading,
  ] = useState(false);

  const [
    dispensingLoading,
    setDispensingLoading,
  ] = useState(false);

  const [
    dispensingSaving,
    setDispensingSaving,
  ] = useState(false);

  const [
    showDispensingForm,
    setShowDispensingForm,
  ] = useState(false);

  const [
    dispensingForm,
    setDispensingForm,
  ] = useState({
    ...EMPTY_DISPENSING_FORM,
  });


  /* =======================================================
     MESSAGES
  ======================================================= */

  const [
    error,
    setError,
  ] = useState("");

  const [
    success,
    setSuccess,
  ] = useState("");


  /* =======================================================
     GENERAL HELPERS
  ======================================================= */

  const clearMessages = () => {
    setError("");
    setSuccess("");
  };

  const textOrNull = (
    value
  ) => {
    if (
      typeof value !== "string"
    ) {
      return null;
    }

    const cleaned =
      value.trim();

    return cleaned || null;
  };

  const numberOrNull = (
    value
  ) => {
    if (
      value === "" ||
      value === null ||
      value === undefined
    ) {
      return null;
    }

    const parsed =
      Number(value);

    return Number.isNaN(parsed)
      ? null
      : parsed;
  };

  const getApiErrorMessage = useCallback((
    err,
    fallback
  ) => {
    const detail =
      err.response?.data?.detail;

    if (
      Array.isArray(detail)
    ) {
      return detail
        .map(
          (item) =>
            item.msg
        )
        .join(", ");
    }

    return detail || fallback;
  }, []);

  const formatDateTime = (
    value
  ) => {
    if (!value) {
      return "-";
    }

    return new Date(
      value
    ).toLocaleString();
  };

  const formatDateOnly = (
    value
  ) => {
    if (!value) {
      return "-";
    }

    return new Date(
      `${value}T00:00:00`
    ).toLocaleDateString();
  };


  /* =======================================================
     DISEASE HELPERS
  ======================================================= */

  const getDiseaseName = (
    diseaseId
  ) => {
    const disease =
      diseases.find(
        (item) =>
          item.id ===
          Number(diseaseId)
      );

    return disease
      ? disease.name
      : `Disease #${diseaseId}`;
  };


  /* =======================================================
     MEDICINE HELPERS
  ======================================================= */

  const getMedicineById = (
    medicineId
  ) => {
    return medicines.find(
      (medicine) =>
        medicine.id ===
        Number(medicineId)
    );
  };

  const getMedicineName = (
    medicineId
  ) => {
    const medicine =
      getMedicineById(
        medicineId
      );

    if (!medicine) {
      return `Medicine #${medicineId}`;
    }

    const strength =
      medicine.dosage_strength
        ? ` ${medicine.dosage_strength}`
        : "";

    return `${medicine.name}${strength}`;
  };

  const getAvailableStock = (
    medicine,
    stockUnit
  ) => {
    if (!medicine) {
      return 0;
    }

    if (
      stockUnit === "PACKAGE"
    ) {
      return (
        medicine.package_stock ??
        0
      );
    }

    return (
      medicine.loose_stock ??
      0
    );
  };

  const getStockUnitLabel = (
    medicine,
    stockUnit
  ) => {
    if (!medicine) {
      return "";
    }

    if (
      stockUnit === "PACKAGE"
    ) {
      return (
        medicine.package_unit ||
        "package(s)"
      );
    }

    return (
      medicine.dispensing_unit ||
      "piece(s)"
    );
  };


  /* =======================================================
     LOAD CONSULTATION
  ======================================================= */

  const loadConsultation =
    useCallback(async () => {
      try {
        setLoading(true);
        setError("");

        const data =
          await getConsultation(
            consultationId
          );

        setConsultation(
          data
        );

        setFormData({
          chief_complaint:
            data.chief_complaint || "",

          symptoms:
            data.symptoms || "",

          temperature:
            data.temperature ?? "",

          systolic_bp:
            data.systolic_bp ?? "",

          diastolic_bp:
            data.diastolic_bp ?? "",

          heart_rate:
            data.heart_rate ?? "",

          respiratory_rate:
            data.respiratory_rate ?? "",

          oxygen_saturation:
            data.oxygen_saturation ?? "",

          weight_kg:
            data.weight_kg ?? "",

          height_cm:
            data.height_cm ?? "",

          assessment:
            data.assessment || "",

          diagnosis:
            data.diagnosis || "",

          treatment_plan:
            data.treatment_plan || "",

          notes:
            data.notes || "",
        });

      } catch (err) {
        console.error(err);

        setError(
          getApiErrorMessage(
            err,
            "Unable to load consultation."
          )
        );

      } finally {
        setLoading(false);
      }
    }, [
      consultationId,
      getApiErrorMessage,
    ]);


  /* =======================================================
     LOAD ML ANALYSIS HISTORY
  ======================================================= */

  const loadPredictionHistory =
    useCallback(async () => {
      if (
        !canPredictDisease
      ) {
        setPredictionHistory([]);
        setPredictionHistoryError("");
        return;
      }

      try {
        setPredictionHistoryLoading(
          true
        );

        setPredictionHistoryError(
          ""
        );

        const data =
          await getConsultationPredictions(
            consultationId
          );

        setPredictionHistory(
          Array.isArray(data)
            ? data
            : []
        );

      } catch (err) {
        console.error(err);

        setPredictionHistoryError(
          getApiErrorMessage(
            err,
            "Unable to load ML analysis history."
          )
        );

      } finally {
        setPredictionHistoryLoading(
          false
        );
      }
    }, [
      canPredictDisease,
      consultationId,
      getApiErrorMessage,
    ]);


  const handleRunPersistentPrediction =
    async () => {
      if (
        !canPredictDisease
      ) {
        return;
      }

      try {
        setPredictionHistorySaving(
          true
        );

        setPredictionHistoryError(
          ""
        );

        clearMessages();

        await createConsultationPrediction(
          consultationId
        );

        await loadPredictionHistory();

        setSuccess(
          "ML decision-support analysis recorded successfully."
        );

      } catch (err) {
        console.error(err);

        setPredictionHistoryError(
          getApiErrorMessage(
            err,
            "Unable to record ML analysis."
          )
        );

      } finally {
        setPredictionHistorySaving(
          false
        );
      }
    };


  /* =======================================================
     LOAD DISEASE CASES
  ======================================================= */

  const loadDiseaseCases =
    useCallback(async () => {
      try {
        setDiseaseCasesLoading(
          true
        );

        const [
          diseaseList,
          caseList,
        ] = await Promise.all([
          getActiveDiseases(),

          getConsultationDiseaseCases(
            consultationId
          ),
        ]);

        setDiseases(
          Array.isArray(diseaseList)
            ? diseaseList
            : []
        );

        setDiseaseCases(
          Array.isArray(caseList)
            ? caseList
            : []
        );

      } catch (err) {
        console.error(err);

        setError(
          getApiErrorMessage(
            err,
            "Unable to load disease cases."
          )
        );

      } finally {
        setDiseaseCasesLoading(
          false
        );
      }
    }, [
      consultationId,
      getApiErrorMessage,
    ]);


  /* =======================================================
     LOAD MEDICINES
  ======================================================= */

  const loadMedicines =
    useCallback(async () => {
      if (!canViewInventory) {
        setMedicines([]);
        return;
      }

      try {
        setMedicineLoading(
          true
        );

        const data =
          await getMedicines(
            "",
            true
          );

        setMedicines(
          Array.isArray(data)
            ? data
            : []
        );

      } catch (err) {
        console.error(err);

        setError(
          getApiErrorMessage(
            err,
            "Unable to load medicines."
          )
        );

      } finally {
        setMedicineLoading(
          false
        );
      }
    }, [
      canViewInventory,
      getApiErrorMessage,
    ]);


  /* =======================================================
     LOAD DISPENSING HISTORY
  ======================================================= */

  const loadDispensedMedicines =
    useCallback(async () => {
      try {
        setDispensingLoading(
          true
        );

        const data =
          await getDispensedMedicines(
            consultationId
          );

        setDispensedMedicines(
          Array.isArray(data)
            ? data
            : []
        );

      } catch (err) {
        console.error(err);

        setError(
          getApiErrorMessage(
            err,
            "Unable to load dispensed medicines."
          )
        );

      } finally {
        setDispensingLoading(
          false
        );
      }
    }, [
      consultationId,
      getApiErrorMessage,
    ]);


  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {
    loadConsultation();
    loadDiseaseCases();
    loadDispensedMedicines();

    if (
      canPredictDisease
    ) {
      loadPredictionHistory();
    }

    if (
      canViewInventory
    ) {
      loadMedicines();
    }

  }, [
    canPredictDisease,
    canViewInventory,
    loadConsultation,
    loadDiseaseCases,
    loadDispensedMedicines,
    loadMedicines,
    loadPredictionHistory,
  ]);


  /* =======================================================
     CONSULTATION FORM
  ======================================================= */

  const handleChange = (
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
  };

  const handleEdit = () => {
    clearMessages();
    setEditing(true);
  };

  const handleCancelEdit =
    async () => {
      clearMessages();
      setEditing(false);

      await loadConsultation();
    };

  const handleSave =
    async (event) => {
      event.preventDefault();

      if (
        !canEditConsultation
      ) {
        setError(
          "You do not have permission to edit consultations."
        );

        return;
      }

      try {
        setSaving(true);
        clearMessages();

        const payload = {
          chief_complaint:
            formData
              .chief_complaint
              .trim(),

          symptoms:
            textOrNull(
              formData.symptoms
            ),

          temperature:
            numberOrNull(
              formData.temperature
            ),

          systolic_bp:
            numberOrNull(
              formData.systolic_bp
            ),

          diastolic_bp:
            numberOrNull(
              formData.diastolic_bp
            ),

          heart_rate:
            numberOrNull(
              formData.heart_rate
            ),

          respiratory_rate:
            numberOrNull(
              formData
                .respiratory_rate
            ),

          oxygen_saturation:
            numberOrNull(
              formData
                .oxygen_saturation
            ),

          weight_kg:
            numberOrNull(
              formData.weight_kg
            ),

          height_cm:
            numberOrNull(
              formData.height_cm
            ),

          assessment:
            textOrNull(
              formData.assessment
            ),

          diagnosis:
            canCreateDiagnosis
              ? textOrNull(
                  formData.diagnosis
                )
              : consultation.diagnosis,

          treatment_plan:
            textOrNull(
              formData
                .treatment_plan
            ),

          notes:
            textOrNull(
              formData.notes
            ),
        };

        const updated =
          await updateConsultation(
            consultationId,
            payload
          );

        setConsultation(
          updated
        );

        setEditing(
          false
        );

        setSuccess(
          "Consultation updated successfully."
        );

      } catch (err) {
        console.error(err);

        setError(
          getApiErrorMessage(
            err,
            "Unable to update consultation."
          )
        );

      } finally {
        setSaving(false);
      }
    };


  /* =======================================================
     DISEASE CASE FORM
  ======================================================= */

  const handleDiseaseCaseChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setDiseaseCaseForm(
      (current) => ({
        ...current,
        [name]: value,
      })
    );
  };

  const resetDiseaseCaseForm = () => {
    setDiseaseCaseForm({
      ...EMPTY_DISEASE_CASE_FORM,
    });
  };

  const handleDiseaseCaseSubmit =
    async (event) => {
      event.preventDefault();

      if (
        !canRecordDiseaseCase
      ) {
        setError(
          "You do not have permission to record disease cases."
        );

        return;
      }

      if (
        !diseaseCaseForm.disease_id
      ) {
        setError(
          "Please select a disease."
        );

        return;
      }

      try {
        setDiseaseCaseSaving(
          true
        );

        clearMessages();

        const payload = {
          disease_id:
            Number(
              diseaseCaseForm
                .disease_id
            ),

          case_status:
            diseaseCaseForm
              .case_status,

          onset_date:
            diseaseCaseForm
              .onset_date ||
            null,

          remarks:
            textOrNull(
              diseaseCaseForm
                .remarks
            ),
        };

        await createDiseaseCase(
          consultationId,
          payload
        );

        resetDiseaseCaseForm();

        await loadDiseaseCases();

        setSuccess(
          "Disease case recorded successfully."
        );

      } catch (err) {
        console.error(err);

        setError(
          getApiErrorMessage(
            err,
            "Unable to record disease case."
          )
        );

      } finally {
        setDiseaseCaseSaving(
          false
        );
      }
    };

  const handleDiseaseCaseValidation =
    async (
      diseaseCaseId,
      validationStatus
    ) => {
      if (
        !canValidateDiseaseCase
      ) {
        setError(
          "You do not have permission to validate disease cases."
        );

        return;
      }

      try {
        setValidatingCaseId(
          diseaseCaseId
        );

        clearMessages();

        await updateDiseaseCaseValidation(
          diseaseCaseId,
          validationStatus
        );

        await loadDiseaseCases();

        setSuccess(
          validationStatus ===
          "VALIDATED"
            ? "Disease case validated successfully."
            : "Disease case rejected successfully."
        );

      } catch (err) {
        console.error(err);

        setError(
          getApiErrorMessage(
            err,
            "Unable to update disease case validation."
          )
        );

      } finally {
        setValidatingCaseId(
          null
        );
      }
    };


  /* =======================================================
     DISPENSING
  ======================================================= */

  const selectedMedicine =
    useMemo(
      () =>
        medicines.find(
          (medicine) =>
            medicine.id ===
            Number(
              dispensingForm
                .medicine_id
            )
        ),
      [
        dispensingForm
          .medicine_id,
        medicines,
      ]
    );

  const availableStock =
    getAvailableStock(
      selectedMedicine,
      dispensingForm
        .stock_unit
    );

  const stockUnitLabel =
    getStockUnitLabel(
      selectedMedicine,
      dispensingForm
        .stock_unit
    );

  const handleDispensingChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;

    setDispensingForm(
      (current) => ({
        ...current,
        [name]: value,
      })
    );
  };

  const openDispensingForm =
    () => {
      if (
        !canDispenseMedicine
      ) {
        return;
      }

      clearMessages();

      setShowDispensingForm(
        true
      );
    };

  const resetDispensingForm =
    () => {
      setDispensingForm({
        ...EMPTY_DISPENSING_FORM,
      });

      setShowDispensingForm(
        false
      );
    };

  const handleDispenseSubmit =
    async (event) => {
      event.preventDefault();

      if (
        !canDispenseMedicine
      ) {
        setError(
          "You do not have permission to dispense medicine."
        );

        return;
      }

      try {
        setDispensingSaving(
          true
        );

        clearMessages();

        const medicineId =
          Number(
            dispensingForm
              .medicine_id
          );

        const quantity =
          Number(
            dispensingForm
              .quantity
          );

        if (!medicineId) {
          setError(
            "Please select a medicine."
          );

          return;
        }

        if (
          Number.isNaN(
            quantity
          ) ||
          quantity <= 0
        ) {
          setError(
            "Quantity must be greater than zero."
          );

          return;
        }

        if (
          quantity >
          availableStock
        ) {
          setError(
            `Insufficient stock. Available: ${availableStock} ${stockUnitLabel}.`
          );

          return;
        }

        const payload = {
          medicine_id:
            medicineId,

          quantity,

          stock_unit:
            dispensingForm
              .stock_unit,

          dosage_instruction:
            textOrNull(
              dispensingForm
                .dosage_instruction
            ),

          remarks:
            textOrNull(
              dispensingForm
                .remarks
            ),
        };

        await dispenseMedicine(
          consultationId,
          payload
        );

        resetDispensingForm();

        await Promise.all([
          canViewInventory
            ? loadMedicines()
            : Promise.resolve(),

          loadDispensedMedicines(),
        ]);

        setSuccess(
          "Medicine dispensed successfully."
        );

      } catch (err) {
        console.error(err);

        setError(
          getApiErrorMessage(
            err,
            "Unable to dispense medicine."
          )
        );

      } finally {
        setDispensingSaving(
          false
        );
      }
    };


  /* =======================================================
     PAGE STATES
  ======================================================= */

  if (loading) {
    return (
      <div className="consultation-details-state">
        Loading consultation...
      </div>
    );
  }

  if (
    error &&
    !consultation
  ) {
    return (
      <div className="consultation-details-state">

        <p>
          {error}
        </p>

        <Link
          to="/consultations"
          className="app-action-link"
        >
          Back to Consultations
        </Link>

      </div>
    );
  }

  if (
    !consultation ||
    !formData
  ) {
    return (
      <div className="consultation-details-state">
        Consultation not found.
      </div>
    );
  }


  /* =======================================================
     PAGE
  ======================================================= */

  return (
    <div className="consultation-details-page">

      {/* ===================================================
          HEADER
      =================================================== */}

      <header className="consultation-details-header">

        <div>

          <Link
            to={`/patients/${consultation.patient_id}`}
            className="consultation-back-link"
          >
            ← Back to Patient Record
          </Link>

          <h1>
            Consultation Details
          </h1>

          <p>
            View consultation information,
            clinical findings, disease cases,
            and medicines dispensed.
          </p>

        </div>


        {canEditConsultation &&
          !editing && (

            <button
              type="button"
              className="app-button app-button-primary"
              onClick={
                handleEdit
              }
            >
              Edit Consultation
            </button>

          )}

      </header>


      {/* ===================================================
          MESSAGES
      =================================================== */}

      {error && (

        <div className="app-message app-message-error consultation-details-message">
          {error}
        </div>

      )}


      {success && (

        <div className="app-message app-message-success consultation-details-message">
          {success}
        </div>

      )}


      {/* ===================================================
          CONSULTATION VIEW / EDIT
      =================================================== */}

      {!editing ? (

        <>

          <section className="consultation-details-card">

            <SectionHeader
              title="Consultation Information"
              subtitle="General consultation details."
            />


            <div className="consultation-info-grid">

              <InfoItem
                label="Consultation ID"
                value={
                  consultation.id
                }
              />

              <InfoItem
                label="Date"
                value={
                  formatDateTime(
                    consultation
                      .consultation_date
                  )
                }
              />

              <InfoItem
                label="Chief Complaint"
                value={
                  consultation
                    .chief_complaint
                }
                full
              />

              <InfoItem
                label="Symptoms"
                value={
                  consultation
                    .symptoms ||
                  "-"
                }
                full
              />

            </div>

          </section>


          <section className="consultation-details-card">

            <SectionHeader
              title="Vital Signs"
              subtitle="Recorded patient measurements."
            />


            <div className="consultation-vitals-grid">

              <VitalCard
                label="Temperature"
                value={
                  consultation.temperature !=
                  null
                    ? `${consultation.temperature} °C`
                    : "-"
                }
              />

              <VitalCard
                label="Blood Pressure"
                value={
                  consultation.systolic_bp !=
                    null &&
                  consultation.diastolic_bp !=
                    null
                    ? `${consultation.systolic_bp}/${consultation.diastolic_bp}`
                    : "-"
                }
              />

              <VitalCard
                label="Heart Rate"
                value={
                  consultation.heart_rate !=
                  null
                    ? `${consultation.heart_rate} bpm`
                    : "-"
                }
              />

              <VitalCard
                label="Respiratory Rate"
                value={
                  consultation.respiratory_rate !=
                  null
                    ? `${consultation.respiratory_rate}/min`
                    : "-"
                }
              />

              <VitalCard
                label="Oxygen Saturation"
                value={
                  consultation.oxygen_saturation !=
                  null
                    ? `${consultation.oxygen_saturation}%`
                    : "-"
                }
              />

              <VitalCard
                label="Weight"
                value={
                  consultation.weight_kg !=
                  null
                    ? `${consultation.weight_kg} kg`
                    : "-"
                }
              />

              <VitalCard
                label="Height"
                value={
                  consultation.height_cm !=
                  null
                    ? `${consultation.height_cm} cm`
                    : "-"
                }
              />

            </div>

          </section>


          <section className="consultation-details-card">

            <SectionHeader
              title="Clinical Information"
              subtitle="Assessment, diagnosis, and treatment."
            />


            <div className="consultation-clinical-list">

              <InfoItem
                label="Assessment"
                value={
                  consultation
                    .assessment ||
                  "-"
                }
                full
              />

              <InfoItem
                label="Diagnosis"
                value={
                  consultation
                    .diagnosis ||
                  "-"
                }
                full
              />

              <InfoItem
                label="Treatment Plan"
                value={
                  consultation
                    .treatment_plan ||
                  "-"
                }
                full
              />

              <InfoItem
                label="Notes"
                value={
                  consultation
                    .notes ||
                  "-"
                }
                full
              />

            </div>

          </section>

        </>

      ) : (

        <section className="consultation-details-card">

          <SectionHeader
            title="Edit Consultation"
            subtitle="Update consultation and clinical information."
          />


          <form
            className="consultation-edit-form"
            onSubmit={
              handleSave
            }
          >

            <div className="consultation-form-section-title">
              Complaint & Symptoms
            </div>

            <ConsultationTextarea
              label="Chief Complaint"
              name="chief_complaint"
              value={
                formData
                  .chief_complaint
              }
              onChange={
                handleChange
              }
              required
            />

            <ConsultationTextarea
              label="Symptoms"
              name="symptoms"
              value={
                formData.symptoms
              }
              onChange={
                handleChange
              }
            />


            <div className="consultation-form-section-title">
              Vital Signs
            </div>

            <ConsultationInput
              label="Temperature (°C)"
              name="temperature"
              type="number"
              step="0.1"
              value={
                formData.temperature
              }
              onChange={
                handleChange
              }
            />

            <ConsultationInput
              label="Heart Rate"
              name="heart_rate"
              type="number"
              value={
                formData.heart_rate
              }
              onChange={
                handleChange
              }
            />

            <ConsultationInput
              label="Systolic BP"
              name="systolic_bp"
              type="number"
              value={
                formData.systolic_bp
              }
              onChange={
                handleChange
              }
            />

            <ConsultationInput
              label="Diastolic BP"
              name="diastolic_bp"
              type="number"
              value={
                formData.diastolic_bp
              }
              onChange={
                handleChange
              }
            />

            <ConsultationInput
              label="Respiratory Rate"
              name="respiratory_rate"
              type="number"
              value={
                formData
                  .respiratory_rate
              }
              onChange={
                handleChange
              }
            />

            <ConsultationInput
              label="Oxygen Saturation (%)"
              name="oxygen_saturation"
              type="number"
              step="0.1"
              value={
                formData
                  .oxygen_saturation
              }
              onChange={
                handleChange
              }
            />

            <ConsultationInput
              label="Weight (kg)"
              name="weight_kg"
              type="number"
              step="0.1"
              value={
                formData.weight_kg
              }
              onChange={
                handleChange
              }
            />

            <ConsultationInput
              label="Height (cm)"
              name="height_cm"
              type="number"
              step="0.1"
              value={
                formData.height_cm
              }
              onChange={
                handleChange
              }
            />


            <div className="consultation-form-section-title">
              Clinical Information
            </div>

            <ConsultationTextarea
              label="Assessment"
              name="assessment"
              value={
                formData.assessment
              }
              onChange={
                handleChange
              }
            />


            <div className="consultation-field consultation-field-full">

              <label htmlFor="diagnosis">
                Diagnosis
              </label>

              <input
                id="diagnosis"
                name="diagnosis"
                value={
                  formData.diagnosis
                }
                onChange={
                  handleChange
                }
                disabled={
                  !canCreateDiagnosis
                }
              />

              {!canCreateDiagnosis && (

                <small className="consultation-field-note">
                  You do not have permission
                  to modify the diagnosis.
                </small>

              )}

            </div>


            <ConsultationTextarea
              label="Treatment Plan"
              name="treatment_plan"
              value={
                formData
                  .treatment_plan
              }
              onChange={
                handleChange
              }
            />

            <ConsultationTextarea
              label="Notes"
              name="notes"
              value={
                formData.notes
              }
              onChange={
                handleChange
              }
            />


            <div className="consultation-form-actions">

              <button
                type="submit"
                className="app-button app-button-primary"
                disabled={
                  saving
                }
              >
                {saving
                  ? "Saving..."
                  : "Save Changes"}
              </button>

              <button
                type="button"
                className="app-button app-button-secondary"
                onClick={
                  handleCancelEdit
                }
                disabled={
                  saving
                }
              >
                Cancel
              </button>

            </div>

          </form>

        </section>

      )}


      {/* ===================================================
          ML DECISION-SUPPORT HISTORY
      =================================================== */}

      {canPredictDisease && (

        <section className="consultation-details-card">

          <div className="consultation-section-header">

            <div>

              <h2>
                ML Decision-Support History
              </h2>

              <p>
                Persistent development analyses
                linked to this consultation.
              </p>

            </div>


            <button
              type="button"
              className="app-button app-button-secondary"
              onClick={
                handleRunPersistentPrediction
              }
              disabled={
                predictionHistorySaving
              }
            >
              {predictionHistorySaving
                ? "Analyzing..."
                : "Run & Record New Analysis"}
            </button>

          </div>


          <div className="consultation-ml-history-notice">
            These records are development
            decision-support outputs only.
            They are not diagnoses and do not
            automatically create or validate
            disease cases.
          </div>


          {predictionHistoryError && (

            <div className="app-message app-message-error consultation-ml-history-error">
              {predictionHistoryError}
            </div>

          )}


          {predictionHistoryLoading ? (

            <div className="consultation-empty">
              Loading ML analysis history...
            </div>

          ) : predictionHistory.length === 0 ? (

            <div className="consultation-empty">
              No persistent ML analysis has
              been recorded for this consultation.
            </div>

          ) : (

            <div className="consultation-ml-history-list">

              {predictionHistory.map(
                (analysis) => (

                  <article
                    className="consultation-ml-history-item"
                    key={
                      analysis.id
                    }
                  >

                    <div className="consultation-ml-history-top">

                      <div>

                        <span className="consultation-ml-history-label">
                          Top Development Result
                        </span>

                        <h3>
                          {
                            analysis
                              .predicted_disease_name
                          }
                        </h3>

                        <p>
                          Development probability:{" "}
                          {(
                            Number(
                              analysis
                                .top_probability ||
                              0
                            )
                            * 100
                          ).toFixed(1)}
                          %
                        </p>

                      </div>


                      <div className="consultation-ml-history-meta">

                        <span>
                          {
                            analysis
                              .model_name
                          }
                        </span>

                        <small>
                          {
                            formatDateTime(
                              analysis
                                .created_at
                            )
                          }
                        </small>

                        <small>
                          Performed by:{" "}
                          {
                            analysis
                              .performed_by_name ||
                            "User unavailable"
                          }
                        </small>

                      </div>

                    </div>


                    <div className="consultation-ml-history-probabilities">

                      {
                        analysis
                          .probabilities
                          ?.map(
                            (item) => (

                              <div
                                className="consultation-ml-history-probability-row"
                                key={
                                  item
                                    .disease_code
                                }
                              >

                                <span>
                                  {
                                    item
                                      .disease_name
                                  }
                                </span>

                                <strong>
                                  {(
                                    Number(
                                      item
                                        .probability ||
                                      0
                                    )
                                    * 100
                                  ).toFixed(1)}
                                  %
                                </strong>

                              </div>

                            )
                          )
                      }

                    </div>


                    <div className="consultation-ml-history-inputs">

                      <span>
                        Symptoms:{" "}
                        {
                          analysis
                            .symptom_codes
                            ?.join(", ") ||
                          "-"
                        }
                      </span>

                      <span>
                        Temp:{" "}
                        {
                          analysis.temperature ??
                          "-"
                        }
                        {
                          analysis.temperature != null
                            ? " °C"
                            : ""
                        }
                      </span>

                      <span>
                        HR:{" "}
                        {
                          analysis.heart_rate ??
                          "-"
                        }
                      </span>

                      <span>
                        RR:{" "}
                        {
                          analysis.respiratory_rate ??
                          "-"
                        }
                      </span>

                      <span>
                        SpO₂:{" "}
                        {
                          analysis.oxygen_saturation ??
                          "-"
                        }
                        {
                          analysis.oxygen_saturation != null
                            ? "%"
                            : ""
                        }
                      </span>

                    </div>


                    <div className="consultation-ml-history-disclaimer">
                      {
                        analysis
                          .decision_support_notice
                      }
                    </div>

                  </article>

                )
              )}

            </div>

          )}

        </section>

      )}


      {/* ===================================================
          DISEASE CASES
      =================================================== */}

      <section className="consultation-details-card">

        <SectionHeader
          title="Disease Case & Surveillance"
          subtitle="Record and validate diseases associated with this consultation."
        />


        {canRecordDiseaseCase && (

          <form
            className="consultation-edit-form"
            onSubmit={
              handleDiseaseCaseSubmit
            }
          >

            <div className="consultation-form-section-title">
              Record Disease Case
            </div>


            <div className="consultation-field">

              <label htmlFor="disease_id">
                Disease
              </label>

              <select
                id="disease_id"
                name="disease_id"
                value={
                  diseaseCaseForm
                    .disease_id
                }
                onChange={
                  handleDiseaseCaseChange
                }
                required
              >
                <option value="">
                  Select Disease
                </option>

                {diseases.map(
                  (disease) => (

                    <option
                      key={
                        disease.id
                      }
                      value={
                        disease.id
                      }
                    >
                      {disease.name}
{disease.is_sensitive
  ? " 🔒 Sensitive"
  : ""}
                    </option>

                  )
                )}
              </select>

            </div>


            <div className="consultation-field">

              <label htmlFor="case_status">
                Case Classification
              </label>

              <select
                id="case_status"
                name="case_status"
                value={
                  diseaseCaseForm
                    .case_status
                }
                onChange={
                  handleDiseaseCaseChange
                }
              >
                <option value="SUSPECTED">
                  Suspected
                </option>

                <option value="PROBABLE">
                  Probable
                </option>

                <option value="CONFIRMED">
                  Confirmed
                </option>
              </select>

            </div>


            <ConsultationInput
              label="Symptom Onset"
              name="onset_date"
              type="date"
              value={
                diseaseCaseForm
                  .onset_date
              }
              onChange={
                handleDiseaseCaseChange
              }
            />


            <ConsultationTextarea
              label="Remarks"
              name="remarks"
              value={
                diseaseCaseForm
                  .remarks
              }
              onChange={
                handleDiseaseCaseChange
              }
              placeholder="Optional clinical remarks"
            />


            <div className="consultation-form-actions">

              <button
                type="submit"
                className="app-button app-button-primary"
                disabled={
                  diseaseCaseSaving
                }
              >
                {diseaseCaseSaving
                  ? "Recording..."
                  : "Record Disease Case"}
              </button>

            </div>

          </form>

        )}


        <div className="dispensing-history">

          <h3>
            Recorded Disease Cases
          </h3>


          {diseaseCasesLoading ? (

            <div className="consultation-empty">
              Loading disease cases...
            </div>

          ) : diseaseCases.length ===
            0 ? (

            <div className="consultation-empty">
              No disease cases recorded for
              this consultation.
            </div>

          ) : (

            <div className="consultation-table-wrap">

              <table className="consultation-table">

                <thead>
                  <tr>
                    <th>Disease</th>
                    <th>Classification</th>
                    <th>Onset Date</th>
                    <th>Validation</th>
                    <th>Remarks</th>

                    {canValidateDiseaseCase && (
                      <th>Actions</th>
                    )}
                  </tr>
                </thead>


                <tbody>

                  {diseaseCases.map(
                    (diseaseCase) => (

                      <tr
                        key={
                          diseaseCase.id
                        }
                      >

                        <td>
                          <strong>
                            {getDiseaseName(
                              diseaseCase
                                .disease_id
                            )}
                          </strong>
                        </td>

                        <td>
                          {
                            diseaseCase
                              .case_status
                          }
                        </td>

                        <td>
                          {formatDateOnly(
                            diseaseCase
                              .onset_date
                          )}
                        </td>

                        <td>
                          {
                            diseaseCase
                              .validation_status
                          }
                        </td>

                        <td>
                          {
                            diseaseCase
                              .remarks ||
                            "-"
                          }
                        </td>


                        {canValidateDiseaseCase && (

                          <td>

                            {diseaseCase
                              .validation_status ===
                            "PENDING" ? (

                              <div className="consultation-case-actions">

                                <button
                                  type="button"
                                  className="app-button app-button-primary"
                                  disabled={
                                    validatingCaseId ===
                                    diseaseCase.id
                                  }
                                  onClick={() =>
                                    handleDiseaseCaseValidation(
                                      diseaseCase.id,
                                      "VALIDATED"
                                    )
                                  }
                                >
                                  Validate
                                </button>

                                <button
                                  type="button"
                                  className="app-button app-button-secondary"
                                  disabled={
                                    validatingCaseId ===
                                    diseaseCase.id
                                  }
                                  onClick={() =>
                                    handleDiseaseCaseValidation(
                                      diseaseCase.id,
                                      "REJECTED"
                                    )
                                  }
                                >
                                  Reject
                                </button>

                              </div>

                            ) : (
                              "-"
                            )}

                          </td>

                        )}

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </div>

      </section>


      {/* ===================================================
          MEDICINE DISPENSING
      =================================================== */}

      <section className="consultation-details-card">

        <div className="consultation-section-header">

          <div>

            <h2>
              Medicines Dispensed
            </h2>

            <p>
              Medicines issued during this
              consultation.
            </p>

          </div>


          {canDispenseMedicine &&
            !showDispensingForm && (

              <button
                type="button"
                className="app-button app-button-primary"
                onClick={
                  openDispensingForm
                }
              >
                + Dispense Medicine
              </button>

            )}

        </div>


        {canDispenseMedicine &&
          showDispensingForm && (

            <form
              className="dispensing-form"
              onSubmit={
                handleDispenseSubmit
              }
            >

              <div className="consultation-form-section-title">
                Dispense Medicine
              </div>


              <div className="consultation-field consultation-field-full">

                <label htmlFor="medicine_id">
                  Medicine
                </label>

                <select
                  id="medicine_id"
                  name="medicine_id"
                  value={
                    dispensingForm
                      .medicine_id
                  }
                  onChange={
                    handleDispensingChange
                  }
                  required
                  disabled={
                    medicineLoading
                  }
                >
                  <option value="">
                    {medicineLoading
                      ? "Loading medicines..."
                      : "Select Medicine"}
                  </option>

                  {medicines.map(
                    (medicine) => (

                      <option
                        key={
                          medicine.id
                        }
                        value={
                          medicine.id
                        }
                      >
                        {medicine.name}

                        {medicine
                          .dosage_strength
                          ? ` - ${medicine.dosage_strength}`
                          : ""}
                      </option>

                    )
                  )}
                </select>

              </div>


              {selectedMedicine && (

                <div className="dispensing-stock-summary">

                  <div>
                    <span>
                      Package Stock
                    </span>

                    <strong>
                      {
                        selectedMedicine
                          .package_stock
                      }{" "}
                      {selectedMedicine
                        .package_unit ||
                        "package(s)"}
                    </strong>
                  </div>


                  <div>
                    <span>
                      Loose Stock
                    </span>

                    <strong>
                      {
                        selectedMedicine
                          .loose_stock
                      }{" "}
                      {selectedMedicine
                        .dispensing_unit ||
                        "piece(s)"}
                    </strong>
                  </div>

                </div>

              )}


              <div className="consultation-field">

                <label htmlFor="stock_unit">
                  Dispense From
                </label>

                <select
                  id="stock_unit"
                  name="stock_unit"
                  value={
                    dispensingForm
                      .stock_unit
                  }
                  onChange={
                    handleDispensingChange
                  }
                >
                  <option value="LOOSE">
                    Loose Stock
                  </option>

                  <option value="PACKAGE">
                    Package Stock
                  </option>
                </select>

              </div>


              <ConsultationInput
                label={`Quantity${
                  stockUnitLabel
                    ? ` (${stockUnitLabel})`
                    : ""
                }`}
                name="quantity"
                type="number"
                min="1"
                max={
                  availableStock > 0
                    ? availableStock
                    : undefined
                }
                value={
                  dispensingForm
                    .quantity
                }
                onChange={
                  handleDispensingChange
                }
                required
              />


              {selectedMedicine && (

                <div className="dispensing-available consultation-field-full">

                  Available:{" "}

                  <strong>
                    {availableStock}{" "}
                    {stockUnitLabel}
                  </strong>

                </div>

              )}


              <ConsultationTextarea
                label="Dosage Instructions"
                name="dosage_instruction"
                value={
                  dispensingForm
                    .dosage_instruction
                }
                onChange={
                  handleDispensingChange
                }
                placeholder="e.g. Take 1 tablet once daily"
              />


              <ConsultationTextarea
                label="Remarks"
                name="remarks"
                value={
                  dispensingForm
                    .remarks
                }
                onChange={
                  handleDispensingChange
                }
              />


              <div className="consultation-form-actions">

                <button
                  type="submit"
                  className="app-button app-button-primary"
                  disabled={
                    dispensingSaving ||
                    !selectedMedicine ||
                    availableStock <= 0
                  }
                >
                  {dispensingSaving
                    ? "Dispensing..."
                    : "Dispense Medicine"}
                </button>


                <button
                  type="button"
                  className="app-button app-button-secondary"
                  onClick={
                    resetDispensingForm
                  }
                  disabled={
                    dispensingSaving
                  }
                >
                  Cancel
                </button>

              </div>

            </form>

          )}


        <div className="dispensing-history">

          <h3>
            Dispensing History
          </h3>


          {dispensingLoading ? (

            <div className="consultation-empty">
              Loading dispensed medicines...
            </div>

          ) : dispensedMedicines.length ===
            0 ? (

            <div className="consultation-empty">
              No medicines dispensed for
              this consultation.
            </div>

          ) : (

            <div className="consultation-table-wrap">

              <table className="consultation-table">

                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Medicine</th>
                    <th>Quantity</th>
                    <th>Unit</th>
                    <th>
                      Dosage Instructions
                    </th>
                    <th>Remarks</th>
                  </tr>
                </thead>


                <tbody>

                  {dispensedMedicines.map(
                    (item) => (

                      <tr
                        key={
                          item.id
                        }
                      >

                        <td>
                          {formatDateTime(
                            item.dispensed_at
                          )}
                        </td>

                        <td>
                          <strong>
                            {getMedicineName(
                              item.medicine_id
                            )}
                          </strong>
                        </td>

                        <td>
                          {item.quantity}
                        </td>

                        <td>
                          {item.stock_unit}
                        </td>

                        <td>
                          {
                            item
                              .dosage_instruction ||
                            "-"
                          }
                        </td>

                        <td>
                          {
                            item.remarks ||
                            "-"
                          }
                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </div>

      </section>

    </div>
  );
}


/* =========================================================
   REUSABLE COMPONENTS
========================================================= */

function SectionHeader({
  title,
  subtitle,
}) {
  return (
    <div className="consultation-section-header">

      <div>

        <h2>
          {title}
        </h2>

        {subtitle && (
          <p>
            {subtitle}
          </p>
        )}

      </div>

    </div>
  );
}


function InfoItem({
  label,
  value,
  full = false,
}) {
  return (
    <div
      className={
        full
          ? "consultation-info-item consultation-info-full"
          : "consultation-info-item"
      }
    >

      <span>
        {label}
      </span>

      <strong>
        {value ?? "-"}
      </strong>

    </div>
  );
}


function VitalCard({
  label,
  value,
}) {
  return (
    <div className="consultation-vital-card">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


function ConsultationInput({
  label,
  name,
  value,
  onChange,
  type = "text",
  step,
  min,
  max,
  required = false,
}) {
  return (
    <div className="consultation-field">

      <label htmlFor={name}>
        {label}
      </label>

      <input
        id={name}
        name={name}
        type={type}
        step={step}
        min={min}
        max={max}
        value={value}
        onChange={onChange}
        required={required}
      />

    </div>
  );
}


function ConsultationTextarea({
  label,
  name,
  value,
  onChange,
  placeholder = "",
  required = false,
}) {
  return (
    <div className="consultation-field consultation-field-full">

      <label htmlFor={name}>
        {label}
      </label>

      <textarea
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
      />

    </div>
  );
}


export default ConsultationDetails;
