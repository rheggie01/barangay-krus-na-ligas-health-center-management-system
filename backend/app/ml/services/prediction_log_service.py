from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consultation import Consultation
from app.models.disease_prediction_log import (
    DiseasePredictionLog,
)
from app.models.patient import Patient
from app.models.user import User
from app.ml.services.prediction_service import (
    calculate_age,
    predict_disease,
)


def _performer_name(
    user: User | None,
) -> str | None:
    if user is None:
        return None

    full_name = " ".join(
        value.strip()
        for value in [
            user.first_name or "",
            user.last_name or "",
        ]
        if value and value.strip()
    )

    return full_name or user.username or None


def create_prediction_log_for_consultation(
    db: Session,
    consultation: Consultation,
    *,
    performed_by: int | None,
    commit: bool = True,
) -> DiseasePredictionLog:
    symptom_codes = list(
        consultation.symptom_codes
    )

    if not symptom_codes:
        raise ValueError(
            "At least one structured symptom "
            "is required before recording "
            "an ML disease analysis."
        )

    patient = db.get(
        Patient,
        consultation.patient_id,
    )

    if patient is None:
        raise ValueError(
            "Patient not found for consultation."
        )

    reference_date = (
        consultation.consultation_date.date()
        if consultation.consultation_date
        else None
    )

    age = calculate_age(
        patient.date_of_birth,
        on_date=reference_date,
    )

    result = predict_disease(
        age=age,
        sex=patient.sex,
        symptom_codes=symptom_codes,
        temperature=consultation.temperature,
        heart_rate=consultation.heart_rate,
        respiratory_rate=consultation.respiratory_rate,
        oxygen_saturation=consultation.oxygen_saturation,
    )

    log = DiseasePredictionLog(
        consultation_id=consultation.id,
        patient_id=patient.id,
        performed_by=performed_by,
        model_name=result["selected_model"],
        predicted_disease_code=(
            result["predicted_disease_code"]
        ),
        predicted_disease_name=(
            result["predicted_disease_name"]
        ),
        top_probability=result["top_probability"],
        probabilities=result["probabilities"],
        age=age,
        sex=str(patient.sex),
        symptom_codes=symptom_codes,
        temperature=consultation.temperature,
        heart_rate=consultation.heart_rate,
        respiratory_rate=consultation.respiratory_rate,
        oxygen_saturation=consultation.oxygen_saturation,
        development_status=result["development_status"],
        decision_support_notice=(
            result["decision_support_notice"]
        ),
    )

    try:
        db.add(log)

        if commit:
            db.commit()
            db.refresh(log)
        else:
            db.flush()

        return log

    except Exception:
        db.rollback()
        raise


def get_consultation_prediction_logs(
    db: Session,
    consultation_id: int,
):
    rows = db.execute(
        select(
            DiseasePredictionLog,
            User,
        )
        .outerjoin(
            User,
            User.id == DiseasePredictionLog.performed_by,
        )
        .where(
            DiseasePredictionLog.consultation_id
            == consultation_id
        )
        .order_by(
            DiseasePredictionLog.created_at.desc(),
            DiseasePredictionLog.id.desc(),
        )
    ).all()

    return [
        prediction_log_to_dict(log, user)
        for log, user in rows
    ]


def prediction_log_to_dict(
    log: DiseasePredictionLog,
    user: User | None = None,
) -> dict:
    return {
        "id": log.id,
        "consultation_id": log.consultation_id,
        "patient_id": log.patient_id,
        "performed_by": log.performed_by,
        "performed_by_name": _performer_name(user),
        "model_name": log.model_name,
        "predicted_disease_code": (
            log.predicted_disease_code
        ),
        "predicted_disease_name": (
            log.predicted_disease_name
        ),
        "top_probability": float(
            log.top_probability
        ),
        "probabilities": log.probabilities or [],
        "age": log.age,
        "sex": log.sex,
        "symptom_codes": log.symptom_codes or [],
        "temperature": log.temperature,
        "heart_rate": log.heart_rate,
        "respiratory_rate": log.respiratory_rate,
        "oxygen_saturation": log.oxygen_saturation,
        "development_status": log.development_status,
        "decision_support_notice": (
            log.decision_support_notice
        ),
        "created_at": log.created_at,
    }
