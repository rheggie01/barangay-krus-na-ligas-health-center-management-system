from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Medicine(Base):
    __tablename__ = "medicines"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # =====================================================
    # MEDICINE INFORMATION
    # =====================================================

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    generic_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    dosage_strength: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    dosage_form: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    # =====================================================
    # FORMULARY / PROGRAM CLASSIFICATION
    # =====================================================

    medicine_category: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="GENERAL",
        index=True,
    )

    formulary_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="CANDIDATE",
        index=True,
    )

    program_type: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
        index=True,
    )

    requires_prescription: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    restricted_dispensing: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    sensitive_inventory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    forecast_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    stock_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # =====================================================
    # PACKAGE / DISPENSING
    # =====================================================

    package_unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    dispensing_unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="piece",
    )

    units_per_package: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # =====================================================
    # INVENTORY
    # =====================================================

    package_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    loose_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reorder_level: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    # =====================================================
    # STATUS
    # =====================================================

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

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

    # =====================================================
    # TOTAL UNITS
    # =====================================================

    @property
    def total_units(self) -> int:
        package_stock = int(
            self.package_stock or 0
        )

        loose_stock = int(
            self.loose_stock or 0
        )

        units_per_package = int(
            self.units_per_package or 0
        )

        if units_per_package > 0:
            return (
                package_stock
                * units_per_package
                + loose_stock
            )

        return (
            package_stock
            + loose_stock
        )
