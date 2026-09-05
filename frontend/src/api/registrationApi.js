import api from "./axios";


/* =========================================================
   PUBLIC USER REGISTRATION
========================================================= */

export const registerUser = async (payload) => {
  const response = await api.post(
    "/auth/register",
    payload
  );

  return response.data;
};