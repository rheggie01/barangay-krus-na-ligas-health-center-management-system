from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    actor_name_snapshot: str | None = None
    role_names: str | None
    action: str
    module: str
    record_id: int | None
    subject_label_snapshot: str | None = None
    description: str
    ip_address: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
