from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.actor_snapshot_service import snapshot_user


def get_request_ip(request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None


def create_audit_log(
    db: Session,
    *,
    action: str,
    module: str,
    description: str,
    user: User | None = None,
    record_id: int | None = None,
    subject_label_snapshot: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    actor = snapshot_user(user)

    audit_log = AuditLog(
        user_id=actor["user_id"],
        actor_username_snapshot=actor["username"],
        actor_name_snapshot=actor["display_name"],
        role_names=actor["role_names"],
        action=action,
        module=module,
        record_id=record_id,
        subject_label_snapshot=subject_label_snapshot,
        description=description,
        ip_address=ip_address,
    )

    db.add(audit_log)
    db.flush()
    return audit_log


def get_audit_logs(
    db: Session,
    *,
    module: str | None = None,
    action: str | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    query = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(limit)
    )

    if module:
        query = query.where(AuditLog.module == module)

    if action:
        query = query.where(AuditLog.action == action)

    return list(db.scalars(query).all())
