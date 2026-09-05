from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_permission
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_log_service import get_audit_logs


router = APIRouter()


def audit_log_to_response(audit_log: AuditLog) -> AuditLogResponse:
    username = audit_log.actor_username_snapshot

    if not username and audit_log.user:
        username = audit_log.user.username

    return AuditLogResponse(
        id=audit_log.id,
        user_id=audit_log.user_id,
        username=username,
        actor_name_snapshot=audit_log.actor_name_snapshot,
        role_names=audit_log.role_names,
        action=audit_log.action,
        module=audit_log.module,
        record_id=audit_log.record_id,
        subject_label_snapshot=audit_log.subject_label_snapshot,
        description=audit_log.description,
        ip_address=audit_log.ip_address,
        created_at=audit_log.created_at,
    )


@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    module: str | None = None,
    action: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("AUDIT_VIEW")),
):
    audit_logs = get_audit_logs(
        db,
        module=module,
        action=action,
        limit=limit,
    )

    return [audit_log_to_response(item) for item in audit_logs]
