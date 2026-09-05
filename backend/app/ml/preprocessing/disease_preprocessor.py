from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


# =========================================================
# MODEL FEATURES
# =========================================================
#
# consultation_date is intentionally excluded so the
# classifier does not learn a shortcut from synthetic
# seasonal generation patterns.
#
# synthetic_record_id, label_source, and data_source are
# metadata only and are never model features.
# =========================================================

NUMERIC_FEATURES = [
    "age",
    "temperature",
    "heart_rate",
    "respiratory_rate",
    "oxygen_saturation",
]

CATEGORICAL_FEATURES = [
    "sex",
]

BINARY_SYMPTOM_FEATURES = [
    "fever",
    "cough",
    "runny_nose",
    "sore_throat",
    "headache",
    "body_pain",
    "vomiting",
    "diarrhea",
    "abdominal_pain",
    "rash",
    "nausea",
    "fatigue",
    "difficulty_breathing",
    "loss_of_appetite",
    "chills",
]

MODEL_FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
    + BINARY_SYMPTOM_FEATURES
)


def build_preprocessor() -> ColumnTransformer:
    """Build a reusable scikit-learn preprocessing pipeline."""

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "one_hot",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
            ),
        ]
    )

    binary_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
            (
                "symptoms",
                binary_pipeline,
                BINARY_SYMPTOM_FEATURES,
            ),
        ],
        remainder="drop",
    )
