from types import SimpleNamespace

import pytest

import app.models  # noqa: F401 - register SQLAlchemy model relationships
from app.models.consultation import Consultation
from app.models.symptom import Symptom
from app.schemas.consultation import ConsultationCreate, ConsultationUpdate
from app.services import consultation_service


class FakeSession:
    def __init__(self, *, commit_error=None):
        self.added = []
        self.flush_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.refresh_count = 0
        self.commit_error = commit_error
        self._next_id = 100

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


def make_actor():
    return SimpleNamespace(id=7, username="doctor.test")


def make_symptom():
    return Symptom(
        id=1,
        code="FEVER",
        name="Fever",
        is_active=True,
    )


def make_create_data():
    return ConsultationCreate(
        chief_complaint="  Fever and cough  ",
        symptom_codes=["FEVER"],
        diagnosis="Acute respiratory infection",
        assessment="Stable",
        treatment_plan="Supportive care",
    )


def test_create_consultation_commits_actor_snapshot_and_audit(monkeypatch):
    db = FakeSession()
    actor = make_actor()
    symptom = make_symptom()
    audit_calls = []

    monkeypatch.setattr(
        consultation_service,
        "_get_active_symptoms_by_codes",
        lambda **_kwargs: [symptom],
    )
    monkeypatch.setattr(
        consultation_service,
        "snapshot_user_by_id",
        lambda _db, _user_id: (
            actor,
            {
                "display_name": "Test Doctor",
                "role_names": "DOCTOR",
            },
        ),
    )
    monkeypatch.setattr(
        consultation_service,
        "create_audit_log",
        lambda _db, **kwargs: audit_calls.append(kwargs),
    )
    monkeypatch.setattr(
        consultation_service,
        "get_consultation_by_id",
        lambda db, consultation_id: db.added[0],
    )

    consultation = consultation_service.create_consultation(
        db=db,
        patient_id=21,
        data=make_create_data(),
        recorded_by=actor.id,
    )

    assert consultation.id == 100
    assert consultation.patient_id == 21
    assert consultation.chief_complaint == "Fever and cough"
    assert consultation.recorded_by == actor.id
    assert consultation.recorded_by_name_snapshot == "Test Doctor"
    assert consultation.recorded_by_role_snapshot == "DOCTOR"
    assert consultation.structured_symptoms == [symptom]
    assert db.flush_count == 1
    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert audit_calls[0]["action"] == "CONSULTATION_CREATE"
    assert audit_calls[0]["module"] == "CLINICAL"
    assert audit_calls[0]["record_id"] == consultation.id


def test_create_consultation_commit_false_leaves_commit_to_outer_transaction(monkeypatch):
    db = FakeSession()
    actor = make_actor()

    monkeypatch.setattr(
        consultation_service,
        "_get_active_symptoms_by_codes",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        consultation_service,
        "snapshot_user_by_id",
        lambda _db, _user_id: (
            actor,
            {"display_name": "Test Doctor", "role_names": "DOCTOR"},
        ),
    )
    monkeypatch.setattr(
        consultation_service,
        "create_audit_log",
        lambda *_args, **_kwargs: None,
    )

    consultation = consultation_service.create_consultation(
        db=db,
        patient_id=21,
        data=ConsultationCreate(chief_complaint="Cough"),
        recorded_by=actor.id,
        commit=False,
    )

    assert consultation.id == 100
    assert db.flush_count == 1
    assert db.commit_count == 0
    assert db.rollback_count == 0


def test_create_consultation_rolls_back_if_audit_write_fails(monkeypatch):
    db = FakeSession()
    actor = make_actor()

    monkeypatch.setattr(
        consultation_service,
        "_get_active_symptoms_by_codes",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        consultation_service,
        "snapshot_user_by_id",
        lambda _db, _user_id: (
            actor,
            {"display_name": "Test Doctor", "role_names": "DOCTOR"},
        ),
    )

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("audit failure")

    monkeypatch.setattr(
        consultation_service,
        "create_audit_log",
        fail_audit,
    )

    with pytest.raises(RuntimeError, match="audit failure"):
        consultation_service.create_consultation(
            db=db,
            patient_id=21,
            data=ConsultationCreate(chief_complaint="Cough"),
            recorded_by=actor.id,
        )

    assert db.commit_count == 0
    assert db.rollback_count == 1


def test_update_consultation_commits_and_records_audit(monkeypatch):
    db = FakeSession()
    actor = make_actor()
    audit_calls = []
    consultation = SimpleNamespace(
        id=55,
        patient_id=21,
        chief_complaint="Old complaint",
        diagnosis="Old diagnosis",
        notes=None,
        structured_symptoms=[],
    )

    monkeypatch.setattr(
        consultation_service,
        "snapshot_user_by_id",
        lambda _db, _user_id: (actor, {}),
    )
    monkeypatch.setattr(
        consultation_service,
        "create_audit_log",
        lambda _db, **kwargs: audit_calls.append(kwargs),
    )
    monkeypatch.setattr(
        consultation_service,
        "get_consultation_by_id",
        lambda **_kwargs: consultation,
    )

    result = consultation_service.update_consultation(
        db=db,
        consultation=consultation,
        data=ConsultationUpdate(
            diagnosis="Updated diagnosis",
            notes="Follow up in one week",
        ),
        updated_by=actor.id,
    )

    assert result is consultation
    assert consultation.diagnosis == "Updated diagnosis"
    assert consultation.notes == "Follow up in one week"
    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert audit_calls[0]["action"] == "CONSULTATION_UPDATE"
    assert audit_calls[0]["record_id"] == 55


def test_update_consultation_rolls_back_when_commit_fails(monkeypatch):
    db = FakeSession(commit_error=RuntimeError("commit failed"))
    actor = make_actor()
    consultation = SimpleNamespace(
        id=55,
        patient_id=21,
        chief_complaint="Old complaint",
        diagnosis="Old diagnosis",
        structured_symptoms=[],
    )

    monkeypatch.setattr(
        consultation_service,
        "snapshot_user_by_id",
        lambda _db, _user_id: (actor, {}),
    )
    monkeypatch.setattr(
        consultation_service,
        "create_audit_log",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(RuntimeError, match="commit failed"):
        consultation_service.update_consultation(
            db=db,
            consultation=consultation,
            data=ConsultationUpdate(diagnosis="Updated diagnosis"),
            updated_by=actor.id,
        )

    assert db.commit_count == 1
    assert db.rollback_count == 1
