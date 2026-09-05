from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User


def get_user_display_name(user: User | None) -> str | None:
    if user is None:
        return None

    full_name = " ".join(
        str(value).strip()
        for value in (
            getattr(user, "first_name", None),
            getattr(user, "last_name", None),
        )
        if value and str(value).strip()
    )

    if full_name:
        return full_name

    for attribute in ("username", "email"):
        value = getattr(user, attribute, None)
        if value:
            return str(value)

    return f"User #{user.id}"


def get_user_role_names(user: User | None) -> str | None:
    if user is None:
        return None

    values = []
    for role in (getattr(user, "roles", []) or []):
        value = getattr(role, "name", None) or getattr(role, "code", None)
        if value:
            values.append(str(value))

    if not values:
        return None

    return ", ".join(sorted(set(values)))


def snapshot_user(user: User | None) -> dict[str, object | None]:
    if user is None:
        return {
            "user_id": None,
            "username": None,
            "display_name": None,
            "role_names": None,
        }

    return {
        "user_id": user.id,
        "username": user.username,
        "display_name": get_user_display_name(user),
        "role_names": get_user_role_names(user),
    }


def get_user_with_roles(db: Session, user_id: int | None) -> User | None:
    if user_id is None:
        return None

    return db.scalar(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )


def snapshot_user_by_id(
    db: Session,
    user_id: int | None,
) -> tuple[User | None, dict[str, object | None]]:
    user = get_user_with_roles(db, user_id)
    return user, snapshot_user(user)
