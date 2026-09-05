"""Train and select the synthetic disease classification pipeline.

IMPORTANT
---------
This module is for technical development and pipeline verification.
The dataset is synthetic. Metrics produced here are NOT evidence of
clinical diagnostic accuracy and must not be presented as such.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.config import (
    DISEASE_CLASSES,
    RANDOM_SEED,
    REPORTS_DIR,
    VALIDATED_DIR,
)
from app.ml.preprocessing.disease_preprocessor import (
    MODEL_FEATURES,
    build_preprocessor,
)


# =========================================================
# PATHS / SETTINGS
# =========================================================

DATASET_PATH = (
    VALIDATED_DIR
    / "disease_classification_2021_2025.csv"
)

ML_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ML_ROOT / "artifacts"

LOGISTIC_MODEL_PATH = (
    ARTIFACTS_DIR
    / "logistic_regression.joblib"
)

RANDOM_FOREST_MODEL_PATH = (
    ARTIFACTS_DIR
    / "random_forest.joblib"
)

SELECTED_MODEL_PATH = (
    ARTIFACTS_DIR
    / "selected_model.joblib"
)

METADATA_PATH = (
    ARTIFACTS_DIR
    / "model_metadata.json"
)

SELECTION_REPORT_PATH = (
    REPORTS_DIR
    / "model_selection_report.json"
)

SPLIT_MANIFEST_PATH = (
    REPORTS_DIR
    / "classification_split_manifest.json"
)

TARGET_COLUMN = "disease_label"

TRAIN_SIZE = 0.70
VALIDATION_SIZE = 0.15
TEST_SIZE = 0.15


# =========================================================
# HELPERS
# =========================================================

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _metric_summary(
    y_true: pd.Series,
    y_pred,
) -> dict[str, float]:
    return {
        "accuracy": round(
            accuracy_score(
                y_true,
                y_pred,
            ),
            6,
        ),
        "precision_macro": round(
            precision_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            ),
            6,
        ),
        "recall_macro": round(
            recall_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            ),
            6,
        ),
        "f1_macro": round(
            f1_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            ),
            6,
        ),
        "f1_weighted": round(
            f1_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            ),
            6,
        ),
    }


def _validate_training_frame(
    frame: pd.DataFrame,
) -> None:
    required = {
        "synthetic_record_id",
        TARGET_COLUMN,
        *MODEL_FEATURES,
    }

    missing = sorted(
        required
        - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Training dataset is missing "
            "required column(s): "
            + ", ".join(missing)
        )

    unknown_labels = sorted(
        set(frame[TARGET_COLUMN].dropna())
        - set(DISEASE_CLASSES)
    )

    if unknown_labels:
        raise ValueError(
            "Unexpected disease label(s): "
            + ", ".join(unknown_labels)
        )

    if frame[
        "synthetic_record_id"
    ].duplicated().any():
        raise ValueError(
            "synthetic_record_id must be unique."
        )


def _make_candidate_models() -> dict[str, Pipeline]:
    return {
        "LOGISTIC_REGRESSION": Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor(),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=2500,
                        class_weight="balanced",
                        random_state=RANDOM_SEED,
                    ),
                ),
            ]
        ),
        "RANDOM_FOREST": Pipeline(
            steps=[
                (
                    "preprocessor",
                    build_preprocessor(),
                ),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=400,
                        min_samples_leaf=2,
                        class_weight="balanced_subsample",
                        random_state=RANDOM_SEED,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def _split_dataset(
    frame: pd.DataFrame,
):
    train_frame, temp_frame = (
        train_test_split(
            frame,
            test_size=(
                VALIDATION_SIZE
                + TEST_SIZE
            ),
            stratify=frame[
                TARGET_COLUMN
            ],
            random_state=RANDOM_SEED,
        )
    )

    validation_fraction_of_temp = (
        VALIDATION_SIZE
        / (
            VALIDATION_SIZE
            + TEST_SIZE
        )
    )

    validation_frame, test_frame = (
        train_test_split(
            temp_frame,
            test_size=(
                1
                - validation_fraction_of_temp
            ),
            stratify=temp_frame[
                TARGET_COLUMN
            ],
            random_state=RANDOM_SEED,
        )
    )

    return (
        train_frame.reset_index(
            drop=True
        ),
        validation_frame.reset_index(
            drop=True
        ),
        test_frame.reset_index(
            drop=True
        ),
    )


def _selection_key(
    metrics: dict[str, float],
):
    # Primary criterion: macro F1.
    # Tie-breakers: macro recall, then accuracy.
    return (
        metrics["f1_macro"],
        metrics["recall_macro"],
        metrics["accuracy"],
    )


# =========================================================
# TRAIN
# =========================================================

def train_disease_classifier() -> dict[str, object]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "Validated classification dataset "
            f"not found: {DATASET_PATH}"
        )

    ARTIFACTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame = pd.read_csv(
        DATASET_PATH
    )

    _validate_training_frame(
        frame
    )

    (
        train_frame,
        validation_frame,
        test_frame,
    ) = _split_dataset(frame)

    X_train = train_frame[
        MODEL_FEATURES
    ]
    y_train = train_frame[
        TARGET_COLUMN
    ]

    X_validation = validation_frame[
        MODEL_FEATURES
    ]
    y_validation = validation_frame[
        TARGET_COLUMN
    ]

    candidates = (
        _make_candidate_models()
    )

    candidate_reports: dict[
        str,
        dict[str, object],
    ] = {}

    fitted_candidates = {}

    for (
        model_name,
        pipeline,
    ) in candidates.items():
        pipeline.fit(
            X_train,
            y_train,
        )

        validation_predictions = (
            pipeline.predict(
                X_validation
            )
        )

        validation_metrics = (
            _metric_summary(
                y_validation,
                validation_predictions,
            )
        )

        candidate_reports[
            model_name
        ] = {
            "validation_metrics":
                validation_metrics,
            "validation_classification_report":
                classification_report(
                    y_validation,
                    validation_predictions,
                    labels=list(
                        DISEASE_CLASSES
                    ),
                    output_dict=True,
                    zero_division=0,
                ),
        }

        fitted_candidates[
            model_name
        ] = pipeline

    selected_model_name = max(
        candidate_reports,
        key=lambda name: _selection_key(
            candidate_reports[
                name
            ][
                "validation_metrics"
            ]
        ),
    )

    # Save candidate models exactly as evaluated
    # on the validation set.
    joblib.dump(
        fitted_candidates[
            "LOGISTIC_REGRESSION"
        ],
        LOGISTIC_MODEL_PATH,
    )

    joblib.dump(
        fitted_candidates[
            "RANDOM_FOREST"
        ],
        RANDOM_FOREST_MODEL_PATH,
    )

    # Refit only the selected model using
    # train + validation data. The test set
    # remains completely untouched here.
    train_validation_frame = pd.concat(
        [
            train_frame,
            validation_frame,
        ],
        ignore_index=True,
    )

    selected_model = clone(
        candidates[
            selected_model_name
        ]
    )

    selected_model.fit(
        train_validation_frame[
            MODEL_FEATURES
        ],
        train_validation_frame[
            TARGET_COLUMN
        ],
    )

    joblib.dump(
        selected_model,
        SELECTED_MODEL_PATH,
    )

    split_manifest = {
        "random_seed": RANDOM_SEED,
        "train_size_fraction": TRAIN_SIZE,
        "validation_size_fraction":
            VALIDATION_SIZE,
        "test_size_fraction": TEST_SIZE,

        "train_record_ids":
            train_frame[
                "synthetic_record_id"
            ].tolist(),

        "validation_record_ids":
            validation_frame[
                "synthetic_record_id"
            ].tolist(),

        "test_record_ids":
            test_frame[
                "synthetic_record_id"
            ].tolist(),
    }

    with SPLIT_MANIFEST_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            split_manifest,
            file,
            indent=2,
        )

    selection_report = {
        "development_status":
            "SYNTHETIC_TECHNICAL_TESTING_ONLY",

        "selection_basis":
            (
                "Highest validation macro F1; "
                "macro recall then accuracy "
                "used only as tie-breakers."
            ),

        "selected_model":
            selected_model_name,

        "candidate_validation_results":
            candidate_reports,

        "dataset_rows":
            len(frame),

        "split_rows": {
            "train":
                len(train_frame),
            "validation":
                len(validation_frame),
            "test":
                len(test_frame),
        },
    }

    with SELECTION_REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            selection_report,
            file,
            indent=2,
        )

    metadata = {
        "created_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "development_status":
            "SYNTHETIC_TECHNICAL_TESTING_ONLY",

        "clinical_use":
            (
                "NOT VALIDATED FOR CLINICAL "
                "DIAGNOSIS OR AUTONOMOUS "
                "MEDICAL DECISION-MAKING"
            ),

        "dataset_path":
            str(DATASET_PATH),

        "dataset_sha256":
            _sha256(DATASET_PATH),

        "target_column":
            TARGET_COLUMN,

        "feature_columns":
            MODEL_FEATURES,

        "excluded_metadata_columns": [
            "synthetic_record_id",
            "consultation_date",
            "label_source",
            "data_source",
        ],

        "disease_classes":
            list(DISEASE_CLASSES),

        "random_seed":
            RANDOM_SEED,

        "selected_model":
            selected_model_name,

        "artifacts": {
            "logistic_regression":
                str(
                    LOGISTIC_MODEL_PATH
                ),
            "random_forest":
                str(
                    RANDOM_FOREST_MODEL_PATH
                ),
            "selected_model":
                str(
                    SELECTED_MODEL_PATH
                ),
        },
    }

    with METADATA_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
        )

    print(
        "Disease classifier training "
        "completed successfully."
    )

    print(
        f"Dataset rows: {len(frame)}"
    )

    print(
        "Split: "
        f"{len(train_frame)} train / "
        f"{len(validation_frame)} validation / "
        f"{len(test_frame)} test"
    )

    print(
        "Validation model comparison:"
    )

    for (
        model_name,
        report,
    ) in candidate_reports.items():
        metrics = report[
            "validation_metrics"
        ]

        print(
            f"  - {model_name}: "
            f"accuracy={metrics['accuracy']:.4f}, "
            f"precision_macro="
            f"{metrics['precision_macro']:.4f}, "
            f"recall_macro="
            f"{metrics['recall_macro']:.4f}, "
            f"f1_macro="
            f"{metrics['f1_macro']:.4f}"
        )

    print(
        f"Selected model: "
        f"{selected_model_name}"
    )

    print(
        f"Selected artifact: "
        f"{SELECTED_MODEL_PATH}"
    )

    print(
        "IMPORTANT: These results are "
        "synthetic technical-development "
        "metrics, not clinical accuracy."
    )

    return selection_report


if __name__ == "__main__":
    train_disease_classifier()
