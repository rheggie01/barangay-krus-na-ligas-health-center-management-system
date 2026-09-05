from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_permission,
)
from app.models.audit_log import AuditLog
from app.models.user import User
from app.ml.schemas.prediction import (
    DiseasePredictionLogResponse,
    DiseasePredictionRequest,
    DiseasePredictionResponse,
)
from app.ml.services.prediction_log_service import (
    create_prediction_log_for_consultation,
    get_consultation_prediction_logs,
    prediction_log_to_dict,
)
from app.ml.services.prediction_service import (
    calculate_age,
    predict_disease,
)
from app.services.consultation_service import (
    get_consultation_by_id,
)
from app.services.patient_service import (
    get_patient_by_id,
)


router = APIRouter()


def get_user_role_names(
    user: User,
) -> str | None:
    role_names = []

    for role in getattr(user, "roles", []) or []:
        value = (
            getattr(role, "name", None)
            or getattr(role, "code", None)
        )

        if value:
            role_names.append(str(value))

    if not role_names:
        return None

    return ", ".join(
        sorted(set(role_names))
    )


def add_prediction_audit(
    db: Session,
    *,
    current_user: User,
    action: str,
    record_id: int,
    description: str,
    request: Request | None = None,
) -> AuditLog:
    ip_address = (
        request.client.host
        if request is not None and request.client
        else None
    )

    audit = AuditLog(
        user_id=current_user.id,
        role_names=get_user_role_names(
            current_user
        ),
        action=action,
        module="ML_DECISION_SUPPORT",
        record_id=record_id,
        description=description,
        ip_address=ip_address,
    )

    db.add(audit)
    return audit


@router.post(
    "/disease",
    response_model=DiseasePredictionResponse,
)
def create_disease_prediction_preview(
    data: DiseasePredictionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "DISEASE_PREDICT"
        )
    ),
):
    patient = get_patient_by_id(
        db,
        data.patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    if (
        getattr(
            patient,
            "record_status",
            "ACTIVE",
        )
        != "ACTIVE"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Disease decision support "
                "cannot be run for an "
                "inactive patient record."
            ),
        )

    try:
        age = calculate_age(
            patient.date_of_birth
        )

        result = predict_disease(
            age=age,
            sex=patient.sex,
            symptom_codes=data.symptom_codes,
            temperature=data.temperature,
            heart_rate=data.heart_rate,
            respiratory_rate=data.respiratory_rate,
            oxygen_saturation=data.oxygen_saturation,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except (
        FileNotFoundError,
        RuntimeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    add_prediction_audit(
        db,
        current_user=current_user,
        action="RUN_DISEASE_PREDICTION_PREVIEW",
        record_id=patient.id,
        description=(
            "Ran a non-persistent synthetic-development "
            "disease classification preview for patient "
            f"{patient.patient_code}. "
            "No diagnosis or disease case was created."
        ),
        request=request,
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return DiseasePredictionResponse(
        patient_id=patient.id,
        age=age,
        sex=str(patient.sex),
        **result,
    )


@router.post(
    "/consultations/{consultation_id}/disease",
    response_model=DiseasePredictionLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_consultation_disease_prediction(
    consultation_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "DISEASE_PREDICT"
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

    try:
        log = create_prediction_log_for_consultation(
            db,
            consultation,
            performed_by=current_user.id,
            commit=False,
        )

        add_prediction_audit(
            db,
            current_user=current_user,
            action="RECORD_DISEASE_PREDICTION",
            record_id=consultation.id,
            description=(
                "Recorded a synthetic-development "
                "ML disease decision-support analysis "
                f"for consultation #{consultation.id}. "
                f"Top result: "
                f"{log.predicted_disease_code} "
                f"({log.top_probability:.4f}). "
                "No diagnosis or disease case "
                "was automatically created."
            ),
            request=request,
        )

        db.commit()
        db.refresh(log)

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

    return prediction_log_to_dict(
        log,
        current_user,
    )


@router.get(
    "/consultations/{consultation_id}",
    response_model=list[
        DiseasePredictionLogResponse
    ],
)
def list_consultation_disease_predictions(
    consultation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "DISEASE_PREDICT"
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

    return get_consultation_prediction_logs(
        db,
        consultation_id,
    )
