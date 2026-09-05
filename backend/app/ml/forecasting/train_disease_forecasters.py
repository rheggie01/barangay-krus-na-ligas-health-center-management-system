"""Select ARIMA/SARIMA specifications using chronological validation.

This is synthetic technical-development forecasting only.
It must not be interpreted as real-world epidemiological performance.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.ml.config import (
    DISEASE_CLASSES,
    REPORTS_DIR,
)
from app.ml.forecasting.common import (
    ARIMA_CANDIDATES,
    SARIMA_CANDIDATES,
    candidate_key,
    fit_model,
    forecast_from_result,
    forecast_metrics,
    get_disease_frame,
    load_validated_disease_timeseries,
    seasonal_signal,
    serialize_order,
    split_disease_frame,
    to_series,
)


SELECTION_REPORT_PATH = (
    REPORTS_DIR
    / "disease_forecast_selection.json"
)


def evaluate_candidate(
    train_series,
    validation_series,
    *,
    model_family: str,
    order,
    seasonal_order=None,
):
    try:
        fitted = fit_model(
            train_series,
            model_family=model_family,
            order=order,
            seasonal_order=(
                seasonal_order
            ),
        )

        predicted = (
            forecast_from_result(
                fitted,
                steps=len(
                    validation_series
                ),
            )
        )

        metrics = (
            forecast_metrics(
                validation_series,
                predicted,
            )
        )

        converged = bool(
            getattr(
                fitted,
                "mle_retvals",
                {},
            ).get(
                "converged",
                True,
            )
        )

        return {
            "status":
                "SUCCESS",

            "model_family":
                model_family,

            "order":
                serialize_order(
                    order
                ),

            "seasonal_order":
                (
                    serialize_order(
                        seasonal_order
                    )
                    if seasonal_order
                    is not None
                    else None
                ),

            "validation_metrics":
                metrics,

            "aic":
                (
                    round(
                        float(
                            fitted.aic
                        ),
                        6,
                    )
                    if getattr(
                        fitted,
                        "aic",
                        None,
                    )
                    is not None
                    else None
                ),

            "converged":
                converged,
        }

    except Exception as exc:
        return {
            "status":
                "FAILED",

            "model_family":
                model_family,

            "order":
                serialize_order(
                    order
                ),

            "seasonal_order":
                (
                    serialize_order(
                        seasonal_order
                    )
                    if seasonal_order
                    is not None
                    else None
                ),

            "error":
                str(exc),
        }


def train_disease_forecasters():
    frame = (
        load_validated_disease_timeseries()
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    disease_reports = {}

    for disease in DISEASE_CLASSES:
        disease_frame = (
            get_disease_frame(
                frame,
                disease,
            )
        )

        split = (
            split_disease_frame(
                disease_frame
            )
        )

        train_series = (
            to_series(
                split.train
            )
        )

        validation_series = (
            to_series(
                split.validation
            )
        )

        signal = (
            seasonal_signal(
                train_series
            )
        )

        candidates = []

        for order in ARIMA_CANDIDATES:
            candidates.append(
                evaluate_candidate(
                    train_series,
                    validation_series,
                    model_family="ARIMA",
                    order=order,
                )
            )

        if signal[
            "sarima_candidate_evaluation_enabled"
        ]:
            for (
                order,
                seasonal_order,
            ) in SARIMA_CANDIDATES:
                candidates.append(
                    evaluate_candidate(
                        train_series,
                        validation_series,
                        model_family="SARIMA",
                        order=order,
                        seasonal_order=(
                            seasonal_order
                        ),
                    )
                )

        successful = [
            candidate
            for candidate in candidates
            if candidate[
                "status"
            ]
            == "SUCCESS"
        ]

        if not successful:
            raise RuntimeError(
                "All forecasting candidates "
                f"failed for {disease}."
            )

        selected = min(
            successful,
            key=candidate_key,
        )

        disease_reports[
            disease
        ] = {
            "rows":
                len(
                    disease_frame
                ),

            "split": {
                "train_rows":
                    len(
                        split.train
                    ),

                "validation_rows":
                    len(
                        split.validation
                    ),

                "test_rows":
                    len(
                        split.test
                    ),

                "train_start":
                    (
                        split.train[
                            "week_start"
                        ]
                        .iloc[0]
                        .date()
                        .isoformat()
                    ),

                "train_end":
                    (
                        split.train[
                            "week_start"
                        ]
                        .iloc[-1]
                        .date()
                        .isoformat()
                    ),

                "validation_start":
                    (
                        split.validation[
                            "week_start"
                        ]
                        .iloc[0]
                        .date()
                        .isoformat()
                    ),

                "validation_end":
                    (
                        split.validation[
                            "week_start"
                        ]
                        .iloc[-1]
                        .date()
                        .isoformat()
                    ),

                "test_start":
                    (
                        split.test[
                            "week_start"
                        ]
                        .iloc[0]
                        .date()
                        .isoformat()
                    ),

                "test_end":
                    (
                        split.test[
                            "week_start"
                        ]
                        .iloc[-1]
                        .date()
                        .isoformat()
                    ),
            },

            "seasonality_screen":
                signal,

            "candidate_results":
                candidates,

            "selected_specification":
                {
                    "model_family":
                        selected[
                            "model_family"
                        ],

                    "order":
                        selected[
                            "order"
                        ],

                    "seasonal_order":
                        selected[
                            "seasonal_order"
                        ],

                    "selection_basis":
                        (
                            "Lowest validation RMSE; "
                            "MAE then nonzero-MAPE "
                            "used as tie-breakers."
                        ),

                    "validation_metrics":
                        selected[
                            "validation_metrics"
                        ],
                },
        }

    report = {
        "created_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "development_status":
            "SYNTHETIC_TECHNICAL_TESTING_ONLY",

        "dataset":
            "disease_timeseries_2021_2025.csv",

        "methodology": {
            "split":
                (
                    "Chronological split per disease: "
                    "183 train weeks, 39 validation "
                    "weeks, 39 untouched test weeks."
                ),

            "seasonality_policy":
                (
                    "SARIMA candidates are evaluated "
                    "only when the training series "
                    "shows an absolute lag-52 "
                    "autocorrelation of at least 0.20 "
                    "and contains at least three "
                    "seasonal cycles."
                ),

            "selection_metric":
                "Validation RMSE",

            "metrics":
                [
                    "MAE",
                    "RMSE",
                    "MAPE excluding zero-actual weeks",
                ],
        },

        "diseases":
            disease_reports,

        "warning":
            (
                "Results are based on synthetic "
                "development data and are not "
                "evidence of real-world disease "
                "forecasting accuracy."
            ),
    }

    with SELECTION_REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    print(
        "Disease forecasting model "
        "selection completed."
    )

    for (
        disease,
        disease_report,
    ) in disease_reports.items():
        selected = (
            disease_report[
                "selected_specification"
            ]
        )

        metrics = (
            selected[
                "validation_metrics"
            ]
        )

        print(
            f"  - {disease}: "
            f"{selected['model_family']} "
            f"order={selected['order']} "
            f"seasonal_order="
            f"{selected['seasonal_order']} "
            f"RMSE={metrics['rmse']:.4f} "
            f"MAE={metrics['mae']:.4f}"
        )

    print(
        f"Selection report: "
        f"{SELECTION_REPORT_PATH}"
    )

    print(
        "IMPORTANT: Synthetic "
        "technical-development "
        "forecasting only."
    )

    return report


if __name__ == "__main__":
    train_disease_forecasters()
