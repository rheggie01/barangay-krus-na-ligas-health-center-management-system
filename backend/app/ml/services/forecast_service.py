from __future__ import annotations

import json
import math
import warnings
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import (
    SARIMAX,
)

from app.ml.config import (
    DISEASE_CLASSES,
    REPORTS_DIR,
    VALIDATED_DIR,
)
from app.ml.services.runtime_forecast_data import (
    actual_next_month_start,
    build_dynamic_disease_series,
    build_dynamic_medicine_series,
    current_week_start,
)


LOCAL_TIMEZONE = ZoneInfo(
    "Asia/Manila"
)

DEVELOPMENT_STATUS = (
    "DYNAMIC_RUNTIME_DEVELOPMENT_FORECAST"
)


# =========================================================
# FILES
# =========================================================

DISEASE_TIMESERIES_PATH = (
    VALIDATED_DIR
    / "disease_timeseries_2021_2025.csv"
)

DISEASE_EVALUATION_REPORT_PATH = (
    REPORTS_DIR
    / "disease_forecast_test_evaluation.json"
)

MEDICINE_TIMESERIES_PATH = (
    VALIDATED_DIR
    / "medicine_consumption_2021_2025.csv"
)

MEDICINE_EVALUATION_REPORT_PATH = (
    REPORTS_DIR
    / "medicine_forecast_test_evaluation.json"
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


RECOMMENDATION_FORMULA = (
    "max(0, Forecast Demand + Safety Stock "
    "- Usable Current Stock)"
)


# =========================================================
# LOADERS
# =========================================================

def _require_files() -> None:
    missing = [
        str(path)
        for path in [
            DISEASE_TIMESERIES_PATH,
            DISEASE_EVALUATION_REPORT_PATH,
            MEDICINE_TIMESERIES_PATH,
            MEDICINE_EVALUATION_REPORT_PATH,
        ]
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Required forecasting file(s) "
            "not found: "
            + ", ".join(
                missing
            )
        )


@lru_cache(maxsize=1)
def _load_disease_baseline() -> pd.DataFrame:
    _require_files()

    return pd.read_csv(
        DISEASE_TIMESERIES_PATH,
        parse_dates=[
            "week_start"
        ],
    )


@lru_cache(maxsize=1)
def _load_disease_report() -> dict:
    _require_files()

    with DISEASE_EVALUATION_REPORT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )


@lru_cache(maxsize=1)
def _load_medicine_baseline() -> pd.DataFrame:
    _require_files()

    return pd.read_csv(
        MEDICINE_TIMESERIES_PATH,
        parse_dates=[
            "month_start"
        ],
    )


@lru_cache(maxsize=1)
def _load_medicine_report() -> dict:
    _require_files()

    with MEDICINE_EVALUATION_REPORT_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )


# =========================================================
# RUNTIME MODEL REFIT
# =========================================================

def _fit_selected_model(
    series: pd.Series,
    *,
    model_family: str,
    order: list[int],
    seasonal_order: (
        list[int]
        | None
    ),
):
    order_tuple = tuple(
        int(value)
        for value in order
    )

    family = (
        model_family
        .strip()
        .upper()
    )

    with warnings.catch_warnings():
        warnings.simplefilter(
            "ignore"
        )

        if family == "ARIMA":
            trend = (
                "ct"
                if order_tuple[1] == 0
                else "t"
            )

            return ARIMA(
                series,
                order=order_tuple,
                trend=trend,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit()

        if family == "SARIMA":
            if seasonal_order is None:
                raise ValueError(
                    "SARIMA requires seasonal_order."
                )

            seasonal_tuple = tuple(
                int(value)
                for value in seasonal_order
            )

            trend = (
                "c"
                if order_tuple[1] == 0
                else "t"
            )

            return SARIMAX(
                series,
                order=order_tuple,
                seasonal_order=seasonal_tuple,
                trend=trend,
                enforce_stationarity=False,
                enforce_invertibility=False,
                simple_differencing=False,
            ).fit(
                disp=False,
                maxiter=100,
            )

    raise ValueError(
        "Unsupported forecasting model family: "
        f"{model_family}"
    )


def _forecast_with_interval(
    fitted,
    *,
    steps: int,
):
    result = fitted.get_forecast(
        steps=steps
    )

    mean = np.clip(
        np.asarray(
            result.predicted_mean,
            dtype=float,
        ),
        0.0,
        None,
    )

    confidence = (
        result.conf_int(
            alpha=0.05
        )
    )

    if hasattr(
        confidence,
        "iloc",
    ):
        lower = (
            confidence.iloc[
                :,
                0
            ].to_numpy(
                dtype=float
            )
        )

        upper = (
            confidence.iloc[
                :,
                1
            ].to_numpy(
                dtype=float
            )
        )

    else:
        values = np.asarray(
            confidence,
            dtype=float,
        )

        lower = values[
            :,
            0
        ]

        upper = values[
            :,
            1
        ]

    return (
        mean,
        np.clip(
            lower,
            0.0,
            None,
        ),
        np.clip(
            upper,
            0.0,
            None,
        ),
    )


def _runtime_message(
    metadata: dict,
    *,
    period_label: str,
) -> str:
    status = metadata[
        "freshness_status"
    ]

    if status == "LIVE_CURRENT":
        return (
            "The runtime series includes stored "
            f"database data through the latest completed "
            f"{period_label}. Forecast parameters are "
            "refit automatically whenever this forecast "
            "is requested."
        )

    if status == "NO_COMPLETED_LIVE_DATA":
        return (
            "The system has started collecting records, "
            f"but no completed {period_label} is available "
            "yet. The runtime forecast remains date-aligned "
            "but currently relies mainly on the development "
            "baseline until a completed live period exists."
        )

    if status == "NO_SAFE_INVENTORY_MATCH":
        return (
            "The forecast is date-aligned, but no exact "
            "safe active inventory formulation is mapped. "
            "Database medicine demand cannot yet be appended "
            "to this baseline medicine series."
        )

    if status == "NO_SYSTEM_ACTIVITY":
        return (
            "No qualifying live database coverage has "
            "started yet. The model is propagated from the "
            "development baseline to the current forecast "
            "date without treating missing periods as zero."
        )

    return (
        "The forecast uses the development baseline plus "
        "any qualifying stored database observations that "
        "are currently available."
    )


def _runtime_status(
    metadata: dict,
    *,
    period_label: str,
) -> dict:
    generated_at = datetime.now(
        LOCAL_TIMEZONE
    ).isoformat()

    return {
        **metadata,

        "forecast_generated_at":
            generated_at,

        "message":
            _runtime_message(
                metadata,
                period_label=period_label,
            ),
    }


# =========================================================
# DISEASE FORECASTS
# =========================================================

def list_disease_forecasts(
    db: Session,
) -> list[dict]:
    report = (
        _load_disease_report()
    )

    rows = []

    for disease_code in DISEASE_CLASSES:
        disease_report = (
            report[
                "diseases"
            ][disease_code]
        )

        metrics = (
            disease_report[
                "test_metrics"
            ]
        )

        rows.append(
            {
                "disease_code":
                    disease_code,

                "disease_name":
                    DISEASE_DISPLAY_NAMES.get(
                        disease_code,
                        disease_code,
                    ),

                "model_family":
                    disease_report[
                        "selected_model_family"
                    ],

                "rmse":
                    float(
                        metrics["rmse"]
                    ),

                "mae":
                    float(
                        metrics["mae"]
                    ),

                "mape_nonzero_pct":
                    (
                        float(
                            metrics[
                                "mape_nonzero_pct"
                            ]
                        )
                        if metrics[
                            "mape_nonzero_pct"
                        ]
                        is not None
                        else None
                    ),
            }
        )

    return rows


def get_disease_forecast(
    db: Session,
    disease_code: str,
) -> dict:
    normalized = (
        disease_code
        .strip()
        .upper()
    )

    if normalized not in DISEASE_CLASSES:
        raise ValueError(
            "Unsupported disease code."
        )

    baseline = (
        _load_disease_baseline()
    )

    report = (
        _load_disease_report()
    )

    disease_report = (
        report[
            "diseases"
        ][normalized]
    )

    metrics = (
        disease_report[
            "test_metrics"
        ]
    )

    (
        runtime_series,
        metadata,
    ) = build_dynamic_disease_series(
        db,
        baseline_frame=baseline,
        disease_code=normalized,
    )

    fitted = _fit_selected_model(
        runtime_series,
        model_family=(
            disease_report[
                "selected_model_family"
            ]
        ),
        order=(
            disease_report[
                "order"
            ]
        ),
        seasonal_order=(
            disease_report[
                "seasonal_order"
            ]
        ),
    )

    horizon = 12

    (
        mean,
        lower,
        upper,
    ) = _forecast_with_interval(
        fitted,
        steps=horizon,
    )

    first_forecast_week = (
        current_week_start()
    )

    forecast_dates = pd.date_range(
        start=first_forecast_week,
        periods=horizon,
        freq="W-MON",
    )

    baseline_end = pd.Timestamp(
        metadata[
            "baseline_end"
        ]
    )

    historical_tail = (
        runtime_series
        .tail(
            52
        )
    )

    historical_points = []

    for (
        timestamp,
        value,
    ) in historical_tail.items():
        historical_points.append(
            {
                "week_start":
                    timestamp
                    .date()
                    .isoformat(),

                "case_count":
                    (
                        float(
                            value
                        )
                        if pd.notna(
                            value
                        )
                        else None
                    ),

                "source":
                    (
                        "DEVELOPMENT_BASELINE"
                        if timestamp
                        <= baseline_end
                        else (
                            "LIVE_DATABASE"
                            if pd.notna(
                                value
                            )
                            else "MISSING_NOT_ZERO"
                        )
                    ),
            }
        )

    forecast_points = [
        {
            "week_start":
                forecast_date
                .date()
                .isoformat(),

            "forecast_case_count":
                round(
                    float(
                        mean[index]
                    ),
                    3,
                ),

            "lower_95":
                round(
                    float(
                        lower[index]
                    ),
                    3,
                ),

            "upper_95":
                round(
                    float(
                        upper[index]
                    ),
                    3,
                ),
        }
        for index, forecast_date
        in enumerate(
            forecast_dates
        )
    ]

    runtime_data = (
        _runtime_status(
            metadata,
            period_label="week",
        )
    )

    return {
        "disease_code":
            normalized,

        "disease_name":
            DISEASE_DISPLAY_NAMES.get(
                normalized,
                normalized,
            ),

        "model_family":
            disease_report[
                "selected_model_family"
            ],

        "order":
            disease_report[
                "order"
            ],

        "seasonal_order":
            disease_report[
                "seasonal_order"
            ],

        "rmse":
            float(
                metrics["rmse"]
            ),

        "mae":
            float(
                metrics["mae"]
            ),

        "mape_nonzero_pct":
            (
                float(
                    metrics[
                        "mape_nonzero_pct"
                    ]
                )
                if metrics[
                    "mape_nonzero_pct"
                ]
                is not None
                else None
            ),

        "historical_points":
            historical_points,

        "forecast_points":
            forecast_points,

        "forecast_horizon_weeks":
            horizon,

        "runtime_data":
            runtime_data,

        "development_status":
            DEVELOPMENT_STATUS,

        "warning":
            (
                "Disease forecasting is decision support "
                "only. Development baseline data remains "
                "synthetic; newly stored VALIDATED disease "
                "cases are automatically incorporated by "
                "completed week when available."
            ),
    }


# =========================================================
# MEDICINE FORECASTS
# =========================================================

def list_medicine_forecasts(
    db: Session,
) -> list[dict]:
    report = (
        _load_medicine_report()
    )

    baseline = (
        _load_medicine_baseline()
    )

    rows = []

    for medicine_code in sorted(
        report[
            "medicines"
        ].keys()
    ):
        medicine_report = (
            report[
                "medicines"
            ][medicine_code]
        )

        medicine_name = (
            medicine_report[
                "medicine_name"
            ]
        )

        metrics = (
            medicine_report[
                "test_metrics"
            ]
        )

        (
            _series,
            _metadata,
            inventory,
        ) = build_dynamic_medicine_series(
            db,
            baseline_frame=baseline,
            baseline_code=medicine_code,
            baseline_name=medicine_name,
        )

        rows.append(
            {
                "medicine_code":
                    medicine_code,

                "medicine_name":
                    medicine_name,

                "model_family":
                    medicine_report[
                        "selected_model_family"
                    ],

                "rmse":
                    float(
                        metrics["rmse"]
                    ),

                "mae":
                    float(
                        metrics["mae"]
                    ),

                "mape_nonzero_pct":
                    (
                        float(
                            metrics[
                                "mape_nonzero_pct"
                            ]
                        )
                        if metrics[
                            "mape_nonzero_pct"
                        ]
                        is not None
                        else None
                    ),

                "inventory_match_status":
                    inventory[
                        "match_status"
                    ],
            }
        )

    return rows


def get_medicine_forecast(
    db: Session,
    medicine_code: str,
) -> dict:
    normalized = (
        medicine_code
        .strip()
        .upper()
    )

    report = (
        _load_medicine_report()
    )

    if normalized not in report[
        "medicines"
    ]:
        raise ValueError(
            "Unsupported medicine forecast code."
        )

    medicine_report = (
        report[
            "medicines"
        ][normalized]
    )

    medicine_name = (
        medicine_report[
            "medicine_name"
        ]
    )

    metrics = (
        medicine_report[
            "test_metrics"
        ]
    )

    baseline = (
        _load_medicine_baseline()
    )

    (
        runtime_series,
        metadata,
        inventory,
    ) = build_dynamic_medicine_series(
        db,
        baseline_frame=baseline,
        baseline_code=normalized,
        baseline_name=medicine_name,
    )

    fitted = _fit_selected_model(
        runtime_series,
        model_family=(
            medicine_report[
                "selected_model_family"
            ]
        ),
        order=(
            medicine_report[
                "order"
            ]
        ),
        seasonal_order=(
            medicine_report[
                "seasonal_order"
            ]
        ),
    )

    target_start = (
        actual_next_month_start()
    )

    last_series_month = (
        runtime_series.index[-1]
        .date()
    )

    immediate_next_month = (
        pd.Timestamp(
            last_series_month
        )
        + pd.offsets.MonthBegin(
            1
        )
    ).date()

    month_gap = (
        (
            target_start.year
            - immediate_next_month.year
        )
        * 12
        + (
            target_start.month
            - immediate_next_month.month
        )
    )

    if month_gap < 0:
        month_gap = 0

    visible_horizon = 6

    total_steps = (
        month_gap
        + visible_horizon
    )

    (
        all_mean,
        all_lower,
        all_upper,
    ) = _forecast_with_interval(
        fitted,
        steps=total_steps,
    )

    mean = all_mean[
        month_gap:
        month_gap
        + visible_horizon
    ]

    lower = all_lower[
        month_gap:
        month_gap
        + visible_horizon
    ]

    upper = all_upper[
        month_gap:
        month_gap
        + visible_horizon
    ]

    forecast_dates = pd.date_range(
        start=target_start,
        periods=visible_horizon,
        freq="MS",
    )

    baseline_end = pd.Timestamp(
        metadata[
            "baseline_end"
        ]
    )

    historical_tail = (
        runtime_series
        .tail(
            24
        )
    )

    historical_points = []

    for (
        timestamp,
        value,
    ) in historical_tail.items():
        historical_points.append(
            {
                "month_start":
                    timestamp
                    .date()
                    .isoformat(),

                "quantity_dispensed":
                    (
                        float(
                            value
                        )
                        if pd.notna(
                            value
                        )
                        else None
                    ),

                "source":
                    (
                        "DEVELOPMENT_BASELINE"
                        if timestamp
                        <= baseline_end
                        else (
                            "LIVE_DATABASE"
                            if pd.notna(
                                value
                            )
                            else "MISSING_NOT_ZERO"
                        )
                    ),
            }
        )

    forecast_points = [
        {
            "month_start":
                forecast_date
                .date()
                .isoformat(),

            "forecast_quantity_dispensed":
                round(
                    float(
                        mean[index]
                    ),
                    3,
                ),

            "lower_95":
                round(
                    float(
                        lower[index]
                    ),
                    3,
                ),

            "upper_95":
                round(
                    float(
                        upper[index]
                    ),
                    3,
                ),
        }
        for index, forecast_date
        in enumerate(
            forecast_dates
        )
    ]

    first_forecast_quantity = float(
        forecast_points[0][
            "forecast_quantity_dispensed"
        ]
    )

    withheld_reasons = []

    if not inventory[
        "matched"
    ]:
        withheld_reasons.append(
            inventory[
                "message"
            ]
        )

    if metadata[
        "freshness_status"
    ] != "LIVE_CURRENT":
        withheld_reasons.append(
            _runtime_message(
                metadata,
                period_label="month",
            )
        )

    if metadata[
        "package_conversion_warning"
    ]:
        withheld_reasons.append(
            (
                "At least one PACKAGE dispensing record "
                "could not be converted to dispensing "
                "units because units_per_package is not "
                "configured."
            )
        )

    if withheld_reasons:
        recommendation = {
            "status":
                "WITHHELD",

            "formula":
                RECOMMENDATION_FORMULA,

            "forecast_month":
                forecast_points[0][
                    "month_start"
                ],

            "forecast_quantity":
                first_forecast_quantity,

            "current_usable_stock":
                inventory[
                    "usable_current_stock"
                ],

            "safety_stock":
                inventory[
                    "reorder_level"
                ],

            "recommended_additional_stock":
                None,

            "dispensing_unit":
                inventory[
                    "dispensing_unit"
                ],

            "withheld_reasons":
                withheld_reasons,

            "note":
                (
                    "The next-month forecast is still "
                    "displayed. The stock recommendation "
                    "remains withheld until live monthly "
                    "database coverage and safe medicine "
                    "identity/conversion requirements are met."
                ),
        }

    else:
        current_stock = int(
            inventory[
                "usable_current_stock"
            ]
            or 0
        )

        safety_stock = int(
            inventory[
                "reorder_level"
            ]
            or 0
        )

        recommended = int(
            math.ceil(
                max(
                    0.0,
                    first_forecast_quantity
                    + safety_stock
                    - current_stock,
                )
            )
        )

        recommendation = {
            "status":
                "AVAILABLE",

            "formula":
                RECOMMENDATION_FORMULA,

            "forecast_month":
                forecast_points[0][
                    "month_start"
                ],

            "forecast_quantity":
                first_forecast_quantity,

            "current_usable_stock":
                current_stock,

            "safety_stock":
                safety_stock,

            "recommended_additional_stock":
                recommended,

            "dispensing_unit":
                inventory[
                    "dispensing_unit"
                ],

            "withheld_reasons":
                [],

            "note":
                (
                    "Advisory only. The selected runtime "
                    "forecast is aligned to the actual next "
                    "calendar month and uses completed live "
                    "database dispensing coverage. No stock "
                    "transaction or purchase order is created."
                ),
        }

    runtime_data = (
        _runtime_status(
            metadata,
            period_label="month",
        )
    )

    return {
        "medicine_code":
            normalized,

        "medicine_name":
            medicine_name,

        "model_family":
            medicine_report[
                "selected_model_family"
            ],

        "order":
            medicine_report[
                "order"
            ],

        "seasonal_order":
            medicine_report[
                "seasonal_order"
            ],

        "rmse":
            float(
                metrics["rmse"]
            ),

        "mae":
            float(
                metrics["mae"]
            ),

        "mape_nonzero_pct":
            (
                float(
                    metrics[
                        "mape_nonzero_pct"
                    ]
                )
                if metrics[
                    "mape_nonzero_pct"
                ]
                is not None
                else None
            ),

        "historical_points":
            historical_points,

        "forecast_points":
            forecast_points,

        "forecast_horizon_months":
            visible_horizon,

        "cumulative_6_month_forecast":
            round(
                sum(
                    point[
                        "forecast_quantity_dispensed"
                    ]
                    for point
                    in forecast_points
                ),
                3,
            ),

        "inventory":
            inventory,

        "runtime_data":
            runtime_data,

        "recommendation":
            recommendation,

        "development_status":
            DEVELOPMENT_STATUS,

        "warning":
            (
                "The 2021-2025 baseline remains synthetic "
                "development history. Completed medicine "
                "dispensing records stored by this system "
                "are appended automatically by month. "
                "Forecast dates are generated relative to "
                "the current system date."
            ),
    }
