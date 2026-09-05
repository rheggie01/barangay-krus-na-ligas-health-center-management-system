from datetime import (
    date,
    timedelta,
)

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from app.models.disease import Disease
from app.models.disease_case import DiseaseCase
from app.models.patient import Patient


# =========================================================
# DISEASE CASE COUNTS
# =========================================================

def get_disease_case_counts(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    include_sensitive: bool = False,
    sensitive_only: bool = False,
):
    """
    Return validated disease case counts.

    Only cases with validation_status = VALIDATED
    are included in surveillance statistics.
    """

    statement = (
        select(
            Disease.id.label(
                "disease_id"
            ),
            Disease.code.label(
                "code"
            ),
            Disease.name.label(
                "name"
            ),
            func.count(
                DiseaseCase.id
            ).label(
                "case_count"
            ),
        )
        .outerjoin(
            DiseaseCase,
            (
                DiseaseCase.disease_id
                == Disease.id
            )
            & (
                DiseaseCase.validation_status
                == "VALIDATED"
            ),
        )
        .where(
            Disease.is_active.is_(
                True
            )
        )
    )


    # -----------------------------------------------------
    # DATE FILTERS
    # -----------------------------------------------------

    if start_date is not None:
        statement = (
            statement.where(
                (
                    DiseaseCase.case_date
                    >= start_date
                )
                |
                (
                    DiseaseCase.id
                    .is_(None)
                )
            )
        )


    if end_date is not None:
        statement = (
            statement.where(
                (
                    DiseaseCase.case_date
                    <= end_date
                )
                |
                (
                    DiseaseCase.id
                    .is_(None)
                )
            )
        )


    # -----------------------------------------------------
    # SENSITIVE DISEASE FILTER
    # -----------------------------------------------------

    if sensitive_only:
        statement = (
            statement.where(
                Disease.is_sensitive.is_(
                    True
                )
            )
        )

    elif not include_sensitive:
        statement = (
            statement.where(
                Disease.is_sensitive.is_(
                    False
                )
            )
        )


    # -----------------------------------------------------
    # GROUP / SORT
    # -----------------------------------------------------

    statement = (
        statement
        .group_by(
            Disease.id,
            Disease.code,
            Disease.name,
        )
        .order_by(
            func.count(
                DiseaseCase.id
            ).desc(),
            Disease.name.asc(),
        )
    )


    rows = db.execute(
        statement
    ).all()


    return [
        {
            "disease_id":
                row.disease_id,

            "code":
                row.code,

            "name":
                row.name,

            "case_count":
                row.case_count,
        }
        for row in rows
    ]


# =========================================================
# WEEKLY DISEASE COMPARISON
# =========================================================

def get_weekly_disease_comparison(
    db: Session,
    include_sensitive: bool = False,
    sensitive_only: bool = False,
):
    """
    Compare validated disease cases for the
    current week against the previous week.

    Weeks run from Monday to Sunday.
    """

    today = date.today()


    # -----------------------------------------------------
    # CURRENT WEEK
    # -----------------------------------------------------

    current_week_start = (
        today
        - timedelta(
            days=today.weekday()
        )
    )

    current_week_end = (
        current_week_start
        + timedelta(
            days=6
        )
    )


    # -----------------------------------------------------
    # PREVIOUS WEEK
    # -----------------------------------------------------

    previous_week_end = (
        current_week_start
        - timedelta(
            days=1
        )
    )

    previous_week_start = (
        previous_week_end
        - timedelta(
            days=6
        )
    )


    # -----------------------------------------------------
    # CASE COUNTS
    # -----------------------------------------------------

    current_counts = (
        get_disease_case_counts(
            db=db,
            start_date=(
                current_week_start
            ),
            end_date=(
                current_week_end
            ),
            include_sensitive=(
                include_sensitive
            ),
            sensitive_only=(
                sensitive_only
            ),
        )
    )


    previous_counts = (
        get_disease_case_counts(
            db=db,
            start_date=(
                previous_week_start
            ),
            end_date=(
                previous_week_end
            ),
            include_sensitive=(
                include_sensitive
            ),
            sensitive_only=(
                sensitive_only
            ),
        )
    )


    previous_map = {
        item["disease_id"]:
            item["case_count"]
        for item
        in previous_counts
    }


    results = []


    # -----------------------------------------------------
    # COMPARE EACH DISEASE
    # -----------------------------------------------------

    for item in current_counts:
        disease_id = (
            item["disease_id"]
        )

        current_count = (
            item["case_count"]
        )

        previous_count = (
            previous_map.get(
                disease_id,
                0,
            )
        )

        difference = (
            current_count
            - previous_count
        )


        # -------------------------------------------------
        # PERCENTAGE CHANGE
        # -------------------------------------------------

        if previous_count == 0:

            if current_count == 0:
                percentage_change = 0.0

            else:
                percentage_change = None

        else:

            percentage_change = round(
                (
                    difference
                    / previous_count
                )
                * 100,
                2,
            )


        # -------------------------------------------------
        # TREND
        # -------------------------------------------------

        if difference > 0:
            trend = "INCREASE"

        elif difference < 0:
            trend = "DECREASE"

        else:
            trend = "NO_CHANGE"


        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        results.append(
            {
                "disease_id":
                    disease_id,

                "code":
                    item["code"],

                "name":
                    item["name"],

                "current_week_cases":
                    current_count,

                "previous_week_cases":
                    previous_count,

                "difference":
                    difference,

                "percentage_change":
                    percentage_change,

                "trend":
                    trend,
            }
        )


    return results


# =========================================================
# DISEASE CASES BY STREET
# =========================================================

def get_disease_cases_by_street(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    disease_id: int | None = None,
    include_sensitive: bool = False,
    sensitive_only: bool = False,
):
    """
    Return validated disease case counts grouped
    by patient street and disease.

    No patient-identifying information is returned.
    """

    street_expression = func.coalesce(
        func.nullif(
            func.trim(
                Patient.street
            ),
            "",
        ),
        "Unknown",
    )


    statement = (
        select(
            street_expression.label(
                "street"
            ),

            Disease.id.label(
                "disease_id"
            ),

            Disease.code.label(
                "code"
            ),

            Disease.name.label(
                "name"
            ),

            func.count(
                DiseaseCase.id
            ).label(
                "case_count"
            ),
        )
        .join(
            DiseaseCase,
            DiseaseCase.disease_id
            == Disease.id,
        )
        .join(
            Patient,
            Patient.id
            == DiseaseCase.patient_id,
        )
        .where(
            DiseaseCase.validation_status
            == "VALIDATED",

            Disease.is_active.is_(
                True
            ),
        )
    )


    # -----------------------------------------------------
    # DATE FILTERS
    # -----------------------------------------------------

    if start_date is not None:
        statement = (
            statement.where(
                DiseaseCase.case_date
                >= start_date
            )
        )


    if end_date is not None:
        statement = (
            statement.where(
                DiseaseCase.case_date
                <= end_date
            )
        )


    # -----------------------------------------------------
    # DISEASE FILTER
    # -----------------------------------------------------

    if disease_id is not None:
        statement = (
            statement.where(
                Disease.id
                == disease_id
            )
        )


    # -----------------------------------------------------
    # SENSITIVE DISEASE FILTER
    # -----------------------------------------------------

    if sensitive_only:
        statement = (
            statement.where(
                Disease.is_sensitive.is_(
                    True
                )
            )
        )

    elif not include_sensitive:
        statement = (
            statement.where(
                Disease.is_sensitive.is_(
                    False
                )
            )
        )


    # -----------------------------------------------------
    # GROUP / SORT
    # -----------------------------------------------------

    statement = (
        statement
        .group_by(
            street_expression,
            Disease.id,
            Disease.code,
            Disease.name,
        )
        .order_by(
            func.count(
                DiseaseCase.id
            ).desc(),
            street_expression.asc(),
            Disease.name.asc(),
        )
    )


    rows = db.execute(
        statement
    ).all()


    return [
        {
            "street":
                row.street,

            "disease_id":
                row.disease_id,

            "code":
                row.code,

            "name":
                row.name,

            "case_count":
                row.case_count,
        }
        for row in rows
    ]