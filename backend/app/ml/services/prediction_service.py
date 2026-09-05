from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from app.ml.config import (
    DISEASE_CLASSES,
    SYMPTOM_CODES,
)
from app.ml.preprocessing.disease_preprocessor import (
    MODEL_FEATURES,
)


ML_ROOT = Path(__file__).resolve().parents[1]

SELECTED_MODEL_PATH = (
    ML_ROOT
    / "artifacts"
    / "selected_model.joblib"
)

MODEL_METADATA_PATH = (
    ML_ROOT
    / "artifacts"
    / "model_metadata.json"
)


DISEASE_DISPLAY_NAMES = {
    "DENGUE":
        "Dengue",

    "ARI":
        "Acute Respiratory Infection (ARI)",

    "ILI":
        "Influenza-Like Illness (ILI)",

    "DIARRHEA_GASTROENTERITIS":
        "Diarrhea / Gastroenteritis",
}


DEVELOPMENT_STATUS = (
    "SYNTHETIC_TECHNICAL_TESTING_ONLY"
)


DECISION_SUPPORT_NOTICE = (
    "Development decision-support output only. "
    "This result is not a medical diagnosis, "
    "must not automatically create a disease case, "
    "and must not replace assessment by an "
    "authorized health professional."
)


# =========================================================
# MODEL LOADING
# =========================================================

@lru_cache(maxsize=1)
def load_model_bundle():
    if not SELECTED_MODEL_PATH.exists():
        raise FileNotFoundError(
            "Selected disease classifier "
            "artifact is not available. "
            "Run Phase 3 model training first."
        )

    if not MODEL_METADATA_PATH.exists():
        raise FileNotFoundError(
            "Disease classifier metadata "
            "is not available. "
            "Run Phase 3 model training first."
        )

    model = joblib.load(
        SELECTED_MODEL_PATH
    )

    with MODEL_METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(
            file
        )

    if not hasattr(
        model,
        "predict_proba",
    ):
        raise RuntimeError(
            "The selected classifier "
            "does not support probability "
            "prediction."
        )

    return model, metadata


def clear_model_cache() -> None:
    load_model_bundle.cache_clear()


# =========================================================
# PATIENT FEATURE HELPERS
# =========================================================

def calculate_age(
    date_of_birth: date,
    on_date: date | None = None,
) -> int:
    reference_date = (
        on_date
        or date.today()
    )

    if date_of_birth > reference_date:
        raise ValueError(
            "Patient date of birth "
            "cannot be in the future."
        )

    age = (
        reference_date.year
        - date_of_birth.year
        - (
            (
                reference_date.month,
                reference_date.day,
            )
            <
            (
                date_of_birth.month,
                date_of_birth.day,
            )
        )
    )

    if age < 0:
        raise ValueError(
            "Unable to calculate "
            "patient age."
        )

    return age


def normalize_patient_sex(
    value: str,
) -> str:
    normalized = str(
        value
    ).strip().upper()

    if normalized in {
        "M",
        "MALE",
    }:
        return "M"

    if normalized in {
        "F",
        "FEMALE",
    }:
        return "F"

    raise ValueError(
        "The current synthetic "
        "development classifier supports "
        "patient sex values M/F only."
    )


def validate_symptom_codes(
    symptom_codes: list[str],
) -> list[str]:
    allowed = set(
        SYMPTOM_CODES
    )

    normalized: list[str] = []

    for raw_code in symptom_codes:
        code = str(
            raw_code
        ).strip().upper()

        if (
            code
            and code not in normalized
        ):
            normalized.append(
                code
            )

    invalid = sorted(
        set(normalized)
        - allowed
    )

    if invalid:
        raise ValueError(
            "Unsupported structured "
            "symptom code(s): "
            + ", ".join(invalid)
        )

    if not normalized:
        raise ValueError(
            "At least one structured "
            "symptom is required."
        )

    return normalized


def build_input_warnings(
    *,
    age: int,
    temperature: float | None,
    heart_rate: int | None,
    respiratory_rate: int | None,
    oxygen_saturation: float | None,
) -> list[str]:
    warnings: list[str] = []

    if age > 85:
        warnings.append(
            "Patient age is outside the "
            "0-85 synthetic development "
            "range used for model testing."
        )

    numeric_values = {
        "Temperature":
            temperature,
        "Heart rate":
            heart_rate,
        "Respiratory rate":
            respiratory_rate,
        "Oxygen saturation":
            oxygen_saturation,
    }

    for label, value in numeric_values.items():
        if value is None:
            warnings.append(
                f"{label} is missing; "
                "the preprocessing pipeline "
                "will use its development "
                "imputation rule."
            )

    if (
        temperature is not None
        and not (
            34.0
            <= temperature
            <= 42.0
        )
    ):
        warnings.append(
            "Temperature is outside the "
            "34-42 °C synthetic "
            "development range."
        )

    if (
        heart_rate is not None
        and not (
            45
            <= heart_rate
            <= 170
        )
    ):
        warnings.append(
            "Heart rate is outside the "
            "45-170 bpm synthetic "
            "development range."
        )

    if (
        respiratory_rate is not None
        and not (
            8
            <= respiratory_rate
            <= 40
        )
    ):
        warnings.append(
            "Respiratory rate is outside "
            "the 8-40 breaths/minute "
            "synthetic development range."
        )

    if (
        oxygen_saturation is not None
        and not (
            80.0
            <= oxygen_saturation
            <= 100.0
        )
    ):
        warnings.append(
            "Oxygen saturation is outside "
            "the 80-100% synthetic "
            "development range."
        )

    return warnings


# =========================================================
# FEATURE FRAME
# =========================================================

def build_feature_frame(
    *,
    age: int,
    sex: str,
    symptom_codes: list[str],
    temperature: float | None,
    heart_rate: int | None,
    respiratory_rate: int | None,
    oxygen_saturation: float | None,
) -> pd.DataFrame:
    normalized_symptoms = (
        validate_symptom_codes(
            symptom_codes
        )
    )

    feature_row = {
        "age":
            age,

        "sex":
            normalize_patient_sex(
                sex
            ),

        "temperature":
            temperature,

        "heart_rate":
            heart_rate,

        "respiratory_rate":
            respiratory_rate,

        "oxygen_saturation":
            oxygen_saturation,
    }

    selected_symptoms = set(
        normalized_symptoms
    )

    for symptom_code in (
        SYMPTOM_CODES
    ):
        feature_row[
            symptom_code.lower()
        ] = int(
            symptom_code
            in selected_symptoms
        )

    return pd.DataFrame(
        [
            feature_row
        ],
        columns=MODEL_FEATURES,
    )


# =========================================================
# PREDICT
# =========================================================

def predict_disease(
    *,
    age: int,
    sex: str,
    symptom_codes: list[str],
    temperature: float | None,
    heart_rate: int | None,
    respiratory_rate: int | None,
    oxygen_saturation: float | None,
) -> dict[str, object]:
    if age < 0:
        raise ValueError(
            "Patient age cannot "
            "be negative."
        )

    model, metadata = (
        load_model_bundle()
    )

    frame = build_feature_frame(
        age=age,
        sex=sex,
        symptom_codes=symptom_codes,
        temperature=temperature,
        heart_rate=heart_rate,
        respiratory_rate=(
            respiratory_rate
        ),
        oxygen_saturation=(
            oxygen_saturation
        ),
    )

    probabilities = model.predict_proba(
        frame
    )[0]

    classes = [
        str(value)
        for value in model.classes_
    ]

    unexpected_classes = sorted(
        set(classes)
        - set(DISEASE_CLASSES)
    )

    if unexpected_classes:
        raise RuntimeError(
            "The selected model contains "
            "unexpected disease class(es): "
            + ", ".join(
                unexpected_classes
            )
        )

    ranked = sorted(
        [
            {
                "disease_code":
                    disease_code,

                "disease_name":
                    DISEASE_DISPLAY_NAMES.get(
                        disease_code,
                        disease_code,
                    ),

                "probability":
                    round(
                        float(probability),
                        6,
                    ),
            }
            for disease_code, probability
            in zip(
                classes,
                probabilities,
            )
        ],
        key=lambda item:
            item["probability"],
        reverse=True,
    )

    top_result = ranked[0]

    warnings = build_input_warnings(
        age=age,
        temperature=temperature,
        heart_rate=heart_rate,
        respiratory_rate=(
            respiratory_rate
        ),
        oxygen_saturation=(
            oxygen_saturation
        ),
    )

    selected_model = str(
        metadata.get(
            "selected_model",
            "UNKNOWN",
        )
    )

    return {
        "predicted_disease_code":
            top_result[
                "disease_code"
            ],

        "predicted_disease_name":
            top_result[
                "disease_name"
            ],

        "top_probability":
            top_result[
                "probability"
            ],

        "probabilities":
            ranked,

        "selected_model":
            selected_model,

        "development_status":
            DEVELOPMENT_STATUS,

        "input_warnings":
            warnings,

        "decision_support_notice":
            DECISION_SUPPORT_NOTICE,
    }
