from datetime import datetime

from pydantic import BaseModel, Field


class PatientHistoryCreate(BaseModel):
    history_type: str = Field(
        min_length=1,
        max_length=50,
    )
    description: str = Field(
        min_length=1,
    )


class PatientHistoryResponse(BaseModel):
    id: int
    patient_id: int
    history_type: str
    description: str
    recorded_by: int | None
    recorded_at: datetime