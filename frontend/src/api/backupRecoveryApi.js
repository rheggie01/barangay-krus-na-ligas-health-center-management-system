import api from "./axios";


export const getBackupRecoveryStatus = async () => {
  const response = await api.get(
    "/backup-recovery/status"
  );

  return response.data;
};


export const runBackupNow = async () => {
  const response = await api.post(
    "/backup-recovery/run-backup"
  );

  return response.data;
};


export const runRestoreTest = async () => {
  const response = await api.post(
    "/backup-recovery/run-restore-test"
  );

  return response.data;
};
