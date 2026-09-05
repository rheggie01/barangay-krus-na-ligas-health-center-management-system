from fastapi import APIRouter

from app.api.v1.endpoints.admin import (
    router as admin_router,
)
from app.api.v1.endpoints.auth import (
    router as auth_router,
)
from app.api.v1.endpoints.audit_logs import (
    router as audit_logs_router,
)
from app.api.v1.endpoints.consultations import (
    router as consultations_router,
)
from app.api.v1.endpoints.dashboard import (
    router as dashboard_router,
)
from app.api.v1.endpoints.disease_cases import (
    router as disease_cases_router,
)
from app.api.v1.endpoints.diseases import (
    router as diseases_router,
)
from app.api.v1.endpoints.dispensing import (
    router as dispensing_router,
)
from app.api.v1.endpoints.forecasts import (
    router as forecasts_router,
)
from app.api.v1.endpoints.health import (
    router as health_router,
)
from app.api.v1.endpoints.inventory import (
    router as inventory_router,
)
from app.api.v1.endpoints.medicines import (
    router as medicines_router,
)
from app.api.v1.endpoints.patient_history import (
    router as patient_history_router,
)
from app.api.v1.endpoints.patients import (
    router as patients_router,
)
from app.api.v1.endpoints.predictions import (
    router as predictions_router,
)
from app.api.v1.endpoints.surveillance import (
    router as surveillance_router,
)
from app.api.v1.endpoints.users import (
    router as users_router,
)


api_router = APIRouter()


api_router.include_router(
    health_router,
    tags=["Health"],
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    dashboard_router,
    prefix="/dashboard",
    tags=["Dashboard"],
)

api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Administration"],
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    audit_logs_router,
    prefix="/audit-logs",
    tags=["Audit Logs"],
)

api_router.include_router(
    patients_router,
    prefix="/patients",
    tags=["Patients"],
)

api_router.include_router(
    patient_history_router,
    prefix="/patients",
    tags=["Patient Medical History"],
)

api_router.include_router(
    consultations_router,
    tags=["Consultations"],
)

api_router.include_router(
    predictions_router,
    prefix="/predictions",
    tags=["ML Decision Support"],
)

api_router.include_router(
    forecasts_router,
    prefix="/forecasts",
    tags=["Forecasts"],
)

api_router.include_router(
    diseases_router,
    prefix="/diseases",
    tags=["Diseases"],
)

api_router.include_router(
    disease_cases_router,
    tags=["Disease Cases"],
)

api_router.include_router(
    surveillance_router,
    prefix="/surveillance",
    tags=["Disease Surveillance"],
)

api_router.include_router(
    medicines_router,
    prefix="/medicines",
    tags=["Medicine Inventory"],
)

api_router.include_router(
    inventory_router,
    prefix="/inventory",
    tags=["Inventory Transactions"],
)

api_router.include_router(
    dispensing_router,
    tags=["Medicine Dispensing"],
)
