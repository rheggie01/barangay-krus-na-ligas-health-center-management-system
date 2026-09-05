from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.consultation import Consultation
from app.models.symptom import Symptom
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationUpdate,
)
from app.services.actor_snapshot_service import (
    snapshot_user_by_id,
)
from app.services.audit_log_service import (
    create_audit_log,
)


def create_consultation(
    db: Session,
    patient_id: int,
    data: ConsultationCreate,
    recorded_by: int | None,
    *,
    commit: bool = True,
) -> Consultation:
    structured_symptoms = _get_active_symptoms_by_codes(
        db=db,
        symptom_codes=data.symptom_codes,
    )

    actor_user, actor = snapshot_user_by_id(
        db,
        recorded_by,
    )

    consultation = Consultation(
        patient_id=patient_id,
        disease_id=data.disease_id,
        chief_complaint=data.chief_complaint.strip(),
        symptoms=data.symptoms,
        temperature=data.temperature,
        systolic_bp=data.systolic_bp,
        diastolic_bp=data.diastolic_bp,
        heart_rate=data.heart_rate,
        respiratory_rate=data.respiratory_rate,
        oxygen_saturation=data.oxygen_saturation,
        weight_kg=data.weight_kg,
        height_cm=data.height_cm,
        assessment=data.assessment,
        diagnosis=data.diagnosis,
        treatment_plan=data.treatment_plan,
        notes=data.notes,
        recorded_by=recorded_by,
        recorded_by_name_snapshot=actor["display_name"],
        recorded_by_role_snapshot=actor["role_names"],
    )

    consultation.structured_symptoms = structured_symptoms

    try:
        db.add(consultation)
        db.flush()

        if actor_user is not None:
            create_audit_log(
                db,
                action="CONSULTATION_CREATE",
                module="CLINICAL",
                user=actor_user,
                record_id=consultation.id,
                subject_label_snapshot=(
                    f"Consultation #{consultation.id}"
                ),
                description=(
                    "Created consultation "
                    f"#{consultation.id} for "
                    f"patient #{patient_id}."
                ),
            )

        if commit:
            db.commit()
            db.refresh(consultation)

            return get_consultation_by_id(
                db=db,
                consultation_id=consultation.id,
            )

        db.refresh(consultation)
        return consultation

    except Exception:
        db.rollback()
        raise


def get_patient_consultations(
    db: Session,
    patient_id: int,
):
    return db.scalars(
        select(Consultation)
        .options(
            selectinload(
                Consultation.structured_symptoms
            )
        )
        .where(
            Consultation.patient_id == patient_id
        )
        .order_by(
            Consultation.consultation_date.desc()
        )
    ).all()


def get_consultation_by_id(
    db: Session,
    consultation_id: int,
):
    return db.scalar(
        select(Consultation)
        .options(
            selectinload(
                Consultation.structured_symptoms
            )
        )
        .where(
            Consultation.id == consultation_id
        )
    )


def update_consultation(
    db: Session,
    consultation: Consultation,
    data: ConsultationUpdate,
    updated_by: int | None = None,
) -> Consultation:
    update_data = data.model_dump(
        exclude_unset=True
    )

    symptom_codes = update_data.pop(
        "symptom_codes",
        None,
    )

    if symptom_codes is not None:
        consultation.structured_symptoms = (
            _get_active_symptoms_by_codes(
                db=db,
                symptom_codes=symptom_codes,
            )
        )

    for field, value in update_data.items():
        setattr(
            consultation,
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
                action="CONSULTATION_UPDATE",
                module="CLINICAL",
                user=actor_user,
                record_id=consultation.id,
                subject_label_snapshot=(
                    f"Consultation #{consultation.id}"
                ),
                description=(
                    "Updated consultation "
                    f"#{consultation.id}."
                ),
            )

        db.commit()
        db.refresh(consultation)

        return get_consultation_by_id(
            db=db,
            consultation_id=consultation.id,
        )

    except Exception:
        db.rollback()
        raise


def _get_active_symptoms_by_codes(
    db: Session,
    symptom_codes: list[str],
) -> list[Symptom]:
    if not symptom_codes:
        return []

    normalized_codes: list[str] = []

    for raw_code in symptom_codes:
        code = str(raw_code).strip().upper()

        if code and code not in normalized_codes:
            normalized_codes.append(code)

    symptoms = db.scalars(
        select(Symptom).where(
            Symptom.code.in_(normalized_codes),
            Symptom.is_active.is_(True),
        )
    ).all()

    symptoms_by_code = {
        symptom.code: symptom
        for symptom in symptoms
    }

    missing_codes = [
        code
        for code in normalized_codes
        if code not in symptoms_by_code
    ]

    if missing_codes:
        raise ValueError(
            "Invalid or inactive symptom code(s): "
            + ", ".join(missing_codes)
        )

    return [
        symptoms_by_code[code]
        for code in normalized_codes
    ]
