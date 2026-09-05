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
from app.models.disease import Disease
from app.models.user import User
from app.schemas.disease_case import (
    DiseaseCaseCreate,
    DiseaseCaseResponse,
    DiseaseCaseUpdate,
    DiseaseCaseValidationUpdate,
)
from app.services.disease_case_service import (
    create_disease_case,
    get_consultation_disease_cases,
    get_disease_case_by_id,
    update_disease_case,
    validate_disease_case,
)


router = APIRouter()


# =========================================================
# PERMISSION HELPERS
# =========================================================

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


def ensure_sensitive_access(
    disease: Disease,
    current_user: User,
) -> None:
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
                "access this sensitive disease record."
            ),
        )


# =========================================================
# LIST DISEASE CASES FOR CONSULTATION
# =========================================================

@router.get(
    "/consultations/{consultation_id}/disease-cases",
    response_model=list[DiseaseCaseResponse],
)
def list_consultation_disease_cases(
    consultation_id: int,
    db: Session = Depends(get_db),
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )

    disease_cases = (
        get_consultation_disease_cases(
            db=db,
            consultation_id=consultation_id,
        )
    )

    if can_view_sensitive_diseases(
        current_user
    ):
        return disease_cases

    visible_cases = []

    for disease_case in disease_cases:
        disease = db.get(
            Disease,
            disease_case.disease_id,
        )

        if (
            disease is not None
            and disease.is_sensitive
        ):
            continue

        visible_cases.append(
            disease_case
        )

    return visible_cases


# =========================================================
# CREATE DISEASE CASE
# =========================================================

@router.post(
    "/consultations/{consultation_id}/disease-cases",
    response_model=DiseaseCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_disease_case(
    consultation_id: int,
    data: DiseaseCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "DISEASE_CASE_CREATE"
        )
    ),
):
    consultation = db.get(
        Consultation,
        consultation_id,
    )

    if consultation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation not found.",
        )

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

    if disease.is_sensitive:
        ensure_sensitive_access(
            disease,
            current_user,
        )

    try:
        return create_disease_case(
            db=db,
            consultation=consultation,
            disease=disease,
            data=data,
            recorded_by=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# =========================================================
# GET DISEASE CASE
# =========================================================

@router.get(
    "/disease-cases/{disease_case_id}",
    response_model=DiseaseCaseResponse,
)
def get_disease_case(
    disease_case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "PATIENT_VIEW"
        )
    ),
):
    disease_case = get_disease_case_by_id(
        db=db,
        disease_case_id=disease_case_id,
    )

    if disease_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disease case not found.",
        )

    disease = db.get(
        Disease,
        disease_case.disease_id,
    )

    if disease is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disease not found.",
        )

    ensure_sensitive_access(
        disease,
        current_user,
    )

    return disease_case


# =========================================================
# UPDATE DISEASE CASE
# =========================================================

@router.patch(
    "/disease-cases/{disease_case_id}",
    response_model=DiseaseCaseResponse,
)
def edit_disease_case(
    disease_case_id: int,
    data: DiseaseCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "DISEASE_CASE_CREATE"
        )
    ),
):
    disease_case = get_disease_case_by_id(
        db=db,
        disease_case_id=disease_case_id,
    )

    if disease_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disease case not found.",
        )

    current_disease = db.get(
        Disease,
        disease_case.disease_id,
    )

    if current_disease is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disease not found.",
        )

    ensure_sensitive_access(
        current_disease,
        current_user,
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

        ensure_sensitive_access(
            new_disease,
            current_user,
        )

    try:
        return update_disease_case(
            db=db,
            disease_case=disease_case,
            data=data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# =========================================================
# VALIDATE / REJECT DISEASE CASE
# =========================================================

@router.patch(
    "/disease-cases/{disease_case_id}/validation",
    response_model=DiseaseCaseResponse,
)
def validate_case(
    disease_case_id: int,
    data: DiseaseCaseValidationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(
            "DISEASE_CASE_VALIDATE"
        )
    ),
):
    disease_case = get_disease_case_by_id(
        db=db,
        disease_case_id=disease_case_id,
    )

    if disease_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disease case not found.",
        )

    disease = db.get(
        Disease,
        disease_case.disease_id,
    )

    if disease is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Disease not found.",
        )

    ensure_sensitive_access(
        disease,
        current_user,
    )

    try:
        return validate_disease_case(
            db=db,
            disease_case=disease_case,
            validation_status=(
                data.validation_status
            ),
            validated_by=current_user.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc