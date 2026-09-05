import api from "./axios";


/* =========================================================
   GET CONSULTATION DISEASE CASES
========================================================= */

export const getConsultationDiseaseCases = async (
  consultationId
) => {
  const response = await api.get(
    `/consultations/${consultationId}/disease-cases`
  );

  return response.data;
};


/* =========================================================
   CREATE DISEASE CASE
========================================================= */

export const createDiseaseCase = async (
  consultationId,
  diseaseCaseData
) => {
  const response = await api.post(
    `/consultations/${consultationId}/disease-cases`,
    diseaseCaseData
  );

  return response.data;
};


/* =========================================================
   GET DISEASE CASE
========================================================= */

export const getDiseaseCase = async (
  diseaseCaseId
) => {
  const response = await api.get(
    `/disease-cases/${diseaseCaseId}`
  );

  return response.data;
};


/* =========================================================
   UPDATE DISEASE CASE
========================================================= */

export const updateDiseaseCase = async (
  diseaseCaseId,
  diseaseCaseData
) => {
  const response = await api.patch(
    `/disease-cases/${diseaseCaseId}`,
    diseaseCaseData
  );

  return response.data;
};


/* =========================================================
   UPDATE VALIDATION STATUS
========================================================= */

export const updateDiseaseCaseValidation = async (
  diseaseCaseId,
  validationStatus
) => {
  const response = await api.patch(
    `/disease-cases/${diseaseCaseId}/validation`,
    {
      validation_status:
        validationStatus,
    }
  );

  return response.data;
};