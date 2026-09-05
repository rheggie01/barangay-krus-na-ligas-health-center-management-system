from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


# =========================================================
# CREATE / DISPENSE MEDICINE
# =========================================================

class ConsultationMedicineCreate(BaseModel):
    medicine_id: int = Field(
        gt=0,
    )

    quantity: int = Field(
        gt=0,
    )

    stock_unit: Literal[
        "PACKAGE",
        "LOOSE",
    ] = "LOOSE"

    dosage_instruction: str | None = Field(
        default=None,
        max_length=255,
    )

    remarks: str | None = None


    @field_validator(
        "dosage_instruction",
        "remarks",
    )
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


# =========================================================
# RESPONSE
# =========================================================

class ConsultationMedicineResponse(BaseModel):
    id: int

    consultation_id: int
    medicine_id: int

    quantity: int
    stock_unit: Literal[
        "PACKAGE",
        "LOOSE",
    ]

    dosage_instruction: str | None = None
    remarks: str | None = None

    dispensed_by: int | None = None
    dispensed_at: datetime

    model_config = {
        "from_attributes": True,
    }