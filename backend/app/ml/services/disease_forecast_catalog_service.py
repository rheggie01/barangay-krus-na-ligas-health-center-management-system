from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.ml.services.forecast_service import (
    list_disease_forecasts,
)
from app.models.disease import Disease


# =========================================================
# CURRENT VALIDATED FORECAST MODEL ALIASES
# =========================================================
#
# The forecasting engine currently has validated development
# model specifications for four disease classes.
#
# The disease catalog itself is dynamic and comes from the
# database. Diseases without a validated model remain visible
# with MODEL_PENDING status instead of being silently hidden.
# =========================================================

FORECAST_MODEL_ALIASES = [
    {
        "forecast_code": "DENGUE",
        "codes": {
            "DENGUE",
            "DENG",
        },
        "names": {
            "dengue",
        },
    },
    {
        "forecast_code": "ARI",
        "codes": {
            "ARI",
        },
        "names": {
            "acute respiratory infection",
            "acute respiratory infection (ari)",
        },
    },
    {
        "forecast_code": "ILI",
        "codes": {
            "ILI",
        },
        "names": {
            "influenza-like illness",
            "influenza-like illness (ili)",
        },
    },
    {
        "forecast_code": "DIARRHEA_GASTROENTERITIS",
        "codes": {
            "DIARRHEA_GASTROENTERITIS",
            "GE",
        },
        "names": {
            "diarrhea / gastroenteritis",
            "diarrhea/gastroenteritis",
            "gastroenteritis",
        },
    },
]


def _normalize_code(
    value: str | None,
) -> str:
    return (
        str(
            value
            or ""
        )
        .strip()
        .upper()
    )


def _normalize_name(
    value: str | None,
) -> str:
    return (
        str(
            value
            or ""
        )
        .strip()
        .lower()
    )


def get_forecast_code_for_disease(
    disease: Disease,
) -> str | None:
    code = _normalize_code(
        disease.code
    )

    name = _normalize_name(
        disease.name
    )

    for alias in FORECAST_MODEL_ALIASES:
        alias_codes = {
            _normalize_code(
                value
            )
            for value
            in alias[
                "codes"
            ]
        }

        alias_names = {
            _normalize_name(
                value
            )
            for value
            in alias[
                "names"
            ]
        }

        if (
            code in alias_codes
            or name in alias_names
        ):
            return alias[
                "forecast_code"
            ]

    return None


def get_disease_for_forecast_code(
    db: Session,
    forecast_code: str,
) -> Disease | None:
    normalized = _normalize_code(
        forecast_code
    )

    alias = next(
        (
            item
            for item
            in FORECAST_MODEL_ALIASES
            if item[
                "forecast_code"
            ] == normalized
        ),
        None,
    )

    if alias is None:
        return None

    code_values = list(
        alias[
            "codes"
        ]
    )

    name_values = [
        value.lower()
        for value
        in alias[
            "names"
        ]
    ]

    return db.scalar(
        select(
            Disease
        )
        .where(
            Disease.is_active.is_(
                True
            ),
            or_(
                func.upper(
                    func.trim(
                        Disease.code
                    )
                ).in_(
                    [
                        value.upper()
                        for value
                        in code_values
                    ]
                ),
                func.lower(
                    func.trim(
                        Disease.name
                    )
                ).in_(
                    name_values
                ),
            ),
        )
        .order_by(
            Disease.id.asc()
        )
        .limit(
            1
        )
    )


def list_disease_forecast_catalog(
    db: Session,
    *,
    include_sensitive: bool,
) -> list[dict]:
    """
    Return ALL active Disease Master rows visible to the
    current permission scope.

    Forecast-capable diseases are linked to the existing
    validated ARIMA/SARIMA model summaries.

    Other diseases/conditions are still returned with
    MODEL_PENDING status.
    """
    active_diseases = list(
        db.scalars(
            select(
                Disease
            )
            .where(
                Disease.is_active.is_(
                    True
                )
            )
            .order_by(
                Disease.name.asc()
            )
        ).all()
    )

    model_summaries = {
        item[
            "disease_code"
        ]:
            item
        for item
        in list_disease_forecasts(
            db
        )
    }

    rows = []

    for disease in active_diseases:
        if (
            disease.is_sensitive
            and not include_sensitive
        ):
            continue

        forecast_code = (
            get_forecast_code_for_disease(
                disease
            )
        )

        summary = (
            model_summaries.get(
                forecast_code
            )
            if forecast_code
            else None
        )

        forecast_available = (
            summary is not None
        )

        rows.append(
            {
                "disease_id":
                    disease.id,

                "disease_code":
                    disease.code,

                "disease_name":
                    disease.name,

                "category":
                    disease.category,

                "transmission_type":
                    disease.transmission_type,

                "is_communicable":
                    bool(
                        disease.is_communicable
                    ),

                "is_reportable":
                    bool(
                        disease.is_reportable
                    ),

                "is_sensitive":
                    bool(
                        disease.is_sensitive
                    ),

                "privacy_category":
                    disease.privacy_category,

                "forecast_code":
                    (
                        forecast_code
                        if forecast_available
                        else None
                    ),

                "forecast_status":
                    (
                        "AVAILABLE"
                        if forecast_available
                        else "MODEL_PENDING"
                    ),

                "model_family":
                    (
                        summary[
                            "model_family"
                        ]
                        if summary
                        else None
                    ),

                "rmse":
                    (
                        summary[
                            "rmse"
                        ]
                        if summary
                        else None
                    ),

                "mae":
                    (
                        summary[
                            "mae"
                        ]
                        if summary
                        else None
                    ),

                "mape_nonzero_pct":
                    (
                        summary[
                            "mape_nonzero_pct"
                        ]
                        if summary
                        else None
                    ),

                "status_message":
                    (
                        "Validated development time-series "
                        "model is available for runtime "
                        "forecasting."
                        if forecast_available
                        else (
                            "This disease/condition is active "
                            "in the Disease Master, but no "
                            "validated time-series forecasting "
                            "configuration has been established "
                            "yet."
                        )
                    ),
            }
        )

    return rows
