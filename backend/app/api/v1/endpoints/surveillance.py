from datetime import date
from typing import Literal

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
from app.schemas.surveillance import (
    DiseaseCaseCountResponse,
    DiseaseStreetCountResponse,
    DiseaseWeeklyComparisonResponse,
)
from app.services.surveillance_service import (
    get_disease_case_counts,
    get_disease_cases_by_street,
    get_weekly_disease_comparison,
)


router = APIRouter()


# =========================================================
# PERMISSION HELPERS
# =========================================================

def user_has_permission(
    user: User,
    permission_code: str,
) -> bool:
    """
    Check whether the current user has a permission
    through any of their assigned roles.
    """

    return any(
        permission.code == permission_code
        for role in user.roles
        for permission in role.permissions
    )


def can_view_sensitive_diseases(
    user: User,
) -> bool:
    """
    Check whether the current user may view
    sensitive disease information.
    """

    return user_has_permission(
        user,
        "SENSITIVE_DISEASE_VIEW",
    )


# =========================================================
# SURVEILLANCE SCOPE
# =========================================================

def resolve_surveillance_scope(
    user: User,
    scope: Literal[
        "GENERAL",
        "SENSITIVE",
    ],
) -> tuple[bool, bool]:
    """
    Return (include_sensitive, sensitive_only).

    GENERAL never includes sensitive disease rows.
    SENSITIVE is a separate restricted aggregate view.
    """

    if scope == "SENSITIVE":
        if not can_view_sensitive_diseases(
            user
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Sensitive / program surveillance "
                    "requires SENSITIVE_DISEASE_VIEW."
                ),
            )

        return (True, True)

    return (False, False)


# =========================================================
# DATE VALIDATION
# =========================================================

def validate_date_range(
    start_date: date | None,
    end_date: date | None,
) -> None:
    """
    Ensure that the selected date range is valid.
    """

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "start_date cannot be later "
                "than end_date."
            ),
        )


# =========================================================
# DISEASE CASE COUNTS
# =========================================================

@router.get(
    "/disease-cases",
    response_model=list[
        DiseaseCaseCountResponse
    ],
)
def disease_case_counts(
    start_date: date | None = Query(
        default=None,
    ),
    end_date: date | None = Query(
        default=None,
    ),
    scope: Literal[
        "GENERAL",
        "SENSITIVE",
    ] = Query(
        default="GENERAL",
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "SURVEILLANCE_VIEW"
        )
    ),
):
    validate_date_range(
        start_date,
        end_date,
    )

    (
        include_sensitive,
        sensitive_only,
    ) = resolve_surveillance_scope(
        current_user,
        scope,
    )

    return get_disease_case_counts(
        db=db,
        start_date=start_date,
        end_date=end_date,
        include_sensitive=(
            include_sensitive
        ),
        sensitive_only=(
            sensitive_only
        ),
    )


# =========================================================
# WEEKLY DISEASE COMPARISON
# =========================================================

@router.get(
    "/weekly-comparison",
    response_model=list[
        DiseaseWeeklyComparisonResponse
    ],
)
def weekly_disease_comparison(
    scope: Literal[
        "GENERAL",
        "SENSITIVE",
    ] = Query(
        default="GENERAL",
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "SURVEILLANCE_VIEW"
        )
    ),
):
    (
        include_sensitive,
        sensitive_only,
    ) = resolve_surveillance_scope(
        current_user,
        scope,
    )

    return get_weekly_disease_comparison(
        db=db,
        include_sensitive=(
            include_sensitive
        ),
        sensitive_only=(
            sensitive_only
        ),
    )


# =========================================================
# DISEASE CASES BY STREET
# =========================================================

@router.get(
    "/by-street",
    response_model=list[
        DiseaseStreetCountResponse
    ],
)
def disease_cases_by_street(
    start_date: date | None = Query(
        default=None,
    ),
    end_date: date | None = Query(
        default=None,
    ),
    disease_id: int | None = Query(
        default=None,
        ge=1,
    ),
    scope: Literal[
        "GENERAL",
        "SENSITIVE",
    ] = Query(
        default="GENERAL",
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: User = Depends(
        require_permission(
            "SURVEILLANCE_VIEW"
        )
    ),
):
    validate_date_range(
        start_date,
        end_date,
    )

    if scope == "SENSITIVE":
        # Deliberately block street-level geographic
        # breakdown for sensitive/program disease data.
        # Aggregate disease counts and weekly trends remain
        # available to authorized users through the other
        # surveillance endpoints.
        resolve_surveillance_scope(
            current_user,
            scope,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Street-level mapping is disabled for "
                "sensitive / program surveillance."
            ),
        )

    return get_disease_cases_by_street(
        db=db,
        start_date=start_date,
        end_date=end_date,
        disease_id=disease_id,
        include_sensitive=False,
        sensitive_only=False,
    )
