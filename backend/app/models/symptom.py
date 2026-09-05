from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


# =========================================================
# CONSULTATION <-> SYMPTOM ASSOCIATION
# =========================================================

consultation_symptoms = Table(
    "consultation_symptoms",
    Base.metadata,

    Column(
        "consultation_id",
        ForeignKey(
            "consultations.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),

    Column(
        "symptom_id",
        ForeignKey(
            "symptoms.id",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    ),
)


# =========================================================
# SYMPTOM MASTER
# =========================================================

class Symptom(Base):
    __tablename__ = "symptoms"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

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

    consultations = relationship(
        "Consultation",
        secondary=consultation_symptoms,
        back_populates="structured_symptoms",
    )
