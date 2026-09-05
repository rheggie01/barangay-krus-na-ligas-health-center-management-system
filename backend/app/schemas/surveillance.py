from pydantic import BaseModel


# =========================================================
# DISEASE CASE COUNT
# =========================================================

class DiseaseCaseCountResponse(BaseModel):
    disease_id: int
    code: str
    name: str
    case_count: int


# =========================================================
# WEEKLY DISEASE COMPARISON
# =========================================================

class DiseaseWeeklyComparisonResponse(BaseModel):
    disease_id: int
    code: str
    name: str

    current_week_cases: int
    previous_week_cases: int

    difference: int
    percentage_change: float | None

    trend: str


# =========================================================
# DISEASE CASES BY STREET
# =========================================================

class DiseaseStreetCountResponse(BaseModel):
    street: str

    disease_id: int
    code: str
    name: str

    case_count: int