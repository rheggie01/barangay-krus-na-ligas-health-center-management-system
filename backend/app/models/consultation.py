from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
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
from app.models.symptom import consultation_symptoms


class Consultation(Base):
    __tablename__ = "consultations"

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # =========================================================
    # RELATIONSHIPS / FOREIGN KEYS
    # =========================================================

    patient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    disease_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "diseases.id",
        ),
        nullable=True,
        index=True,
    )

    # =========================================================
    # CONSULTATION DATE
    # =========================================================

    consultation_date: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # =========================================================
    # REASON / COMPLAINT
    # =========================================================

    chief_complaint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Legacy/additional free-text symptom notes.
    # Structured symptoms are stored through the
    # consultation_symptoms association table.
    symptoms: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # =========================================================
    # VITAL SIGNS
    # =========================================================

    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    systolic_bp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    diastolic_bp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    heart_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    respiratory_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    oxygen_saturation: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    weight_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    height_cm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =========================================================
    # CLINICAL INFORMATION
    # =========================================================

    assessment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Legacy/free-text diagnosis.
    # New records should increasingly use disease_id.
    diagnosis: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    treatment_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
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

    # =========================================================
    # TIMESTAMPS
    # =========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # =========================================================
    # ORM RELATIONSHIPS
    # =========================================================

    patient = relationship(
        "Patient",
        back_populates="consultations",
    )

    disease = relationship(
        "Disease",
    )

    disease_cases = relationship(
        "DiseaseCase",
        back_populates="consultation",
        cascade="all, delete-orphan",
    )

    structured_symptoms = relationship(
        "Symptom",
        secondary=consultation_symptoms,
        back_populates="consultations",
        order_by="Symptom.name",
    )

    @property
    def symptom_codes(self) -> list[str]:
        return [
            symptom.code
            for symptom in self.structured_symptoms
        ]
