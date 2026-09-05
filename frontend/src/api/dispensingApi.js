import api from "./axios";


export const getDispensedMedicines = async (
  consultationId
) => {
  const response = await api.get(
    `/consultations/${consultationId}/medicines`
  );

  return response.data;
};


export const dispenseMedicine = async (
  consultationId,
  data
) => {
  const response = await api.post(
    `/consultations/${consultationId}/medicines`,
    data
  );

  return response.data;
};