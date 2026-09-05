import api from "./axios";


/* =========================================================
   GET INVENTORY TRANSACTIONS
========================================================= */

export const getInventoryTransactions =
  async (
    medicineId = null
  ) => {
    const params = {};


    if (medicineId) {
      params.medicine_id =
        medicineId;
    }


    const response =
      await api.get(
        "/inventory/transactions",
        {
          params,
        }
      );


    return response.data;
  };


/* =========================================================
   CREATE INVENTORY TRANSACTION
========================================================= */

export const createInventoryTransaction =
  async (
    medicineId,
    transactionData
  ) => {
    const response =
      await api.post(
        `/inventory/medicines/${medicineId}/transactions`,
        transactionData
      );


    return response.data;
  };


/* =========================================================
   GET MEDICINE DISPENSING HISTORY
========================================================= */

export const getMedicineDispensings =
  async ({
    patientId = null,
    medicineId = null,
  } = {}) => {
    const params = {};


    if (patientId) {
      params.patient_id =
        patientId;
    }


    if (medicineId) {
      params.medicine_id =
        medicineId;
    }


    const response =
      await api.get(
        "/inventory/dispensings",
        {
          params,
        }
      );


    return response.data;
  };


/* =========================================================
   DISPENSE MEDICINE
========================================================= */

export const createMedicineDispensing =
  async (
    dispensingData
  ) => {
    const response =
      await api.post(
        "/inventory/dispensings",
        dispensingData
      );


    return response.data;
  };