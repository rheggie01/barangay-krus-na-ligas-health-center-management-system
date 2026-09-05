from datetime import date, datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# =========================================================
# ALLOWED VALUES
# =========================================================

SexValue = Literal[
    "Male",
    "Female",
]


CivilStatusValue = Literal[
    "Single",
    "Married",
    "Widowed",
    "Separated",
]


RecordStatusValue = Literal[
    "ACTIVE",
    "INACTIVE",
]


SuffixValue = Literal[
    "Jr.",
    "Sr.",
    "II",
    "III",
    "IV",
    "V",
]


# =========================================================
# BASE PATIENT SCHEMA
# =========================================================

class PatientBase(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    middle_name: str | None = Field(
        default=None,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    suffix: SuffixValue | None = None

    date_of_birth: date

    sex: SexValue

    civil_status: CivilStatusValue | None = None

    # Boolean category flag used by the Patient Records PWD filter.
    # No disability diagnosis/details are stored here.
    is_pwd: bool = False

    street: str | None = Field(
        default=None,
        max_length=150,
    )

    barangay: str | None = Field(
        default=None,
        max_length=150,
    )

    city: str | None = Field(
        default=None,
        max_length=150,
    )

    address: str = Field(
        min_length=1,
    )

    contact_number: str | None = Field(
        default=None,
        max_length=30,
    )

    emergency_contact_name: str | None = Field(
        default=None,
        max_length=150,
    )

    emergency_contact_number: str | None = Field(
        default=None,
        max_length=30,
    )


    # =====================================================
    # CLEAN TEXT
    # =====================================================

    @field_validator(
        "first_name",
        "middle_name",
        "last_name",
        "street",
        "barangay",
        "city",
        "address",
        "contact_number",
        "emergency_contact_name",
        "emergency_contact_number",
        mode="before",
    )
    @classmethod
    def clean_text(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        cleaned = value.strip()

        return cleaned or None


    # =====================================================
    # DATE VALIDATION
    # =====================================================

    @field_validator(
        "date_of_birth"
    )
    @classmethod
    def validate_date_of_birth(
        cls,
        value: date,
    ) -> date:
        if value > date.today():
            raise ValueError(
                "Date of birth cannot be in the future."
            )

        return value


# =========================================================
# CREATE PATIENT
# =========================================================

class PatientCreate(PatientBase):
    pass


# =========================================================
# UPDATE PATIENT
# =========================================================

class PatientUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    middle_name: str | None = Field(
        default=None,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    suffix: SuffixValue | None = None

    date_of_birth: date | None = None

    sex: SexValue | None = None

    civil_status: CivilStatusValue | None = None

    is_pwd: bool | None = None

    street: str | None = Field(
        default=None,
        max_length=150,
    )

    barangay: str | None = Field(
        default=None,
        max_length=150,
    )

    city: str | None = Field(
        default=None,
        max_length=150,
    )

    address: str | None = None

    contact_number: str | None = Field(
        default=None,
        max_length=30,
    )

    emergency_contact_name: str | None = Field(
        default=None,
        max_length=150,
    )

    emergency_contact_number: str | None = Field(
        default=None,
        max_length=30,
    )

    record_status: RecordStatusValue | None = None


    @field_validator(
        "first_name",
        "middle_name",
        "last_name",
        "street",
        "barangay",
        "city",
        "address",
        "contact_number",
        "emergency_contact_name",
        "emergency_contact_number",
        mode="before",
    )
    @classmethod
    def clean_text(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        cleaned = value.strip()

        return cleaned or None


    @field_validator(
        "date_of_birth"
    )
    @classmethod
    def validate_date_of_birth(
        cls,
        value: date | None,
    ) -> date | None:
        if value is None:
            return None

        if value > date.today():
            raise ValueError(
                "Date of birth cannot be in the future."
            )

        return value


# =========================================================
# PATIENT RESPONSE
# =========================================================

class PatientResponse(PatientBase):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    patient_code: str

    record_status: RecordStatusValue

    created_at: datetime | None = None

    updated_at: datetime | None = None


# =========================================================
# OPTIONAL LIST RESPONSE
# =========================================================

class PatientListResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    patient_code: str

    first_name: str

    middle_name: str | None = None

    last_name: str

    suffix: SuffixValue | None = None

    date_of_birth: date

    sex: SexValue

    civil_status: CivilStatusValue | None = None

    is_pwd: bool = False

    street: str | None = None

    contact_number: str | None = None

    record_status: RecordStatusValue
