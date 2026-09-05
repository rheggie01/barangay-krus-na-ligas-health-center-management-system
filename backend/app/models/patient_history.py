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

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # =====================================================
    # PATIENT
    # =====================================================

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # =====================================================
    # HISTORY INFORMATION
    # =====================================================

    history_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # =====================================================
    # AUDIT INFORMATION
    # =====================================================

    recorded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # =====================================================
    # ORM RELATIONSHIPS
    # =====================================================

    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="medical_histories",
    )