from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


class ConsultationCreate(BaseModel):
    disease_id: int | None = Field(default=None, gt=0)

    chief_complaint: str = Field(min_length=1)

    symptoms: str | None = None

    symptom_codes: list[str] = Field(
        default_factory=list,
    )

    # True only when the current ML preview is still valid.
    # The backend will create the consultation and persistent
    # ML analysis in one transaction.
    run_ml_analysis: bool = False

    temperature: float | None = None

    systolic_bp: int | None = None
    diastolic_bp: int | None = None

    heart_rate: int | None = None
    respiratory_rate: int | None = None

    oxygen_saturation: float | None = None

    weight_kg: float | None = None
    height_cm: float | None = None

    assessment: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    notes: str | None = None

    @field_validator(
        "symptoms",
        "assessment",
        "diagnosis",
        "treatment_plan",
        "notes",
    )
    @classmethod
    def clean_optional_text_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _clean_optional_text(value)

    @field_validator("symptom_codes")
    @classmethod
    def normalize_symptom_codes(
        cls,
        values: list[str],
    ) -> list[str]:
        normalized: list[str] = []

        for value in values:
            code = str(value).strip().upper()

            if code and code not in normalized:
                normalized.append(code)

        return normalized


class ConsultationUpdate(BaseModel):
    disease_id: int | None = Field(default=None, gt=0)

    chief_complaint: str | None = None

    symptoms: str | None = None
    symptom_codes: list[str] | None = None

    temperature: float | None = None

    systolic_bp: int | None = None
    diastolic_bp: int | None = None

    heart_rate: int | None = None
    respiratory_rate: int | None = None

    oxygen_saturation: float | None = None

    weight_kg: float | None = None
    height_cm: float | None = None

    assessment: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    notes: str | None = None

    @field_validator(
        "symptoms",
        "assessment",
        "diagnosis",
        "treatment_plan",
        "notes",
    )
    @classmethod
    def clean_optional_text_fields(
        cls,
        value: str | None,
    ) -> str | None:
        return _clean_optional_text(value)

    @field_validator("symptom_codes")
    @classmethod
    def normalize_symptom_codes(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None

        normalized: list[str] = []

        for value in values:
            code = str(value).strip().upper()

            if code and code not in normalized:
                normalized.append(code)

        return normalized


class ConsultationResponse(BaseModel):
    id: int
    patient_id: int
    disease_id: int | None

    consultation_date: datetime

    chief_complaint: str
    symptoms: str | None

    symptom_codes: list[str] = Field(
        default_factory=list,
    )

    temperature: float | None

    systolic_bp: int | None
    diastolic_bp: int | None

    heart_rate: int | None
    respiratory_rate: int | None

    oxygen_saturation: float | None

    weight_kg: float | None
    height_cm: float | None

    assessment: str | None
    diagnosis: str | None
    treatment_plan: str | None
    notes: str | None

    recorded_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
