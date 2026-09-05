from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_permission,
)
from app.models.user import User
from app.schemas.disease import (
    DiseaseCreate,
    DiseaseResponse,
    DiseaseUpdate,
)
from app.services.disease_service import (
    create_disease,
    get_active_diseases,
    get_disease_by_id,
    get_diseases,
    update_disease,
)


router = APIRouter()


# =========================================================
# LIST DISEASES
# =========================================================

@router.get(
    "/",
    response_model=list[DiseaseResponse],
)
def list_diseases(
    active_only: bool = Query(
        default=False,
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "PATIENT_VIEW"
        )
    ),
):
    if active_only:
        return get_active_diseases(
            db
        )

    return get_diseases(
        db
    )


# =========================================================
# GET DISEASE
# =========================================================

@router.get(
    "/{disease_id}",
    response_model=DiseaseResponse,
)
def get_disease(
    disease_id: int,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "PATIENT_VIEW"
        )
    ),
):
    disease = get_disease_by_id(
        db,
        disease_id,
    )

    if disease is None:
        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail="Disease not found.",
        )

    return disease


# =========================================================
# CREATE DISEASE
# =========================================================

@router.post(
    "/",
    response_model=DiseaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_disease(
    data: DiseaseCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "USER_MANAGE"
        )
    ),
):
    try:
        return create_disease(
            db=db,
            data=data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# =========================================================
# UPDATE DISEASE
# =========================================================

@router.patch(
    "/{disease_id}",
    response_model=DiseaseResponse,
)
def edit_disease(
    disease_id: int,
    data: DiseaseUpdate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "USER_MANAGE"
        )
    ),
):
    disease = get_disease_by_id(
        db,
        disease_id,
    )

    if disease is None:
        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail="Disease not found.",
        )

    try:
        return update_disease(
            db=db,
            disease=disease,
            data=data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc