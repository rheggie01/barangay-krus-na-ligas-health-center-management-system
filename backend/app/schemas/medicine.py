from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MedicineCategory = Literal[
    "GENERAL",
    "ANTI_INFECTIVE",
    "ANTI_THROMBOTIC",
    "ANTI_ASTHMA_COPD",
    "SUPPORTIVE_OTHER",
    "ANTI_DIABETIC",
    "ANTI_DYSLIPIDEMIA",
    "ANTI_HYPERTENSIVE_CARDIOLOGY",
    "NERVOUS_SYSTEM",
    "SENSITIVE_PROGRAM",
]

FormularyStatus = Literal[
    "CANDIDATE",
    "VERIFIED",
    "NOT_STOCKED",
]

ProgramType = Literal[
    "TB",
    "HIV",
    "STI",
]


class MedicineCreate(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=50,
    )

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    generic_name: str | None = None
    dosage_strength: str | None = None
    dosage_form: str | None = None

    medicine_category: MedicineCategory = "GENERAL"
    formulary_status: FormularyStatus = "CANDIDATE"
    program_type: ProgramType | None = None

    requires_prescription: bool = False
    restricted_dispensing: bool = False
    sensitive_inventory: bool = False
    forecast_enabled: bool = True
    stock_verified: bool = False

    package_unit: str | None = None

    dispensing_unit: str = "piece"

    units_per_package: int | None = Field(
        default=None,
        gt=0,
    )

    package_stock: int = Field(
        default=0,
        ge=0,
    )

    loose_stock: int = Field(
        default=0,
        ge=0,
    )

    reorder_level: int = Field(
        default=10,
        ge=0,
    )

    is_active: bool = True


class MedicineUpdate(BaseModel):
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    generic_name: str | None = None
    dosage_strength: str | None = None
    dosage_form: str | None = None

    medicine_category: MedicineCategory | None = None
    formulary_status: FormularyStatus | None = None
    program_type: ProgramType | None = None

    requires_prescription: bool | None = None
    restricted_dispensing: bool | None = None
    sensitive_inventory: bool | None = None
    forecast_enabled: bool | None = None
    stock_verified: bool | None = None

    package_unit: str | None = None
    dispensing_unit: str | None = None

    units_per_package: int | None = Field(
        default=None,
        gt=0,
    )

    package_stock: int | None = Field(
        default=None,
        ge=0,
    )

    loose_stock: int | None = Field(
        default=None,
        ge=0,
    )

    reorder_level: int | None = Field(
        default=None,
        ge=0,
    )

    is_active: bool | None = None


class MedicineResponse(BaseModel):
    id: int

    code: str
    name: str

    generic_name: str | None
    dosage_strength: str | None
    dosage_form: str | None

    medicine_category: str
    formulary_status: str
    program_type: str | None

    requires_prescription: bool
    restricted_dispensing: bool
    sensitive_inventory: bool
    forecast_enabled: bool
    stock_verified: bool

    package_unit: str | None
    dispensing_unit: str

    units_per_package: int | None

    package_stock: int
    loose_stock: int

    reorder_level: int

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
