from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient_history import PatientMedicalHistory
from app.schemas.patient_history import PatientHistoryCreate


def get_patient_histories(
    db: Session,
    patient_id: int,
):
    return db.scalars(
        select(PatientMedicalHistory)
        .where(
            PatientMedicalHistory.patient_id == patient_id
        )
        .order_by(
            PatientMedicalHistory.recorded_at.desc()
        )
    ).all()


def create_patient_history(
    db: Session,
    patient_id: int,
    data: PatientHistoryCreate,
    recorded_by: int | None,
):
    history = PatientMedicalHistory(
        patient_id=patient_id,
        history_type=data.history_type,
        description=data.description.strip(),
        recorded_by=recorded_by,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history