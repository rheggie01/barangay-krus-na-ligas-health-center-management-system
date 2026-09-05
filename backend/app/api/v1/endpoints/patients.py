from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_permission,
)
from app.models.user import User
from app.schemas.patient import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
)
from app.services.patient_service import (
    create_patient,
    get_patient_by_id,
    get_patients,
    update_patient,
)


router = APIRouter()


# =========================================================
# LIST PATIENTS
# =========================================================

@router.get(
    "/",
    response_model=list[PatientResponse],
)
def list_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "PATIENT_VIEW"
        )
    ),
):
    return get_patients(db)


# =========================================================
# REGISTER PATIENT
# =========================================================

@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "PATIENT_CREATE"
        )
    ),
):
    return create_patient(
        db,
        data,
        registered_by=current_user.id,
    )


# =========================================================
# VIEW PATIENT
# =========================================================

@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)
def view_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "PATIENT_VIEW"
        )
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

    return patient


# =========================================================
# UPDATE PATIENT
# =========================================================

@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
)
def edit_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "PATIENT_UPDATE"
        )
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

    return update_patient(
        db,
        patient,
        data,
    )