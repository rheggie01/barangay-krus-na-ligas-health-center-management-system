from datetime import date
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import forecasts as forecast_endpoints
from app.ml.services import forecast_service


def disease_report():
    return {
        "diseases": {
            "DENGUE": {
                "selected_model_family": "SARIMA",
                "order": [1, 0, 0],
                "seasonal_order": [1, 0, 0, 52],
                "test_metrics": {
                    "rmse": 2.5,
                    "mae": 1.75,
                    "mape_nonzero_pct": 12.0,
                },
            }
        }
    }


def runtime_metadata():
    return {
        "data_mode": "BASELINE_PLUS_LIVE_DATABASE",
        "baseline_end": "2025-12-29",
        "system_coverage_start": "2026-01-05",
        "latest_completed_period": "2026-08-31",
        "latest_live_covered_period": "2026-08-31",
        "live_periods_used": 35,
        "missing_bridge_periods": 0,
        "freshness_status": "LIVE_CURRENT",
        "automatic_refresh": True,
    }


def patch_disease_forecast(monkeypatch, mean=None):
    baseline = pd.DataFrame(
        {
            "week_start": [pd.Timestamp("2025-12-29")],
            "disease_label": ["DENGUE"],
            "validated_case_count": [4.0],
        }
    )
    series = pd.Series(
        [4.0, 5.0, np.nan, 7.0],
        index=pd.to_datetime(
            ["2025-12-29", "2026-01-05", "2026-01-12", "2026-01-19"]
        ),
        dtype=float,
    )
    captures = {}

    monkeypatch.setattr(forecast_service, "_load_disease_baseline", lambda: baseline)
    monkeypatch.setattr(forecast_service, "_load_disease_report", disease_report)
    monkeypatch.setattr(
        forecast_service,
        "build_dynamic_disease_series",
        lambda _db, **_kwargs: (series, runtime_metadata()),
    )

    def fake_fit(series_arg, *, model_family, order, seasonal_order):
        captures["series"] = series_arg
        captures["model_family"] = model_family
        captures["order"] = order
        captures["seasonal_order"] = seasonal_order
        return object()

    monkeypatch.setattr(forecast_service, "_fit_selected_model", fake_fit)
    values = np.asarray(mean if mean is not None else np.arange(1, 13), dtype=float)
    monkeypatch.setattr(
        forecast_service,
        "_forecast_with_interval",
        lambda _fitted, *, steps: (
            values[:steps],
            np.maximum(values[:steps] - 0.5, 0.0),
            values[:steps] + 0.5,
        ),
    )
    monkeypatch.setattr(
        forecast_service,
        "current_week_start",
        lambda: date(2026, 9, 7),
    )
    return captures


def test_disease_forecast_normalizes_code_and_uses_validated_model(monkeypatch):
    captures = patch_disease_forecast(monkeypatch)

    result = forecast_service.get_disease_forecast(object(), "  dengue  ")

    assert result["disease_code"] == "DENGUE"
    assert result["model_family"] == "SARIMA"
    assert result["order"] == [1, 0, 0]
    assert result["seasonal_order"] == [1, 0, 0, 52]
    assert captures["model_family"] == "SARIMA"
    assert captures["order"] == [1, 0, 0]
    assert captures["seasonal_order"] == [1, 0, 0, 52]


def test_disease_forecast_is_exactly_twelve_completed_week_aligned_points(monkeypatch):
    patch_disease_forecast(monkeypatch)

    result = forecast_service.get_disease_forecast(object(), "DENGUE")

    assert result["forecast_horizon_weeks"] == 12
    assert len(result["forecast_points"]) == 12
    assert result["forecast_points"][0]["week_start"] == "2026-09-07"
    assert result["forecast_points"][1]["week_start"] == "2026-09-14"
    assert result["forecast_points"][-1]["week_start"] == "2026-11-23"


def test_disease_forecast_preserves_baseline_live_and_missing_source_labels(monkeypatch):
    patch_disease_forecast(monkeypatch)

    result = forecast_service.get_disease_forecast(object(), "DENGUE")
    by_week = {item["week_start"]: item for item in result["historical_points"]}

    assert by_week["2025-12-29"]["source"] == "DEVELOPMENT_BASELINE"
    assert by_week["2026-01-05"]["source"] == "LIVE_DATABASE"
    assert by_week["2026-01-12"]["source"] == "MISSING_NOT_ZERO"


def test_disease_forecast_carries_runtime_freshness_and_decision_support_warning(
    monkeypatch,
):
    patch_disease_forecast(monkeypatch)

    result = forecast_service.get_disease_forecast(object(), "DENGUE")

    assert result["runtime_data"]["freshness_status"] == "LIVE_CURRENT"
    assert result["runtime_data"]["automatic_refresh"] is True
    assert result["development_status"] == "DYNAMIC_RUNTIME_DEVELOPMENT_FORECAST"
    assert "decision support" in result["warning"].lower()
    assert "synthetic" in result["warning"].lower()


def test_unsupported_disease_code_is_rejected_before_forecast_execution():
    with pytest.raises(ValueError, match="Unsupported disease code"):
        forecast_service.get_disease_forecast(object(), "HYPERTENSION")


def test_forecast_interval_helper_clips_negative_mean_and_lower_bound():
    class ForecastResult:
        predicted_mean = np.asarray([-3.0, 4.5])

        def conf_int(self, alpha):
            assert alpha == 0.05
            return np.asarray([[-7.0, 2.0], [1.0, 8.0]])

    class Fitted:
        def get_forecast(self, steps):
            assert steps == 2
            return ForecastResult()

    mean, lower, upper = forecast_service._forecast_with_interval(Fitted(), steps=2)

    assert mean.tolist() == [0.0, 4.5]
    assert lower.tolist() == [0.0, 1.0]
    assert upper.tolist() == [2.0, 8.0]


def test_disease_endpoint_translates_unsupported_forecast_to_404(monkeypatch):
    monkeypatch.setattr(
        forecast_endpoints,
        "get_disease_for_forecast_code",
        lambda *_args, **_kwargs: SimpleNamespace(is_sensitive=False),
    )
    monkeypatch.setattr(
        forecast_endpoints,
        "get_disease_forecast",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("unsupported")),
    )

    with pytest.raises(HTTPException) as exc:
        forecast_endpoints.get_disease_forecast_detail(
            disease_code="NO_MODEL",
            db=object(),
            current_user=SimpleNamespace(roles=[]),
        )

    assert exc.value.status_code == 404


def test_disease_endpoint_translates_missing_model_artifact_to_503(monkeypatch):
    monkeypatch.setattr(
        forecast_endpoints,
        "get_disease_for_forecast_code",
        lambda *_args, **_kwargs: SimpleNamespace(is_sensitive=False),
    )
    monkeypatch.setattr(
        forecast_endpoints,
        "get_disease_forecast",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )

    with pytest.raises(HTTPException) as exc:
        forecast_endpoints.get_disease_forecast_detail(
            disease_code="DENGUE",
            db=object(),
            current_user=SimpleNamespace(roles=[]),
        )

    assert exc.value.status_code == 503
