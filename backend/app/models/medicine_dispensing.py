from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
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


class MedicineDispensing(Base):
    __tablename__ = "medicine_dispensings"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    dispensing_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    # =====================================================
    # REFERENCES
    # =====================================================

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id"),
        nullable=False,
        index=True,
    )

    consultation_id: Mapped[int | None] = mapped_column(
        ForeignKey("consultations.id"),
        nullable=True,
        index=True,
    )

    # =====================================================
    # DISPENSING INFORMATION
    # =====================================================

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    dispensing_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    distribution_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="FREE",
    )

    program_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    purpose: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # =====================================================
    # STOCK SNAPSHOT
    # =====================================================

    previous_total_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    new_total_units: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # =====================================================
    # PATIENT SNAPSHOT
    # =====================================================

    patient_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    patient_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # =====================================================
    # MEDICINE SNAPSHOT
    # =====================================================

    medicine_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    medicine_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # =====================================================
    # STAFF SNAPSHOT
    # =====================================================

    dispensed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    dispensed_by_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    dispensed_by_role_names: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================

    dispensed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # =====================================================
    # RELATIONSHIPS
    #
    # One-way relationships para hindi natin kailangang
    # baguhin ang Patient, Medicine, Consultation, at User
    # models at maiwasan ang mapper/back_populates problems.
    # =====================================================

    patient = relationship(
        "Patient",
        foreign_keys=[patient_id],
    )

    medicine = relationship(
        "Medicine",
        foreign_keys=[medicine_id],
    )

    consultation = relationship(
        "Consultation",
        foreign_keys=[consultation_id],
    )

    dispensed_by_user = relationship(
        "User",
        foreign_keys=[dispensed_by],
    )