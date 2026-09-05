from datetime import datetime

from pydantic import BaseModel, Field


class InventoryTransactionCreate(BaseModel):
    transaction_type: str

    quantity: int = Field(
        gt=0,
    )

    stock_unit: str

    reference: str | None = None
    reason: str | None = None
    notes: str | None = None


class InventoryTransactionResponse(BaseModel):
    id: int
    medicine_id: int

    transaction_type: str
    quantity: int
    stock_unit: str

    reference: str | None
    reason: str | None
    notes: str | None

    recorded_by: int | None

    recorded_by_name_snapshot: str | None = None
    recorded_by_role_snapshot: str | None = None

    # Human-readable audit identity exposed from the existing
    # recorded_by -> users.id relationship.
    recorded_by_name: str | None = None
    recorded_by_role_names: str | None = None

    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
