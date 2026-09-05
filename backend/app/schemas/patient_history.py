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
    recorded_by_name_snapshot: str | None = None
    recorded_by_role_snapshot: str | None = None

    recorded_at: datetime

    model_config = {
        "from_attributes": True,
    }