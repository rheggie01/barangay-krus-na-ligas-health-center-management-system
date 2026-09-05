from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_db,
)
from app.models.user import User
from app.schemas.backup_recovery import (
    BackupRecoveryStatus,
)
from app.services.audit_log_service import (
    create_audit_log,
    get_request_ip,
)
from app.services.backup_recovery_service import (
    get_backup_recovery_status,
    run_backup_now,
    run_restore_test,
)


router = APIRouter()

VIEW_ROLES = {
    "SYSTEM_ADMIN",
    "HEALTH_CENTER_ADMIN",
}

ACTION_ROLES = {
    "SYSTEM_ADMIN",
}


def _role_names(
    user: User,
) -> set[str]:
    return {
        role.name
        for role in user.roles
    }


def _require_view_access(
    user: User,
) -> None:
    if not (
        _role_names(user)
        & VIEW_ROLES
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Backup and recovery status "
                "is restricted to authorized "
                "administrative roles."
            ),
        )


def _require_action_access(
    user: User,
) -> None:
    if not (
        _role_names(user)
        & ACTION_ROLES
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Only the System Administrator "
                "may run backup or restore-test "
                "operations."
            ),
        )


@router.get(
    "/status",
    response_model=BackupRecoveryStatus,
)
def backup_recovery_status(
    current_user: User = Depends(
        get_current_user
    ),
):
    _require_view_access(
        current_user
    )

    can_run = bool(
        _role_names(current_user)
        & ACTION_ROLES
    )

    return get_backup_recovery_status(
        viewer_can_run_actions=can_run,
    )


@router.post(
    "/run-backup",
)
def run_backup(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    _require_action_access(
        current_user
    )

    try:
        result = run_backup_now()

        create_audit_log(
            db,
            action="BACKUP_RUN_MANUAL",
            module="BACKUP_RECOVERY",
            user=current_user,
            subject_label_snapshot=(
                "Database Backup"
            ),
            description=(
                "System Administrator manually "
                "ran the database backup."
            ),
            ip_address=get_request_ip(
                request
            ),
        )

        db.commit()
        return result

    except Exception as exc:
        db.rollback()

        try:
            create_audit_log(
                db,
                action=(
                    "BACKUP_RUN_MANUAL_FAILED"
                ),
                module="BACKUP_RECOVERY",
                user=current_user,
                subject_label_snapshot=(
                    "Database Backup"
                ),
                description=(
                    "Manual database backup "
                    f"failed: {str(exc)[:500]}"
                ),
                ip_address=get_request_ip(
                    request
                ),
            )
            db.commit()
        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post(
    "/run-restore-test",
)
def run_restore_verification(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    _require_action_access(
        current_user
    )

    try:
        result = run_restore_test()

        create_audit_log(
            db,
            action="BACKUP_RESTORE_TEST",
            module="BACKUP_RECOVERY",
            user=current_user,
            subject_label_snapshot=(
                "Backup Restore Verification"
            ),
            description=(
                "System Administrator ran a "
                "temporary backup restore "
                "verification test."
            ),
            ip_address=get_request_ip(
                request
            ),
        )

        db.commit()
        return result

    except Exception as exc:
        db.rollback()

        try:
            create_audit_log(
                db,
                action=(
                    "BACKUP_RESTORE_TEST_FAILED"
                ),
                module="BACKUP_RECOVERY",
                user=current_user,
                subject_label_snapshot=(
                    "Backup Restore Verification"
                ),
                description=(
                    "Backup restore verification "
                    f"failed: {str(exc)[:500]}"
                ),
                ip_address=get_request_ip(
                    request
                ),
            )
            db.commit()
        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
