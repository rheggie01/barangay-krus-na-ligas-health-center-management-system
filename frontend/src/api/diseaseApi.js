import api from "./axios";


/* =========================================================
   GET ALL DISEASES
========================================================= */

export const getDiseases = async () => {
  const response = await api.get(
    "/diseases/"
  );

  return response.data;
};


/* =========================================================
   GET ACTIVE DISEASES
========================================================= */

export const getActiveDiseases = async () => {
  const response = await api.get(
    "/diseases/",
    {
      params: {
        active_only: true,
      },
    }
  );

  return response.data;
};