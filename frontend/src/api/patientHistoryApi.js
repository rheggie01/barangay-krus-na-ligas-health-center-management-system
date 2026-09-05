import api from "./axios";


export const getPatientHistory = async (patientId) => {
  const response = await api.get(
    `/patients/${patientId}/history`
  );

  return response.data;
};


export const createPatientHistory = async (
  patientId,
  historyData
) => {
  const response = await api.post(
    `/patients/${patientId}/history`,
    historyData
  );

  return response.data;
};