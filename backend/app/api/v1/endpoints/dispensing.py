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
from app.models.consultation import Consultation
from app.models.user import User
from app.schemas.consultation_medicine import (
    ConsultationMedicineCreate,
    ConsultationMedicineResponse,
)
from app.services.dispensing_service import (
    dispense_medicine,
    get_consultation_medicines,
)
from app.services.medicine_service import (
    get_medicine_by_id,
)


router = APIRouter()


def _user_has_permission(
    user: User,
    permission_code: str,
) -> bool:
    return any(
        permission.code
        == permission_code
        for role in user.roles
        for permission
        in role.permissions
    )


# =========================================================
# GET DISPENSED MEDICINES
# =========================================================

@router.get(
    "/consultations/{consultation_id}/medicines",
    response_model=list[
        ConsultationMedicineResponse
    ],
)
def list_dispensed_medicines(
    consultation_id: int,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "PATIENT_VIEW"
        )
    ),
):
    consultation = db.get(
        Consultation,
        consultation_id,
    )

    if consultation is None:
        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )

    return get_consultation_medicines(
        db=db,
        consultation_id=consultation_id,
    )


# =========================================================
# DISPENSE MEDICINE
# =========================================================

@router.post(
    "/consultations/{consultation_id}/medicines",
    response_model=
        ConsultationMedicineResponse,
    status_code=
        status.HTTP_201_CREATED,
)
def add_dispensed_medicine(
    consultation_id: int,
    data: ConsultationMedicineCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "MEDICINE_DISPENSE"
        )
    ),
):
    # -----------------------------------------------------
    # FIND CONSULTATION
    # -----------------------------------------------------

    consultation = db.get(
        Consultation,
        consultation_id,
    )

    if consultation is None:
        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )


    # -----------------------------------------------------
    # FIND MEDICINE
    # -----------------------------------------------------

    medicine = get_medicine_by_id(
        db,
        data.medicine_id,
    )

    if medicine is None:
        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail="Medicine not found.",
        )


    # -----------------------------------------------------
    # CHECK MEDICINE STATUS
    # -----------------------------------------------------

    if not medicine.is_active:
        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail="Medicine is inactive.",
        )


    if not medicine.stock_verified:
        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail=(
                "Medicine stock/formulary status "
                "has not been verified for dispensing."
            ),
        )


    if (
        medicine.restricted_dispensing
        and not _user_has_permission(
            current_user,
            "SENSITIVE_MEDICINE_DISPENSE",
        )
    ):
        raise HTTPException(
            status_code=
                status.HTTP_403_FORBIDDEN,
            detail=(
                "This medicine is restricted to "
                "authorized sensitive/program "
                "dispensing personnel."
            ),
        )


    # -----------------------------------------------------
    # DISPENSE
    # -----------------------------------------------------

    try:
        return dispense_medicine(
            db=db,
            consultation=consultation,
            medicine=medicine,
            data=data,
            dispensed_by=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc