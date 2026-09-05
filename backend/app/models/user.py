from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # PENDING = never approved, ACTIVE = login allowed,
    # INACTIVE = previously approved but access disabled.
    account_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        server_default="ACTIVE",
        index=True,
    )

    # Backward-compatible login flag. Lifecycle services keep it
    # synchronized with account_status.
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    status_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    status_changed_by: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    status_changed_by_name_snapshot: Mapped[str | None] = mapped_column(
        String(201), nullable=True
    )

    status_changed_by_role_snapshot: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
    )
