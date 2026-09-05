from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.consultation import Consultation
from app.models.medicine import Medicine
from app.models.patient import Patient
from app.services.surveillance_service import (
    get_disease_case_counts,
)


def _get_total_stock(
    medicine: Medicine,
) -> int:
    if medicine.units_per_package is not None:
        return (
            medicine.package_stock
            * medicine.units_per_package
            + medicine.loose_stock
        )

    return (
        medicine.package_stock
        + medicine.loose_stock
    )


def _get_stock_status(
    medicine: Medicine,
) -> str:
    stock = _get_total_stock(
        medicine
    )

    if stock <= 0:
        return "OUT OF STOCK"

    if stock <= medicine.reorder_level:
        return "LOW STOCK"

    return "IN STOCK"


def _get_stock_display(
    medicine: Medicine,
) -> str:
    parts = []

    if medicine.package_stock > 0:
        package_label = (
            medicine.package_unit
            or "package"
        )

        parts.append(
            f"{medicine.package_stock} "
            f"{package_label}"
        )

    if medicine.loose_stock > 0:
        loose_label = (
            medicine.dispensing_unit
            or "piece"
        )

        parts.append(
            f"{medicine.loose_stock} "
            f"{loose_label}"
        )

    if not parts:
        return (
            f"0 "
            f"{medicine.dispensing_unit}"
        )

    return " + ".join(parts)


def get_dashboard_summary(
    db: Session,
):
    today = date.today()

    # =====================================================
    # DATE RANGES
    # =====================================================

    today_start = datetime.combine(
        today,
        time.min,
    )

    today_end = datetime.combine(
        today,
        time.max,
    )

    week_start_date = (
        today
        - timedelta(
            days=today.weekday()
        )
    )

    week_end_date = (
        week_start_date
        + timedelta(days=6)
    )

    week_start = datetime.combine(
        week_start_date,
        time.min,
    )

    week_end = datetime.combine(
        week_end_date,
        time.max,
    )

    # =====================================================
    # PATIENT COUNT
    # =====================================================

    total_patients = db.scalar(
        select(
            func.count(Patient.id)
        )
    ) or 0

    # =====================================================
    # CONSULTATIONS TODAY
    # =====================================================

    consultations_today = db.scalar(
        select(
            func.count(
                Consultation.id
            )
        )
        .where(
            Consultation.consultation_date
            >= today_start,
            Consultation.consultation_date
            <= today_end,
        )
    ) or 0

    # =====================================================
    # CONSULTATIONS THIS WEEK
    # =====================================================

    consultations_this_week = db.scalar(
        select(
            func.count(
                Consultation.id
            )
        )
        .where(
            Consultation.consultation_date
            >= week_start,
            Consultation.consultation_date
            <= week_end,
        )
    ) or 0

    # =====================================================
    # MEDICINE INVENTORY
    # =====================================================

    medicines = db.scalars(
        select(Medicine)
        .where(
            Medicine.is_active.is_(True)
        )
        .order_by(
            Medicine.name.asc()
        )
    ).all()

    active_medicines = len(
        medicines
    )

    low_stock_list = []

    low_stock_count = 0
    out_of_stock_count = 0

    for medicine in medicines:
        status = _get_stock_status(
            medicine
        )

        if status == "LOW STOCK":
            low_stock_count += 1

        if status == "OUT OF STOCK":
            out_of_stock_count += 1

        if status in {
            "LOW STOCK",
            "OUT OF STOCK",
        }:
            low_stock_list.append(
                {
                    "medicine_id":
                        medicine.id,

                    "code":
                        medicine.code,

                    "name":
                        medicine.name,

                    "stock_display":
                        _get_stock_display(
                            medicine
                        ),

                    "status":
                        status,
                }
            )

    # =====================================================
    # DISEASE CASES THIS WEEK
    # =====================================================

    disease_cases = (
        get_disease_case_counts(
            db=db,
            start_date=week_start_date,
            end_date=week_end_date,
        )
    )

    # =====================================================
    # RECENT CONSULTATIONS
    # =====================================================

    recent_rows = db.execute(
        select(
            Consultation,
            Patient,
        )
        .join(
            Patient,
            Patient.id
            == Consultation.patient_id,
        )
        .order_by(
            Consultation
            .consultation_date
            .desc()
        )
        .limit(5)
    ).all()

    recent_consultations = []

    for consultation, patient in recent_rows:
        patient_name = " ".join(
            part
            for part in [
                patient.first_name,
                patient.middle_name,
                patient.last_name,
            ]
            if part
        )

        recent_consultations.append(
            {
                "consultation_id":
                    consultation.id,

                "patient_id":
                    patient.id,

                "patient_name":
                    patient_name,

                "diagnosis":
                    consultation.diagnosis,

                "consultation_date":
                    consultation
                    .consultation_date
                    .isoformat(),
            }
        )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "total_patients":
            total_patients,

        "consultations_today":
            consultations_today,

        "consultations_this_week":
            consultations_this_week,

        "active_medicines":
            active_medicines,

        "low_stock_medicines":
            low_stock_count,

        "out_of_stock_medicines":
            out_of_stock_count,

        "disease_cases_this_week":
            disease_cases,

        "low_stock_list":
            low_stock_list,

        "recent_consultations":
            recent_consultations,
    }