from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


# =========================================================
# ALLOWED VALUES
# =========================================================

CaseStatus = Literal[
    "SUSPECTED",
    "PROBABLE",
    "CONFIRMED",
]

ValidationStatus = Literal[
    "PENDING",
    "VALIDATED",
    "REJECTED",
]


# =========================================================
# CREATE DISEASE CASE
# =========================================================

class DiseaseCaseCreate(BaseModel):
    disease_id: int = Field(
        gt=0,
    )

    case_status: CaseStatus = (
        "SUSPECTED"
    )

    onset_date: date | None = None

    remarks: str | None = None


    @field_validator("remarks")
    @classmethod
    def clean_remarks(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


# =========================================================
# UPDATE DISEASE CASE
# =========================================================

class DiseaseCaseUpdate(BaseModel):
    disease_id: int | None = Field(
        default=None,
        gt=0,
    )

    case_status: CaseStatus | None = None

    onset_date: date | None = None

    remarks: str | None = None


    @field_validator("remarks")
    @classmethod
    def clean_remarks(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


# =========================================================
# VALIDATE DISEASE CASE
# =========================================================

class DiseaseCaseValidationUpdate(
    BaseModel
):
    validation_status: (
        ValidationStatus
    )


# =========================================================
# RESPONSE
# =========================================================

class DiseaseCaseResponse(BaseModel):
    id: int

    patient_id: int
    consultation_id: int
    disease_id: int

    case_status: str

    onset_date: date | None
    case_date: date

    remarks: str | None

    validation_status: str

    validated_by: int | None
    validated_at: datetime | None

    recorded_by: int | None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }