"""Evaluate selected medicine-demand models and forecast six months."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from app.ml.config import REPORTS_DIR
from app.ml.medicine_forecasting.common import (
    deserialize_order,
    fit_model,
    forecast_from_result,
    forecast_metrics,
    forecast_with_interval,
    get_medicine_codes,
    get_medicine_frame,
    load_validated_medicine_timeseries,
    safe_filename,
    split_medicine_frame,
    to_series,
)
from app.ml.medicine_forecasting.train_medicine_forecasters import (
    SELECTION_REPORT_PATH,
)


ML_ROOT = Path(__file__).resolve().parents[1]

ARTIFACTS_DIR = (
    ML_ROOT
    / "artifacts"
    / "medicine_forecasting"
)

EVALUATION_REPORT_PATH = (
    REPORTS_DIR
    / "medicine_forecast_test_evaluation.json"
)

FUTURE_FORECAST_PATH = (
    REPORTS_DIR
    / "medicine_forecast_6_month.csv"
)

FORECAST_HORIZON_MONTHS = 6


def load_selection_report():
    if not SELECTION_REPORT_PATH.exists():
        raise FileNotFoundError(
            "Medicine forecast selection report "
            "not found. Run "
            "train_medicine_forecasters first."
        )

    with SELECTION_REPORT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )


def evaluate_medicine_forecasters():
    frame = (
        load_validated_medicine_timeseries()
    )

    selection_report = (
        load_selection_report()
    )

    ARTIFACTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    medicine_evaluations = {}
    future_rows = []

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

        specification = (
            selection_report[
                "medicines"
            ][
                medicine_code
            ][
                "selected_specification"
            ]
        )

        model_family = specification[
            "model_family"
        ]

        order = deserialize_order(
            specification[
                "order"
            ]
        )

        seasonal_order = (
            deserialize_order(
                specification[
                    "seasonal_order"
                ]
            )
            if specification[
                "seasonal_order"
            ]
            is not None
            else None
        )

        train_validation_frame = (
            pd.concat(
                [
                    split.train,
                    split.validation,
                ],
                ignore_index=True,
            )
        )

        train_validation_series = (
            to_series(
                train_validation_frame
            )
        )

        test_series = to_series(
            split.test
        )

        evaluation_model = fit_model(
            train_validation_series,
            model_family=model_family,
            order=order,
            seasonal_order=seasonal_order,
        )

        test_predictions = (
            forecast_from_result(
                evaluation_model,
                steps=len(
                    test_series
                ),
            )
        )

        test_metrics = forecast_metrics(
            test_series,
            test_predictions,
        )

        full_series = to_series(
            medicine_frame
        )

        final_model = fit_model(
            full_series,
            model_family=model_family,
            order=order,
            seasonal_order=seasonal_order,
        )

        artifact_path = (
            ARTIFACTS_DIR
            / (
                safe_filename(
                    medicine_code
                )
                + ".joblib"
            )
        )

        joblib.dump(
            final_model,
            artifact_path,
        )

        (
            forecast_mean,
            forecast_lower,
            forecast_upper,
        ) = forecast_with_interval(
            final_model,
            steps=(
                FORECAST_HORIZON_MONTHS
            ),
        )

        last_month = (
            medicine_frame[
                "month_start"
            ]
            .iloc[-1]
        )

        future_dates = pd.date_range(
            start=(
                last_month
                + pd.offsets.MonthBegin(
                    1
                )
            ),
            periods=(
                FORECAST_HORIZON_MONTHS
            ),
            freq="MS",
        )

        for (
            month_start,
            mean_value,
            lower_value,
            upper_value,
        ) in zip(
            future_dates,
            forecast_mean,
            forecast_lower,
            forecast_upper,
        ):
            future_rows.append(
                {
                    "month_start":
                        month_start
                        .date()
                        .isoformat(),

                    "medicine_code":
                        medicine_code,

                    "medicine_name":
                        medicine_name,

                    "model_family":
                        model_family,

                    "forecast_quantity_dispensed":
                        round(
                            float(
                                mean_value
                            ),
                            3,
                        ),

                    "lower_95":
                        round(
                            float(
                                lower_value
                            ),
                            3,
                        ),

                    "upper_95":
                        round(
                            float(
                                upper_value
                            ),
                            3,
                        ),

                    "development_status":
                        (
                            "SYNTHETIC_"
                            "TECHNICAL_"
                            "TESTING_ONLY"
                        ),
                }
            )

        medicine_evaluations[
            medicine_code
        ] = {
            "medicine_name":
                medicine_name,

            "selected_model_family":
                model_family,

            "order":
                list(
                    order
                ),

            "seasonal_order":
                (
                    list(
                        seasonal_order
                    )
                    if seasonal_order
                    is not None
                    else None
                ),

            "test_rows":
                len(
                    test_series
                ),

            "test_period": {
                "start":
                    split.test[
                        "month_start"
                    ]
                    .iloc[0]
                    .date()
                    .isoformat(),

                "end":
                    split.test[
                        "month_start"
                    ]
                    .iloc[-1]
                    .date()
                    .isoformat(),
            },

            "test_metrics":
                test_metrics,

            "final_model_training_rows":
                len(
                    full_series
                ),

            "final_model_artifact":
                str(
                    artifact_path
                ),

            "future_forecast_horizon_months":
                FORECAST_HORIZON_MONTHS,
        }

    future_frame = pd.DataFrame(
        future_rows
    )

    future_frame.to_csv(
        FUTURE_FORECAST_PATH,
        index=False,
    )

    evaluation_report = {
        "created_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "development_status":
            "SYNTHETIC_TECHNICAL_TESTING_ONLY",

        "evaluation_policy":
            (
                "Selected specification is "
                "refit on train + validation "
                "and evaluated once on the "
                "untouched chronological test "
                "period. It is then refit on "
                "all available synthetic history "
                "for a six-month development "
                "medicine-demand forecast."
            ),

        "medicines":
            medicine_evaluations,

        "future_forecast_file":
            str(
                FUTURE_FORECAST_PATH
            ),

        "warning":
            (
                "Forecasts and metrics are "
                "synthetic technical-development "
                "outputs only and must not be "
                "presented as validated medicine "
                "demand or procurement requirements."
            ),
    }

    with EVALUATION_REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            evaluation_report,
            file,
            indent=2,
        )

    print(
        "Medicine forecast test evaluation "
        "and 6-month forecast completed."
    )

    for (
        medicine_code,
        medicine_report,
    ) in medicine_evaluations.items():
        metrics = medicine_report[
            "test_metrics"
        ]

        print(
            f"  - {medicine_code} "
            f"{medicine_report['medicine_name']}: "
            f"{medicine_report['selected_model_family']} "
            f"RMSE={metrics['rmse']:.4f} "
            f"MAE={metrics['mae']:.4f} "
            f"MAPE(nonzero)="
            f"{metrics['mape_nonzero_pct']:.2f}%"
        )

    print(
        f"Evaluation report: "
        f"{EVALUATION_REPORT_PATH}"
    )

    print(
        f"6-month forecast: "
        f"{FUTURE_FORECAST_PATH}"
    )

    print(
        f"Model artifacts: "
        f"{ARTIFACTS_DIR}"
    )

    print(
        "IMPORTANT: Synthetic "
        "technical-development "
        "forecasting only."
    )

    return evaluation_report


if __name__ == "__main__":
    evaluate_medicine_forecasters()
