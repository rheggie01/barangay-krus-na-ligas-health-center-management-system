from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_permission
from app.models.role import Role
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserStatusUpdate,
)
from app.services.audit_log_service import (
    create_audit_log,
    get_request_ip,
)
from app.services.user_service import (
    ACCOUNT_ACTIVE,
    ACCOUNT_INACTIVE,
    ACCOUNT_PENDING,
    create_user,
    delete_pending_user,
    get_user_by_id,
    get_users,
    soft_delete_inactive_user,
    transition_user_account,
)


router = APIRouter()


def user_to_response(user: User) -> UserResponse:
    account_status = (
        user.account_status
        or (ACCOUNT_ACTIVE if user.is_active else ACCOUNT_PENDING)
    )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        account_status=account_status,
        is_active=user.is_active,
        is_deleted=getattr(user, "is_deleted", False),
        deleted_at=getattr(user, "deleted_at", None),
        deleted_by=getattr(user, "deleted_by", None),
        status_changed_at=user.status_changed_at,
        status_changed_by=user.status_changed_by,
        status_changed_by_name_snapshot=(
            user.status_changed_by_name_snapshot
        ),
        status_changed_by_role_snapshot=(
            user.status_changed_by_role_snapshot
        ),
        roles=[role.name for role in user.roles],
    )


def _require_target_user(db: Session, user_id: int) -> User:
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


def _protect_last_system_admin(
    db: Session,
    user: User,
) -> None:
    is_system_admin = any(
        role.name == "SYSTEM_ADMIN"
        for role in user.roles
    )

    if not is_system_admin:
        return

    active_system_admins = (
        db.scalar(
            select(func.count(User.id))
            .join(User.roles)
            .where(
                User.account_status == ACCOUNT_ACTIVE,
                User.is_active.is_(True),
                Role.name == "SYSTEM_ADMIN",
            )
        )
        or 0
    )

    if active_system_admins <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The last active System Administrator "
                "cannot be deactivated."
            ),
        )


def _protect_last_remaining_system_admin(
    db: Session,
    user: User,
) -> None:
    is_system_admin = any(
        role.name == "SYSTEM_ADMIN"
        for role in user.roles
    )

    if not is_system_admin:
        return

    filters = [
        Role.name == "SYSTEM_ADMIN",
    ]

    is_deleted_column = getattr(
        User,
        "is_deleted",
        None,
    )

    if is_deleted_column is not None:
        filters.insert(
            0,
            is_deleted_column.is_(False),
        )

    remaining_system_admins = (
        db.scalar(
            select(func.count(User.id))
            .join(User.roles)
            .where(*filters)
        )
        or 0
    )

    if remaining_system_admins <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The last remaining System Administrator "
                "account cannot be deleted."
            ),
        )


def _commit_and_reload(
    db: Session,
    user: User,
) -> UserResponse:
    db.commit()
    refreshed = get_user_by_id(db, user.id)
    return user_to_response(refreshed)


@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    return [
        user_to_response(user)
        for user in get_users(db)
    ]


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_user(
    data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    try:
        user = create_user(db, data, commit=False)

        create_audit_log(
            db,
            action="USER_CREATE",
            module="ADMINISTRATION",
            user=current_user,
            record_id=user.id,
            subject_label_snapshot=f"@{user.username}",
            description=(
                "Created ACTIVE user account "
                f"{user.username}."
            ),
            ip_address=get_request_ip(request),
        )

        return _commit_and_reload(db, user)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/{user_id}/approve",
    response_model=UserResponse,
)
def approve_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    user = _require_target_user(db, user_id)

    try:
        transition_user_account(
            db,
            user=user,
            new_status=ACCOUNT_ACTIVE,
            changed_by=current_user,
        )

        create_audit_log(
            db,
            action="USER_APPROVE",
            module="ADMINISTRATION",
            user=current_user,
            record_id=user.id,
            subject_label_snapshot=f"@{user.username}",
            description=(
                "Approved pending account "
                f"{user.username}."
            ),
            ip_address=get_request_ip(request),
        )

        return _commit_and_reload(db, user)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
)
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    user = _require_target_user(db, user_id)

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )

    _protect_last_system_admin(db, user)

    try:
        transition_user_account(
            db,
            user=user,
            new_status=ACCOUNT_INACTIVE,
            changed_by=current_user,
        )

        create_audit_log(
            db,
            action="USER_DEACTIVATE",
            module="ADMINISTRATION",
            user=current_user,
            record_id=user.id,
            subject_label_snapshot=f"@{user.username}",
            description=(
                "Deactivated previously approved account "
                f"{user.username}. Historical clinical, "
                "inventory, dispensing, and audit records "
                "were preserved."
            ),
            ip_address=get_request_ip(request),
        )

        return _commit_and_reload(db, user)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/{user_id}/reactivate",
    response_model=UserResponse,
)
def reactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    user = _require_target_user(db, user_id)

    try:
        transition_user_account(
            db,
            user=user,
            new_status=ACCOUNT_ACTIVE,
            changed_by=current_user,
        )

        create_audit_log(
            db,
            action="USER_REACTIVATE",
            module="ADMINISTRATION",
            user=current_user,
            record_id=user.id,
            subject_label_snapshot=f"@{user.username}",
            description=(
                "Reactivated inactive account "
                f"{user.username}."
            ),
            ip_address=get_request_ip(request),
        )

        return _commit_and_reload(db, user)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_inactive_staff_account(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    user = _require_target_user(db, user_id)

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )

    _protect_last_remaining_system_admin(
        db,
        user,
    )

    username = user.username
    full_name = (
        f"{user.first_name} {user.last_name}".strip()
    )

    try:
        soft_delete_inactive_user(
            db,
            user=user,
            deleted_by=current_user,
        )

        create_audit_log(
            db,
            action="USER_SOFT_DELETE",
            module="ADMINISTRATION",
            user=current_user,
            record_id=user.id,
            subject_label_snapshot=(
                f"@{username} | {full_name}"
            ),
            description=(
                "Soft-deleted inactive staff account "
                f"@{username}. Historical clinical, "
                "inventory, dispensing, and audit records "
                "were preserved."
            ),
            ip_address=get_request_ip(request),
        )

        db.commit()

        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.delete(
    "/{user_id}/pending",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_pending_account_request(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    user = _require_target_user(db, user_id)

    username = user.username
    full_name = f"{user.first_name} {user.last_name}".strip()

    try:
        delete_pending_user(db, user)

        create_audit_log(
            db,
            action="USER_PENDING_DELETE",
            module="ADMINISTRATION",
            user=current_user,
            record_id=user_id,
            subject_label_snapshot=(
                f"@{username} | {full_name}"
            ),
            description=(
                "Permanently deleted never-approved "
                f"PENDING account request @{username}. "
                "No operational/audit actor references existed."
            ),
            ip_address=get_request_ip(request),
        )

        db.commit()
        return Response(
            status_code=status.HTTP_204_NO_CONTENT
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# Backward compatibility for older frontend/API clients.
@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    user = _require_target_user(db, user_id)

    current_status = (
        user.account_status
        or (ACCOUNT_ACTIVE if user.is_active else ACCOUNT_PENDING)
    )

    target_status = (
        ACCOUNT_ACTIVE
        if data.is_active
        else ACCOUNT_INACTIVE
    )

    if target_status == ACCOUNT_INACTIVE:
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account.",
            )

        _protect_last_system_admin(db, user)

    try:
        transition_user_account(
            db,
            user=user,
            new_status=target_status,
            changed_by=current_user,
        )

        action = (
            "USER_APPROVE"
            if (
                current_status == ACCOUNT_PENDING
                and target_status == ACCOUNT_ACTIVE
            )
            else (
                "USER_REACTIVATE"
                if target_status == ACCOUNT_ACTIVE
                else "USER_DEACTIVATE"
            )
        )

        create_audit_log(
            db,
            action=action,
            module="ADMINISTRATION",
            user=current_user,
            record_id=user.id,
            subject_label_snapshot=f"@{user.username}",
            description=(
                "Backward-compatible status transition "
                f"{current_status} -> {target_status} "
                f"for {user.username}."
            ),
            ip_address=get_request_ip(request),
        )

        return _commit_and_reload(db, user)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
