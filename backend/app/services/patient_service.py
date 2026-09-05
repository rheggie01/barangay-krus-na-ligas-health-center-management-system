from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
)


# =========================================================
# HELPERS
# =========================================================

def _clean_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned or None


# =========================================================
# GENERATE PATIENT CODE
# =========================================================

def generate_patient_code(
    db: Session,
) -> str:
    last_patient = db.scalar(
        select(Patient)
        .order_by(
            Patient.id.desc()
        )
        .limit(1)
    )

    next_number = 1

    if last_patient:
        next_number = (
            last_patient.id + 1
        )

    current_year = (
        datetime.now().year
    )

    return (
        f"KNL-{current_year}-"
        f"{next_number:05d}"
    )


# =========================================================
# CREATE PATIENT
# =========================================================

def create_patient(
    db: Session,
    data: PatientCreate,
    registered_by: int | None = None,
) -> Patient:
    patient = Patient(
        patient_code=
            generate_patient_code(db),

        first_name=
            data.first_name.strip(),

        middle_name=
            _clean_optional_text(
                data.middle_name
            ),

        last_name=
            data.last_name.strip(),

        suffix=
            data.suffix,

        date_of_birth=
            data.date_of_birth,

        sex=
            data.sex,

        civil_status=
            data.civil_status,

        is_pwd=
            data.is_pwd,

        street=
            _clean_optional_text(
                data.street
            ),

        barangay=
            _clean_optional_text(
                data.barangay
            ),

        city=
            _clean_optional_text(
                data.city
            ),

        address=
            data.address.strip(),

        contact_number=
            _clean_optional_text(
                data.contact_number
            ),

        emergency_contact_name=
            _clean_optional_text(
                data.emergency_contact_name
            ),

        emergency_contact_number=
            _clean_optional_text(
                data.emergency_contact_number
            ),

        record_status="ACTIVE",
    )


    # -----------------------------------------------------
    # REGISTERED BY
    #
    # Keep this only if the Patient model actually has
    # a registered_by column.
    # -----------------------------------------------------

    if hasattr(
        patient,
        "registered_by",
    ):
        patient.registered_by = (
            registered_by
        )


    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    try:
        db.add(patient)
        db.commit()
        db.refresh(patient)

    except Exception:
        db.rollback()
        raise


    return patient


# =========================================================
# GET ALL PATIENTS
# =========================================================

def get_patients(
    db: Session,
):
    return db.scalars(
        select(Patient)
        .order_by(
            Patient.created_at.desc()
        )
    ).all()


# =========================================================
# GET PATIENT BY ID
# =========================================================

def get_patient_by_id(
    db: Session,
    patient_id: int,
):
    return db.scalar(
        select(Patient).where(
            Patient.id == patient_id
        )
    )


# =========================================================
# UPDATE PATIENT
# =========================================================

def update_patient(
    db: Session,
    patient: Patient,
    data: PatientUpdate,
) -> Patient:
    update_data = (
        data.model_dump(
            exclude_unset=True
        )
    )


    # -----------------------------------------------------
    # CLEAN STRING VALUES
    # -----------------------------------------------------

    for field, value in (
        update_data.items()
    ):
        if (
            isinstance(
                value,
                str,
            )
        ):
            value = (
                value.strip()
                or None
            )

        setattr(
            patient,
            field,
            value,
        )


    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    try:
        db.commit()
        db.refresh(patient)

    except Exception:
        db.rollback()
        raise


    return patient
