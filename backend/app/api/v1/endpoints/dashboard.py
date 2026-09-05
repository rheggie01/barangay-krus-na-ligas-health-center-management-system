from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_permission,
)
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummaryResponse,
)
from app.services.dashboard_service import (
    get_dashboard_summary,
)


router = APIRouter()


# =========================================================
# DASHBOARD SUMMARY
# =========================================================

@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("PATIENT_VIEW")
    ),
):
    return get_dashboard_summary(
        db=db,
    )