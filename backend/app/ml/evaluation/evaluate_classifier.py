"""Evaluate the selected classifier on the untouched test split."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from app.ml.config import (
    DISEASE_CLASSES,
    REPORTS_DIR,
    VALIDATED_DIR,
)
from app.ml.preprocessing.disease_preprocessor import (
    MODEL_FEATURES,
)


ML_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    VALIDATED_DIR
    / "disease_classification_2021_2025.csv"
)

SELECTED_MODEL_PATH = (
    ML_ROOT
    / "artifacts"
    / "selected_model.joblib"
)

METADATA_PATH = (
    ML_ROOT
    / "artifacts"
    / "model_metadata.json"
)

SPLIT_MANIFEST_PATH = (
    REPORTS_DIR
    / "classification_split_manifest.json"
)

EVALUATION_REPORT_PATH = (
    REPORTS_DIR
    / "classifier_test_evaluation.json"
)

CONFUSION_MATRIX_PATH = (
    REPORTS_DIR
    / "classifier_test_confusion_matrix.csv"
)

TARGET_COLUMN = "disease_label"


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


def evaluate_selected_classifier() -> dict[str, object]:
    required_paths = [
        DATASET_PATH,
        SELECTED_MODEL_PATH,
        METADATA_PATH,
        SPLIT_MANIFEST_PATH,
    ]

    missing = [
        str(path)
        for path in required_paths
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Required Phase 3 file(s) "
            "not found: "
            + ", ".join(missing)
        )

    frame = pd.read_csv(
        DATASET_PATH
    )

    with SPLIT_MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        split_manifest = json.load(
            file
        )

    with METADATA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(
            file
        )

    test_ids = set(
        split_manifest[
            "test_record_ids"
        ]
    )

    test_frame = frame[
        frame[
            "synthetic_record_id"
        ].isin(test_ids)
    ].copy()

    if len(test_frame) != len(
        test_ids
    ):
        raise ValueError(
            "The validated dataset no "
            "longer matches the saved "
            "test split manifest."
        )

    model = joblib.load(
        SELECTED_MODEL_PATH
    )

    X_test = test_frame[
        MODEL_FEATURES
    ]

    y_test = test_frame[
        TARGET_COLUMN
    ]

    predictions = model.predict(
        X_test
    )

    metrics = _metric_summary(
        y_test,
        predictions,
    )

    report = classification_report(
        y_test,
        predictions,
        labels=list(
            DISEASE_CLASSES
        ),
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=list(
            DISEASE_CLASSES
        ),
    )

    evaluation = {
        "development_status":
            "SYNTHETIC_TECHNICAL_TESTING_ONLY",

        "selected_model":
            metadata[
                "selected_model"
            ],

        "test_rows":
            len(test_frame),

        "metrics":
            metrics,

        "classification_report":
            report,

        "disease_class_order":
            list(DISEASE_CLASSES),

        "interpretation_warning":
            (
                "Held-out performance on "
                "synthetic scenario data only. "
                "It is not evidence of clinical "
                "diagnostic accuracy."
            ),
    }

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with EVALUATION_REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            evaluation,
            file,
            indent=2,
        )

    with CONFUSION_MATRIX_PATH.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(
            file
        )

        writer.writerow(
            [
                "actual\\predicted",
                *DISEASE_CLASSES,
            ]
        )

        for (
            disease,
            row,
        ) in zip(
            DISEASE_CLASSES,
            matrix,
        ):
            writer.writerow(
                [
                    disease,
                    *[
                        int(value)
                        for value in row
                    ],
                ]
            )

    print(
        "Selected classifier test "
        "evaluation completed."
    )

    print(
        f"Selected model: "
        f"{metadata['selected_model']}"
    )

    print(
        f"Test rows: "
        f"{len(test_frame)}"
    )

    print(
        f"Accuracy: "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Precision (macro): "
        f"{metrics['precision_macro']:.4f}"
    )

    print(
        f"Recall (macro): "
        f"{metrics['recall_macro']:.4f}"
    )

    print(
        f"F1 (macro): "
        f"{metrics['f1_macro']:.4f}"
    )

    print(
        f"Evaluation report: "
        f"{EVALUATION_REPORT_PATH}"
    )

    print(
        f"Confusion matrix: "
        f"{CONFUSION_MATRIX_PATH}"
    )

    print(
        "IMPORTANT: Synthetic technical "
        "testing only; not clinical accuracy."
    )

    return evaluation


if __name__ == "__main__":
    evaluate_selected_classifier()
