from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.patient import Patient


class PatientMedicalHistory(Base):
    __tablename__ = "patient_medical_histories"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    history_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    recorded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    recorded_by_name_snapshot: Mapped[str | None] = mapped_column(
        String(201),
        nullable=True,
    )

    recorded_by_role_snapshot: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="medical_histories",
    )
