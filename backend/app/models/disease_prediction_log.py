from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DiseasePredictionLog(Base):
    __tablename__ = "disease_prediction_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    consultation_id: Mapped[int] = mapped_column(
        ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    performed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    predicted_disease_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    predicted_disease_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    top_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    probabilities: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    age: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sex: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    symptom_codes: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    temperature: Mapped[float | None] = mapped_column(
        Float,
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

    development_status: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    decision_support_notice: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )
