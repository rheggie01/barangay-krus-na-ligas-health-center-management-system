from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.ml.config import VALIDATED_DIR


DATASET_PATH = (
    VALIDATED_DIR
    / "medicine_consumption_2021_2025.csv"
)

DATE_COLUMN = "month_start"
CODE_COLUMN = "medicine_code"
NAME_COLUMN = "medicine_name"
TARGET_COLUMN = "quantity_dispensed"

SEASONAL_PERIOD = 12
SEASONAL_SIGNAL_THRESHOLD = 0.20

VALIDATION_MONTHS = 9
TEST_MONTHS = 9

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


def load_validated_medicine_timeseries() -> pd.DataFrame:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "Validated medicine-consumption dataset "
            f"not found: {DATASET_PATH}"
        )

    frame = pd.read_csv(
        DATASET_PATH,
        parse_dates=[DATE_COLUMN],
    )

    validate_medicine_timeseries(
        frame
    )

    return (
        frame
        .sort_values(
            [
                CODE_COLUMN,
                DATE_COLUMN,
            ]
        )
        .reset_index(
            drop=True
        )
    )


def validate_medicine_timeseries(
    frame: pd.DataFrame,
) -> None:
    required = {
        DATE_COLUMN,
        CODE_COLUMN,
        NAME_COLUMN,
        TARGET_COLUMN,
    }

    missing = sorted(
        required
        - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Medicine forecasting dataset "
            "is missing required column(s): "
            + ", ".join(missing)
        )

    if frame.empty:
        raise ValueError(
            "Medicine forecasting dataset is empty."
        )

    if frame[
        [
            DATE_COLUMN,
            CODE_COLUMN,
            NAME_COLUMN,
            TARGET_COLUMN,
        ]
    ].isna().any().any():
        raise ValueError(
            "Medicine forecasting dataset "
            "contains missing required values."
        )

    if (
        frame[
            TARGET_COLUMN
        ] < 0
    ).any():
        raise ValueError(
            "quantity_dispensed cannot be negative."
        )

    if frame.duplicated(
        subset=[
            DATE_COLUMN,
            CODE_COLUMN,
        ]
    ).any():
        raise ValueError(
            "Duplicate medicine/month rows were found."
        )

    for medicine_code in sorted(
        frame[
            CODE_COLUMN
        ].unique()
    ):
        medicine_frame = (
            frame[
                frame[
                    CODE_COLUMN
                ]
                == medicine_code
            ]
            .sort_values(
                DATE_COLUMN
            )
            .reset_index(
                drop=True
            )
        )

        if len(
            medicine_frame
        ) < (
            VALIDATION_MONTHS
            + TEST_MONTHS
            + (
                SEASONAL_PERIOD
                * 3
            )
        ):
            raise ValueError(
                f"{medicine_code} does not have "
                "enough monthly history for "
                "the configured forecasting workflow."
            )

        expected_dates = pd.date_range(
            start=(
                medicine_frame[
                    DATE_COLUMN
                ]
                .iloc[0]
            ),
            periods=len(
                medicine_frame
            ),
            freq="MS",
        )

        if not (
            medicine_frame[
                DATE_COLUMN
            ]
            .reset_index(
                drop=True
            )
            == expected_dates
        ).all():
            raise ValueError(
                f"{medicine_code} monthly dates "
                "are not continuous month-start values."
            )


def get_medicine_codes(
    frame: pd.DataFrame,
) -> list[str]:
    return sorted(
        str(value)
        for value in frame[
            CODE_COLUMN
        ].unique()
    )


def get_medicine_frame(
    frame: pd.DataFrame,
    medicine_code: str,
) -> pd.DataFrame:
    return (
        frame[
            frame[
                CODE_COLUMN
            ]
            == medicine_code
        ]
        .sort_values(
            DATE_COLUMN
        )
        .reset_index(
            drop=True
        )
    )


def split_medicine_frame(
    medicine_frame: pd.DataFrame,
) -> ForecastSplit:
    total_rows = len(
        medicine_frame
    )

    train_end = (
        total_rows
        - VALIDATION_MONTHS
        - TEST_MONTHS
    )

    validation_end = (
        total_rows
        - TEST_MONTHS
    )

    if train_end <= 0:
        raise ValueError(
            "Insufficient medicine history for "
            "chronological split."
        )

    return ForecastSplit(
        train=(
            medicine_frame
            .iloc[
                :train_end
            ]
            .copy()
        ),
        validation=(
            medicine_frame
            .iloc[
                train_end:
                validation_end
            ]
            .copy()
        ),
        test=(
            medicine_frame
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
        value = None
        supported = False

    else:
        value = float(
            correlation
        )

        supported = (
            len(series)
            >= (
                SEASONAL_PERIOD
                * 3
            )
            and abs(
                value
            )
            >= (
                SEASONAL_SIGNAL_THRESHOLD
            )
        )

    return {
        "method":
            (
                "Lag-12 autocorrelation "
                "screening on training data"
            ),

        "seasonal_period_months":
            SEASONAL_PERIOD,

        "threshold_absolute_correlation":
            SEASONAL_SIGNAL_THRESHOLD,

        "lag_12_autocorrelation":
            (
                round(
                    value,
                    6,
                )
                if value is not None
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

    predicted_array = np.clip(
        np.asarray(
            predicted,
            dtype=float,
        ),
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

        coverage = int(
            nonzero_mask.sum()
        )

    else:
        mape = None
        coverage = 0

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
            coverage,

        "total_rows":
            int(
                len(
                    actual_array
                )
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

        if family == "SARIMA":
            if seasonal_order is None:
                raise ValueError(
                    "SARIMA requires seasonal_order."
                )

            trend = (
                "c"
                if order[1] == 0
                else "t"
            )

            return SARIMAX(
                series,
                order=order,
                seasonal_order=seasonal_order,
                trend=trend,
                enforce_stationarity=False,
                enforce_invertibility=False,
                simple_differencing=False,
            ).fit(
                disp=False,
                maxiter=100,
            )

    raise ValueError(
        f"Unsupported forecasting model family: {model_family}"
    )


def forecast_from_result(
    fitted_result,
    steps: int,
) -> np.ndarray:
    values = (
        fitted_result
        .get_forecast(
            steps=steps
        )
        .predicted_mean
    )

    return np.clip(
        np.asarray(
            values,
            dtype=float,
        ),
        0.0,
        None,
    )


def forecast_with_interval(
    fitted_result,
    steps: int,
):
    result = fitted_result.get_forecast(
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
        values = np.asarray(
            interval,
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


def candidate_key(
    candidate_result: dict[str, Any],
):
    metrics = candidate_result[
        "validation_metrics"
    ]

    mape = metrics[
        "mape_nonzero_pct"
    ]

    return (
        metrics["rmse"],
        metrics["mae"],
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
    value: str,
) -> str:
    return (
        value
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
        .replace(
            "-",
            "_",
        )
    )
