from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
)


# =========================================================
# BASE DISEASE FIELDS
# =========================================================

class DiseaseBase(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=50,
    )

    name: str = Field(
        min_length=1,
        max_length=150,
    )

    category: str | None = Field(
        default=None,
        max_length=100,
    )

    transmission_type: str | None = Field(
        default=None,
        max_length=100,
    )

    description: str | None = None

    is_communicable: bool = False
    is_reportable: bool = False
    is_sensitive: bool = False

    privacy_category: str = Field(
        default="STANDARD",
        max_length=50,
    )


# =========================================================
# CREATE DISEASE
# =========================================================

class DiseaseCreate(DiseaseBase):
    pass


# =========================================================
# UPDATE DISEASE
# =========================================================

class DiseaseUpdate(BaseModel):
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

    category: str | None = Field(
        default=None,
        max_length=100,
    )

    transmission_type: str | None = Field(
        default=None,
        max_length=100,
    )

    description: str | None = None

    is_communicable: bool | None = None
    is_reportable: bool | None = None
    is_sensitive: bool | None = None

    privacy_category: str | None = Field(
        default=None,
        max_length=50,
    )

    is_active: bool | None = None


# =========================================================
# DISEASE RESPONSE
# =========================================================

class DiseaseResponse(DiseaseBase):
    id: int

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }