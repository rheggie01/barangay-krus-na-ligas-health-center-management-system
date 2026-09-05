from datetime import date

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import forecasts as forecast_endpoints
from app.ml.services import forecast_service


MEDICINE_CODE = "PARACETAMOL_TEST"


def medicine_report():
    return {
        "medicines": {
            MEDICINE_CODE: {
                "medicine_name": "Paracetamol 500 mg Tablet",
                "selected_model_family": "ARIMA",
                "order": [1, 0, 0],
                "seasonal_order": None,
                "test_metrics": {
                    "rmse": 5.0,
                    "mae": 4.0,
                    "mape_nonzero_pct": 9.0,
                },
            }
        }
    }


def inventory_snapshot(**overrides):
    values = {
        "matched": True,
        "match_status": "MATCHED",
        "match_strategy": "EXACT_CODE",
        "message": "Matched by exact active inventory code.",
        "medicine_id": 8,
        "inventory_code": MEDICINE_CODE,
        "inventory_name": "Paracetamol 500 mg Tablet",
        "dispensing_unit": "tablet",
        "package_unit": "box",
        "units_per_package": 10,
        "package_stock": 0,
        "loose_stock": 3,
        "usable_current_stock": 3,
        "reorder_level": 2,
    }
    values.update(overrides)
    return values


def runtime_metadata(**overrides):
    values = {
        "data_mode": "BASELINE_PLUS_LIVE_DATABASE",
        "baseline_end": "2025-12-01",
        "system_coverage_start": "2026-01-01",
        "latest_completed_period": "2026-08-01",
        "latest_live_covered_period": "2026-08-01",
        "live_periods_used": 8,
        "missing_bridge_periods": 0,
        "freshness_status": "LIVE_CURRENT",
        "automatic_refresh": True,
        "package_conversion_warning": False,
    }
    values.update(overrides)
    return values


def patch_medicine_forecast(
    monkeypatch,
    *,
    inventory=None,
    metadata=None,
    values=None,
):
    baseline = pd.DataFrame(
        {
            "month_start": [pd.Timestamp("2025-12-01")],
            "medicine_code": [MEDICINE_CODE],
            "quantity_dispensed": [12.0],
        }
    )
    series = pd.Series(
        [12.0, 13.0, 14.0],
        index=pd.to_datetime(["2026-06-01", "2026-07-01", "2026-08-01"]),
        dtype=float,
    )
    inventory = inventory or inventory_snapshot()
    metadata = metadata or runtime_metadata()
    forecast_values = np.asarray(
        values if values is not None else [5.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        dtype=float,
    )
    captures = {}

    monkeypatch.setattr(forecast_service, "_load_medicine_report", medicine_report)
    monkeypatch.setattr(forecast_service, "_load_medicine_baseline", lambda: baseline)
    monkeypatch.setattr(
        forecast_service,
        "build_dynamic_medicine_series",
        lambda _db, **_kwargs: (series, metadata, inventory),
    )
    monkeypatch.setattr(
        forecast_service,
        "_fit_selected_model",
        lambda *_args, **_kwargs: object(),
    )

    def fake_forecast(_fitted, *, steps):
        captures["steps"] = steps
        selected = forecast_values[:steps]
        return selected, np.maximum(selected - 1.0, 0.0), selected + 1.0

    monkeypatch.setattr(forecast_service, "_forecast_with_interval", fake_forecast)
    monkeypatch.setattr(
        forecast_service,
        "actual_next_month_start",
        lambda: date(2026, 10, 1),
    )
    return captures


def test_medicine_forecast_targets_actual_next_month_and_six_visible_months(monkeypatch):
    captures = patch_medicine_forecast(monkeypatch)

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)

    assert captures["steps"] == 7  # one hidden bridge month + six visible months
    assert result["forecast_horizon_months"] == 6
    assert len(result["forecast_points"]) == 6
    assert result["forecast_points"][0]["month_start"] == "2026-10-01"
    assert result["forecast_points"][-1]["month_start"] == "2027-03-01"


def test_available_recommendation_uses_documented_stock_formula(monkeypatch):
    patch_medicine_forecast(monkeypatch)

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)
    recommendation = result["recommendation"]

    # Visible first forecast is 10 because the first model step bridges September.
    assert recommendation["forecast_quantity"] == 10.0
    assert recommendation["current_usable_stock"] == 3
    assert recommendation["safety_stock"] == 2
    assert recommendation["recommended_additional_stock"] == 9
    assert (
        recommendation["formula"]
        == "max(0, Forecast Demand + Safety Stock - Usable Current Stock)"
    )
    assert recommendation["status"] == "AVAILABLE"


def test_recommendation_never_goes_below_zero(monkeypatch):
    patch_medicine_forecast(
        monkeypatch,
        inventory=inventory_snapshot(usable_current_stock=100, reorder_level=5),
    )

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)

    assert result["recommendation"]["recommended_additional_stock"] == 0


def test_fractional_forecast_recommendation_rounds_up_to_whole_stock_unit(monkeypatch):
    patch_medicine_forecast(
        monkeypatch,
        values=[5.0, 10.2, 11.0, 12.0, 13.0, 14.0, 15.0],
    )

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)

    # ceil(10.2 + 2 - 3) = 10
    assert result["recommendation"]["recommended_additional_stock"] == 10


def test_recommendation_is_withheld_when_inventory_has_no_safe_match(monkeypatch):
    inventory = inventory_snapshot(
        matched=False,
        match_status="NO_EXACT_FORMULATION_MATCH",
        match_strategy=None,
        message="No exact active inventory formulation matched the forecast medicine.",
        medicine_id=None,
        usable_current_stock=None,
        reorder_level=None,
    )
    patch_medicine_forecast(monkeypatch, inventory=inventory)

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)

    recommendation = result["recommendation"]
    assert recommendation["status"] == "WITHHELD"
    assert recommendation["recommended_additional_stock"] is None
    assert recommendation["withheld_reasons"]


def test_recommendation_is_withheld_until_completed_live_month_is_current(monkeypatch):
    patch_medicine_forecast(
        monkeypatch,
        metadata=runtime_metadata(
            freshness_status="NO_COMPLETED_LIVE_DATA",
            live_periods_used=0,
            latest_live_covered_period=None,
        ),
    )

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)

    assert result["recommendation"]["status"] == "WITHHELD"
    assert result["recommendation"]["recommended_additional_stock"] is None


def test_package_conversion_warning_withholds_stock_recommendation(monkeypatch):
    patch_medicine_forecast(
        monkeypatch,
        metadata=runtime_metadata(package_conversion_warning=True),
    )

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)

    reasons = result["recommendation"]["withheld_reasons"]
    assert result["recommendation"]["status"] == "WITHHELD"
    assert any("PACKAGE" in reason for reason in reasons)


def test_dss_output_explicitly_states_no_stock_or_purchase_order_is_created(monkeypatch):
    patch_medicine_forecast(monkeypatch)

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)
    note = result["recommendation"]["note"].lower()

    assert "no stock transaction" in note
    assert "purchase order" in note


def test_cumulative_six_month_forecast_matches_visible_points(monkeypatch):
    patch_medicine_forecast(monkeypatch)

    result = forecast_service.get_medicine_forecast(object(), MEDICINE_CODE)
    expected = round(
        sum(point["forecast_quantity_dispensed"] for point in result["forecast_points"]),
        3,
    )

    assert result["cumulative_6_month_forecast"] == expected


def test_forecast_read_path_does_not_call_session_write_methods(monkeypatch):
    patch_medicine_forecast(monkeypatch)

    class ReadOnlyGuardDB:
        def add(self, *_args, **_kwargs):
            raise AssertionError("forecast must not add database records")

        def flush(self, *_args, **_kwargs):
            raise AssertionError("forecast must not flush database writes")

        def commit(self, *_args, **_kwargs):
            raise AssertionError("forecast must not commit database writes")

    result = forecast_service.get_medicine_forecast(ReadOnlyGuardDB(), MEDICINE_CODE)

    assert result["recommendation"]["status"] == "AVAILABLE"


def test_unsupported_medicine_forecast_code_is_rejected(monkeypatch):
    monkeypatch.setattr(forecast_service, "_load_medicine_report", medicine_report)

    with pytest.raises(ValueError, match="Unsupported medicine forecast code"):
        forecast_service.get_medicine_forecast(object(), "UNKNOWN_MEDICINE")


def test_medicine_endpoint_translates_unsupported_code_to_404(monkeypatch):
    monkeypatch.setattr(
        forecast_endpoints,
        "get_medicine_forecast",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("unsupported")),
    )

    with pytest.raises(HTTPException) as exc:
        forecast_endpoints.get_medicine_forecast_detail(
            medicine_code="UNKNOWN",
            db=object(),
            current_user=object(),
        )

    assert exc.value.status_code == 404
