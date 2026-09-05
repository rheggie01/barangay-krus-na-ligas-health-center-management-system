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


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "medicines.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(30),
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

    # =====================================================
    # STOCK SNAPSHOT
    # =====================================================

    previous_total_units: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    new_total_units: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # =====================================================
    # TRANSACTION INFORMATION
    # =====================================================

    reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recorded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
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
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    medicine = relationship(
        "Medicine",
    )

    recorded_by_user = relationship(
        "User",
        foreign_keys=[
            recorded_by,
        ],
        lazy="selectin",
    )

    # =====================================================
    # AUDIT DISPLAY PROPERTIES
    # =====================================================

    @property
    def recorded_by_name(
        self,
    ) -> str | None:
        if self.recorded_by_name_snapshot:
            return self.recorded_by_name_snapshot

        user = self.recorded_by_user

        if user is None:
            return None

        first_name = getattr(
            user,
            "first_name",
            None,
        )

        last_name = getattr(
            user,
            "last_name",
            None,
        )

        full_name = " ".join(
            str(value).strip()
            for value in (
                first_name,
                last_name,
            )
            if value
            and str(value).strip()
        )

        if full_name:
            return full_name

        for attribute in (
            "username",
            "email",
        ):
            value = getattr(
                user,
                attribute,
                None,
            )

            if value:
                return str(value)

        return (
            f"User #{user.id}"
        )

    @property
    def recorded_by_role_names(
        self,
    ) -> str | None:
        if self.recorded_by_role_snapshot:
            return self.recorded_by_role_snapshot

        user = self.recorded_by_user

        if user is None:
            return None

        role_names = []

        for role in (
            getattr(
                user,
                "roles",
                [],
            )
            or []
        ):
            value = (
                getattr(
                    role,
                    "name",
                    None,
                )
                or getattr(
                    role,
                    "code",
                    None,
                )
            )

            if value:
                role_names.append(
                    str(value)
                )

        if not role_names:
            return None

        return ", ".join(
            sorted(
                set(
                    role_names
                )
            )
        )
