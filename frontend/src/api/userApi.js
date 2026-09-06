import api from "./axios";


export const getUsers = async () => {
  const response =
    await api.get(
      "/users/"
    );

  return response.data;
};


export const approveUser =
  async (
    userId
  ) => {
    const response =
      await api.post(
        `/users/${userId}/approve`
      );

    return response.data;
  };


export const deactivateUser =
  async (
    userId
  ) => {
    const response =
      await api.post(
        `/users/${userId}/deactivate`
      );

    return response.data;
  };


export const reactivateUser =
  async (
    userId
  ) => {
    const response =
      await api.post(
        `/users/${userId}/reactivate`
      );

    return response.data;
  };


export const deleteInactiveUser =
  async (
    userId
  ) => {
    await api.delete(
      `/users/${userId}`
    );

    return true;
  };


export const deletePendingUser =
  async (
    userId
  ) => {
    await api.delete(
      `/users/${userId}/pending`
    );

    return true;
  };


/* Backward-compatible helper for older callers. */
export const updateUserStatus =
  async (
    userId,
    isActive
  ) => {
    const response =
      await api.patch(
        `/users/${userId}/status`,
        {
          is_active:
            isActive,
        }
      );

    return response.data;
  };
