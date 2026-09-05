from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConsultationMedicine(Base):
    __tablename__ = "consultation_medicines"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "consultations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "medicines.id",
        ),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    stock_unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="LOOSE",
    )

    dosage_instruction: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    dispensed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    dispensed_by_name_snapshot: Mapped[str | None] = mapped_column(
        String(201),
        nullable=True,
    )

    dispensed_by_role_snapshot: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    dispensed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    consultation = relationship(
        "Consultation",
    )

    medicine = relationship(
        "Medicine",
    )