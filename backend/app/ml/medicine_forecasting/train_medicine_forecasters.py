"""Select ARIMA/SARIMA models for synthetic medicine demand."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app.ml.config import REPORTS_DIR
from app.ml.medicine_forecasting.common import (
    ARIMA_CANDIDATES,
    SARIMA_CANDIDATES,
    candidate_key,
    fit_model,
    forecast_from_result,
    forecast_metrics,
    get_medicine_codes,
    get_medicine_frame,
    load_validated_medicine_timeseries,
    seasonal_signal,
    serialize_order,
    split_medicine_frame,
    to_series,
)


SELECTION_REPORT_PATH = (
    REPORTS_DIR
    / "medicine_forecast_selection.json"
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
            seasonal_order=seasonal_order,
        )

        prediction = (
            forecast_from_result(
                fitted,
                steps=len(
                    validation_series
                ),
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
                forecast_metrics(
                    validation_series,
                    prediction,
                ),

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


def train_medicine_forecasters():
    frame = (
        load_validated_medicine_timeseries()
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    medicine_reports = {}

    for medicine_code in get_medicine_codes(
        frame
    ):
        medicine_frame = (
            get_medicine_frame(
                frame,
                medicine_code,
            )
        )

        medicine_name = str(
            medicine_frame[
                "medicine_name"
            ].iloc[0]
        )

        split = split_medicine_frame(
            medicine_frame
        )

        train_series = to_series(
            split.train
        )

        validation_series = to_series(
            split.validation
        )

        signal = seasonal_signal(
            train_series
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
                        seasonal_order=seasonal_order,
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
                "All medicine forecasting candidates "
                f"failed for {medicine_code}."
            )

        selected = min(
            successful,
            key=candidate_key,
        )

        medicine_reports[
            medicine_code
        ] = {
            "medicine_code":
                medicine_code,

            "medicine_name":
                medicine_name,

            "rows":
                len(
                    medicine_frame
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
                    split.train[
                        "month_start"
                    ]
                    .iloc[0]
                    .date()
                    .isoformat(),

                "train_end":
                    split.train[
                        "month_start"
                    ]
                    .iloc[-1]
                    .date()
                    .isoformat(),

                "validation_start":
                    split.validation[
                        "month_start"
                    ]
                    .iloc[0]
                    .date()
                    .isoformat(),

                "validation_end":
                    split.validation[
                        "month_start"
                    ]
                    .iloc[-1]
                    .date()
                    .isoformat(),

                "test_start":
                    split.test[
                        "month_start"
                    ]
                    .iloc[0]
                    .date()
                    .isoformat(),

                "test_end":
                    split.test[
                        "month_start"
                    ]
                    .iloc[-1]
                    .date()
                    .isoformat(),
            },

            "seasonality_screen":
                signal,

            "candidate_results":
                candidates,

            "selected_specification": {
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
            "medicine_consumption_2021_2025.csv",

        "methodology": {
            "split":
                (
                    "Chronological split per medicine: "
                    "42 train months, 9 validation "
                    "months, 9 untouched test months."
                ),

            "seasonality_policy":
                (
                    "SARIMA candidates are evaluated "
                    "only when the training series "
                    "shows an absolute lag-12 "
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
                    "MAPE excluding zero-actual months",
                ],
        },

        "medicines":
            medicine_reports,

        "warning":
            (
                "Results are based on synthetic "
                "development data and are not "
                "validated real-world medicine "
                "demand forecasts."
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
        "Medicine forecasting model "
        "selection completed."
    )

    for (
        medicine_code,
        medicine_report,
    ) in medicine_reports.items():
        selected = (
            medicine_report[
                "selected_specification"
            ]
        )

        metrics = selected[
            "validation_metrics"
        ]

        print(
            f"  - {medicine_code} "
            f"{medicine_report['medicine_name']}: "
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
    train_medicine_forecasters()
