import api from "./axios";


export const getMedicines = async (
  search = "",
  activeOnly = false,
  filters = {}
) => {
  const response = await api.get(
    "/medicines/",
    {
      params: {
        search:
          search || undefined,

        active_only:
          activeOnly,

        medicine_category:
          filters
            .medicineCategory ||
          undefined,

        formulary_status:
          filters
            .formularyStatus ||
          undefined,

        forecast_enabled:
          filters
            .forecastEnabled,

        stock_verified:
          filters
            .stockVerified,
      },
    }
  );

  return response.data;
};


export const getMedicine = async (
  medicineId
) => {
  const response = await api.get(
    `/medicines/${medicineId}`
  );

  return response.data;
};


export const createMedicine = async (
  medicineData
) => {
  const response = await api.post(
    "/medicines/",
    medicineData
  );

  return response.data;
};


export const updateMedicine = async (
  medicineId,
  medicineData
) => {
  const response = await api.patch(
    `/medicines/${medicineId}`,
    medicineData
  );

  return response.data;
};
