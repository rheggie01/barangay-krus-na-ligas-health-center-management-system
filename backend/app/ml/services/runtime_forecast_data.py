from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.consultation import Consultation
from app.models.consultation_medicine import (
    ConsultationMedicine,
)
from app.models.disease import Disease
from app.models.disease_case import DiseaseCase
from app.models.medicine import Medicine


LOCAL_TIMEZONE = ZoneInfo(
    "Asia/Manila"
)


# =========================================================
# CURRENT PERIOD HELPERS
# =========================================================

def local_today() -> date:
    return datetime.now(
        LOCAL_TIMEZONE
    ).date()


def monday_of_week(
    value: date,
) -> date:
    return (
        value
        - timedelta(
            days=value.weekday()
        )
    )


def latest_completed_week_start() -> date:
    """
    Disease forecasting uses Monday-Sunday weeks.

    The currently open week is not treated as complete.
    """
    current_week_start = monday_of_week(
        local_today()
    )

    return (
        current_week_start
        - timedelta(
            days=7
        )
    )


def current_week_start() -> date:
    return monday_of_week(
        local_today()
    )


def month_start(
    value: date,
) -> date:
    return date(
        value.year,
        value.month,
        1,
    )


def latest_completed_month_start() -> date:
    current = month_start(
        local_today()
    )

    return (
        pd.Timestamp(
            current
        )
        - pd.offsets.MonthBegin(
            1
        )
    ).date()


def actual_next_month_start() -> date:
    current = month_start(
        local_today()
    )

    return (
        pd.Timestamp(
            current
        )
        + pd.offsets.MonthBegin(
            1
        )
    ).date()


# =========================================================
# DATABASE COVERAGE
# =========================================================

def get_consultation_coverage_start(
    db: Session,
) -> date | None:
    value = db.scalar(
        select(
            func.min(
                Consultation.consultation_date
            )
        )
    )

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    return pd.Timestamp(
        value
    ).date()


def get_dispensing_coverage_start(
    db: Session,
) -> date | None:
    value = db.scalar(
        select(
            func.min(
                ConsultationMedicine.dispensed_at
            )
        )
    )

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    return pd.Timestamp(
        value
    ).date()


# =========================================================
# DISEASE LIVE SERIES
# =========================================================

def get_validated_disease_week_counts(
    db: Session,
    *,
    disease_code: str,
    start_week: date,
    end_week: date,
) -> dict[date, int]:
    """
    Aggregate only doctor/authorized validated disease cases.

    Weeks are Monday-Sunday.
    """
    end_date = (
        end_week
        + timedelta(
            days=6
        )
    )

    statement = (
        select(
            DiseaseCase.case_date
        )
        .join(
            Disease,
            Disease.id
            == DiseaseCase.disease_id,
        )
        .where(
            Disease.code
            == disease_code,
            DiseaseCase.validation_status
            == "VALIDATED",
            DiseaseCase.case_date
            >= start_week,
            DiseaseCase.case_date
            <= end_date,
        )
    )

    rows = db.scalars(
        statement
    ).all()

    counts: dict[date, int] = {}

    for case_date in rows:
        week = monday_of_week(
            case_date
        )

        counts[week] = (
            counts.get(
                week,
                0,
            )
            + 1
        )

    return counts


def build_dynamic_disease_series(
    db: Session,
    *,
    baseline_frame: pd.DataFrame,
    disease_code: str,
) -> tuple[pd.Series, dict[str, Any]]:
    disease_baseline = (
        baseline_frame[
            baseline_frame[
                "disease_label"
            ]
            == disease_code
        ]
        .sort_values(
            "week_start"
        )
        .copy()
    )

    if disease_baseline.empty:
        raise ValueError(
            "No baseline disease history "
            f"for {disease_code}."
        )

    disease_baseline[
        "week_start"
    ] = pd.to_datetime(
        disease_baseline[
            "week_start"
        ]
    )

    baseline_series = pd.Series(
        data=(
            disease_baseline[
                "validated_case_count"
            ]
            .astype(float)
            .to_numpy()
        ),
        index=(
            disease_baseline[
                "week_start"
            ]
        ),
        dtype=float,
    )

    baseline_series.index = pd.DatetimeIndex(
        baseline_series.index
    )

    baseline_end = (
        baseline_series.index[-1]
        .date()
    )

    completed_week = (
        latest_completed_week_start()
    )

    next_baseline_week = (
        baseline_end
        + timedelta(
            days=7
        )
    )

    coverage_date = (
        get_consultation_coverage_start(
            db
        )
    )

    if completed_week < next_baseline_week:
        metadata = {
            "data_mode":
                "BASELINE_ONLY",

            "baseline_end":
                baseline_end.isoformat(),

            "system_coverage_start":
                (
                    coverage_date.isoformat()
                    if coverage_date
                    else None
                ),

            "latest_completed_period":
                completed_week.isoformat(),

            "latest_live_covered_period":
                None,

            "live_periods_used":
                0,

            "missing_bridge_periods":
                0,

            "freshness_status":
                "BASELINE_CURRENT",

            "automatic_refresh":
                True,
        }

        return (
            baseline_series.asfreq(
                "W-MON"
            ),
            metadata,
        )

    extension_index = pd.date_range(
        start=next_baseline_week,
        end=completed_week,
        freq="W-MON",
    )

    extension = pd.Series(
        np.nan,
        index=extension_index,
        dtype=float,
    )

    live_periods_used = 0
    missing_bridge_periods = len(
        extension
    )
    latest_live_covered = None

    if coverage_date is not None:
        coverage_week = max(
            monday_of_week(
                coverage_date
            ),
            next_baseline_week,
        )

        if coverage_week <= completed_week:
            covered_index = pd.date_range(
                start=coverage_week,
                end=completed_week,
                freq="W-MON",
            )

            # Once the consultation module is operating,
            # no validated case for a disease in a completed
            # week means an observed zero for that disease.
            extension.loc[
                covered_index
            ] = 0.0

            live_counts = (
                get_validated_disease_week_counts(
                    db,
                    disease_code=disease_code,
                    start_week=coverage_week,
                    end_week=completed_week,
                )
            )

            for (
                week,
                count,
            ) in live_counts.items():
                timestamp = pd.Timestamp(
                    week
                )

                if timestamp in extension.index:
                    extension.loc[
                        timestamp
                    ] = float(
                        count
                    )

            live_periods_used = len(
                covered_index
            )

            missing_bridge_periods = int(
                extension.isna().sum()
            )

            latest_live_covered = (
                completed_week
            )

    combined = pd.concat(
        [
            baseline_series,
            extension,
        ]
    ).asfreq(
        "W-MON"
    )

    if live_periods_used > 0:
        data_mode = (
            "BASELINE_PLUS_LIVE_DATABASE"
        )

        freshness_status = (
            "LIVE_CURRENT"
        )

    elif coverage_date is None:
        data_mode = (
            "BASELINE_ONLY"
        )

        freshness_status = (
            "NO_SYSTEM_ACTIVITY"
        )

    else:
        data_mode = (
            "BASELINE_WITH_MISSING_BRIDGE"
        )

        freshness_status = (
            "NO_COMPLETED_LIVE_DATA"
        )

    metadata = {
        "data_mode":
            data_mode,

        "baseline_end":
            baseline_end.isoformat(),

        "system_coverage_start":
            (
                coverage_date.isoformat()
                if coverage_date
                else None
            ),

        "latest_completed_period":
            completed_week.isoformat(),

        "latest_live_covered_period":
            (
                latest_live_covered.isoformat()
                if latest_live_covered
                else None
            ),

        "live_periods_used":
            live_periods_used,

        "missing_bridge_periods":
            missing_bridge_periods,

        "freshness_status":
            freshness_status,

        "automatic_refresh":
            True,
    }

    return (
        combined,
        metadata,
    )


# =========================================================
# MEDICINE INVENTORY MATCHING
# =========================================================

def normalize_medicine_text(
    value: Any,
) -> str:
    if value is None:
        return ""

    import re

    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(
            value
        ).lower(),
    )


def strict_formulation_keys(
    medicine: Medicine,
) -> set[str]:
    """
    Intentionally excludes generic_name by itself.

    Example:
    "Paracetamol Combination" must not be silently
    treated as "Paracetamol 500 mg Tablet".
    """
    name = medicine.name
    strength = medicine.dosage_strength
    dosage_form = medicine.dosage_form

    raw_values = [
        name,
        " ".join(
            str(value)
            for value in [
                name,
                strength,
            ]
            if value
        ),
        " ".join(
            str(value)
            for value in [
                name,
                strength,
                dosage_form,
            ]
            if value
        ),
        " ".join(
            str(value)
            for value in [
                name,
                dosage_form,
            ]
            if value
        ),
    ]

    return {
        normalized
        for normalized in (
            normalize_medicine_text(
                value
            )
            for value in raw_values
        )
        if normalized
    }


def match_baseline_medicine_to_inventory(
    db: Session,
    *,
    baseline_code: str,
    baseline_name: str,
) -> tuple[
    Medicine | None,
    str,
    str,
]:
    active_medicines = list(
        db.scalars(
            select(
                Medicine
            )
            .where(
                Medicine.is_active.is_(
                    True
                ),
                Medicine.stock_verified.is_(
                    True
                ),
                Medicine.forecast_enabled.is_(
                    True
                ),
                Medicine.sensitive_inventory.is_(
                    False
                ),
            )
            .order_by(
                Medicine.id.asc()
            )
        ).all()
    )

    normalized_code = (
        baseline_code
        .strip()
        .upper()
    )

    code_matches = [
        medicine
        for medicine
        in active_medicines
        if medicine.code
        .strip()
        .upper()
        == normalized_code
    ]

    if len(
        code_matches
    ) == 1:
        return (
            code_matches[0],
            "EXACT_CODE",
            "Matched by exact active inventory code.",
        )

    if len(
        code_matches
    ) > 1:
        return (
            None,
            "AMBIGUOUS_CODE",
            "Multiple active medicines matched the code.",
        )

    normalized_name = (
        normalize_medicine_text(
            baseline_name
        )
    )

    formulation_matches = [
        medicine
        for medicine
        in active_medicines
        if normalized_name
        in strict_formulation_keys(
            medicine
        )
    ]

    if len(
        formulation_matches
    ) == 1:
        return (
            formulation_matches[0],
            "EXACT_FORMULATION",
            (
                "Matched using exact normalized "
                "medicine name + formulation fields."
            ),
        )

    if len(
        formulation_matches
    ) > 1:
        return (
            None,
            "AMBIGUOUS_FORMULATION",
            (
                "Multiple active inventory formulations "
                "matched the forecast medicine."
            ),
        )

    return (
        None,
        "NO_EXACT_FORMULATION_MATCH",
        (
            "No exact active inventory formulation "
            "matched the forecast medicine."
        ),
    )


def medicine_total_units(
    medicine: Medicine,
) -> int:
    package_stock = int(
        medicine.package_stock
        or 0
    )

    loose_stock = int(
        medicine.loose_stock
        or 0
    )

    units_per_package = int(
        medicine.units_per_package
        or 0
    )

    if units_per_package > 0:
        return (
            package_stock
            * units_per_package
            + loose_stock
        )

    return (
        package_stock
        + loose_stock
    )


# =========================================================
# MEDICINE LIVE SERIES
# =========================================================

def get_medicine_month_counts(
    db: Session,
    *,
    medicine: Medicine,
    start_month: date,
    end_month: date,
) -> tuple[
    dict[date, float],
    bool,
]:
    """
    Aggregate actual ConsultationMedicine dispensing records.

    PACKAGE quantities are converted to dispensing units
    when units_per_package is configured.

    When units_per_package is not configured, the existing
    inventory model already treats one package as one stock
    unit. This function follows that existing behavior and
    returns a conversion warning flag.
    """
    end_exclusive = (
        pd.Timestamp(
            end_month
        )
        + pd.offsets.MonthBegin(
            1
        )
    ).to_pydatetime()

    statement = (
        select(
            ConsultationMedicine.quantity,
            ConsultationMedicine.stock_unit,
            ConsultationMedicine.dispensed_at,
        )
        .where(
            ConsultationMedicine.medicine_id
            == medicine.id,
            ConsultationMedicine.dispensed_at
            >= datetime.combine(
                start_month,
                datetime.min.time(),
            ),
            ConsultationMedicine.dispensed_at
            < end_exclusive,
        )
    )

    rows = db.execute(
        statement
    ).all()

    monthly: dict[
        date,
        float,
    ] = {}

    package_conversion_warning = False

    for row in rows:
        dispensed_at = (
            row.dispensed_at
        )

        period = date(
            dispensed_at.year,
            dispensed_at.month,
            1,
        )

        quantity = float(
            row.quantity
        )

        stock_unit = (
            row.stock_unit
            or "LOOSE"
        ).strip().upper()

        if stock_unit == "PACKAGE":
            units_per_package = int(
                medicine.units_per_package
                or 0
            )

            if units_per_package > 0:
                quantity = (
                    quantity
                    * units_per_package
                )
            else:
                package_conversion_warning = True

        monthly[
            period
        ] = (
            monthly.get(
                period,
                0.0,
            )
            + quantity
        )

    return (
        monthly,
        package_conversion_warning,
    )


def build_dynamic_medicine_series(
    db: Session,
    *,
    baseline_frame: pd.DataFrame,
    baseline_code: str,
    baseline_name: str,
) -> tuple[
    pd.Series,
    dict[str, Any],
    dict[str, Any],
]:
    medicine_baseline = (
        baseline_frame[
            baseline_frame[
                "medicine_code"
            ]
            == baseline_code
        ]
        .sort_values(
            "month_start"
        )
        .copy()
    )

    if medicine_baseline.empty:
        raise ValueError(
            "No baseline medicine history "
            f"for {baseline_code}."
        )

    medicine_baseline[
        "month_start"
    ] = pd.to_datetime(
        medicine_baseline[
            "month_start"
        ]
    )

    baseline_series = pd.Series(
        data=(
            medicine_baseline[
                "quantity_dispensed"
            ]
            .astype(float)
            .to_numpy()
        ),
        index=(
            medicine_baseline[
                "month_start"
            ]
        ),
        dtype=float,
    )

    baseline_series.index = pd.DatetimeIndex(
        baseline_series.index
    )

    baseline_end = (
        baseline_series.index[-1]
        .date()
    )

    completed_month = (
        latest_completed_month_start()
    )

    next_baseline_month = (
        pd.Timestamp(
            baseline_end
        )
        + pd.offsets.MonthBegin(
            1
        )
    ).date()

    (
        inventory_medicine,
        match_status,
        match_message,
    ) = (
        match_baseline_medicine_to_inventory(
            db,
            baseline_code=baseline_code,
            baseline_name=baseline_name,
        )
    )

    inventory_snapshot = {
        "matched":
            inventory_medicine
            is not None,

        "match_status":
            (
                "MATCHED"
                if inventory_medicine
                is not None
                else match_status
            ),

        "match_strategy":
            (
                match_status
                if inventory_medicine
                is not None
                else None
            ),

        "message":
            match_message,

        "medicine_id":
            (
                inventory_medicine.id
                if inventory_medicine
                else None
            ),

        "inventory_code":
            (
                inventory_medicine.code
                if inventory_medicine
                else None
            ),

        "inventory_name":
            (
                inventory_medicine.name
                if inventory_medicine
                else None
            ),

        "dispensing_unit":
            (
                inventory_medicine.dispensing_unit
                if inventory_medicine
                else None
            ),

        "package_unit":
            (
                inventory_medicine.package_unit
                if inventory_medicine
                else None
            ),

        "units_per_package":
            (
                inventory_medicine.units_per_package
                if inventory_medicine
                else None
            ),

        "package_stock":
            (
                int(
                    inventory_medicine.package_stock
                    or 0
                )
                if inventory_medicine
                else None
            ),

        "loose_stock":
            (
                int(
                    inventory_medicine.loose_stock
                    or 0
                )
                if inventory_medicine
                else None
            ),

        "usable_current_stock":
            (
                medicine_total_units(
                    inventory_medicine
                )
                if inventory_medicine
                else None
            ),

        "reorder_level":
            (
                int(
                    inventory_medicine.reorder_level
                    or 0
                )
                if inventory_medicine
                else None
            ),
    }

    if completed_month < next_baseline_month:
        metadata = {
            "data_mode":
                "BASELINE_ONLY",

            "baseline_end":
                baseline_end.isoformat(),

            "system_coverage_start":
                None,

            "latest_completed_period":
                completed_month.isoformat(),

            "latest_live_covered_period":
                None,

            "live_periods_used":
                0,

            "missing_bridge_periods":
                0,

            "freshness_status":
                "BASELINE_CURRENT",

            "automatic_refresh":
                True,

            "package_conversion_warning":
                False,
        }

        return (
            baseline_series.asfreq(
                "MS"
            ),
            metadata,
            inventory_snapshot,
        )

    extension_index = pd.date_range(
        start=next_baseline_month,
        end=completed_month,
        freq="MS",
    )

    extension = pd.Series(
        np.nan,
        index=extension_index,
        dtype=float,
    )

    coverage_date = (
        get_dispensing_coverage_start(
            db
        )
    )

    live_periods_used = 0
    missing_bridge_periods = len(
        extension
    )
    latest_live_covered = None
    package_conversion_warning = False

    if (
        inventory_medicine
        is not None
        and coverage_date
        is not None
    ):
        coverage_month = max(
            month_start(
                coverage_date
            ),
            next_baseline_month,
        )

        if coverage_month <= completed_month:
            covered_index = pd.date_range(
                start=coverage_month,
                end=completed_month,
                freq="MS",
            )

            # From the first month the dispensing module is
            # operating, absence of this medicine in a completed
            # month is treated as observed zero demand.
            extension.loc[
                covered_index
            ] = 0.0

            (
                monthly_counts,
                package_conversion_warning,
            ) = get_medicine_month_counts(
                db,
                medicine=inventory_medicine,
                start_month=coverage_month,
                end_month=completed_month,
            )

            for (
                period,
                quantity,
            ) in monthly_counts.items():
                timestamp = pd.Timestamp(
                    period
                )

                if timestamp in extension.index:
                    extension.loc[
                        timestamp
                    ] = float(
                        quantity
                    )

            live_periods_used = len(
                covered_index
            )

            missing_bridge_periods = int(
                extension.isna().sum()
            )

            latest_live_covered = (
                completed_month
            )

    combined = pd.concat(
        [
            baseline_series,
            extension,
        ]
    ).asfreq(
        "MS"
    )

    if live_periods_used > 0:
        data_mode = (
            "BASELINE_PLUS_LIVE_DATABASE"
        )

        freshness_status = (
            "LIVE_CURRENT"
        )

    elif inventory_medicine is None:
        data_mode = (
            "BASELINE_ONLY_UNMAPPED"
        )

        freshness_status = (
            "NO_SAFE_INVENTORY_MATCH"
        )

    elif coverage_date is None:
        data_mode = (
            "BASELINE_ONLY"
        )

        freshness_status = (
            "NO_SYSTEM_ACTIVITY"
        )

    else:
        data_mode = (
            "BASELINE_WITH_MISSING_BRIDGE"
        )

        freshness_status = (
            "NO_COMPLETED_LIVE_DATA"
        )

    metadata = {
        "data_mode":
            data_mode,

        "baseline_end":
            baseline_end.isoformat(),

        "system_coverage_start":
            (
                coverage_date.isoformat()
                if coverage_date
                else None
            ),

        "latest_completed_period":
            completed_month.isoformat(),

        "latest_live_covered_period":
            (
                latest_live_covered.isoformat()
                if latest_live_covered
                else None
            ),

        "live_periods_used":
            live_periods_used,

        "missing_bridge_periods":
            missing_bridge_periods,

        "freshness_status":
            freshness_status,

        "automatic_refresh":
            True,

        "package_conversion_warning":
            package_conversion_warning,
    }

    return (
        combined,
        metadata,
        inventory_snapshot,
    )
