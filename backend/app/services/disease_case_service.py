from datetime import (
    date,
    datetime,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consultation import Consultation
from app.models.disease import Disease
from app.models.disease_case import DiseaseCase
from app.schemas.disease_case import (
    DiseaseCaseCreate,
    DiseaseCaseUpdate,
)
from app.services.actor_snapshot_service import (
    snapshot_user_by_id,
)
from app.services.audit_log_service import (
    create_audit_log,
)


# =========================================================
# GET CASES FOR CONSULTATION
# =========================================================

def get_consultation_disease_cases(
    db: Session,
    consultation_id: int,
):
    return db.scalars(
        select(DiseaseCase)
        .where(
            DiseaseCase.consultation_id
            == consultation_id
        )
        .order_by(
            DiseaseCase.case_date.desc()
        )
    ).all()


# =========================================================
# GET DISEASE CASE BY ID
# =========================================================

def get_disease_case_by_id(
    db: Session,
    disease_case_id: int,
):
    return db.scalar(
        select(DiseaseCase).where(
            DiseaseCase.id
            == disease_case_id
        )
    )


# =========================================================
# CREATE DISEASE CASE
# =========================================================

def create_disease_case(
    db: Session,
    consultation: Consultation,
    disease: Disease,
    data: DiseaseCaseCreate,
    recorded_by: int | None,
):
    existing = db.scalar(
        select(DiseaseCase).where(
            DiseaseCase.consultation_id
            == consultation.id,

            DiseaseCase.disease_id
            == disease.id,
        )
    )

    if existing:
        raise ValueError(
            "This disease is already recorded "
            "for the consultation."
        )

    actor_user, actor = snapshot_user_by_id(
        db,
        recorded_by,
    )

    disease_case = DiseaseCase(
        patient_id=(
            consultation.patient_id
        ),

        consultation_id=(
            consultation.id
        ),

        disease_id=(
            disease.id
        ),

        case_status=(
            data.case_status
        ),

        onset_date=(
            data.onset_date
        ),

        case_date=(
            date.today()
        ),

        remarks=(
            data.remarks
        ),

        validation_status="PENDING",

        recorded_by=(
            recorded_by
        ),

        recorded_by_name_snapshot=(
            actor["display_name"]
        ),

        recorded_by_role_snapshot=(
            actor["role_names"]
        ),
    )

    try:
        db.add(
            disease_case
        )

        db.flush()

        if actor_user is not None:
            create_audit_log(
                db,
                action="DISEASE_CASE_CREATE",
                module="SURVEILLANCE",
                user=actor_user,
                record_id=disease_case.id,
                subject_label_snapshot=(
                    f"{disease.code} | "
                    f"Disease Case #{disease_case.id}"
                ),
                description=(
                    "Created disease case "
                    f"#{disease_case.id} for "
                    f"{disease.name}."
                ),
            )

        db.commit()

        db.refresh(
            disease_case
        )

    except Exception:
        db.rollback()
        raise

    return disease_case


# =========================================================
# UPDATE DISEASE CASE
# =========================================================

def update_disease_case(
    db: Session,
    disease_case: DiseaseCase,
    data: DiseaseCaseUpdate,
    updated_by: int | None = None,
):
    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in (
        update_data.items()
    ):
        setattr(
            disease_case,
            field,
            value,
        )

    actor_user, _actor = snapshot_user_by_id(
        db,
        updated_by,
    )

    try:
        db.flush()

        if actor_user is not None:
            create_audit_log(
                db,
                action="DISEASE_CASE_UPDATE",
                module="SURVEILLANCE",
                user=actor_user,
                record_id=disease_case.id,
                subject_label_snapshot=(
                    f"Disease Case #{disease_case.id}"
                ),
                description=(
                    "Updated disease case "
                    f"#{disease_case.id}."
                ),
            )

        db.commit()

        db.refresh(
            disease_case
        )

    except Exception:
        db.rollback()
        raise

    return disease_case


# =========================================================
# VALIDATE / REJECT DISEASE CASE
# =========================================================

def validate_disease_case(
    db: Session,
    disease_case: DiseaseCase,
    validation_status: str,
    validated_by: int,
):
    actor_user, actor = snapshot_user_by_id(
        db,
        validated_by,
    )

    disease_case.validation_status = (
        validation_status
    )

    disease_case.validated_by = (
        validated_by
    )

    disease_case.validated_by_name_snapshot = (
        actor["display_name"]
    )

    disease_case.validated_by_role_snapshot = (
        actor["role_names"]
    )

    disease_case.validated_at = (
        datetime.now()
    )

    try:
        db.flush()

        if actor_user is not None:
            create_audit_log(
                db,
                action=(
                    "DISEASE_CASE_"
                    f"{validation_status}"
                ),
                module="SURVEILLANCE",
                user=actor_user,
                record_id=disease_case.id,
                subject_label_snapshot=(
                    f"Disease Case #{disease_case.id}"
                ),
                description=(
                    "Set disease case "
                    f"#{disease_case.id} "
                    "validation status to "
                    f"{validation_status}."
                ),
            )

        db.commit()

        db.refresh(
            disease_case
        )

    except Exception:
        db.rollback()
        raise

    return disease_case