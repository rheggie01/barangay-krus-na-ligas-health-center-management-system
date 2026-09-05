from types import SimpleNamespace

import pytest

import app.models  # noqa: F401 - register SQLAlchemy model relationships
from app.models.audit_log import AuditLog
from app.models.inventory_transaction import InventoryTransaction
from app.models.medicine import Medicine
from app.models.medicine_dispensing import MedicineDispensing
from app.schemas.medicine_dispensing import MedicineDispensingCreate
from app.services import medicine_dispensing_service


class FakeSession:
    def __init__(self, *, scalar_result=None, commit_error=None):
        self.added = []
        self.flush_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.refresh_count = 0
        self.scalar_result = scalar_result
        self.commit_error = commit_error
        self._next_id = 300

    def scalar(self, _statement):
        return self.scalar_result

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flush_count += 1
        for obj in self.added:
            if getattr(obj, "id", None) is None:
                obj.id = self._next_id
                self._next_id += 1

    def commit(self):
        self.commit_count += 1
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self):
        self.rollback_count += 1

    def refresh(self, _obj):
        self.refresh_count += 1


def make_medicine(**overrides):
    values = {
        "id": 8,
        "code": "MED-008",
        "name": "Amoxicillin 500 mg",
        "package_stock": 2,
        "loose_stock": 3,
        "units_per_package": 10,
        "package_unit": "box",
        "dispensing_unit": "capsule",
        "is_active": True,
        "stock_verified": True,
    }
    values.update(overrides)
    return Medicine(**values)


def make_patient():
    return SimpleNamespace(
        id=33,
        patient_code="PT-0033",
        first_name="Juan",
        middle_name=None,
        last_name="Dela Cruz",
        suffix=None,
        record_status="ACTIVE",
    )


def make_user():
    return SimpleNamespace(
        id=12,
        first_name="Ana",
        last_name="Nurse",
        username="ana.nurse",
        email="ana.nurse@healthcenter-demo.com",
        roles=[SimpleNamespace(name="NURSE")],
    )


def make_data(**overrides):
    values = {
        "patient_id": 33,
        "medicine_id": 8,
        "consultation_id": 91,
        "quantity": 5,
        "stock_unit": "LOOSE",
        "program_name": "General Medicine",
        "purpose": "Prescribed treatment",
        "notes": "After meals",
    }
    values.update(overrides)
    return MedicineDispensingCreate(**values)


def patch_service_lookups(monkeypatch, patient, medicine):
    monkeypatch.setattr(
        medicine_dispensing_service,
        "_get_active_patient",
        lambda **_kwargs: patient,
    )
    monkeypatch.setattr(
        medicine_dispensing_service,
        "_get_active_medicine_for_update",
        lambda **_kwargs: medicine,
    )
    monkeypatch.setattr(
        medicine_dispensing_service,
        "_validate_consultation",
        lambda **_kwargs: None,
    )


def test_loose_dispensing_opens_package_and_preserves_remainder():
    medicine = make_medicine(package_stock=2, loose_stock=3, units_per_package=10)

    medicine_dispensing_service.deduct_dispensing_units(
        medicine=medicine,
        quantity=5,
    )

    assert medicine.package_stock == 1
    assert medicine.loose_stock == 8
    assert medicine_dispensing_service.get_total_dispensable_units(medicine) == 18


def test_insufficient_loose_dispensing_does_not_mutate_stock():
    medicine = make_medicine(package_stock=1, loose_stock=2, units_per_package=10)

    with pytest.raises(ValueError, match="Insufficient medicine stock"):
        medicine_dispensing_service.deduct_dispensing_units(
            medicine=medicine,
            quantity=20,
        )

    assert medicine.package_stock == 1
    assert medicine.loose_stock == 2


def test_package_dispensing_deducts_whole_packages_only():
    medicine = make_medicine(package_stock=4, loose_stock=6)

    medicine_dispensing_service.deduct_package_stock(
        medicine=medicine,
        quantity=2,
    )

    assert medicine.package_stock == 2
    assert medicine.loose_stock == 6


def test_free_medicine_dispensing_creates_patient_record_ledger_and_audit(monkeypatch):
    db = FakeSession()
    patient = make_patient()
    medicine = make_medicine()
    user = make_user()
    patch_service_lookups(monkeypatch, patient, medicine)

    result = medicine_dispensing_service.dispense_medicine(
        db=db,
        data=make_data(),
        current_user=user,
        ip_address="127.0.0.1",
    )

    dispensing = next(
        obj for obj in db.added if isinstance(obj, MedicineDispensing)
    )
    ledger = next(
        obj for obj in db.added if isinstance(obj, InventoryTransaction)
    )
    audit = next(
        obj for obj in db.added if isinstance(obj, AuditLog)
    )

    assert result is dispensing
    assert dispensing.dispensing_code.startswith("DISP-")
    assert dispensing.patient_id == patient.id
    assert dispensing.patient_code == patient.patient_code
    assert dispensing.patient_name == "Juan Dela Cruz"
    assert dispensing.medicine_code == medicine.code
    assert dispensing.dispensed_by == user.id
    assert dispensing.dispensed_by_name == "Ana Nurse"
    assert dispensing.dispensed_by_role_names == "NURSE"
    assert dispensing.previous_total_units == 23
    assert dispensing.new_total_units == 18
    assert ledger.transaction_type == "DISPENSE"
    assert ledger.reference == dispensing.dispensing_code
    assert ledger.previous_total_units == 23
    assert ledger.new_total_units == 18
    assert audit.action == "DISPENSE_MEDICINE"
    assert audit.module == "INVENTORY"
    assert audit.user_id == user.id
    assert audit.ip_address == "127.0.0.1"
    assert medicine.package_stock == 1
    assert medicine.loose_stock == 8
    assert db.flush_count == 2
    assert db.commit_count == 1
    assert db.rollback_count == 0


def test_free_medicine_dispensing_rolls_back_on_commit_error(monkeypatch):
    db = FakeSession(commit_error=RuntimeError("commit failed"))
    patient = make_patient()
    medicine = make_medicine()
    user = make_user()
    patch_service_lookups(monkeypatch, patient, medicine)

    with pytest.raises(RuntimeError, match="commit failed"):
        medicine_dispensing_service.dispense_medicine(
            db=db,
            data=make_data(quantity=1, stock_unit="PACKAGE"),
            current_user=user,
            ip_address="127.0.0.1",
        )

    assert db.commit_count == 1
    assert db.rollback_count == 1
    assert any(isinstance(obj, MedicineDispensing) for obj in db.added)
    assert any(isinstance(obj, InventoryTransaction) for obj in db.added)
    assert any(isinstance(obj, AuditLog) for obj in db.added)


def test_consultation_must_belong_to_selected_patient():
    db = FakeSession(
        scalar_result=SimpleNamespace(
            id=91,
            patient_id=999,
        )
    )

    with pytest.raises(ValueError, match="does not belong to this patient"):
        medicine_dispensing_service._validate_consultation(
            db=db,
            consultation_id=91,
            patient_id=33,
        )


def test_inactive_patient_is_rejected():
    db = FakeSession(
        scalar_result=SimpleNamespace(
            id=33,
            record_status="INACTIVE",
        )
    )

    with pytest.raises(ValueError, match="inactive patient record"):
        medicine_dispensing_service._get_active_patient(
            db=db,
            patient_id=33,
        )
