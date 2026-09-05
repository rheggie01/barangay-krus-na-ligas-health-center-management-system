import api from "./axios";


export const getDiseaseCaseCounts = async (
  startDate = "",
  endDate = "",
  scope = "GENERAL"
) => {
  const params = {
    scope,
  };

  if (startDate) {
    params.start_date = startDate;
  }

  if (endDate) {
    params.end_date = endDate;
  }

  const response = await api.get(
    "/surveillance/disease-cases",
    {
      params,
    }
  );

  return response.data;
};


export const getWeeklyDiseaseComparison = async (
  scope = "GENERAL"
) => {
  const response = await api.get(
    "/surveillance/weekly-comparison",
    {
      params: {
        scope,
      },
    }
  );

  return response.data;
};


export const getDiseaseCasesByStreet = async (
  startDate = "",
  endDate = "",
  diseaseId = null,
  scope = "GENERAL"
) => {
  const params = {
    scope,
  };

  if (startDate) {
    params.start_date = startDate;
  }

  if (endDate) {
    params.end_date = endDate;
  }

  if (diseaseId) {
    params.disease_id = diseaseId;
  }

  const response = await api.get(
    "/surveillance/by-street",
    {
      params,
    }
  );

  return response.data;
};