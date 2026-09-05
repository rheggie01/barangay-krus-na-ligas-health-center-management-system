from types import SimpleNamespace

from app.ml.services import disease_forecast_catalog_service as catalog


class FakeScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeDB:
    def __init__(self, diseases=None):
        self.diseases = diseases or []
        self.scalar_called = False

    def scalars(self, _statement):
        return FakeScalars(self.diseases)

    def scalar(self, _statement):
        self.scalar_called = True
        return None


def make_disease(**overrides):
    values = {
        "id": 1,
        "code": "DENGUE",
        "name": "Dengue",
        "category": "COMMUNICABLE",
        "transmission_type": "VECTOR_BORNE",
        "is_communicable": True,
        "is_reportable": True,
        "is_sensitive": False,
        "privacy_category": "STANDARD",
        "is_active": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def model_summary(code="DENGUE", family="SARIMA"):
    return {
        "disease_code": code,
        "disease_name": code,
        "model_family": family,
        "rmse": 1.5,
        "mae": 1.1,
        "mape_nonzero_pct": 8.0,
    }


def test_dengue_alias_code_maps_to_validated_model():
    disease = make_disease(code="DENG", name="Dengue")
    assert catalog.get_forecast_code_for_disease(disease) == "DENGUE"


def test_ari_name_alias_maps_to_validated_model():
    disease = make_disease(
        code="RESP-ARI",
        name="Acute Respiratory Infection (ARI)",
    )
    assert catalog.get_forecast_code_for_disease(disease) == "ARI"


def test_ili_code_maps_to_validated_model():
    disease = make_disease(code="ILI", name="Influenza-Like Illness")
    assert catalog.get_forecast_code_for_disease(disease) == "ILI"


def test_gastroenteritis_alias_maps_to_validated_model():
    disease = make_disease(code="GE", name="Gastroenteritis")
    assert (
        catalog.get_forecast_code_for_disease(disease)
        == "DIARRHEA_GASTROENTERITIS"
    )


def test_unknown_condition_has_no_forecast_code():
    disease = make_disease(code="HTN", name="Hypertension")
    assert catalog.get_forecast_code_for_disease(disease) is None


def test_unknown_forecast_code_does_not_query_database():
    db = FakeDB()
    assert catalog.get_disease_for_forecast_code(db, "NOT_A_MODEL") is None
    assert db.scalar_called is False


def test_catalog_marks_validated_model_available_and_other_condition_pending(
    monkeypatch,
):
    diseases = [
        make_disease(id=1, code="DENGUE", name="Dengue"),
        make_disease(
            id=2,
            code="HTN",
            name="Hypertension",
            category="NCD",
            transmission_type=None,
            is_communicable=False,
            is_reportable=False,
        ),
    ]
    monkeypatch.setattr(
        catalog,
        "list_disease_forecasts",
        lambda _db: [model_summary()],
    )

    rows = catalog.list_disease_forecast_catalog(
        FakeDB(diseases),
        include_sensitive=False,
    )

    dengue = next(row for row in rows if row["disease_code"] == "DENGUE")
    hypertension = next(row for row in rows if row["disease_code"] == "HTN")
    assert dengue["forecast_status"] == "AVAILABLE"
    assert dengue["forecast_code"] == "DENGUE"
    assert dengue["model_family"] == "SARIMA"
    assert hypertension["forecast_status"] == "MODEL_PENDING"
    assert hypertension["forecast_code"] is None
    assert hypertension["model_family"] is None
    assert "no validated time-series" in hypertension["status_message"].lower()


def test_catalog_excludes_sensitive_diseases_when_scope_is_general(monkeypatch):
    diseases = [
        make_disease(id=1, code="DENGUE", name="Dengue"),
        make_disease(
            id=2,
            code="HIV",
            name="HIV",
            is_sensitive=True,
            privacy_category="SENSITIVE",
        ),
    ]
    monkeypatch.setattr(
        catalog,
        "list_disease_forecasts",
        lambda _db: [model_summary()],
    )

    rows = catalog.list_disease_forecast_catalog(
        FakeDB(diseases),
        include_sensitive=False,
    )

    assert [row["disease_code"] for row in rows] == ["DENGUE"]


def test_catalog_can_include_sensitive_disease_but_keeps_model_pending(monkeypatch):
    diseases = [
        make_disease(
            id=2,
            code="HIV",
            name="HIV",
            is_sensitive=True,
            privacy_category="SENSITIVE",
        )
    ]
    monkeypatch.setattr(
        catalog,
        "list_disease_forecasts",
        lambda _db: [],
    )

    rows = catalog.list_disease_forecast_catalog(
        FakeDB(diseases),
        include_sensitive=True,
    )

    assert len(rows) == 1
    assert rows[0]["is_sensitive"] is True
    assert rows[0]["forecast_status"] == "MODEL_PENDING"
    assert rows[0]["forecast_code"] is None
