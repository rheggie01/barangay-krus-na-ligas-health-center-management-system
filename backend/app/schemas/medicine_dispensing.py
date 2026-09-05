from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


StockUnit = Literal["PACKAGE", "LOOSE"]


class MedicineDispensingCreate(BaseModel):
    patient_id: int = Field(gt=0)
    medicine_id: int = Field(gt=0)

    consultation_id: int | None = Field(
        default=None,
        gt=0,
    )

    quantity: int = Field(gt=0)

    # The user may dispense either whole packages
    # or loose dispensing units such as tablets/capsules.
    stock_unit: StockUnit = "LOOSE"

    distribution_type: Literal["FREE"] = "FREE"

    program_name: str = Field(
        min_length=1,
        max_length=100,
    )

    purpose: str = Field(
        min_length=1,
        max_length=255,
    )

    notes: str | None = None


class MedicineDispensingResponse(BaseModel):
    id: int
    dispensing_code: str

    patient_id: int
    medicine_id: int
    consultation_id: int | None

    quantity: int
    dispensing_unit: str

    distribution_type: str

    program_name: str
    purpose: str
    notes: str | None

    # For PACKAGE dispensing, these values represent
    # package stock before/after.
    #
    # For LOOSE dispensing, these values represent
    # available dispensing units before/after.
    previous_total_units: int
    new_total_units: int

    patient_code: str
    patient_name: str

    medicine_code: str
    medicine_name: str

    dispensed_by: int
    dispensed_by_name: str | None
    dispensed_by_role_names: str | None

    dispensed_at: datetime

    model_config = {
        "from_attributes": True,
    }
