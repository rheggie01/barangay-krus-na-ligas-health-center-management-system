from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_permission,
)
from app.models.user import User
from app.schemas.inventory_transaction import (
    InventoryTransactionCreate,
    InventoryTransactionResponse,
)
from app.schemas.medicine_dispensing import (
    MedicineDispensingCreate,
    MedicineDispensingResponse,
)
from app.services.inventory_service import (
    create_inventory_transaction,
    get_inventory_transactions,
)
from app.services.medicine_dispensing_service import (
    dispense_medicine,
    get_medicine_dispensings,
)
from app.services.medicine_service import (
    get_medicine_by_id,
)


router = APIRouter()


# =========================================================
# LIST INVENTORY TRANSACTIONS
# =========================================================

@router.get(
    "/transactions",
    response_model=list[
        InventoryTransactionResponse
    ],
)
def list_inventory_transactions(
    medicine_id: int | None = Query(
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
    return get_inventory_transactions(
        db=db,
        medicine_id=medicine_id,
    )


# =========================================================
# CREATE MANUAL INVENTORY TRANSACTION
#
# STOCK_IN
# ADJUSTMENT_IN
# ADJUSTMENT_OUT
#
# DISPENSE is intentionally NOT handled here.
# Medicine dispensing has its own patient-linked endpoint.
# =========================================================

@router.post(
    "/medicines/{medicine_id}/transactions",
    response_model=InventoryTransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_inventory_transaction(
    medicine_id: int,
    data: InventoryTransactionCreate,
    request: Request,
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
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Medicine not found",
        )

    ip_address = (
        request.client.host
        if request.client
        else None
    )

    try:
        return create_inventory_transaction(
            db=db,
            medicine=medicine,
            data=data,
            current_user=current_user,
            ip_address=ip_address,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        )


# =========================================================
# LIST MEDICINE DISPENSING HISTORY
# =========================================================

@router.get(
    "/dispensings",
    response_model=list[
        MedicineDispensingResponse
    ],
)
def list_medicine_dispensings(
    patient_id: int | None = Query(
        default=None,
    ),
    medicine_id: int | None = Query(
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
    return get_medicine_dispensings(
        db=db,
        patient_id=patient_id,
        medicine_id=medicine_id,
    )


# =========================================================
# DISPENSE FREE MEDICINE
#
# IMPORTANT:
# This uses MEDICINE_DISPENSE instead of INVENTORY_ADJUST.
# =========================================================

@router.post(
    "/dispensings",
    response_model=MedicineDispensingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_medicine_dispensing(
    data: MedicineDispensingCreate,
    request: Request,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "MEDICINE_DISPENSE"
        )
    ),
):
    ip_address = (
        request.client.host
        if request.client
        else None
    )

    try:
        return dispense_medicine(
            db=db,
            data=data,
            current_user=current_user,
            ip_address=ip_address,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        )