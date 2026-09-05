from pydantic import BaseModel


class DashboardDiseaseCase(BaseModel):
    disease_id: int
    code: str
    name: str
    case_count: int


class DashboardLowStockMedicine(BaseModel):
    medicine_id: int
    code: str
    name: str
    stock_display: str
    status: str


class DashboardRecentConsultation(BaseModel):
    consultation_id: int
    patient_id: int
    patient_name: str
    diagnosis: str | None
    consultation_date: str


class DashboardSummaryResponse(BaseModel):
    total_patients: int

    consultations_today: int
    consultations_this_week: int

    active_medicines: int
    low_stock_medicines: int
    out_of_stock_medicines: int

    disease_cases_this_week: list[
        DashboardDiseaseCase
    ]

    low_stock_list: list[
        DashboardLowStockMedicine
    ]

    recent_consultations: list[
        DashboardRecentConsultation
    ]