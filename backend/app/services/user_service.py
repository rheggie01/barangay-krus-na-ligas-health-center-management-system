from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.consultation import Consultation
from app.models.consultation_medicine import ConsultationMedicine
from app.models.disease_case import DiseaseCase
from app.models.inventory_transaction import InventoryTransaction
from app.models.patient_history import PatientMedicalHistory
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.actor_snapshot_service import snapshot_user


ACCOUNT_PENDING = "PENDING"
ACCOUNT_ACTIVE = "ACTIVE"
ACCOUNT_INACTIVE = "INACTIVE"

VALID_ACCOUNT_STATUSES = {
    ACCOUNT_PENDING,
    ACCOUNT_ACTIVE,
    ACCOUNT_INACTIVE,
}


def get_users(db: Session) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .options(selectinload(User.roles))
            .where(User.is_deleted.is_(False))
            .order_by(User.id.asc())
        ).all()
    )


def get_user_by_id(
    db: Session,
    user_id: int,
    *,
    include_deleted: bool = False,
) -> User | None:
    statement = (
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )

    if not include_deleted:
        statement = statement.where(
            User.is_deleted.is_(False)
        )

    return db.scalar(statement)


def create_user(
    db: Session,
    data: UserCreate,
    commit: bool = True,
) -> User:
    username = data.username.strip()
    email = str(data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(
            or_(
                User.username == username,
                User.email == email,
            )
        )
    )

    if existing_user:
        raise ValueError("Username or email already exists.")

    requested_roles = set(data.role_names)

    roles = list(
        db.scalars(
            select(Role).where(
                Role.name.in_(requested_roles)
            )
        ).all()
    )

    found_roles = {role.name for role in roles}
    missing_roles = requested_roles - found_roles

    if missing_roles:
        raise ValueError(
            "Invalid role(s): "
            + ", ".join(sorted(missing_roles))
        )

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(data.password),
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        account_status=ACCOUNT_ACTIVE,
        is_active=True,
        is_deleted=False,
    )

    user.roles = roles
    db.add(user)

    if commit:
        db.commit()
        db.refresh(user)
    else:
        db.flush()

    return get_user_by_id(db, user.id)


def transition_user_account(
    db: Session,
    *,
    user: User,
    new_status: str,
    changed_by: User,
) -> User:
    target_status = str(new_status).strip().upper()

    if getattr(user, "is_deleted", False):
        raise ValueError(
            "Deleted staff accounts cannot be reactivated "
            "or changed."
        )

    if target_status not in VALID_ACCOUNT_STATUSES:
        raise ValueError("Invalid account status.")

    current_status = (
        user.account_status
        or (ACCOUNT_ACTIVE if user.is_active else ACCOUNT_PENDING)
    )

    allowed_transitions = {
        (ACCOUNT_PENDING, ACCOUNT_ACTIVE),
        (ACCOUNT_ACTIVE, ACCOUNT_INACTIVE),
        (ACCOUNT_INACTIVE, ACCOUNT_ACTIVE),
    }

    if (current_status, target_status) not in allowed_transitions:
        if current_status == target_status:
            return user

        raise ValueError(
            "Invalid account lifecycle transition: "
            f"{current_status} -> {target_status}."
        )

    actor = snapshot_user(changed_by)

    user.account_status = target_status
    user.is_active = target_status == ACCOUNT_ACTIVE
    user.status_changed_at = datetime.now()
    user.status_changed_by = changed_by.id
    user.status_changed_by_name_snapshot = actor["display_name"]
    user.status_changed_by_role_snapshot = actor["role_names"]

    db.flush()
    return user


def soft_delete_inactive_user(
    db: Session,
    *,
    user: User,
    deleted_by: User,
) -> User:
    if user.id == deleted_by.id:
        raise ValueError(
            "You cannot delete your own account."
        )

    if getattr(user, "is_deleted", False):
        raise ValueError(
            "This staff account has already been deleted."
        )

    status_value = (
        user.account_status
        or (
            ACCOUNT_ACTIVE
            if user.is_active
            else ACCOUNT_PENDING
        )
    )

    if (
        status_value != ACCOUNT_INACTIVE
        or user.is_active
    ):
        raise ValueError(
            "Only INACTIVE staff accounts can be deleted. "
            "Deactivate the account first."
        )

    user.is_deleted = True
    user.deleted_at = datetime.now()
    user.deleted_by = deleted_by.id
    user.account_status = ACCOUNT_INACTIVE
    user.is_active = False

    db.flush()
    return user


def get_user_reference_counts(
    db: Session,
    user_id: int,
) -> dict[str, int]:
    def count_for(model, *criteria) -> int:
        return int(
            db.scalar(
                select(func.count())
                .select_from(model)
                .where(*criteria)
            )
            or 0
        )

    return {
        "consultations":
            count_for(
                Consultation,
                Consultation.recorded_by == user_id,
            ),

        "consultation_medicines":
            count_for(
                ConsultationMedicine,
                ConsultationMedicine.dispensed_by == user_id,
            ),

        "inventory_transactions":
            count_for(
                InventoryTransaction,
                InventoryTransaction.recorded_by == user_id,
            ),

        "disease_cases_recorded":
            count_for(
                DiseaseCase,
                DiseaseCase.recorded_by == user_id,
            ),

        "disease_cases_validated":
            count_for(
                DiseaseCase,
                DiseaseCase.validated_by == user_id,
            ),

        "patient_histories":
            count_for(
                PatientMedicalHistory,
                PatientMedicalHistory.recorded_by == user_id,
            ),

        "audit_logs_as_actor":
            count_for(
                AuditLog,
                AuditLog.user_id == user_id,
            ),
    }


def delete_pending_user(db: Session, user: User) -> None:
    status_value = (
        user.account_status
        or (ACCOUNT_ACTIVE if user.is_active else ACCOUNT_PENDING)
    )

    if status_value != ACCOUNT_PENDING:
        raise ValueError(
            "Only never-approved PENDING account requests can be "
            "permanently deleted. Approved staff accounts must "
            "be deactivated instead."
        )

    references = get_user_reference_counts(db, user.id)

    blocking = {
        key: value
        for key, value in references.items()
        if value > 0
    }

    if blocking:
        details = ", ".join(
            f"{key}={value}"
            for key, value in blocking.items()
        )

        raise ValueError(
            "This account request has linked operational/audit "
            "records and cannot be hard-deleted. "
            f"References: {details}."
        )

    db.delete(user)
    db.flush()
