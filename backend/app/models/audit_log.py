from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    actor_username_snapshot: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    actor_name_snapshot: Mapped[str | None] = mapped_column(
        String(201), nullable=True
    )

    # Existing field becomes the immutable role snapshot.
    role_names: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    module: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    record_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    subject_label_snapshot: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    description: Mapped[str] = mapped_column(Text, nullable=False)

    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    user = relationship("User")
