from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class DiseaseCase(Base):
    __tablename__ = "disease_cases"

    __table_args__ = (
        UniqueConstraint(
            "consultation_id",
            "disease_id",
            name=(
                "uq_disease_case_"
                "consultation_disease"
            ),
        ),
    )


    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )


    # =========================================================
    # PATIENT
    # =========================================================

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )


    # =========================================================
    # CONSULTATION
    # =========================================================

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "consultations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )


    # =========================================================
    # DISEASE
    # =========================================================

    disease_id: Mapped[int] = mapped_column(
        ForeignKey(
            "diseases.id",
        ),
        nullable=False,
        index=True,
    )


    # =========================================================
    # CASE INFORMATION
    # =========================================================

    case_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="SUSPECTED",
        index=True,
    )

    onset_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    case_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        index=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


    # =========================================================
    # VALIDATION
    # =========================================================

    validation_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )

    validated_by: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
        ),
        nullable=True,
    )

    validated_by_name_snapshot: Mapped[str | None] = mapped_column(
        String(201),
        nullable=True,
    )

    validated_by_role_snapshot: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


    # =========================================================
    # AUDIT INFORMATION
    # =========================================================

    recorded_by: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
        ),
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


    # =========================================================
    # ORM RELATIONSHIPS
    # =========================================================

    patient = relationship(
        "Patient",
    )

    consultation = relationship(
        "Consultation",
        back_populates="disease_cases",
    )

    disease = relationship(
        "Disease",
    )

    recorder = relationship(
        "User",
        foreign_keys=[
            recorded_by,
        ],
    )

    validator = relationship(
        "User",
        foreign_keys=[
            validated_by,
        ],
    )