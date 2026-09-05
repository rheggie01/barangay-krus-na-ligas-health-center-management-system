from pathlib import Path


ML_ROOT = Path(__file__).resolve().parent
DATASETS_ROOT = ML_ROOT / "datasets"
SYNTHETIC_DIR = DATASETS_ROOT / "synthetic"
VALIDATED_DIR = DATASETS_ROOT / "validated"
REPORTS_DIR = DATASETS_ROOT / "reports"

SYNTHETIC_SOURCE = "SYNTHETIC_DEVELOPMENT_DATA"
SYNTHETIC_LABEL_SOURCE = "SYNTHETIC_SCENARIO_LABEL"

START_DATE = "2021-01-01"
END_DATE = "2025-12-31"
RANDOM_SEED = 20260904
CLASSIFICATION_ROWS_PER_YEAR = 1200

DISEASE_CLASSES = (
    "DENGUE",
    "ARI",
    "ILI",
    "DIARRHEA_GASTROENTERITIS",
)

SYMPTOM_CODES = (
    "FEVER",
    "COUGH",
    "RUNNY_NOSE",
    "SORE_THROAT",
    "HEADACHE",
    "BODY_PAIN",
    "VOMITING",
    "DIARRHEA",
    "ABDOMINAL_PAIN",
    "RASH",
    "NAUSEA",
    "FATIGUE",
    "DIFFICULTY_BREATHING",
    "LOSS_OF_APPETITE",
    "CHILLS",
)

FORBIDDEN_PII_COLUMNS = {
    "patient_id",
    "patient_code",
    "first_name",
    "middle_name",
    "last_name",
    "full_name",
    "contact_number",
    "email",
    "address",
    "street",
    "latitude",
    "longitude",
}
