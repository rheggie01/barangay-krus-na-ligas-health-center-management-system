from sqlalchemy import select
from sqlalchemy.orm import (
    Session,
    selectinload,
)

from app.models.inventory_transaction import (
    InventoryTransaction,
)
from app.models.medicine import Medicine
from app.models.user import User
from app.schemas.inventory_transaction import (
    InventoryTransactionCreate,
)
from app.services.actor_snapshot_service import snapshot_user
from app.services.audit_log_service import create_audit_log


# =========================================================
# MANUAL INVENTORY TRANSACTION TYPES
#
# DISPENSE is intentionally excluded.
# Medicine dispensing must use the dedicated
# patient-linked dispensing workflow.
# =========================================================

VALID_TRANSACTION_TYPES = {
    "STOCK_IN",
    "ADJUSTMENT_IN",
    "ADJUSTMENT_OUT",
}


VALID_STOCK_UNITS = {
    "PACKAGE",
    "LOOSE",
}


# =========================================================
# LIST TRANSACTIONS
# =========================================================

def get_inventory_transactions(
    db: Session,
    medicine_id: int | None = None,
):
    statement = (
        select(
            InventoryTransaction
        )
        .options(
            selectinload(
                InventoryTransaction.recorded_by_user
            ).selectinload(
                User.roles
            )
        )
    )

    if medicine_id is not None:
        statement = statement.where(
            InventoryTransaction.medicine_id
            == medicine_id
        )

    statement = statement.order_by(
        InventoryTransaction.created_at.desc()
    )

    return db.scalars(
        statement
    ).all()


# =========================================================
# CREATE MANUAL INVENTORY TRANSACTION
# =========================================================

def create_inventory_transaction(
    db: Session,
    medicine: Medicine,
    data: InventoryTransactionCreate,
    current_user: User,
    ip_address: str | None = None,
):
    transaction_type = (
        data.transaction_type
        .strip()
        .upper()
    )

    stock_unit = (
        data.stock_unit
        .strip()
        .upper()
    )

    # -----------------------------------------------------
    # VALIDATE TYPE
    # -----------------------------------------------------

    if (
        transaction_type
        not in VALID_TRANSACTION_TYPES
    ):
        raise ValueError(
            "Invalid inventory transaction type."
        )

    # -----------------------------------------------------
    # VALIDATE UNIT
    # -----------------------------------------------------

    if (
        stock_unit
        not in VALID_STOCK_UNITS
    ):
        raise ValueError(
            "Invalid stock unit."
        )

    # -----------------------------------------------------
    # REQUIRE REASON FOR OUTGOING ADJUSTMENT
    # -----------------------------------------------------

    if (
        transaction_type
        == "ADJUSTMENT_OUT"
        and not (
            data.reason
            and data.reason.strip()
        )
    ):
        raise ValueError(
            "A reason is required for Adjustment Out."
        )

    # -----------------------------------------------------
    # STOCK SNAPSHOT BEFORE
    # -----------------------------------------------------

    previous_total_units = (
        medicine.total_units
    )

    # -----------------------------------------------------
    # MOVEMENT TYPE
    # -----------------------------------------------------

    is_addition = (
        transaction_type
        in {
            "STOCK_IN",
            "ADJUSTMENT_IN",
        }
    )

    is_deduction = (
        transaction_type
        == "ADJUSTMENT_OUT"
    )

    # -----------------------------------------------------
    # PACKAGE STOCK
    # -----------------------------------------------------

    if stock_unit == "PACKAGE":
        current_stock = (
            medicine.package_stock
        )

        if (
            is_deduction
            and data.quantity
            > current_stock
        ):
            raise ValueError(
                "Insufficient package stock."
            )

        if is_addition:
            medicine.package_stock += (
                data.quantity
            )

        if is_deduction:
            medicine.package_stock -= (
                data.quantity
            )

    # -----------------------------------------------------
    # LOOSE STOCK
    # -----------------------------------------------------

    else:
        current_stock = (
            medicine.loose_stock
        )

        if (
            is_deduction
            and data.quantity
            > current_stock
        ):
            raise ValueError(
                "Insufficient loose stock."
            )

        if is_addition:
            medicine.loose_stock += (
                data.quantity
            )

        if is_deduction:
            medicine.loose_stock -= (
                data.quantity
            )

    # -----------------------------------------------------
    # STOCK SNAPSHOT AFTER
    # -----------------------------------------------------

    new_total_units = (
        medicine.total_units
    )

    # -----------------------------------------------------
    # ACTOR SNAPSHOT
    # -----------------------------------------------------

    actor = snapshot_user(
        current_user
    )

    # -----------------------------------------------------
    # INVENTORY TRANSACTION
    # -----------------------------------------------------

    transaction = InventoryTransaction(
        medicine_id=medicine.id,

        transaction_type=transaction_type,

        quantity=data.quantity,

        stock_unit=stock_unit,

        previous_total_units=(
            previous_total_units
        ),

        new_total_units=(
            new_total_units
        ),

        reference=data.reference,

        reason=data.reason,

        notes=data.notes,

        # Backend-authoritative audit identity:
        # always use the authenticated user.
        recorded_by=current_user.id,

        recorded_by_name_snapshot=(
            actor["display_name"]
        ),

        recorded_by_role_snapshot=(
            actor["role_names"]
        ),
    )

    db.add(
        transaction
    )

    # -----------------------------------------------------
    # FLUSH SO TRANSACTION GETS AN ID
    # -----------------------------------------------------

    db.flush()

    # -----------------------------------------------------
    # AUDIT LOG
    # -----------------------------------------------------

    create_audit_log(
        db,
        action=f"INVENTORY_{transaction_type}",
        module="INVENTORY",
        user=current_user,
        record_id=transaction.id,
        subject_label_snapshot=(
            f"{medicine.code} | {medicine.name}"
        ),
        description=(
            f"{transaction_type} for "
            f"{medicine.name} ({medicine.code}), "
            f"quantity {data.quantity} {stock_unit}. "
            f"Total stock changed from "
            f"{previous_total_units} to {new_total_units}."
        ),
        ip_address=ip_address,
    )

    # -----------------------------------------------------
    # ONE COMMIT
    # -----------------------------------------------------

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(
        transaction
    )

    db.refresh(
        medicine
    )

    return transaction


# =========================================================
# USER ROLE NAMES
# =========================================================

def get_role_names(
    user: User,
) -> str | None:
    role_names = []

    for role in (
        getattr(
            user,
            "roles",
            [],
        )
        or []
    ):
        value = (
            getattr(
                role,
                "name",
                None,
            )
            or getattr(
                role,
                "code",
                None,
            )
        )

        if value:
            role_names.append(
                str(value)
            )

    if not role_names:
        return None

    return ", ".join(
        sorted(
            set(role_names)
        )
    )
