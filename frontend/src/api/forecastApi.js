import api from "./axios";


/* =========================================================
   DISEASE FORECASTS
========================================================= */

export const getDiseaseForecasts =
  async () => {
    const response =
      await api.get(
        "/forecasts/diseases"
      );

    return response.data;
  };


export const getDiseaseForecast =
  async (
    diseaseCode
  ) => {
    const response =
      await api.get(
        `/forecasts/diseases/${diseaseCode}`
      );

    return response.data;
  };


export const getDiseaseForecastCatalog =
  async ({
    includeSensitive = null,
  } = {}) => {
    const params =
      includeSensitive === null
        ? {}
        : {
            include_sensitive:
              includeSensitive,
          };

    const response =
      await api.get(
        "/forecasts/diseases/catalog",
        {
          params,
        }
      );

    return response.data;
  };


/* =========================================================
   MEDICINE DEMAND FORECASTS + RESOURCE ALLOCATION DSS
========================================================= */

export const getMedicineForecasts =
  async () => {
    const response =
      await api.get(
        "/forecasts/medicines"
      );

    return response.data;
  };


export const getMedicineForecast =
  async (
    medicineCode
  ) => {
    const response =
      await api.get(
        `/forecasts/medicines/${medicineCode}`
      );

    return response.data;
  };



/* =========================================================
   DEVELOPMENT DISEASE -> MEDICINE MAPPING
========================================================= */

export const getDiseaseMedicineMappings =
  async ({
    includeSensitive = null,
  } = {}) => {
    const params =
      includeSensitive === null
        ? {}
        : {
            include_sensitive:
              includeSensitive,
          };

    const response =
      await api.get(
        "/forecasts/disease-medicine-mappings",
        {
          params,
        }
      );

    return response.data;
  };
