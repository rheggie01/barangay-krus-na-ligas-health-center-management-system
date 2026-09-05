import api from "./axios";


export const predictDisease =
  async (
    predictionData
  ) => {
    const response =
      await api.post(
        "/predictions/disease",
        predictionData
      );

    return response.data;
  };


export const createConsultationPrediction =
  async (
    consultationId
  ) => {
    const response =
      await api.post(
        `/predictions/consultations/${consultationId}/disease`
      );

    return response.data;
  };


export const getConsultationPredictions =
  async (
    consultationId
  ) => {
    const response =
      await api.get(
        `/predictions/consultations/${consultationId}`
      );

    return response.data;
  };
