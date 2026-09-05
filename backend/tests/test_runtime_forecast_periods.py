from datetime import date
from types import SimpleNamespace

import pandas as pd

from app.ml.services import runtime_forecast_data as runtime


def test_current_and_latest_completed_week_exclude_open_week(monkeypatch):
    monkeypatch.setattr(runtime, "local_today", lambda: date(2026, 9, 6))

    assert runtime.current_week_start() == date(2026, 8, 31)
    assert runtime.latest_completed_week_start() == date(2026, 8, 24)


def test_latest_completed_and_next_month_are_calendar_aligned(monkeypatch):
    monkeypatch.setattr(runtime, "local_today", lambda: date(2026, 9, 6))

    assert runtime.latest_completed_month_start() == date(2026, 8, 1)
    assert runtime.actual_next_month_start() == date(2026, 10, 1)


def test_medicine_total_units_converts_packages_to_dispensing_units():
    medicine = SimpleNamespace(
        package_stock=4,
        loose_stock=3,
        units_per_package=10,
    )

    assert runtime.medicine_total_units(medicine) == 43


def test_medicine_total_units_uses_existing_fallback_when_conversion_not_configured():
    medicine = SimpleNamespace(
        package_stock=4,
        loose_stock=3,
        units_per_package=None,
    )

    assert runtime.medicine_total_units(medicine) == 7


def test_dynamic_disease_series_requests_only_through_latest_completed_week(monkeypatch):
    baseline = pd.DataFrame(
        {
            "week_start": [pd.Timestamp("2025-12-29")],
            "disease_label": ["DENGUE"],
            "validated_case_count": [3.0],
        }
    )
    completed_week = date(2026, 1, 12)
    captured = {}

    monkeypatch.setattr(
        runtime,
        "latest_completed_week_start",
        lambda: completed_week,
    )
    monkeypatch.setattr(
        runtime,
        "get_consultation_coverage_start",
        lambda _db: date(2026, 1, 1),
    )

    def fake_counts(_db, *, disease_code, start_week, end_week):
        captured["disease_code"] = disease_code
        captured["start_week"] = start_week
        captured["end_week"] = end_week
        return {completed_week: 2}

    monkeypatch.setattr(runtime, "get_validated_disease_week_counts", fake_counts)

    series, metadata = runtime.build_dynamic_disease_series(
        object(),
        baseline_frame=baseline,
        disease_code="DENGUE",
    )

    assert captured["end_week"] == completed_week
    assert series.index[-1].date() == completed_week
    assert metadata["latest_completed_period"] == completed_week.isoformat()
    assert metadata["freshness_status"] == "LIVE_CURRENT"


def test_dynamic_medicine_series_requests_only_through_latest_completed_month(monkeypatch):
    baseline = pd.DataFrame(
        {
            "month_start": [pd.Timestamp("2025-12-01")],
            "medicine_code": ["MED-A"],
            "quantity_dispensed": [10.0],
        }
    )
    completed_month = date(2026, 2, 1)
    captured = {}
    medicine = SimpleNamespace(
        id=9,
        code="MED-A",
        name="Medicine A",
        dispensing_unit="tablet",
        package_unit="box",
        units_per_package=10,
        package_stock=2,
        loose_stock=4,
        reorder_level=5,
    )

    monkeypatch.setattr(
        runtime,
        "latest_completed_month_start",
        lambda: completed_month,
    )
    monkeypatch.setattr(
        runtime,
        "match_baseline_medicine_to_inventory",
        lambda *_args, **_kwargs: (
            medicine,
            "EXACT_CODE",
            "Matched by exact active inventory code.",
        ),
    )
    monkeypatch.setattr(
        runtime,
        "get_dispensing_coverage_start",
        lambda _db: date(2026, 1, 10),
    )

    def fake_month_counts(_db, *, medicine, start_month, end_month):
        captured["medicine_id"] = medicine.id
        captured["start_month"] = start_month
        captured["end_month"] = end_month
        return ({date(2026, 2, 1): 7.0}, False)

    monkeypatch.setattr(runtime, "get_medicine_month_counts", fake_month_counts)

    series, metadata, inventory = runtime.build_dynamic_medicine_series(
        object(),
        baseline_frame=baseline,
        baseline_code="MED-A",
        baseline_name="Medicine A",
    )

    assert captured["end_month"] == completed_month
    assert series.index[-1].date() == completed_month
    assert metadata["latest_completed_period"] == completed_month.isoformat()
    assert metadata["freshness_status"] == "LIVE_CURRENT"
    assert inventory["usable_current_stock"] == 24
