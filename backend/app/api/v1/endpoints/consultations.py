from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_permission,
)
from app.models.disease import Disease
from app.models.user import User
from app.ml.services.prediction_log_service import (
    create_prediction_log_for_consultation,
)
from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationResponse,
    ConsultationUpdate,
)
from app.services.consultation_service import (
    create_consultation,
    get_consultation_by_id,
    get_patient_consultations,
    update_consultation,
)
from app.services.audit_log_service import (
    create_audit_log,
)
from app.services.patient_service import (
    get_patient_by_id,
)


router = APIRouter()

RESTRICTED_DIAGNOSIS_LABEL = (
    "Restricted Sensitive Record"
)


def user_has_permission(
    user: User,
    permission_code: str,
) -> bool:
    return any(
        permission.code == permission_code
        for role in user.roles
        for permission in role.permissions
    )


def can_view_sensitive_diseases(
    user: User,
) -> bool:
    return user_has_permission(
        user,
        "SENSITIVE_DISEASE_VIEW",
    )


def get_user_role_names(
    user: User,
) -> str | None:
    names = [
        str(getattr(role, "name", "")).strip()
        for role in user.roles
    ]

    names = [name for name in names if name]

    return (
        ", ".join(sorted(set(names)))
        if names
        else None
    )


def get_consultation_disease(
    db: Session,
    consultation,
) -> Disease | None:
    if consultation.disease_id is not None:
        disease = db.get(
            Disease,
            consultation.disease_id,
        )

        if disease is not None:
            return disease

    if consultation.diagnosis:
        return db.scalar(
            select(Disease).where(
                func.lower(Disease.name)
                == consultation.diagnosis.strip().lower()
            )
        )

    return None


def ensure_disease_access(
    disease: Disease | None,
    current_user: User,
) -> None:
    if disease is None:
        return

    if (
        disease.is_sensitive
        and not can_view_sensitive_diseases(
            current_user
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "access this sensitive health record."
            ),
        )


def consultation_response_for_user(
    db: Session,
    consultation,
    current_user: User,
) -> ConsultationResponse:
    response = ConsultationResponse.model_validate(
        consultation,
        from_attributes=True,
    )

    disease = get_consultation_disease(
        db,
        consultation,
    )

    if (
        disease is not None
        and disease.is_sensitive
        and not can_view_sensitive_diseases(
            current_user
        )
    ):
        return response.model_copy(
            update={
                "disease_id": None,
                "diagnosis": RESTRICTED_DIAGNOSIS_LABEL,
            }
        )

    return response


@router.get(
    "/patients/{patient_id}/consultations",
    response_model=list[ConsultationResponse],
)
def list_patient_consultations(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("PATIENT_VIEW")
    ),
):
    patient = get_patient_by_id(
        db,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    consultations = get_patient_consultations(
        db,
        patient_id,
    )

    return [
        consultation_response_for_user(
            db,
            consultation,
            current_user,
        )
        for consultation in consultations
    ]


@router.post(
    "/patients/{patient_id}/consultations",
    response_model=ConsultationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_consultation(
    patient_id: int,
    data: ConsultationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "CONSULTATION_CREATE"
        )
    ),
):
    patient = get_patient_by_id(
        db,
        patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    if (
        data.run_ml_analysis
        and not user_has_permission(
            current_user,
            "DISEASE_PREDICT",
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to record an ML disease analysis."
            ),
        )

    if (
        data.diagnosis
        and not user_has_permission(
            current_user,
            "DIAGNOSIS_CREATE",
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to create a diagnosis."
            ),
        )

    disease = None

    if data.disease_id is not None:
        disease = db.get(
            Disease,
            data.disease_id,
        )

        if disease is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disease not found.",
            )

        if not disease.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disease is inactive.",
            )

        ensure_disease_access(
            disease,
            current_user,
        )

    if data.run_ml_analysis:
        try:
            consultation = create_consultation(
                db,
                patient_id,
                data,
                recorded_by=current_user.id,
                commit=False,
            )

            prediction_log = (
                create_prediction_log_for_consultation(
                    db,
                    consultation,
                    performed_by=current_user.id,
                    commit=False,
                )
            )

            create_audit_log(
                db,
                action="RECORD_DISEASE_PREDICTION",
                module="ML_DECISION_SUPPORT",
                user=current_user,
                record_id=consultation.id,
                subject_label_snapshot=(
                    f"Consultation #{consultation.id}"
                ),
                description=(
                    "Recorded a synthetic-development "
                    "ML disease decision-support analysis "
                    "together with consultation "
                    f"#{consultation.id}. "
                    "Top result: "
                    f"{prediction_log.predicted_disease_code} "
                    f"({prediction_log.top_probability:.4f}). "
                    "No diagnosis or disease case "
                    "was automatically created."
                ),
                ip_address=None,
            )

            db.commit()

            consultation = get_consultation_by_id(
                db,
                consultation.id,
            )

        except ValueError as exc:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

        except (
            FileNotFoundError,
            RuntimeError,
        ) as exc:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            )

        except Exception:
            db.rollback()
            raise

    else:
        try:
            consultation = create_consultation(
                db,
                patient_id,
                data,
                recorded_by=current_user.id,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )

    return consultation_response_for_user(
        db,
        consultation,
        current_user,
    )


@router.get(
    "/consultations/{consultation_id}",
    response_model=ConsultationResponse,
)
def view_consultation(
    consultation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("PATIENT_VIEW")
    ),
):
    consultation = get_consultation_by_id(
        db,
        consultation_id,
    )

    if consultation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )

    disease = get_consultation_disease(
        db,
        consultation,
    )

    ensure_disease_access(
        disease,
        current_user,
    )

    return consultation_response_for_user(
        db,
        consultation,
        current_user,
    )


@router.patch(
    "/consultations/{consultation_id}",
    response_model=ConsultationResponse,
)
def edit_consultation(
    consultation_id: int,
    data: ConsultationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "CONSULTATION_CREATE"
        )
    ),
):
    consultation = get_consultation_by_id(
        db,
        consultation_id,
    )

    if consultation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )

    current_disease = get_consultation_disease(
        db,
        consultation,
    )

    ensure_disease_access(
        current_disease,
        current_user,
    )

    if (
        data.diagnosis is not None
        and data.diagnosis != consultation.diagnosis
        and not user_has_permission(
            current_user,
            "DIAGNOSIS_CREATE",
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to create or modify a diagnosis."
            ),
        )

    if data.disease_id is not None:
        new_disease = db.get(
            Disease,
            data.disease_id,
        )

        if new_disease is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disease not found.",
            )

        if not new_disease.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disease is inactive.",
            )

        ensure_disease_access(
            new_disease,
            current_user,
        )

    try:
        updated = update_consultation(
            db,
            consultation,
            data,
            updated_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return consultation_response_for_user(
        db,
        updated,
        current_user,
    )
