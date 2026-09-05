from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.consultation import Consultation
    from app.models.patient_history import PatientMedicalHistory


class Patient(Base):
    __tablename__ = "patients"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    # =====================================================
    # PATIENT IDENTIFIER
    # =====================================================

    patient_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    # =====================================================
    # PERSONAL INFORMATION
    # =====================================================

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    middle_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    suffix: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    sex: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    civil_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # PWD is intentionally stored only as a boolean category flag.
    # Detailed disability/medical information is not required for
    # the Patient Records category filter.
    is_pwd: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )

    # =====================================================
    # ADDRESS INFORMATION
    # =====================================================

    street: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    barangay: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # =====================================================
    # CONTACT INFORMATION
    # =====================================================

    contact_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    emergency_contact_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    emergency_contact_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # =====================================================
    # RECORD STATUS
    # =====================================================

    record_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # =====================================================
    # ORM RELATIONSHIPS
    # =====================================================

    consultations: Mapped[list["Consultation"]] = relationship(
        "Consultation",
        back_populates="patient",
    )

    medical_histories: Mapped[
        list["PatientMedicalHistory"]
    ] = relationship(
        "PatientMedicalHistory",
        back_populates="patient",
    )

    # =====================================================
    # DISPLAY
    # =====================================================

    def __repr__(self) -> str:
        return (
            f"<Patient "
            f"id={self.id} "
            f"patient_code={self.patient_code!r} "
            f"name={self.last_name!r}, {self.first_name!r}>"
        )
