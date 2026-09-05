import api from "./axios";


/* =========================================================
   GET PATIENT CONSULTATIONS
========================================================= */

export const getPatientConsultations = async (
  patientId
) => {
  const response = await api.get(
    `/patients/${patientId}/consultations`
  );

  return response.data;
};


/* =========================================================
   CREATE CONSULTATION
========================================================= */

export const createConsultation = async (
  patientId,
  consultationData
) => {
  const response = await api.post(
    `/patients/${patientId}/consultations`,
    consultationData
  );

  return response.data;
};


/* =========================================================
   GET CONSULTATION
========================================================= */

export const getConsultation = async (
  consultationId
) => {
  const response = await api.get(
    `/consultations/${consultationId}`
  );

  return response.data;
};


/* =========================================================
   UPDATE CONSULTATION
========================================================= */

export const updateConsultation = async (
  consultationId,
  consultationData
) => {
  const response = await api.patch(
    `/consultations/${consultationId}`,
    consultationData
  );

  return response.data;
};