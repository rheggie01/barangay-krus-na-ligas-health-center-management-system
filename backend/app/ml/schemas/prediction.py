from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class DiseasePredictionRequest(BaseModel):
    patient_id: int = Field(gt=0)

    symptom_codes: list[str] = Field(
        min_length=1,
    )

    temperature: float | None = Field(
        default=None,
        ge=30.0,
        le=45.0,
    )

    heart_rate: int | None = Field(
        default=None,
        ge=20,
        le=250,
    )

    respiratory_rate: int | None = Field(
        default=None,
        ge=5,
        le=80,
    )

    oxygen_saturation: float | None = Field(
        default=None,
        ge=50.0,
        le=100.0,
    )

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

        if not normalized:
            raise ValueError(
                "At least one structured "
                "symptom is required."
            )

        return normalized


class DiseaseProbability(BaseModel):
    disease_code: str
    disease_name: str
    probability: float


class DiseasePredictionResponse(BaseModel):
    patient_id: int

    age: int
    sex: str

    predicted_disease_code: str
    predicted_disease_name: str
    top_probability: float

    probabilities: list[DiseaseProbability]

    selected_model: str
    development_status: str

    input_warnings: list[str]

    decision_support_notice: str


class DiseasePredictionLogResponse(BaseModel):
    id: int

    consultation_id: int
    patient_id: int

    performed_by: int | None
    performed_by_name: str | None

    model_name: str

    predicted_disease_code: str
    predicted_disease_name: str
    top_probability: float

    probabilities: list[DiseaseProbability]

    age: int
    sex: str

    symptom_codes: list[str]

    temperature: float | None
    heart_rate: int | None
    respiratory_rate: int | None
    oxygen_saturation: float | None

    development_status: str
    decision_support_notice: str

    created_at: datetime
