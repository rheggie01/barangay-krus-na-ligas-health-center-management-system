import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  createMedicine,
  getMedicines,
  updateMedicine,
} from "../api/medicineApi";

import {
  createInventoryTransaction,
  getInventoryTransactions,
} from "../api/inventoryApi";

import {
  useAuth,
} from "../context/AuthContext";

import {
  hasPermission,
} from "../utils/permissions";

import "../styles/Inventory.css";
import "../styles/InventoryAudit.css";


/* =========================================================
   DEFAULT FORM VALUES
========================================================= */

const MEDICINE_CATEGORIES = [
  ["", "All Categories"],
  ["GENERAL", "General"],
  ["ANTI_INFECTIVE", "Anti-infective"],
  ["ANTI_THROMBOTIC", "Anti-thrombotic"],
  ["ANTI_ASTHMA_COPD", "Anti-asthma / COPD"],
  ["SUPPORTIVE_OTHER", "Supportive / Other"],
  ["ANTI_DIABETIC", "Anti-diabetic"],
  ["ANTI_DYSLIPIDEMIA", "Anti-dyslipidemia"],
  [
    "ANTI_HYPERTENSIVE_CARDIOLOGY",
    "Anti-hypertensive / Cardiology",
  ],
  ["NERVOUS_SYSTEM", "Nervous System"],
  ["SENSITIVE_PROGRAM", "Sensitive / Program-managed"],
];


const FORMULARY_STATUSES = [
  ["", "All Formulary Statuses"],
  ["CANDIDATE", "Candidate"],
  ["VERIFIED", "Verified"],
  ["NOT_STOCKED", "Not Stocked"],
];


const PROGRAM_TYPES = [
  ["", "None"],
  ["TB", "TB"],
  ["HIV", "HIV"],
  ["STI", "STI"],
];


const EMPTY_MEDICINE_FORM = {
  code: "",
  name: "",
  generic_name: "",
  dosage_strength: "",
  dosage_form: "",
  medicine_category: "GENERAL",
  formulary_status: "CANDIDATE",
  program_type: "",
  requires_prescription: false,
  restricted_dispensing: false,
  sensitive_inventory: false,
  forecast_enabled: true,
  stock_verified: false,
  package_unit: "",
  dispensing_unit: "piece",
  units_per_package: "",
  package_stock: "0",
  loose_stock: "0",
  reorder_level: "10",
  is_active: true,
};


const EMPTY_TRANSACTION_FORM = {
  transaction_type: "STOCK_IN",
  stock_unit: "PACKAGE",
  quantity: "",
  reference: "",
  reason: "",
  notes: "",
};


/* =========================================================
   INVENTORY PAGE
========================================================= */

function Inventory() {
  // =======================================================
  // AUTHORIZATION
  // =======================================================

  const {
    user,
    loading: authLoading,
  } = useAuth();


  const permissions =
    user?.permissions ?? [];


  const canViewInventory =
    hasPermission(
      permissions,
      "INVENTORY_VIEW"
    );


  const canAdjustInventory =
    hasPermission(
      permissions,
      "INVENTORY_ADJUST"
    );


  // =======================================================
  // MEDICINES
  // =======================================================

  const [
    medicines,
    setMedicines,
  ] = useState([]);


  const [
    search,
    setSearch,
  ] = useState("");


  const [
    activeOnly,
    setActiveOnly,
  ] = useState(false);


  const [
    categoryFilter,
    setCategoryFilter,
  ] = useState("");


  const [
    formularyStatusFilter,
    setFormularyStatusFilter,
  ] = useState("");


  const [
    recordsView,
    setRecordsView,
  ] = useState("ACTIVE");


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    saving,
    setSaving,
  ] = useState(false);


  // =======================================================
  // MEDICINE FORM
  // =======================================================

  const [
    showMedicineForm,
    setShowMedicineForm,
  ] = useState(false);


  const [
    editingMedicineId,
    setEditingMedicineId,
  ] = useState(null);


  const [
    verificationMode,
    setVerificationMode,
  ] = useState(false);


  const [
    medicineForm,
    setMedicineForm,
  ] = useState({
    ...EMPTY_MEDICINE_FORM,
  });


  // =======================================================
  // INVENTORY TRANSACTIONS
  // =======================================================

  const [
    transactions,
    setTransactions,
  ] = useState([]);


  const [
    transactionLoading,
    setTransactionLoading,
  ] = useState(true);


  const [
    transactionSaving,
    setTransactionSaving,
  ] = useState(false);


  const [
    selectedMedicine,
    setSelectedMedicine,
  ] = useState(null);


  const [
    showTransactionForm,
    setShowTransactionForm,
  ] = useState(false);


  const [
    transactionForm,
    setTransactionForm,
  ] = useState({
    ...EMPTY_TRANSACTION_FORM,
  });


  // =======================================================
  // MESSAGES
  // =======================================================

  const [
    error,
    setError,
  ] = useState("");


  const [
    success,
    setSuccess,
  ] = useState("");


  // =======================================================
  // HELPERS
  // =======================================================

  const clearMessages = () => {
    setError("");
    setSuccess("");
  };


  const textOrNull = (
    value
  ) => {
    if (
      typeof value !== "string"
    ) {
      return null;
    }

    const cleaned =
      value.trim();

    return cleaned || null;
  };


  const numberOrNull = (
    value
  ) => {
    if (
      value === ""
    ) {
      return null;
    }

    const parsed =
      Number(value);

    return Number.isNaN(parsed)
      ? null
      : parsed;
  };


  const numberOrZero = (
    value
  ) => {
    const parsed =
      Number(value);

    return Number.isNaN(parsed)
      ? 0
      : parsed;
  };


  const getStockQuantity = useCallback((
    medicine
  ) => {
    const packageStock =
      Number(
        medicine.package_stock ?? 0
      );

    const looseStock =
      Number(
        medicine.loose_stock ?? 0
      );

    const unitsPerPackage =
      Number(
        medicine.units_per_package ?? 0
      );


    if (
      unitsPerPackage > 0
    ) {
      return (
        packageStock *
          unitsPerPackage +
        looseStock
      );
    }


    return (
      packageStock +
      looseStock
    );
  }, []);


  const getStockDisplay = (
    medicine
  ) => {
    const parts = [];


    if (
      medicine.package_stock > 0
    ) {
      parts.push(
        medicine.package_unit
          ? `${medicine.package_stock} ${medicine.package_unit}`
          : `${medicine.package_stock} package(s)`
      );
    }


    if (
      medicine.loose_stock > 0
    ) {
      parts.push(
        `${medicine.loose_stock} ${
          medicine.dispensing_unit ||
          "piece(s)"
        }`
      );
    }


    if (
      parts.length === 0
    ) {
      return `0 ${
        medicine.dispensing_unit ||
        "piece(s)"
      }`;
    }


    return parts.join(
      " + "
    );
  };


  const getStockStatus = useCallback((
    medicine
  ) => {
    const stock =
      getStockQuantity(
        medicine
      );


    if (
      !medicine.stock_verified
    ) {
      return "UNVERIFIED";
    }


    if (
      stock <= 0
    ) {
      return "OUT OF STOCK";
    }


    if (
      stock <=
      Number(
        medicine.reorder_level ?? 0
      )
    ) {
      return "LOW STOCK";
    }


    return "IN STOCK";
  }, [
    getStockQuantity,
  ]);


  const getStockStatusClass = (
    medicine
  ) => {
    const status =
      getStockStatus(
        medicine
      );


    if (
      status === "OUT OF STOCK"
    ) {
      return (
        "inventory-status " +
        "inventory-status-out"
      );
    }


    if (
      status === "LOW STOCK"
    ) {
      return (
        "inventory-status " +
        "inventory-status-low"
      );
    }


    if (
      status === "UNVERIFIED"
    ) {
      return (
        "inventory-status " +
        "inventory-status-unverified"
      );
    }


    return (
      "inventory-status " +
      "inventory-status-good"
    );
  };


  const getTransactionSign = (
    transactionType
  ) => {
    if (
      transactionType ===
        "STOCK_IN" ||
      transactionType ===
        "ADJUSTMENT_IN"
    ) {
      return "+";
    }


    if (
      transactionType ===
        "ADJUSTMENT_OUT" ||
      transactionType ===
        "DISPENSE"
    ) {
      return "-";
    }


    return "";
  };


  const getMedicineName = (
    medicineId
  ) => {
    const medicine =
      medicines.find(
        (item) =>
          item.id === medicineId
      );


    return medicine
      ? medicine.name
      : `Medicine #${medicineId}`;
  };


  const formatTransactionType = (
    type
  ) => {
    if (!type) {
      return "-";
    }


    return type
      .replaceAll(
        "_",
        " "
      )
      .toLowerCase()
      .replace(
        /\b\w/g,
        (letter) =>
          letter.toUpperCase()
      );
  };


  const getErrorMessage = useCallback((
    err,
    fallback
  ) => {
    const detail =
      err.response?.data?.detail;


    if (
      Array.isArray(detail)
    ) {
      return detail
        .map(
          (item) =>
            item.msg
        )
        .join(", ");
    }


    return (
      detail ||
      fallback
    );
  }, []);


  // =======================================================
  // LOAD MEDICINES
  // =======================================================

  const loadMedicines = useCallback(async (
    searchValue,
    activeValue
  ) => {
    if (
      !canViewInventory
    ) {
      setMedicines([]);
      setLoading(false);

      return;
    }


    try {
      setLoading(true);
      setError("");


      const data =
        await getMedicines(
          searchValue,
          activeValue,
          {
            medicineCategory:
              categoryFilter,

            formularyStatus:
              formularyStatusFilter,
          }
        );


      setMedicines(
        data
      );

    } catch (err) {
      console.error(
        err
      );


      setError(
        getErrorMessage(
          err,
          "Unable to load medicine inventory."
        )
      );

    } finally {
      setLoading(false);
    }
  }, [
    canViewInventory,
    categoryFilter,
    formularyStatusFilter,
    getErrorMessage,
  ]);


  // =======================================================
  // LOAD TRANSACTIONS
  // =======================================================

  const loadTransactions =
    useCallback(async () => {
      if (
        !canViewInventory
      ) {
        setTransactions([]);
        setTransactionLoading(
          false
        );

        return;
      }


      try {
        setTransactionLoading(
          true
        );


        const data =
          await getInventoryTransactions();


        setTransactions(
          data
        );

      } catch (err) {
        console.error(
          err
        );


        setError(
          getErrorMessage(
            err,
            "Unable to load inventory transactions."
          )
        );

      } finally {
        setTransactionLoading(
          false
        );
      }
    }, [
      canViewInventory,
      getErrorMessage,
    ]);


  // =======================================================
  // INITIAL LOAD
  // =======================================================

  useEffect(() => {
    if (
      authLoading
    ) {
      return;
    }


    if (
      !canViewInventory
    ) {
      setLoading(false);
      setTransactionLoading(
        false
      );

      return;
    }


    loadMedicines(
      "",
      activeOnly
    );

    loadTransactions();

  }, [
    activeOnly,
    authLoading,
    canViewInventory,
    loadMedicines,
    loadTransactions,
  ]);


  // =======================================================
  // ACTIVE FILTER
  // =======================================================

  useEffect(() => {
    if (
      authLoading ||
      !canViewInventory
    ) {
      return;
    }


    loadMedicines(
      search,
      activeOnly
    );

  }, [
    activeOnly,
    authLoading,
    canViewInventory,
    loadMedicines,
    categoryFilter,
    formularyStatusFilter,
    search,
  ]);


  // =======================================================
  // SEARCH
  // =======================================================

  const handleSearchSubmit =
    async (event) => {
      event.preventDefault();


      if (
        !canViewInventory
      ) {
        return;
      }


      await loadMedicines(
        search,
        activeOnly
      );
    };


  const handleClearSearch =
    async () => {
      setSearch("");


      if (
        !canViewInventory
      ) {
        return;
      }


      await loadMedicines(
        "",
        activeOnly
      );
    };


  // =======================================================
  // MEDICINE FORM
  // =======================================================

  const handleMedicineChange = (
    event
  ) => {
    const {
      name,
      value,
      type,
      checked,
    } = event.target;


    setMedicineForm(
      (current) => ({
        ...current,

        [name]:
          type === "checkbox"
            ? checked
            : value,
      })
    );
  };


  const resetMedicineForm =
    () => {
      setMedicineForm({
        ...EMPTY_MEDICINE_FORM,
      });


      setEditingMedicineId(
        null
      );


      setVerificationMode(
        false
      );


      setShowMedicineForm(
        false
      );
    };


  const handleAddMedicine =
    () => {
      if (
        !canAdjustInventory
      ) {
        setError(
          "You do not have permission to add medicines."
        );

        return;
      }


      clearMessages();


      setMedicineForm({
        ...EMPTY_MEDICINE_FORM,
      });


      setEditingMedicineId(
        null
      );


      setVerificationMode(
        false
      );


      setShowMedicineForm(
        true
      );
    };


  const handleEditMedicine = (
    medicine
  ) => {
    if (
      !canAdjustInventory
    ) {
      setError(
        "You do not have permission to edit medicines."
      );

      return;
    }


    clearMessages();


    setEditingMedicineId(
      medicine.id
    );


    setVerificationMode(
      false
    );


    setMedicineForm({
      code:
        medicine.code || "",

      name:
        medicine.name || "",

      generic_name:
        medicine.generic_name ||
        "",

      dosage_strength:
        medicine.dosage_strength ||
        "",

      dosage_form:
        medicine.dosage_form ||
        "",

      medicine_category:
        medicine.medicine_category ||
        "GENERAL",

      formulary_status:
        medicine.formulary_status ||
        "CANDIDATE",

      program_type:
        medicine.program_type ||
        "",

      requires_prescription:
        Boolean(
          medicine
            .requires_prescription
        ),

      restricted_dispensing:
        Boolean(
          medicine
            .restricted_dispensing
        ),

      sensitive_inventory:
        Boolean(
          medicine
            .sensitive_inventory
        ),

      forecast_enabled:
        Boolean(
          medicine
            .forecast_enabled
        ),

      stock_verified:
        Boolean(
          medicine
            .stock_verified
        ),

      package_unit:
        medicine.package_unit ||
        "",

      dispensing_unit:
        medicine.dispensing_unit ||
        "piece",

      units_per_package:
        medicine.units_per_package ??
        "",

      package_stock:
        medicine.package_stock ??
        0,

      loose_stock:
        medicine.loose_stock ??
        0,

      reorder_level:
        medicine.reorder_level ??
        10,

      is_active:
        medicine.is_active,
    });


    setShowMedicineForm(
      true
    );
  };


  const handleVerifyCandidate = (
    medicine
  ) => {
    if (
      !canAdjustInventory
    ) {
      setError(
        "You do not have permission to verify formulary medicines."
      );

      return;
    }


    if (
      medicine.stock_verified
    ) {
      setError(
        "This medicine is already part of the active inventory."
      );

      return;
    }


    handleEditMedicine(
      medicine
    );


    setVerificationMode(
      true
    );


    setMedicineForm(
      (current) => ({
        ...current,

        formulary_status:
          "VERIFIED",

        stock_verified:
          true,

        is_active:
          true,
      })
    );
  };


  const handleMedicineSubmit =
    async (event) => {
      event.preventDefault();


      if (
        !canAdjustInventory
      ) {
        setError(
          "You do not have permission to modify medicine records."
        );

        return;
      }


      try {
        setSaving(true);
        clearMessages();


        const payload = {
          code:
            medicineForm.code
              .trim()
              .toUpperCase(),

          name:
            medicineForm.name
              .trim(),

          generic_name:
            textOrNull(
              medicineForm.generic_name
            ),

          dosage_strength:
            textOrNull(
              medicineForm
                .dosage_strength
            ),

          dosage_form:
            textOrNull(
              medicineForm.dosage_form
            ),

          medicine_category:
            medicineForm
              .medicine_category,

          formulary_status:
            medicineForm
              .formulary_status,

          program_type:
            textOrNull(
              medicineForm
                .program_type
            ),

          requires_prescription:
            medicineForm
              .requires_prescription,

          restricted_dispensing:
            medicineForm
              .restricted_dispensing,

          sensitive_inventory:
            medicineForm
              .sensitive_inventory,

          forecast_enabled:
            medicineForm
              .forecast_enabled,

          stock_verified:
            medicineForm
              .stock_verified,

          package_unit:
            textOrNull(
              medicineForm.package_unit
            ),

          dispensing_unit:
            medicineForm
              .dispensing_unit
              .trim(),

          units_per_package:
            numberOrNull(
              medicineForm
                .units_per_package
            ),

          package_stock:
            numberOrZero(
              medicineForm
                .package_stock
            ),

          loose_stock:
            numberOrZero(
              medicineForm
                .loose_stock
            ),

          reorder_level:
            numberOrZero(
              medicineForm
                .reorder_level
            ),

          is_active:
            medicineForm.is_active,
        };


        if (
          verificationMode
        ) {
          payload.formulary_status =
            "VERIFIED";

          payload.stock_verified =
            true;

          payload.is_active =
            true;
        }


        if (
          editingMedicineId
        ) {
          await updateMedicine(
            editingMedicineId,
            payload
          );


          setSuccess(
            verificationMode
              ? "Medicine verified and added to active inventory."
              : "Medicine updated successfully."
          );

        } else {
          await createMedicine(
            payload
          );


          setSuccess(
            "Medicine added successfully."
          );
        }


        resetMedicineForm();


        await loadMedicines(
          search,
          activeOnly
        );

      } catch (err) {
        console.error(
          err
        );


        setError(
          getErrorMessage(
            err,
            "Unable to save medicine."
          )
        );

      } finally {
        setSaving(false);
      }
    };


  // =======================================================
  // INVENTORY TRANSACTION FORM
  // =======================================================

  const handleTransactionChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target;


    setTransactionForm(
      (current) => ({
        ...current,
        [name]: value,
      })
    );
  };


  const openStockInForm = (
    medicine
  ) => {
    if (
      !canAdjustInventory
    ) {
      setError(
        "You do not have permission to update inventory stock."
      );

      return;
    }


    if (
      !medicine.stock_verified
    ) {
      setError(
        "Verify this candidate formulation before recording stock."
      );

      return;
    }


    clearMessages();


    setSelectedMedicine(
      medicine
    );


    setTransactionForm({
      transaction_type:
        "STOCK_IN",

      stock_unit:
        medicine.package_unit
          ? "PACKAGE"
          : "LOOSE",

      quantity: "",
      reference: "",
      reason: "",
      notes: "",
    });


    setShowTransactionForm(
      true
    );
  };


  const openAdjustmentForm = (
    medicine
  ) => {
    if (
      !canAdjustInventory
    ) {
      setError(
        "You do not have permission to adjust inventory."
      );

      return;
    }


    if (
      !medicine.stock_verified
    ) {
      setError(
        "Verify this candidate formulation before recording stock."
      );

      return;
    }


    clearMessages();


    setSelectedMedicine(
      medicine
    );


    setTransactionForm({
      transaction_type:
        "ADJUSTMENT_OUT",

      stock_unit:
        medicine.package_stock > 0
          ? "PACKAGE"
          : "LOOSE",

      quantity: "",
      reference: "",
      reason: "",
      notes: "",
    });


    setShowTransactionForm(
      true
    );
  };


  const closeTransactionForm =
    () => {
      setShowTransactionForm(
        false
      );


      setSelectedMedicine(
        null
      );


      setTransactionForm({
        ...EMPTY_TRANSACTION_FORM,
      });
    };


  const handleTransactionSubmit =
    async (event) => {
      event.preventDefault();


      if (
        !canAdjustInventory
      ) {
        setError(
          "You do not have permission to record inventory transactions."
        );

        return;
      }


      if (
        !selectedMedicine
      ) {
        setError(
          "Please select a medicine."
        );

        return;
      }


      try {
        setTransactionSaving(
          true
        );

        clearMessages();


        const quantity =
          Number(
            transactionForm.quantity
          );


        if (
          Number.isNaN(quantity) ||
          quantity <= 0
        ) {
          setError(
            "Quantity must be greater than zero."
          );

          return;
        }


        const payload = {
          transaction_type:
            transactionForm
              .transaction_type,

          quantity,

          stock_unit:
            transactionForm
              .stock_unit,

          reference:
            textOrNull(
              transactionForm.reference
            ),

          reason:
            textOrNull(
              transactionForm.reason
            ),

          notes:
            textOrNull(
              transactionForm.notes
            ),
        };


        await createInventoryTransaction(
          selectedMedicine.id,
          payload
        );


        setSuccess(
          "Inventory transaction recorded successfully."
        );


        closeTransactionForm();


        await Promise.all([
          loadMedicines(
            search,
            activeOnly
          ),

          loadTransactions(),
        ]);

      } catch (err) {
        console.error(
          err
        );


        setError(
          getErrorMessage(
            err,
            "Unable to record inventory transaction."
          )
        );

      } finally {
        setTransactionSaving(
          false
        );
      }
    };


  // =======================================================
  // ACTIVE INVENTORY / CANDIDATE FORMULARY
  // =======================================================

  const activeInventoryMedicines =
    useMemo(
      () =>
        medicines.filter(
          (medicine) =>
            medicine.stock_verified
        ),
      [
        medicines,
      ]
    );


  const candidateFormularyMedicines =
    useMemo(
      () =>
        medicines.filter(
          (medicine) =>
            !medicine.stock_verified
        ),
      [
        medicines,
      ]
    );


  const visibleRecordMedicines =
    recordsView === "CANDIDATE"
      ? candidateFormularyMedicines
      : activeInventoryMedicines;


  // =======================================================
  // INVENTORY SUMMARY
  // =======================================================

  const summary =
    useMemo(
      () => {
        let lowStock = 0;
        let outOfStock = 0;


        activeInventoryMedicines.forEach(
          (medicine) => {
            const status =
              getStockStatus(
                medicine
              );


            if (
              status ===
              "LOW STOCK"
            ) {
              lowStock += 1;
            }


            if (
              status ===
              "OUT OF STOCK"
            ) {
              outOfStock += 1;
            }
          }
        );


        return {
          active:
            activeInventoryMedicines.length,

          candidate:
            candidateFormularyMedicines.length,

          lowStock,

          outOfStock,
        };
      },
      [
        activeInventoryMedicines,
        candidateFormularyMedicines,
        getStockStatus,
      ]
    );


  const lowStockMedicines =
    useMemo(
      () =>
        activeInventoryMedicines.filter(
          (medicine) => {
            const status =
              getStockStatus(
                medicine
              );


            return (
              status ===
                "LOW STOCK" ||
              status ===
                "OUT OF STOCK"
            );
          }
        ),
      [
        activeInventoryMedicines,
        getStockStatus,
      ]
    );


  // =======================================================
  // MODAL BEHAVIOR
  // =======================================================

  useEffect(
    () => {
      const modalOpen =
        showMedicineForm ||
        (
          showTransactionForm &&
          selectedMedicine
        );


      if (!modalOpen) {
        return undefined;
      }


      const previousOverflow =
        document.body.style.overflow;


      document.body.style.overflow =
        "hidden";


      const handleKeyDown = (
        event
      ) => {
        if (
          event.key !== "Escape"
        ) {
          return;
        }


        if (
          saving ||
          transactionSaving
        ) {
          return;
        }


        if (
          showMedicineForm
        ) {
          resetMedicineForm();

          return;
        }


        if (
          showTransactionForm
        ) {
          closeTransactionForm();
        }
      };


      document.addEventListener(
        "keydown",
        handleKeyDown
      );


      return () => {
        document.body.style.overflow =
          previousOverflow;

        document.removeEventListener(
          "keydown",
          handleKeyDown
        );
      };
    },
    [
      selectedMedicine,
      showMedicineForm,
      showTransactionForm,
      saving,
      transactionSaving,
    ]
  );


  // =======================================================
  // AUTH LOADING
  // =======================================================

  if (
    authLoading
  ) {
    return (
      <div className="inventory-page">
        <div className="inventory-empty">
          Loading inventory...
        </div>
      </div>
    );
  }


  // =======================================================
  // ACCESS DENIED
  // =======================================================

  if (
    !canViewInventory
  ) {
    return (
      <div className="inventory-page">

        <section className="inventory-card">

          <div className="inventory-empty">

            You do not have permission
            to view the medicine inventory.

          </div>

        </section>

      </div>
    );
  }


  // =======================================================
  // PAGE
  // =======================================================

  return (
    <div className="inventory-page">

      {/* ===================================================
          PAGE HEADER
      =================================================== */}

      <header className="inventory-page-header">

        <div>

          <h1>
            Medicine Inventory
          </h1>

          <p>
            Manage medicines, stock levels,
            and inventory transactions.
          </p>

        </div>


        {canAdjustInventory && (

          <button
            type="button"
            className="app-button app-button-primary"
            onClick={
              handleAddMedicine
            }
          >
            + Add Medicine
          </button>

        )}

      </header>


      {/* ===================================================
          MESSAGES
      =================================================== */}

      {error && (

        <div className="app-message app-message-error inventory-message">
          {error}
        </div>

      )}


      {success && (

        <div className="app-message app-message-success inventory-message">
          {success}
        </div>

      )}


      {/* ===================================================
          SUMMARY
      =================================================== */}

      <div className="inventory-summary-grid">

        <InventorySummaryCard
          label="Active Inventory"
          value={
            summary.active
          }
        />


        <InventorySummaryCard
          label="Candidate Formulary"
          value={
            summary.candidate
          }
          type="candidate"
        />


        <InventorySummaryCard
          label="Low Stock"
          value={
            summary.lowStock
          }
          type="warning"
        />


        <InventorySummaryCard
          label="Out of Stock"
          value={
            summary.outOfStock
          }
          type="danger"
        />

      </div>


      {/* ===================================================
          SEARCH
      =================================================== */}

      <section className="inventory-card">

        <div className="inventory-card-header">

          <div>

            <h2>
              Search Inventory
            </h2>

            <p>
              Find medicines by code,
              name, or generic name.
            </p>

          </div>

        </div>


        <form
          className="inventory-search-form"
          onSubmit={
            handleSearchSubmit
          }
        >

          <input
            className="inventory-search-input"
            type="text"
            value={
              search
            }
            placeholder="Search code, medicine, or generic name"
            onChange={
              (event) =>
                setSearch(
                  event.target.value
                )
            }
          />


          <div className="app-button-group">

            <button
              type="submit"
              className="app-button app-button-primary"
              disabled={
                loading
              }
            >
              Search
            </button>


            <button
              type="button"
              className="app-button app-button-secondary"
              onClick={
                handleClearSearch
              }
              disabled={
                loading
              }
            >
              Clear
            </button>

          </div>

        </form>


        <div className="inventory-catalog-filters">

          <div className="inventory-field">

            <label htmlFor="medicine_category_filter">
              Category
            </label>

            <select
              id="medicine_category_filter"
              value={categoryFilter}
              onChange={
                (event) =>
                  setCategoryFilter(
                    event.target.value
                  )
              }
            >
              {
                MEDICINE_CATEGORIES.map(
                  ([value, label]) => (
                    <option
                      key={
                        value ||
                        "ALL"
                      }
                      value={value}
                    >
                      {label}
                    </option>
                  )
                )
              }
            </select>

          </div>


          <div className="inventory-field">

            <label htmlFor="formulary_status_filter">
              Formulary Status
            </label>

            <select
              id="formulary_status_filter"
              value={
                formularyStatusFilter
              }
              onChange={
                (event) =>
                  setFormularyStatusFilter(
                    event.target.value
                  )
              }
            >
              {
                FORMULARY_STATUSES.map(
                  ([value, label]) => (
                    <option
                      key={
                        value ||
                        "ALL"
                      }
                      value={value}
                    >
                      {label}
                    </option>
                  )
                )
              }
            </select>

          </div>

        </div>


        <label className="inventory-checkbox">

          <input
            type="checkbox"
            checked={
              activeOnly
            }
            onChange={
              (event) =>
                setActiveOnly(
                  event.target.checked
                )
            }
          />

          <span>
            Active Medicines Only
          </span>

        </label>

      </section>


      {/* ===================================================
          STOCK ALERTS
      =================================================== */}

      <section className="inventory-card">

        <div className="inventory-card-header">

          <div>

            <h2>
              Stock Alerts
            </h2>

            <p>
              Medicines requiring inventory
              attention.
            </p>

          </div>

        </div>


        {lowStockMedicines.length ===
        0 ? (

          <div className="inventory-empty">
            No low-stock medicines.
          </div>

        ) : (

          <div className="inventory-table-wrap">

            <table className="inventory-table">

              <thead>

                <tr>
                  <th>Medicine</th>
                  <th>Current Stock</th>
                  <th>Status</th>
                </tr>

              </thead>


              <tbody>

                {lowStockMedicines.map(
                  (medicine) => (

                    <tr
                      key={
                        medicine.id
                      }
                    >

                      <td>

                        <strong>
                          {medicine.name}
                        </strong>

                      </td>


                      <td>

                        {getStockDisplay(
                          medicine
                        )}

                      </td>


                      <td>

                        <span
                          className={
                            getStockStatusClass(
                              medicine
                            )
                          }
                        >
                          {getStockStatus(
                            medicine
                          )}
                        </span>

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>


      {/* ===================================================
          MEDICINE FORM
      =================================================== */}

      {canAdjustInventory &&
        showMedicineForm && (

          <div
            className="inventory-modal-backdrop"
            role="presentation"
            onMouseDown={
              (event) => {
                if (
                  event.target ===
                    event.currentTarget &&
                  !saving
                ) {
                  resetMedicineForm();
                }
              }
            }
          >

            <section
              className="inventory-modal inventory-modal-large"
              role="dialog"
              aria-modal="true"
              aria-labelledby="medicine-modal-title"
            >

              <div className="inventory-modal-header">

                <div>

                <h2 id="medicine-modal-title">
                  {
                    verificationMode
                      ? "Verify & Add to Active Inventory"
                      : editingMedicineId
                        ? "Edit Medicine"
                        : "Add Medicine"
                  }
                </h2>

                <p>
                  {
                    verificationMode
                      ? "Confirm the exact health-center formulation before activating inventory controls."
                      : "Enter medicine information and inventory settings."
                  }
                </p>

              </div>


              <button
                type="button"
                className="inventory-modal-close"
                aria-label="Close medicine form"
                onClick={
                  resetMedicineForm
                }
                disabled={
                  saving
                }
              >
                ×
              </button>

            </div>


            <div className="inventory-modal-body">

            <form
              className="inventory-form"
              onSubmit={
                handleMedicineSubmit
              }
            >

              {verificationMode && (

                <div className="inventory-verification-banner inventory-field-full">

                  <strong>
                    Verification Required
                  </strong>

                  <span>
                    Confirm the exact medicine name, strength,
                    dosage form, dispensing unit, packaging,
                    and health-center availability. This action
                    marks the formulation as VERIFIED and enables
                    stock transactions. It does not create stock
                    quantity automatically.
                  </span>

                </div>

              )}


              <div className="inventory-form-section-title">
                Medicine Information
              </div>


              <InventoryField
                label="Medicine Code"
                name="code"
                value={
                  medicineForm.code
                }
                onChange={
                  handleMedicineChange
                }
                required
              />


              <InventoryField
                label="Medicine Name"
                name="name"
                value={
                  medicineForm.name
                }
                onChange={
                  handleMedicineChange
                }
                required
              />


              <InventoryField
                label="Generic Name"
                name="generic_name"
                value={
                  medicineForm
                    .generic_name
                }
                onChange={
                  handleMedicineChange
                }
              />


              <InventoryField
                label="Strength"
                name="dosage_strength"
                value={
                  medicineForm
                    .dosage_strength
                }
                onChange={
                  handleMedicineChange
                }
              />


              <InventoryField
                label="Dosage Form"
                name="dosage_form"
                value={
                  medicineForm
                    .dosage_form
                }
                onChange={
                  handleMedicineChange
                }
              />


              <div className="inventory-form-section-title">
                Formulary Classification & Safety
              </div>


              <div className="inventory-field">

                <label htmlFor="medicine_category">
                  Medicine Category
                </label>

                <select
                  id="medicine_category"
                  name="medicine_category"
                  value={
                    medicineForm
                      .medicine_category
                  }
                  onChange={
                    handleMedicineChange
                  }
                >
                  {
                    MEDICINE_CATEGORIES
                      .filter(
                        ([value]) =>
                          value
                      )
                      .map(
                        ([value, label]) => (
                          <option
                            key={value}
                            value={value}
                          >
                            {label}
                          </option>
                        )
                      )
                  }
                </select>

              </div>


              <div className="inventory-field">

                <label htmlFor="formulary_status">
                  Formulary Status
                </label>

                <select
                  id="formulary_status"
                  name="formulary_status"
                  value={
                    medicineForm
                      .formulary_status
                  }
                  onChange={
                    handleMedicineChange
                  }
                  disabled={
                    verificationMode
                  }
                >
                  {
                    FORMULARY_STATUSES
                      .filter(
                        ([value]) =>
                          value
                      )
                      .map(
                        ([value, label]) => (
                          <option
                            key={value}
                            value={value}
                          >
                            {label}
                          </option>
                        )
                      )
                  }
                </select>

              </div>


              <div className="inventory-field">

                <label htmlFor="program_type">
                  Program Type
                </label>

                <select
                  id="program_type"
                  name="program_type"
                  value={
                    medicineForm
                      .program_type
                  }
                  onChange={
                    handleMedicineChange
                  }
                >
                  {
                    PROGRAM_TYPES.map(
                      ([value, label]) => (
                        <option
                          key={
                            value ||
                            "NONE"
                          }
                          value={value}
                        >
                          {label}
                        </option>
                      )
                    )
                  }
                </select>

              </div>


              <div className="inventory-field-full inventory-safety-panel">

                <div className="inventory-safety-panel-header">

                  <div>
                    <strong>
                      Safety & Operational Controls
                    </strong>

                    <span>
                      Set how this formulation can be dispensed,
                      viewed, and used by forecasting.
                    </span>
                  </div>

                </div>


                <div className="inventory-safety-grid">

                  <label className="inventory-safety-option">

                    <input
                      type="checkbox"
                      name="requires_prescription"
                      checked={
                        medicineForm
                          .requires_prescription
                      }
                      onChange={
                        handleMedicineChange
                      }
                    />

                    <span className="inventory-safety-option-copy">
                      <strong>
                        Requires Prescription
                      </strong>

                      <small>
                        Clinician authorization is required
                        before dispensing.
                      </small>
                    </span>

                  </label>


                  <label className="inventory-safety-option">

                    <input
                      type="checkbox"
                      name="restricted_dispensing"
                      checked={
                        medicineForm
                          .restricted_dispensing
                      }
                      onChange={
                        handleMedicineChange
                      }
                    />

                    <span className="inventory-safety-option-copy">
                      <strong>
                        Restricted Dispensing
                      </strong>

                      <small>
                        Only personnel with the required
                        permission may dispense it.
                      </small>
                    </span>

                  </label>


                  <label className="inventory-safety-option">

                    <input
                      type="checkbox"
                      name="sensitive_inventory"
                      checked={
                        medicineForm
                          .sensitive_inventory
                      }
                      onChange={
                        handleMedicineChange
                      }
                    />

                    <span className="inventory-safety-option-copy">
                      <strong>
                        Sensitive / Program Inventory
                      </strong>

                      <small>
                        Apply restricted visibility for
                        program-managed medicines.
                      </small>
                    </span>

                  </label>


                  <label className="inventory-safety-option">

                    <input
                      type="checkbox"
                      name="forecast_enabled"
                      checked={
                        medicineForm
                          .forecast_enabled
                      }
                      onChange={
                        handleMedicineChange
                      }
                    />

                    <span className="inventory-safety-option-copy">
                      <strong>
                        Forecast Eligible
                      </strong>

                      <small>
                        Allow this verified medicine to use
                        demand forecasting when data is sufficient.
                      </small>
                    </span>

                  </label>


                  <label
                    className={
                      medicineForm
                        .stock_verified
                        ? "inventory-safety-option inventory-safety-option-wide inventory-safety-option-verified"
                        : "inventory-safety-option inventory-safety-option-wide"
                    }
                  >

                    <input
                      type="checkbox"
                      name="stock_verified"
                      checked={
                        medicineForm
                          .stock_verified
                      }
                      onChange={
                        handleMedicineChange
                      }
                      disabled={
                        Boolean(
                          editingMedicineId
                        )
                        && !verificationMode
                        && !medicineForm
                          .stock_verified
                      }
                    />

                    <span className="inventory-safety-option-copy">
                      <strong>
                        Actual Stock / Formulation Verified
                      </strong>

                      <small>
                        Confirm only after matching the exact
                        medicine, strength, dosage form, and
                        actual health-center stock.
                      </small>
                    </span>

                    <span className="inventory-safety-state">
                      {
                        medicineForm
                          .stock_verified
                          ? "Verified"
                          : "Unverified"
                      }
                    </span>

                  </label>

                </div>

              </div>


              <div className="inventory-note inventory-field-full">

                <strong>
                  Candidate Formulary Safety
                </strong>

                <span>
                  A medicine can exist in the catalog without being
                  confirmed as actual health-center stock. Unverified
                  entries cannot be dispensed and are excluded from
                  live medicine-demand forecast matching.
                </span>

              </div>


              <div className="inventory-form-section-title">
                Packaging & Dispensing
              </div>


              <InventoryField
                label="Package Unit"
                name="package_unit"
                value={
                  medicineForm
                    .package_unit
                }
                onChange={
                  handleMedicineChange
                }
                placeholder="e.g. box, bottle"
              />


              <InventoryField
                label="Dispensing Unit"
                name="dispensing_unit"
                value={
                  medicineForm
                    .dispensing_unit
                }
                onChange={
                  handleMedicineChange
                }
                placeholder="e.g. tablet, piece"
                required
              />


              <InventoryField
                label="Units Per Package"
                name="units_per_package"
                type="number"
                min="1"
                value={
                  medicineForm
                    .units_per_package
                }
                onChange={
                  handleMedicineChange
                }
              />


              <InventoryField
                label="Reorder Level"
                name="reorder_level"
                type="number"
                min="0"
                value={
                  medicineForm
                    .reorder_level
                }
                onChange={
                  handleMedicineChange
                }
              />


              <div className="inventory-field inventory-field-full">

                <label className="inventory-checkbox">

                  <input
                    type="checkbox"
                    name="is_active"
                    checked={
                      medicineForm
                        .is_active
                    }
                    onChange={
                      handleMedicineChange
                    }
                  />

                  <span>
                    Active Medicine
                  </span>

                </label>

              </div>


              <div className="inventory-note inventory-field-full">

                <strong>
                  Stock Management
                </strong>

                <span>
                  Use Stock In or Adjust
                  after creating a medicine
                  to update normal stock
                  quantities.
                </span>

              </div>


              <div className="inventory-form-actions">

                <button
                  type="submit"
                  className="app-button app-button-primary"
                  disabled={
                    saving
                  }
                >
                  {saving
                    ? "Saving..."
                    : verificationMode
                      ? "Verify & Add to Active Inventory"
                      : editingMedicineId
                        ? "Save Changes"
                        : "Add Medicine"}
                </button>


                <button
                  type="button"
                  className="app-button app-button-secondary"
                  onClick={
                    resetMedicineForm
                  }
                  disabled={
                    saving
                  }
                >
                  Cancel
                </button>

              </div>

            </form>

            </div>

          </section>

          </div>

        )}


      {/* ===================================================
          INVENTORY TRANSACTION FORM
      =================================================== */}

      {canAdjustInventory &&
        showTransactionForm &&
        selectedMedicine && (

          <div
            className="inventory-modal-backdrop"
            role="presentation"
            onMouseDown={
              (event) => {
                if (
                  event.target ===
                    event.currentTarget &&
                  !transactionSaving
                ) {
                  closeTransactionForm();
                }
              }
            }
          >

            <section
              className="inventory-modal inventory-modal-medium"
              role="dialog"
              aria-modal="true"
              aria-labelledby="inventory-transaction-modal-title"
            >

              <div className="inventory-modal-header">

                <div>

                  <h2 id="inventory-transaction-modal-title">
                    Inventory Transaction
                  </h2>

                <p>
                  Record stock movement for{" "}

                  <strong>
                    {selectedMedicine.name}
                  </strong>
                  .
                </p>

              </div>


              <button
                type="button"
                className="inventory-modal-close"
                aria-label="Close inventory transaction form"
                onClick={
                  closeTransactionForm
                }
                disabled={
                  transactionSaving
                }
              >
                ×
              </button>

            </div>


            <div className="inventory-modal-body">


            <div className="inventory-selected-medicine">

              <div>

                <span>
                  Medicine
                </span>

                <strong>
                  {selectedMedicine.name}
                </strong>

              </div>


              <div>

                <span>
                  Current Stock
                </span>

                <strong>
                  {getStockDisplay(
                    selectedMedicine
                  )}
                </strong>

              </div>


              <div>

                <span>
                  Status
                </span>

                <strong>
                  {getStockStatus(
                    selectedMedicine
                  )}
                </strong>

              </div>

            </div>


            <form
              className="inventory-form"
              onSubmit={
                handleTransactionSubmit
              }
            >

              <div className="inventory-field">

                <label htmlFor="transaction_type">
                  Transaction Type
                </label>


                <select
                  id="transaction_type"
                  name="transaction_type"
                  value={
                    transactionForm
                      .transaction_type
                  }
                  onChange={
                    handleTransactionChange
                  }
                >

                  <option value="STOCK_IN">
                    Stock In
                  </option>

                  <option value="ADJUSTMENT_IN">
                    Adjustment In
                  </option>

                  <option value="ADJUSTMENT_OUT">
                    Adjustment Out
                  </option>

                </select>

              </div>


              <div className="inventory-field">

                <label htmlFor="stock_unit">
                  Stock Unit
                </label>


                <select
                  id="stock_unit"
                  name="stock_unit"
                  value={
                    transactionForm
                      .stock_unit
                  }
                  onChange={
                    handleTransactionChange
                  }
                >

                  <option value="PACKAGE">
                    Package
                  </option>

                  <option value="LOOSE">
                    Loose
                  </option>

                </select>

              </div>


              <InventoryField
                label="Quantity"
                name="quantity"
                type="number"
                min="1"
                value={
                  transactionForm.quantity
                }
                onChange={
                  handleTransactionChange
                }
                required
              />


              <InventoryField
                label="Reference"
                name="reference"
                value={
                  transactionForm.reference
                }
                onChange={
                  handleTransactionChange
                }
                placeholder="e.g. DOH Delivery"
              />


              <InventoryField
                label="Reason"
                name="reason"
                value={
                  transactionForm.reason
                }
                onChange={
                  handleTransactionChange
                }
                placeholder="Reason for transaction"
              />


              <div className="inventory-field inventory-field-full">

                <label htmlFor="notes">
                  Notes
                </label>


                <textarea
                  id="notes"
                  name="notes"
                  value={
                    transactionForm.notes
                  }
                  onChange={
                    handleTransactionChange
                  }
                />

              </div>


              <div className="inventory-form-actions">

                <button
                  type="submit"
                  className="app-button app-button-primary"
                  disabled={
                    transactionSaving
                  }
                >
                  {transactionSaving
                    ? "Saving..."
                    : "Save Transaction"}
                </button>


                <button
                  type="button"
                  className="app-button app-button-secondary"
                  onClick={
                    closeTransactionForm
                  }
                  disabled={
                    transactionSaving
                  }
                >
                  Cancel
                </button>

              </div>

            </form>

            </div>

          </section>

          </div>

        )}


      {/* ===================================================
          ACTIVE INVENTORY / CANDIDATE FORMULARY
      =================================================== */}

      <section className="inventory-card">

        <div className="inventory-card-header">

          <div>

            <h2>
              Medicine Records
            </h2>

            <p>
              Keep verified operational stock
              separate from the standardized
              candidate formulary.
            </p>

          </div>


          <span className="inventory-record-count">
            {
              visibleRecordMedicines.length
            } records
          </span>

        </div>


        <div className="inventory-record-tabs">

          <button
            type="button"
            className={
              recordsView === "ACTIVE"
                ? "inventory-record-tab inventory-record-tab-active"
                : "inventory-record-tab"
            }
            onClick={
              () =>
                setRecordsView(
                  "ACTIVE"
                )
            }
          >
            Active Inventory

            <span>
              {
                activeInventoryMedicines.length
              }
            </span>
          </button>


          <button
            type="button"
            className={
              recordsView === "CANDIDATE"
                ? "inventory-record-tab inventory-record-tab-active"
                : "inventory-record-tab"
            }
            onClick={
              () =>
                setRecordsView(
                  "CANDIDATE"
                )
            }
          >
            Candidate Formulary

            <span>
              {
                candidateFormularyMedicines.length
              }
            </span>
          </button>

        </div>


        {
          recordsView === "ACTIVE"
            ? (
              <div className="inventory-record-view-note">

                <strong>
                  Active Inventory
                </strong>

                <span>
                  Verified formulations only. Stock In,
                  adjustments, dispensing safeguards, and
                  medicine-demand forecast eligibility apply
                  from this operational inventory.
                </span>

              </div>
            )
            : (
              <div className="inventory-record-view-note inventory-record-view-note-candidate">

                <strong>
                  Candidate Formulary
                </strong>

                <span>
                  Standardized candidate formulations are not
                  assumed to be actual Krus na Ligas stock.
                  Verify the exact product before recording
                  stock or using it in live demand forecasting.
                </span>

              </div>
            )
        }


        {loading ? (

          <div className="inventory-empty">
            Loading medicines...
          </div>

        ) : visibleRecordMedicines.length ===
          0 ? (

          <div className="inventory-empty">
            {
              recordsView === "ACTIVE"
                ? "No active inventory medicines match the current filters."
                : "No candidate formulary medicines match the current filters."
            }
          </div>

        ) : recordsView === "ACTIVE" ? (

          <div className="inventory-table-wrap">

            <table className="inventory-table">

              <thead>

                <tr>
                  <th>Code</th>
                  <th>Medicine</th>
                  <th>Generic</th>
                  <th>Strength</th>
                  <th>Form</th>
                  <th>Category</th>
                  <th>Controls</th>
                  <th>Stock</th>
                  <th>Reorder</th>
                  <th>Status</th>

                  {canAdjustInventory && (
                    <th>Actions</th>
                  )}

                </tr>

              </thead>


              <tbody>

                {activeInventoryMedicines.map(
                  (medicine) => (

                    <tr
                      key={
                        medicine.id
                      }
                    >

                      <td>
                        <span className="inventory-code">
                          {medicine.code}
                        </span>
                      </td>


                      <td>
                        <strong>
                          {medicine.name}
                        </strong>
                      </td>


                      <td>
                        {medicine.generic_name ||
                          "-"}
                      </td>


                      <td>
                        {medicine.dosage_strength ||
                          "-"}
                      </td>


                      <td>
                        {medicine.dosage_form ||
                          "-"}
                      </td>


                      <td>
                        <span className="inventory-catalog-badge inventory-catalog-badge-verified">
                          {
                            medicine
                              .medicine_category
                              ?.replaceAll(
                                "_",
                                " "
                              )
                          }
                        </span>
                      </td>


                      <td>
                        <div className="inventory-control-badges">

                          {medicine.sensitive_inventory && (
                            <span className="inventory-mini-badge inventory-mini-badge-sensitive">
                              Sensitive
                            </span>
                          )}

                          {medicine.restricted_dispensing && (
                            <span className="inventory-mini-badge">
                              Restricted
                            </span>
                          )}

                          {medicine.forecast_enabled && (
                            <span className="inventory-mini-badge inventory-mini-badge-verified">
                              Forecast Enabled
                            </span>
                          )}

                          <span className="inventory-mini-badge inventory-mini-badge-verified">
                            Stock Verified
                          </span>

                        </div>
                      </td>


                      <td>
                        {getStockDisplay(
                          medicine
                        )}
                      </td>


                      <td>
                        {
                          medicine
                            .reorder_level
                        }
                      </td>


                      <td>
                        <span
                          className={
                            getStockStatusClass(
                              medicine
                            )
                          }
                        >
                          {getStockStatus(
                            medicine
                          )}
                        </span>
                      </td>


                      {canAdjustInventory && (

                        <td>

                          <div className="inventory-table-actions">

                            <button
                              type="button"
                              className="app-button app-button-secondary app-button-small"
                              onClick={
                                () =>
                                  handleEditMedicine(
                                    medicine
                                  )
                              }
                            >
                              Edit
                            </button>


                            <button
                              type="button"
                              className="app-button app-button-primary app-button-small"
                              onClick={
                                () =>
                                  openStockInForm(
                                    medicine
                                  )
                              }
                            >
                              Stock In
                            </button>


                            <button
                              type="button"
                              className="app-button app-button-secondary app-button-small"
                              onClick={
                                () =>
                                  openAdjustmentForm(
                                    medicine
                                  )
                              }
                            >
                              Adjust
                            </button>

                          </div>

                        </td>

                      )}

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        ) : (

          <div className="inventory-table-wrap">

            <table className="inventory-table">

              <thead>

                <tr>
                  <th>Code</th>
                  <th>Medicine</th>
                  <th>Generic</th>
                  <th>Strength</th>
                  <th>Form</th>
                  <th>Category</th>
                  <th>Formulary</th>
                  <th>Controls</th>

                  {canAdjustInventory && (
                    <th>Actions</th>
                  )}

                </tr>

              </thead>


              <tbody>

                {candidateFormularyMedicines.map(
                  (medicine) => (

                    <tr
                      key={
                        medicine.id
                      }
                    >

                      <td>
                        <span className="inventory-code">
                          {medicine.code}
                        </span>
                      </td>


                      <td>
                        <strong>
                          {medicine.name}
                        </strong>
                      </td>


                      <td>
                        {medicine.generic_name ||
                          "-"}
                      </td>


                      <td>
                        {medicine.dosage_strength ||
                          "-"}
                      </td>


                      <td>
                        {medicine.dosage_form ||
                          "-"}
                      </td>


                      <td>
                        <span className="inventory-catalog-badge">
                          {
                            medicine
                              .medicine_category
                              ?.replaceAll(
                                "_",
                                " "
                              )
                          }
                        </span>
                      </td>


                      <td>
                        <span className="inventory-catalog-badge">
                          {
                            medicine
                              .formulary_status
                          }
                        </span>
                      </td>


                      <td>
                        <div className="inventory-control-badges">

                          {medicine.sensitive_inventory && (
                            <span className="inventory-mini-badge inventory-mini-badge-sensitive">
                              Sensitive
                            </span>
                          )}

                          {medicine.restricted_dispensing && (
                            <span className="inventory-mini-badge">
                              Restricted
                            </span>
                          )}

                          {medicine.forecast_enabled && (
                            <span className="inventory-mini-badge">
                              Forecast Eligible
                            </span>
                          )}

                          <span className="inventory-mini-badge inventory-mini-badge-unverified">
                            Unverified
                          </span>

                        </div>
                      </td>


                      {canAdjustInventory && (

                        <td>

                          <div className="inventory-table-actions inventory-candidate-actions">

                            <button
                              type="button"
                              className="app-button app-button-primary app-button-small"
                              onClick={
                                () =>
                                  handleVerifyCandidate(
                                    medicine
                                  )
                              }
                            >
                              Verify & Add to Inventory
                            </button>


                            <button
                              type="button"
                              className="app-button app-button-secondary app-button-small"
                              onClick={
                                () =>
                                  handleEditMedicine(
                                    medicine
                                  )
                              }
                            >
                              Edit Candidate
                            </button>

                          </div>

                        </td>

                      )}

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>


      {/* ===================================================
          TRANSACTION HISTORY
      =================================================== */}

      <section className="inventory-card">

        <div className="inventory-card-header">

          <div>

            <h2>
              Inventory Transaction History
            </h2>

            <p>
              Previous stock-in,
              adjustments, and dispensing
              activity.
            </p>

          </div>

        </div>


        {transactionLoading ? (

          <div className="inventory-empty">
            Loading transactions...
          </div>

        ) : transactions.length ===
          0 ? (

          <div className="inventory-empty">
            No inventory transactions found.
          </div>

        ) : (

          <div className="inventory-table-wrap">

            <table className="inventory-table">

              <thead>

                <tr>
                  <th>Date</th>
                  <th>Medicine</th>
                  <th>Type</th>
                  <th>Quantity</th>
                  <th>Unit</th>
                  <th>Reference</th>
                  <th>Performed By</th>
                  <th>Reason</th>
                </tr>

              </thead>


              <tbody>

                {transactions.map(
                  (transaction) => {

                    const sign =
                      getTransactionSign(
                        transaction
                          .transaction_type
                      );


                    const quantityClass =
                      sign === "+"
                        ? "inventory-quantity-positive"
                        : sign === "-"
                          ? "inventory-quantity-negative"
                          : "";


                    return (

                      <tr
                        key={
                          transaction.id
                        }
                      >

                        <td>
                          {new Date(
                            transaction
                              .created_at
                          ).toLocaleString()}
                        </td>


                        <td>
                          {getMedicineName(
                            transaction
                              .medicine_id
                          )}
                        </td>


                        <td>

                          <span className="inventory-transaction-type">

                            {formatTransactionType(
                              transaction
                                .transaction_type
                            )}

                          </span>

                        </td>


                        <td>

                          <strong
                            className={
                              quantityClass
                            }
                          >
                            {sign}
                            {
                              transaction
                                .quantity
                            }
                          </strong>

                        </td>


                        <td>
                          {
                            transaction
                              .stock_unit
                          }
                        </td>


                        <td>
                          {transaction.reference ||
                            "-"}
                        </td>


                        <td>

                          {transaction
                            .recorded_by_name ? (

                            <div className="inventory-performed-by">

                              <strong>
                                {
                                  transaction
                                    .recorded_by_name
                                }
                              </strong>

                              <span>
                                {
                                  transaction
                                    .recorded_by_role_names
                                  || "Staff"
                                }
                              </span>

                            </div>

                          ) : (

                            <span className="inventory-performed-by-missing">
                              Not recorded
                            </span>

                          )}

                        </td>


                        <td>
                          {transaction.reason ||
                            "-"}
                        </td>

                      </tr>

                    );
                  }
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>

    </div>
  );
}


/* =========================================================
   REUSABLE FIELD
========================================================= */

function InventoryField({
  label,
  name,
  value,
  onChange,
  type = "text",
  placeholder = "",
  min,
  max,
  step,
  required = false,
  disabled = false,
}) {
  return (
    <div className="inventory-field">

      <label htmlFor={name}>
        {label}
      </label>


      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        required={required}
        disabled={disabled}
      />

    </div>
  );
}


/* =========================================================
   SUMMARY CARD
========================================================= */

function InventorySummaryCard({
  label,
  value,
  type = "default",
}) {
  return (
    <div
      className={
        `inventory-summary-card ` +
        `inventory-summary-${type}`
      }
    >

      <span>
        {label}
      </span>


      <strong>
        {value}
      </strong>

    </div>
  );
}


export default Inventory;
