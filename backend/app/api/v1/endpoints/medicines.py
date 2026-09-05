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
from app.schemas.medicine import (
    MedicineCreate,
    MedicineResponse,
    MedicineUpdate,
)
from app.services.medicine_service import (
    create_medicine,
    get_medicine_by_id,
    get_medicines,
    update_medicine,
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


def _can_view_sensitive(
    user: User,
) -> bool:
    return _user_has_permission(
        user,
        "SENSITIVE_MEDICINE_VIEW",
    )


def _ensure_sensitive_manage_allowed(
    *,
    user: User,
    sensitive_inventory: bool,
) -> None:
    if (
        sensitive_inventory
        and not _can_view_sensitive(
            user
        )
    ):
        raise HTTPException(
            status_code=
                status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to manage sensitive/program "
                "medicine records."
            ),
        )


# =========================================================
# LIST MEDICINES
# =========================================================

@router.get(
    "/",
    response_model=list[MedicineResponse],
)
def list_medicines(
    search: str | None = Query(
        default=None,
    ),
    active_only: bool = Query(
        default=False,
    ),
    medicine_category: str | None = Query(
        default=None,
    ),
    formulary_status: str | None = Query(
        default=None,
    ),
    forecast_enabled: bool | None = Query(
        default=None,
    ),
    stock_verified: bool | None = Query(
        default=None,
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "INVENTORY_VIEW"
        )
    ),
):
    return get_medicines(
        db=db,
        search=search,
        active_only=active_only,
        medicine_category=medicine_category,
        formulary_status=formulary_status,
        forecast_enabled=forecast_enabled,
        stock_verified=stock_verified,
        include_sensitive=_can_view_sensitive(
            current_user
        ),
    )


# =========================================================
# ADD MEDICINE
# =========================================================

@router.post(
    "/",
    response_model=MedicineResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_medicine(
    data: MedicineCreate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "INVENTORY_ADJUST"
        )
    ),
):
    _ensure_sensitive_manage_allowed(
        user=current_user,
        sensitive_inventory=(
            data.sensitive_inventory
            or data.medicine_category
            == "SENSITIVE_PROGRAM"
        ),
    )

    try:
        return create_medicine(
            db=db,
            data=data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# =========================================================
# GET MEDICINE
# =========================================================

@router.get(
    "/{medicine_id}",
    response_model=MedicineResponse,
)
def get_medicine(
    medicine_id: int,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "INVENTORY_VIEW"
        )
    ),
):
    medicine = get_medicine_by_id(
        db,
        medicine_id,
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    if (
        medicine.sensitive_inventory
        and not _can_view_sensitive(
            current_user
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to view this sensitive/program "
                "medicine record."
            ),
        )

    return medicine


# =========================================================
# UPDATE MEDICINE
# =========================================================

@router.patch(
    "/{medicine_id}",
    response_model=MedicineResponse,
)
def edit_medicine(
    medicine_id: int,
    data: MedicineUpdate,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "INVENTORY_ADJUST"
        )
    ),
):
    medicine = get_medicine_by_id(
        db,
        medicine_id,
    )

    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    target_sensitive = (
        data.sensitive_inventory
        if data.sensitive_inventory
        is not None
        else medicine.sensitive_inventory
    )

    target_category = (
        data.medicine_category
        if data.medicine_category
        is not None
        else medicine.medicine_category
    )

    _ensure_sensitive_manage_allowed(
        user=current_user,
        sensitive_inventory=(
            bool(
                target_sensitive
            )
            or target_category
            == "SENSITIVE_PROGRAM"
        ),
    )

    try:
        return update_medicine(
            db=db,
            medicine=medicine,
            data=data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
