from pydantic import BaseModel


# =========================================================
# RUNTIME DATA SOURCE METADATA
# =========================================================

class RuntimeDataStatus(BaseModel):
    data_mode: str

    baseline_end: str

    system_coverage_start: str | None
    latest_completed_period: str
    latest_live_covered_period: str | None

    live_periods_used: int
    missing_bridge_periods: int

    freshness_status: str

    automatic_refresh: bool

    package_conversion_warning: bool = False

    forecast_generated_at: str

    message: str


# =========================================================
# DISEASE FORECASTING
# =========================================================

class DiseaseForecastSummary(BaseModel):
    disease_code: str
    disease_name: str
    model_family: str
    rmse: float
    mae: float
    mape_nonzero_pct: float | None


class HistoricalPoint(BaseModel):
    week_start: str
    case_count: float | None
    source: str


class ForecastPoint(BaseModel):
    week_start: str
    forecast_case_count: float
    lower_95: float
    upper_95: float


class DiseaseForecastDetail(BaseModel):
    disease_code: str
    disease_name: str

    model_family: str
    order: list[int]
    seasonal_order: list[int] | None

    rmse: float
    mae: float
    mape_nonzero_pct: float | None

    historical_points: list[
        HistoricalPoint
    ]

    forecast_points: list[
        ForecastPoint
    ]

    forecast_horizon_weeks: int

    runtime_data: RuntimeDataStatus

    development_status: str
    warning: str


# =========================================================
# MEDICINE FORECASTING
# =========================================================

class MedicineForecastSummary(BaseModel):
    medicine_code: str
    medicine_name: str
    model_family: str

    rmse: float
    mae: float
    mape_nonzero_pct: float | None

    inventory_match_status: str


class MedicineHistoricalPoint(BaseModel):
    month_start: str
    quantity_dispensed: float | None
    source: str


class MedicineForecastPoint(BaseModel):
    month_start: str
    forecast_quantity_dispensed: float
    lower_95: float
    upper_95: float


class MedicineInventorySnapshot(BaseModel):
    matched: bool

    match_status: str
    match_strategy: str | None
    message: str

    medicine_id: int | None
    inventory_code: str | None
    inventory_name: str | None

    dispensing_unit: str | None
    package_unit: str | None
    units_per_package: int | None

    package_stock: int | None
    loose_stock: int | None
    usable_current_stock: int | None

    reorder_level: int | None


class MedicineStockRecommendation(BaseModel):
    status: str

    formula: str

    forecast_month: str
    forecast_quantity: float

    current_usable_stock: int | None
    safety_stock: int | None

    recommended_additional_stock: int | None

    dispensing_unit: str | None

    withheld_reasons: list[str]

    note: str


class MedicineForecastDetail(BaseModel):
    medicine_code: str
    medicine_name: str

    model_family: str
    order: list[int]
    seasonal_order: list[int] | None

    rmse: float
    mae: float
    mape_nonzero_pct: float | None

    historical_points: list[
        MedicineHistoricalPoint
    ]

    forecast_points: list[
        MedicineForecastPoint
    ]

    forecast_horizon_months: int
    cumulative_6_month_forecast: float

    inventory: MedicineInventorySnapshot

    runtime_data: RuntimeDataStatus

    recommendation: MedicineStockRecommendation

    development_status: str
    warning: str
