from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consultation import Consultation
from app.models.consultation_medicine import ConsultationMedicine
from app.models.inventory_transaction import InventoryTransaction
from app.models.medicine import Medicine
from app.schemas.consultation_medicine import (
    ConsultationMedicineCreate,
)


VALID_STOCK_UNITS = {
    "PACKAGE",
    "LOOSE",
}


# =========================================================
# GET DISPENSED MEDICINES
# =========================================================

def get_consultation_medicines(
    db: Session,
    consultation_id: int,
) -> list[ConsultationMedicine]:
    statement = (
        select(ConsultationMedicine)
        .where(
            ConsultationMedicine.consultation_id
            == consultation_id
        )
        .order_by(
            ConsultationMedicine.dispensed_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


# =========================================================
# DISPENSE MEDICINE
# =========================================================

def dispense_medicine(
    db: Session,
    consultation: Consultation,
    medicine: Medicine,
    data: ConsultationMedicineCreate,
    dispensed_by: int | None,
) -> ConsultationMedicine:

    # -----------------------------------------------------
    # NORMALIZE STOCK UNIT
    # -----------------------------------------------------

    stock_unit = (
        data.stock_unit
        .strip()
        .upper()
    )


    # -----------------------------------------------------
    # VALIDATE QUANTITY
    # -----------------------------------------------------

    if data.quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )


    # -----------------------------------------------------
    # VALIDATE STOCK UNIT
    # -----------------------------------------------------

    if stock_unit not in VALID_STOCK_UNITS:
        raise ValueError(
            "Invalid stock unit. "
            "Use PACKAGE or LOOSE."
        )


    # -----------------------------------------------------
    # VALIDATE MEDICINE
    # -----------------------------------------------------

    if not medicine.is_active:
        raise ValueError(
            "Medicine is inactive."
        )


    if not medicine.stock_verified:
        raise ValueError(
            "Medicine stock/formulary status "
            "has not been verified for dispensing."
        )


    # -----------------------------------------------------
    # DEDUCT PACKAGE STOCK
    # -----------------------------------------------------

    if stock_unit == "PACKAGE":
        current_stock = (
            medicine.package_stock or 0
        )

        if data.quantity > current_stock:
            raise ValueError(
                "Insufficient package stock."
            )

        medicine.package_stock = (
            current_stock -
            data.quantity
        )


    # -----------------------------------------------------
    # DEDUCT LOOSE STOCK
    # -----------------------------------------------------

    else:
        current_stock = (
            medicine.loose_stock or 0
        )

        if data.quantity > current_stock:
            raise ValueError(
                "Insufficient loose stock."
            )

        medicine.loose_stock = (
            current_stock -
            data.quantity
        )


    # -----------------------------------------------------
    # CONSULTATION MEDICINE RECORD
    # -----------------------------------------------------

    consultation_medicine = (
        ConsultationMedicine(
            consultation_id=
                consultation.id,

            medicine_id=
                medicine.id,

            quantity=
                data.quantity,

            stock_unit=
                stock_unit,

            dosage_instruction=
                data.dosage_instruction,

            remarks=
                data.remarks,

            dispensed_by=
                dispensed_by,
        )
    )

    db.add(
        consultation_medicine
    )


    # -----------------------------------------------------
    # INVENTORY TRANSACTION
    # -----------------------------------------------------

    inventory_transaction = (
        InventoryTransaction(
            medicine_id=
                medicine.id,

            transaction_type=
                "DISPENSE",

            quantity=
                data.quantity,

            stock_unit=
                stock_unit,

            reference=(
                f"Consultation "
                f"#{consultation.id}"
            ),

            reason=(
                "Medicine dispensed "
                "to patient"
            ),

            notes=
                data.dosage_instruction,

            recorded_by=
                dispensed_by,
        )
    )

    db.add(
        inventory_transaction
    )


    # -----------------------------------------------------
    # SAVE AS ONE DATABASE TRANSACTION
    # -----------------------------------------------------

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise


    # -----------------------------------------------------
    # REFRESH
    # -----------------------------------------------------

    db.refresh(
        consultation_medicine
    )

    db.refresh(
        medicine
    )


    return consultation_medicine