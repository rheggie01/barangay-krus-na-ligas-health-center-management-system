from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.ml.config import (
    DISEASE_CLASSES,
    VALIDATED_DIR,
)


DATASET_PATH = (
    VALIDATED_DIR
    / "disease_timeseries_2021_2025.csv"
)

DATE_COLUMN = "week_start"
TARGET_COLUMN = "validated_case_count"
DISEASE_COLUMN = "disease_label"

SEASONAL_PERIOD = 52
SEASONAL_SIGNAL_THRESHOLD = 0.20

TEST_WEEKS = 39
VALIDATION_WEEKS = 39

ARIMA_CANDIDATES = (
    (1, 0, 0),
    (1, 0, 1),
    (1, 1, 0),
    (0, 1, 1),
    (1, 1, 1),
)

SARIMA_CANDIDATES = (
    (
        (1, 0, 0),
        (1, 0, 0, SEASONAL_PERIOD),
    ),
    (
        (1, 0, 1),
        (1, 0, 0, SEASONAL_PERIOD),
    ),
)


@dataclass(frozen=True)
class ForecastSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def load_validated_disease_timeseries() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "Validated disease time-series dataset "
            f"not found: {DATASET_PATH}"
        )

    frame = pd.read_csv(
        DATASET_PATH,
        parse_dates=[DATE_COLUMN],
    )

    validate_disease_timeseries(
        frame
    )

    return frame.sort_values(
        [
            DISEASE_COLUMN,
            DATE_COLUMN,
        ]
    ).reset_index(drop=True)


def validate_disease_timeseries(
    frame: pd.DataFrame,
) -> None:
    required = {
        DATE_COLUMN,
        DISEASE_COLUMN,
        TARGET_COLUMN,
    }

    missing = sorted(
        required
        - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Disease forecasting dataset "
            "is missing required column(s): "
            + ", ".join(missing)
        )

    if frame.empty:
        raise ValueError(
            "Disease forecasting dataset is empty."
        )

    if frame[
        [
            DATE_COLUMN,
            DISEASE_COLUMN,
            TARGET_COLUMN,
        ]
    ].isna().any().any():
        raise ValueError(
            "Disease forecasting dataset "
            "contains missing required values."
        )

    unknown_diseases = sorted(
        set(
            frame[
                DISEASE_COLUMN
            ].astype(str)
        )
        - set(DISEASE_CLASSES)
    )

    if unknown_diseases:
        raise ValueError(
            "Unexpected disease label(s): "
            + ", ".join(
                unknown_diseases
            )
        )

    if (
        frame[
            TARGET_COLUMN
        ] < 0
    ).any():
        raise ValueError(
            "validated_case_count "
            "cannot contain negative values."
        )

    if frame.duplicated(
        subset=[
            DATE_COLUMN,
            DISEASE_COLUMN,
        ]
    ).any():
        raise ValueError(
            "Duplicate disease/week rows "
            "were found."
        )

    for disease in DISEASE_CLASSES:
        disease_frame = (
            frame[
                frame[
                    DISEASE_COLUMN
                ]
                == disease
            ]
            .sort_values(
                DATE_COLUMN
            )
            .reset_index(
                drop=True
            )
        )

        if disease_frame.empty:
            raise ValueError(
                f"No rows found for {disease}."
            )

        if len(
            disease_frame
        ) < (
            TEST_WEEKS
            + VALIDATION_WEEKS
            + (
                SEASONAL_PERIOD
                * 3
            )
        ):
            raise ValueError(
                f"{disease} does not have "
                "enough weekly history for "
                "the configured forecasting "
                "workflow."
            )

        date_differences = (
            disease_frame[
                DATE_COLUMN
            ]
            .diff()
            .dropna()
            .dt.days
        )

        if not (
            date_differences
            == 7
        ).all():
            raise ValueError(
                f"{disease} weekly dates "
                "are not continuous."
            )


def get_disease_frame(
    frame: pd.DataFrame,
    disease: str,
) -> pd.DataFrame:
    return (
        frame[
            frame[
                DISEASE_COLUMN
            ]
            == disease
        ]
        .sort_values(
            DATE_COLUMN
        )
        .reset_index(
            drop=True
        )
    )


def split_disease_frame(
    disease_frame: pd.DataFrame,
) -> ForecastSplit:
    total_rows = len(
        disease_frame
    )

    train_end = (
        total_rows
        - VALIDATION_WEEKS
        - TEST_WEEKS
    )

    validation_end = (
        total_rows
        - TEST_WEEKS
    )

    if train_end <= 0:
        raise ValueError(
            "Insufficient history for "
            "chronological train/validation/test split."
        )

    return ForecastSplit(
        train=(
            disease_frame
            .iloc[
                :train_end
            ]
            .copy()
        ),
        validation=(
            disease_frame
            .iloc[
                train_end:
                validation_end
            ]
            .copy()
        ),
        test=(
            disease_frame
            .iloc[
                validation_end:
            ]
            .copy()
        ),
    )


def to_series(
    frame: pd.DataFrame,
) -> pd.Series:
    return (
        frame[
            TARGET_COLUMN
        ]
        .astype(float)
        .reset_index(
            drop=True
        )
    )


def seasonal_signal(
    series: pd.Series,
) -> dict[str, Any]:
    correlation = (
        series.autocorr(
            lag=SEASONAL_PERIOD
        )
    )

    if (
        correlation is None
        or not np.isfinite(
            correlation
        )
    ):
        correlation_value = None
        supported = False

    else:
        correlation_value = float(
            correlation
        )

        supported = (
            len(series)
            >= (
                SEASONAL_PERIOD
                * 3
            )
            and abs(
                correlation_value
            )
            >= (
                SEASONAL_SIGNAL_THRESHOLD
            )
        )

    return {
        "method":
            (
                "Lag-52 autocorrelation "
                "screening on training data"
            ),

        "seasonal_period_weeks":
            SEASONAL_PERIOD,

        "threshold_absolute_correlation":
            SEASONAL_SIGNAL_THRESHOLD,

        "lag_52_autocorrelation":
            (
                round(
                    correlation_value,
                    6,
                )
                if correlation_value
                is not None
                else None
            ),

        "sarima_candidate_evaluation_enabled":
            supported,
    }


def forecast_metrics(
    actual,
    predicted,
) -> dict[str, Any]:
    actual_array = np.asarray(
        actual,
        dtype=float,
    )

    predicted_array = np.asarray(
        predicted,
        dtype=float,
    )

    predicted_array = np.clip(
        predicted_array,
        0.0,
        None,
    )

    errors = (
        actual_array
        - predicted_array
    )

    mae = float(
        np.mean(
            np.abs(
                errors
            )
        )
    )

    rmse = float(
        math.sqrt(
            np.mean(
                errors ** 2
            )
        )
    )

    nonzero_mask = (
        actual_array
        != 0
    )

    if nonzero_mask.any():
        mape = float(
            np.mean(
                np.abs(
                    errors[
                        nonzero_mask
                    ]
                    / actual_array[
                        nonzero_mask
                    ]
                )
            )
            * 100.0
        )

        mape_coverage = int(
            nonzero_mask.sum()
        )

    else:
        mape = None
        mape_coverage = 0

    return {
        "mae":
            round(
                mae,
                6,
            ),

        "rmse":
            round(
                rmse,
                6,
            ),

        "mape_nonzero_pct":
            (
                round(
                    mape,
                    6,
                )
                if mape is not None
                else None
            ),

        "mape_nonzero_rows":
            mape_coverage,

        "total_rows":
            int(
                len(
                    actual_array
                )
            ),

        "mape_note":
            (
                "MAPE excludes rows where "
                "the actual case count is zero."
            ),
    }


def fit_model(
    series: pd.Series,
    *,
    model_family: str,
    order: tuple[int, int, int],
    seasonal_order: (
        tuple[
            int,
            int,
            int,
            int,
        ]
        | None
    ) = None,
):
    model_family = (
        model_family
        .strip()
        .upper()
    )

    with warnings.catch_warnings():
        warnings.simplefilter(
            "ignore"
        )

        if model_family == "ARIMA":
            trend = (
                "ct"
                if order[1] == 0
                else "t"
            )

            return ARIMA(
                series,
                order=order,
                trend=trend,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit()

        if model_family == "SARIMA":
            if seasonal_order is None:
                raise ValueError(
                    "SARIMA requires "
                    "seasonal_order."
                )

            trend = (
                "c"
                if order[1] == 0
                else "t"
            )

            return SARIMAX(
                series,
                order=order,
                seasonal_order=(
                    seasonal_order
                ),
                trend=trend,
                enforce_stationarity=False,
                enforce_invertibility=False,
                simple_differencing=False,
            ).fit(
                disp=False,
                maxiter=100,
            )

    raise ValueError(
        "Unsupported forecasting "
        f"model family: {model_family}"
    )


def forecast_from_result(
    fitted_result,
    steps: int,
) -> np.ndarray:
    forecast = (
        fitted_result
        .get_forecast(
            steps=steps
        )
        .predicted_mean
    )

    return np.clip(
        np.asarray(
            forecast,
            dtype=float,
        ),
        0.0,
        None,
    )


def forecast_with_interval(
    fitted_result,
    steps: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    result = (
        fitted_result
        .get_forecast(
            steps=steps
        )
    )

    mean = np.clip(
        np.asarray(
            result.predicted_mean,
            dtype=float,
        ),
        0.0,
        None,
    )

    interval = result.conf_int(
        alpha=0.05
    )

    if hasattr(
        interval,
        "iloc",
    ):
        lower = (
            interval
            .iloc[
                :,
                0
            ]
            .to_numpy(
                dtype=float
            )
        )

        upper = (
            interval
            .iloc[
                :,
                1
            ]
            .to_numpy(
                dtype=float
            )
        )

    else:
        interval_array = np.asarray(
            interval,
            dtype=float,
        )

        lower = (
            interval_array[
                :,
                0
            ]
        )

        upper = (
            interval_array[
                :,
                1
            ]
        )

    lower = np.clip(
        lower,
        0.0,
        None,
    )

    upper = np.clip(
        upper,
        0.0,
        None,
    )

    return (
        mean,
        lower,
        upper,
    )


def candidate_key(
    candidate_result: dict[str, Any],
):
    metrics = (
        candidate_result[
            "validation_metrics"
        ]
    )

    mape = (
        metrics[
            "mape_nonzero_pct"
        ]
    )

    return (
        metrics[
            "rmse"
        ],
        metrics[
            "mae"
        ],
        (
            mape
            if mape is not None
            else float("inf")
        ),
    )


def serialize_order(
    order,
) -> list[int]:
    return [
        int(value)
        for value in order
    ]


def deserialize_order(
    order,
) -> tuple[int, ...]:
    return tuple(
        int(value)
        for value in order
    )


def safe_filename(
    disease: str,
) -> str:
    return (
        disease
        .strip()
        .lower()
        .replace(
            "/",
            "_",
        )
        .replace(
            " ",
            "_",
        )
    )
