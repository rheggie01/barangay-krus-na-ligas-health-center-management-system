from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient_history import PatientMedicalHistory
from app.schemas.patient_history import PatientHistoryCreate
from app.services.actor_snapshot_service import (
    snapshot_user_by_id,
)
from app.services.audit_log_service import (
    create_audit_log,
)


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
    actor_user, actor = snapshot_user_by_id(
        db,
        recorded_by,
    )

    history = PatientMedicalHistory(
        patient_id=patient_id,
        history_type=data.history_type,
        description=data.description.strip(),
        recorded_by=recorded_by,
        recorded_by_name_snapshot=actor["display_name"],
        recorded_by_role_snapshot=actor["role_names"],
    )

    try:
        db.add(history)
        db.flush()

        if actor_user is not None:
            create_audit_log(
                db,
                action="PATIENT_HISTORY_CREATE",
                module="CLINICAL",
                user=actor_user,
                record_id=history.id,
                subject_label_snapshot=(
                    f"Patient #{patient_id} | "
                    f"{data.history_type}"
                ),
                description=(
                    "Created patient medical "
                    f"history record #{history.id}."
                ),
            )

        db.commit()
        db.refresh(history)
        return history

    except Exception:
        db.rollback()
        raise