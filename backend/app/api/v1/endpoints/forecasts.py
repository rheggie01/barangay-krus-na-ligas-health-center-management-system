from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db,
    require_permission,
)
from app.models.user import User
from app.ml.schemas.forecast import (
    DiseaseForecastDetail,
    DiseaseForecastSummary,
    MedicineForecastDetail,
    MedicineForecastSummary,
)
from app.ml.services.forecast_service import (
    get_disease_forecast,
    get_medicine_forecast,
    list_disease_forecasts,
    list_medicine_forecasts,
)
from app.ml.services.disease_medicine_mapping_service import (
    list_disease_medicine_mappings,
)
from app.ml.services.disease_forecast_catalog_service import (
    get_disease_for_forecast_code,
    list_disease_forecast_catalog,
)


router = APIRouter()


# =========================================================
# PERMISSION HELPERS
# =========================================================

def _user_has_permission(
    user: User,
    permission_code: str,
) -> bool:
    return any(
        permission.code == permission_code
        for role in user.roles
        for permission in role.permissions
    )


# =========================================================
# DISEASE FORECASTS
# =========================================================

@router.get(
    "/diseases",
    response_model=list[
        DiseaseForecastSummary
    ],
)
def get_disease_forecast_summaries(
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "FORECAST_VIEW"
        )
    ),
):
    try:
        return list_disease_forecasts(
            db
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc


@router.get(
    "/diseases/catalog",
)
def get_disease_forecast_catalog(
    include_sensitive: bool | None = Query(
        default=None,
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "FORECAST_VIEW"
        )
    ),
):
    can_view_sensitive = _user_has_permission(
        current_user,
        "SENSITIVE_DISEASE_VIEW",
    )

    if (
        include_sensitive is True
        and not can_view_sensitive
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Sensitive disease forecast catalog "
                "requires SENSITIVE_DISEASE_VIEW."
            ),
        )

    resolved_include_sensitive = (
        can_view_sensitive
        if include_sensitive is None
        else include_sensitive
    )

    try:
        return list_disease_forecast_catalog(
            db,
            include_sensitive=(
                resolved_include_sensitive
            ),
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc


@router.get(
    "/diseases/{disease_code}",
    response_model=(
        DiseaseForecastDetail
    ),
)
def get_disease_forecast_detail(
    disease_code: str,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "FORECAST_VIEW"
        )
    ),
):
    disease = get_disease_for_forecast_code(
        db,
        disease_code,
    )

    if (
        disease is not None
        and disease.is_sensitive
        and not _user_has_permission(
            current_user,
            "SENSITIVE_DISEASE_VIEW",
        )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Sensitive disease forecasting requires "
                "SENSITIVE_DISEASE_VIEW."
            ),
        )

    try:
        return get_disease_forecast(
            db,
            disease_code,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc


# =========================================================
# DEVELOPMENT DISEASE -> MEDICINE MAPPING
# =========================================================

@router.get(
    "/disease-medicine-mappings",
)
def get_disease_medicine_mapping_rows(
    include_sensitive: bool | None = Query(
        default=None,
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "FORECAST_VIEW"
        )
    ),
):
    can_view_sensitive = _user_has_permission(
        current_user,
        "SENSITIVE_DISEASE_VIEW",
    )

    if (
        include_sensitive is True
        and not can_view_sensitive
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Sensitive disease-medicine mapping "
                "requires SENSITIVE_DISEASE_VIEW."
            ),
        )

    resolved_include_sensitive = (
        can_view_sensitive
        if include_sensitive is None
        else include_sensitive
    )

    return list_disease_medicine_mappings(
        db,
        include_sensitive=resolved_include_sensitive,
    )


# =========================================================
# MEDICINE FORECASTS
# =========================================================

@router.get(
    "/medicines",
    response_model=list[
        MedicineForecastSummary
    ],
)
def get_medicine_forecast_summaries(
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "FORECAST_VIEW"
        )
    ),
):
    try:
        return list_medicine_forecasts(
            db
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc


@router.get(
    "/medicines/{medicine_code}",
    response_model=(
        MedicineForecastDetail
    ),
)
def get_medicine_forecast_detail(
    medicine_code: str,
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "FORECAST_VIEW"
        )
    ),
):
    try:
        return get_medicine_forecast(
            db,
            medicine_code,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(exc),
        ) from exc
