from types import SimpleNamespace

import pytest

import app.models  # noqa: F401 - register SQLAlchemy model relationships
from app.models.consultation_medicine import ConsultationMedicine
from app.models.inventory_transaction import InventoryTransaction
from app.models.medicine import Medicine
from app.schemas.consultation_medicine import ConsultationMedicineCreate
from app.services import dispensing_service


class FakeSession:
    def __init__(self, *, commit_error=None):
        self.added = []
        self.flush_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.refresh_count = 0
        self.commit_error = commit_error
        self._next_id = 200

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
        "id": 5,
        "code": "MED-005",
        "name": "Paracetamol 500 mg",
        "package_stock": 10,
        "loose_stock": 5,
        "units_per_package": 20,
        "package_unit": "box",
        "dispensing_unit": "tablet",
        "is_active": True,
        "stock_verified": True,
    }
    values.update(overrides)
    return Medicine(**values)


def prepare_actor_mocks(monkeypatch, audit_calls):
    actor = SimpleNamespace(id=9, username="nurse.test")
    monkeypatch.setattr(
        dispensing_service,
        "snapshot_user_by_id",
        lambda _db, _user_id: (
            actor,
            {
                "display_name": "Test Nurse",
                "role_names": "NURSE",
            },
        ),
    )
    monkeypatch.setattr(
        dispensing_service,
        "create_audit_log",
        lambda _db, **kwargs: audit_calls.append(kwargs),
    )
    return actor


def test_consultation_package_dispensing_updates_stock_ledger_and_audit(monkeypatch):
    db = FakeSession()
    audit_calls = []
    actor = prepare_actor_mocks(monkeypatch, audit_calls)
    medicine = make_medicine()
    consultation = SimpleNamespace(id=77)
    data = ConsultationMedicineCreate(
        medicine_id=medicine.id,
        quantity=2,
        stock_unit="PACKAGE",
        dosage_instruction="Take as instructed",
    )

    result = dispensing_service.dispense_medicine(
        db=db,
        consultation=consultation,
        medicine=medicine,
        data=data,
        dispensed_by=actor.id,
    )

    consultation_record = next(
        obj for obj in db.added if isinstance(obj, ConsultationMedicine)
    )
    ledger = next(
        obj for obj in db.added if isinstance(obj, InventoryTransaction)
    )

    assert result is consultation_record
    assert medicine.package_stock == 8
    assert medicine.loose_stock == 5
    assert consultation_record.consultation_id == 77
    assert consultation_record.quantity == 2
    assert consultation_record.stock_unit == "PACKAGE"
    assert consultation_record.dispensed_by == actor.id
    assert consultation_record.dispensed_by_name_snapshot == "Test Nurse"
    assert consultation_record.dispensed_by_role_snapshot == "NURSE"
    assert ledger.transaction_type == "DISPENSE"
    assert ledger.previous_total_units == 205
    assert ledger.new_total_units == 165
    assert ledger.recorded_by == actor.id
    assert ledger.recorded_by_name_snapshot == "Test Nurse"
    assert ledger.recorded_by_role_snapshot == "NURSE"
    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert audit_calls[0]["action"] == "CONSULTATION_MEDICINE_DISPENSE"
    assert audit_calls[0]["module"] == "INVENTORY"


def test_consultation_loose_dispensing_only_deducts_loose_stock(monkeypatch):
    db = FakeSession()
    audit_calls = []
    actor = prepare_actor_mocks(monkeypatch, audit_calls)
    medicine = make_medicine(package_stock=2, loose_stock=10)

    dispensing_service.dispense_medicine(
        db=db,
        consultation=SimpleNamespace(id=78),
        medicine=medicine,
        data=ConsultationMedicineCreate(
            medicine_id=medicine.id,
            quantity=3,
            stock_unit="LOOSE",
        ),
        dispensed_by=actor.id,
    )

    ledger = next(
        obj for obj in db.added if isinstance(obj, InventoryTransaction)
    )
    assert medicine.package_stock == 2
    assert medicine.loose_stock == 7
    assert ledger.previous_total_units == 50
    assert ledger.new_total_units == 47
    assert db.commit_count == 1


def test_consultation_dispensing_rejects_insufficient_package_stock_without_mutation(monkeypatch):
    db = FakeSession()
    audit_calls = []
    actor = prepare_actor_mocks(monkeypatch, audit_calls)
    medicine = make_medicine(package_stock=1)

    with pytest.raises(ValueError, match="Insufficient package stock"):
        dispensing_service.dispense_medicine(
            db=db,
            consultation=SimpleNamespace(id=79),
            medicine=medicine,
            data=ConsultationMedicineCreate(
                medicine_id=medicine.id,
                quantity=2,
                stock_unit="PACKAGE",
            ),
            dispensed_by=actor.id,
        )

    assert medicine.package_stock == 1
    assert db.added == []
    assert db.commit_count == 0
    assert audit_calls == []


def test_consultation_dispensing_rejects_unverified_medicine(monkeypatch):
    db = FakeSession()
    audit_calls = []
    actor = prepare_actor_mocks(monkeypatch, audit_calls)
    medicine = make_medicine(stock_verified=False)

    with pytest.raises(ValueError, match="has not been verified"):
        dispensing_service.dispense_medicine(
            db=db,
            consultation=SimpleNamespace(id=80),
            medicine=medicine,
            data=ConsultationMedicineCreate(
                medicine_id=medicine.id,
                quantity=1,
                stock_unit="LOOSE",
            ),
            dispensed_by=actor.id,
        )

    assert db.commit_count == 0
    assert db.added == []


def test_consultation_dispensing_rolls_back_if_atomic_commit_fails(monkeypatch):
    db = FakeSession(commit_error=RuntimeError("database commit failed"))
    audit_calls = []
    actor = prepare_actor_mocks(monkeypatch, audit_calls)
    medicine = make_medicine(package_stock=3, loose_stock=0)

    with pytest.raises(RuntimeError, match="database commit failed"):
        dispensing_service.dispense_medicine(
            db=db,
            consultation=SimpleNamespace(id=81),
            medicine=medicine,
            data=ConsultationMedicineCreate(
                medicine_id=medicine.id,
                quantity=1,
                stock_unit="PACKAGE",
            ),
            dispensed_by=actor.id,
        )

    assert db.flush_count == 1
    assert db.commit_count == 1
    assert db.rollback_count == 1
    assert len(db.added) == 2
    assert len(audit_calls) == 1
