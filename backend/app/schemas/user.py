from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


AccountStatusValue = Literal["PENDING", "ACTIVE", "INACTIVE"]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role_names: list[str]


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str

    account_status: AccountStatusValue
    is_active: bool

    status_changed_at: datetime | None = None
    status_changed_by: int | None = None
    status_changed_by_name_snapshot: str | None = None
    status_changed_by_role_snapshot: str | None = None

    roles: list[str]


class UserStatusUpdate(BaseModel):
    is_active: bool
