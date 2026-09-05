from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


def authenticate_user(
    db: Session,
    username: str,
    password: str,
):
    login_name = username.strip()
    login_email = login_name.lower()

    user = db.scalar(
        select(User).where(
            or_(
                User.username == login_name,
                User.email == login_email,
            )
        )
    )

    if not user:
        return None

    if (
        user.account_status != "ACTIVE"
        or not user.is_active
    ):
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user
