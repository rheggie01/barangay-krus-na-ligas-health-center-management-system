from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_permission
from app.models.user import User
from app.schemas.patient_history import (
    PatientHistoryCreate,
    PatientHistoryResponse,
)
from app.services.patient_history_service import (
    create_patient_history,
    get_patient_histories,
)
from app.services.patient_service import get_patient_by_id


router = APIRouter()


@router.get(
    "/{patient_id}/history",
    response_model=list[PatientHistoryResponse],
)
def list_patient_history(
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

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return get_patient_histories(
        db,
        patient_id,
    )


@router.post(
    "/{patient_id}/history",
    response_model=PatientHistoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_patient_history(
    patient_id: int,
    data: PatientHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("PATIENT_UPDATE")
    ),
):
    patient = get_patient_by_id(
        db,
        patient_id,
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return create_patient_history(
        db,
        patient_id,
        data,
        recorded_by=current_user.id,
    )