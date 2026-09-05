import api from "./axios";


export const getAuditLogs = async ({
  module = "",
  action = "",
  limit = 100,
} = {}) => {
  const response = await api.get(
    "/audit-logs/",
    {
      params: {
        module: module || undefined,
        action: action || undefined,
        limit,
      },
    }
  );

  return response.data;
};
