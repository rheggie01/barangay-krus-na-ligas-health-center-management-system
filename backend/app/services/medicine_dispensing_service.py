from datetime import datetime
from math import ceil
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.consultation import Consultation
from app.models.inventory_transaction import InventoryTransaction
from app.models.medicine import Medicine
from app.models.medicine_dispensing import MedicineDispensing
from app.models.patient import Patient
from app.models.user import User
from app.schemas.medicine_dispensing import MedicineDispensingCreate


# =========================================================
# GET DISPENSING HISTORY
# =========================================================

def get_medicine_dispensings(
    db: Session,
    patient_id: int | None = None,
    medicine_id: int | None = None,
):
    statement = select(MedicineDispensing)

    if patient_id is not None:
        statement = statement.where(
            MedicineDispensing.patient_id == patient_id
        )

    if medicine_id is not None:
        statement = statement.where(
            MedicineDispensing.medicine_id == medicine_id
        )

    statement = statement.order_by(
        MedicineDispensing.dispensed_at.desc(),
        MedicineDispensing.id.desc(),
    )

    return db.scalars(statement).all()


# =========================================================
# DISPENSE MEDICINE
# =========================================================

def dispense_medicine(
    db: Session,
    data: MedicineDispensingCreate,
    current_user: User,
    ip_address: str | None = None,
):
    try:
        patient = _get_active_patient(
            db=db,
            patient_id=data.patient_id,
        )

        medicine = _get_active_medicine_for_update(
            db=db,
            medicine_id=data.medicine_id,
        )

        _validate_consultation(
            db=db,
            consultation_id=data.consultation_id,
            patient_id=patient.id,
        )

        program_name = data.program_name.strip()
        purpose = data.purpose.strip()
        notes = _clean_optional_text(data.notes)

        stock_unit = data.stock_unit
        dispensing_unit = _get_dispensing_unit_label(
            medicine=medicine,
            stock_unit=stock_unit,
        )

        previous_stock = _get_available_stock(
            medicine=medicine,
            stock_unit=stock_unit,
        )

        _deduct_stock(
            medicine=medicine,
            quantity=data.quantity,
            stock_unit=stock_unit,
        )

        new_stock = _get_available_stock(
            medicine=medicine,
            stock_unit=stock_unit,
        )

        patient_name = get_patient_display_name(patient)
        staff_name = get_user_display_name(current_user)
        role_names = get_user_role_names(current_user)

        dispensing = MedicineDispensing(
            dispensing_code="TMP-" + uuid4().hex.upper(),

            patient_id=patient.id,
            medicine_id=medicine.id,
            consultation_id=data.consultation_id,

            quantity=data.quantity,
            dispensing_unit=dispensing_unit,

            distribution_type="FREE",

            program_name=program_name,
            purpose=purpose,
            notes=notes,

            previous_total_units=previous_stock,
            new_total_units=new_stock,

            patient_code=patient.patient_code,
            patient_name=patient_name,

            medicine_code=medicine.code,
            medicine_name=medicine.name,

            dispensed_by=current_user.id,
            dispensed_by_name=staff_name,
            dispensed_by_role_names=role_names,
        )

        db.add(dispensing)
        db.flush()

        dispensing.dispensing_code = (
            f"DISP-{datetime.now().year}-{dispensing.id:06d}"
        )

        inventory_transaction = InventoryTransaction(
            medicine_id=medicine.id,
            transaction_type="DISPENSE",

            quantity=data.quantity,
            stock_unit=stock_unit,

            previous_total_units=previous_stock,
            new_total_units=new_stock,

            reference=dispensing.dispensing_code,

            reason=(
                "Free medicine dispensing - "
                f"{program_name}"
            ),

            notes=notes,
            recorded_by=current_user.id,
        )

        db.add(inventory_transaction)
        db.flush()

        audit = AuditLog(
            user_id=current_user.id,
            role_names=role_names,

            action="DISPENSE_MEDICINE",
            module="INVENTORY",
            record_id=dispensing.id,

            description=(
                f"Dispensed {data.quantity} {dispensing_unit} "
                f"of {medicine.name} ({medicine.code}) "
                f"to patient {patient.patient_code} - "
                f"{patient_name}. "
                f"Stock source: {stock_unit}. "
                f"Program: {program_name}. "
                f"Purpose: {purpose}. "
                f"Stock changed from {previous_stock} "
                f"to {new_stock} {dispensing_unit}. "
                f"Reference: {dispensing.dispensing_code}."
            ),

            ip_address=ip_address,
        )

        db.add(audit)

        # Medicine update, dispensing record, ledger record,
        # and audit log are committed atomically.
        db.commit()

        db.refresh(medicine)
        db.refresh(dispensing)

        return dispensing

    except ValueError:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


# =========================================================
# DATABASE LOOKUPS / VALIDATION
# =========================================================

def _get_active_patient(
    db: Session,
    patient_id: int,
) -> Patient:
    patient = db.scalar(
        select(Patient).where(
            Patient.id == patient_id
        )
    )

    if not patient:
        raise ValueError(
            "Patient not found."
        )

    if (
        getattr(
            patient,
            "record_status",
            "ACTIVE",
        )
        != "ACTIVE"
    ):
        raise ValueError(
            "Medicine cannot be dispensed "
            "to an inactive patient record."
        )

    return patient


def _get_active_medicine_for_update(
    db: Session,
    medicine_id: int,
) -> Medicine:
    medicine = db.scalar(
        select(Medicine)
        .where(
            Medicine.id == medicine_id
        )
        .with_for_update()
    )

    if not medicine:
        raise ValueError(
            "Medicine not found."
        )

    if not medicine.is_active:
        raise ValueError(
            "This medicine is inactive."
        )

    return medicine


def _validate_consultation(
    db: Session,
    consultation_id: int | None,
    patient_id: int,
) -> None:
    if consultation_id is None:
        return

    consultation = db.scalar(
        select(Consultation).where(
            Consultation.id == consultation_id
        )
    )

    if not consultation:
        raise ValueError(
            "Consultation not found."
        )

    if consultation.patient_id != patient_id:
        raise ValueError(
            "The selected consultation "
            "does not belong to this patient."
        )


# =========================================================
# STOCK HELPERS
# =========================================================

def _get_dispensing_unit_label(
    medicine: Medicine,
    stock_unit: str,
) -> str:
    if stock_unit == "PACKAGE":
        return (
            medicine.package_unit
            or "package"
        )

    return (
        medicine.dispensing_unit
        or "piece"
    )


def _get_available_stock(
    medicine: Medicine,
    stock_unit: str,
) -> int:
    if stock_unit == "PACKAGE":
        return int(
            medicine.package_stock
            or 0
        )

    return get_total_dispensable_units(
        medicine
    )


def _deduct_stock(
    medicine: Medicine,
    quantity: int,
    stock_unit: str,
) -> None:
    if stock_unit == "PACKAGE":
        deduct_package_stock(
            medicine=medicine,
            quantity=quantity,
        )
        return

    deduct_dispensing_units(
        medicine=medicine,
        quantity=quantity,
    )


def get_total_dispensable_units(
    medicine: Medicine,
) -> int:
    package_stock = int(
        medicine.package_stock or 0
    )

    loose_stock = int(
        medicine.loose_stock or 0
    )

    units_per_package = int(
        medicine.units_per_package or 0
    )

    if units_per_package <= 0:
        return loose_stock

    return (
        package_stock
        * units_per_package
        + loose_stock
    )


def deduct_package_stock(
    medicine: Medicine,
    quantity: int,
) -> None:
    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    package_stock = int(
        medicine.package_stock or 0
    )

    if package_stock <= 0:
        raise ValueError(
            "No package stock is available."
        )

    if quantity > package_stock:
        raise ValueError(
            "Insufficient package stock. "
            f"Available: {package_stock} "
            f"{medicine.package_unit or 'package'}."
        )

    medicine.package_stock = (
        package_stock
        - quantity
    )


def deduct_dispensing_units(
    medicine: Medicine,
    quantity: int,
) -> None:
    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    loose_stock = int(
        medicine.loose_stock or 0
    )

    package_stock = int(
        medicine.package_stock or 0
    )

    units_per_package = int(
        medicine.units_per_package or 0
    )

    # Use existing loose stock first.
    if loose_stock >= quantity:
        medicine.loose_stock = (
            loose_stock
            - quantity
        )
        return

    remaining_quantity = (
        quantity
        - loose_stock
    )

    if (
        package_stock > 0
        and units_per_package <= 0
    ):
        raise ValueError(
            "Units per package must be configured "
            "before dispensing loose units "
            "from package stock."
        )

    if units_per_package <= 0:
        raise ValueError(
            "Insufficient loose stock."
        )

    packages_to_open = ceil(
        remaining_quantity
        / units_per_package
    )

    if packages_to_open > package_stock:
        available_units = (
            package_stock
            * units_per_package
            + loose_stock
        )

        raise ValueError(
            "Insufficient medicine stock. "
            f"Available: {available_units} "
            f"{medicine.dispensing_unit or 'unit'}."
        )

    medicine.package_stock = (
        package_stock
        - packages_to_open
    )

    units_from_opened_packages = (
        packages_to_open
        * units_per_package
    )

    medicine.loose_stock = (
        units_from_opened_packages
        - remaining_quantity
    )


# =========================================================
# TEXT / DISPLAY HELPERS
# =========================================================

def _clean_optional_text(
    value: str | None,
) -> str | None:
    if not value:
        return None

    cleaned = value.strip()
    return cleaned or None


def get_patient_display_name(
    patient: Patient,
) -> str:
    parts = [
        patient.first_name,
        patient.middle_name,
        patient.last_name,
        patient.suffix,
    ]

    return " ".join(
        str(value).strip()
        for value in parts
        if value
        and str(value).strip()
    )


def get_user_display_name(
    user: User,
) -> str:
    first_name = getattr(
        user,
        "first_name",
        None,
    )

    last_name = getattr(
        user,
        "last_name",
        None,
    )

    full_name = " ".join(
        str(value).strip()
        for value in (
            first_name,
            last_name,
        )
        if value
        and str(value).strip()
    )

    if full_name:
        return full_name

    for attribute in (
        "full_name",
        "name",
        "username",
        "email",
    ):
        value = getattr(
            user,
            attribute,
            None,
        )

        if value:
            return str(value)

    return f"User #{user.id}"


def get_user_role_names(
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
