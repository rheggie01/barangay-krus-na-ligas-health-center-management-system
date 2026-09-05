from fastapi import APIRouter, Depends

from app.api.dependencies import require_permission
from app.models.user import User


router = APIRouter()


@router.get("/test-permission")
def test_admin_permission(
    current_user: User = Depends(
        require_permission("USER_MANAGE")
    ),
):
    return {
        "message": "Permission granted",
        "username": current_user.username,
        "required_permission": "USER_MANAGE",
    }