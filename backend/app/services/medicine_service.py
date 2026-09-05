from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.medicine import Medicine
from app.schemas.medicine import (
    MedicineCreate,
    MedicineUpdate,
)


def get_medicines(
    db: Session,
    search: str | None = None,
    active_only: bool = False,
    medicine_category: str | None = None,
    formulary_status: str | None = None,
    forecast_enabled: bool | None = None,
    stock_verified: bool | None = None,
    include_sensitive: bool = False,
):
    statement = select(Medicine)

    if search:
        search_value = f"%{search.strip()}%"

        statement = statement.where(
            or_(
                Medicine.code.ilike(search_value),
                Medicine.name.ilike(search_value),
                Medicine.generic_name.ilike(
                    search_value
                ),
                Medicine.dosage_strength.ilike(
                    search_value
                ),
                Medicine.dosage_form.ilike(
                    search_value
                ),
            )
        )

    if active_only:
        statement = statement.where(
            Medicine.is_active.is_(True)
        )

    if medicine_category:
        statement = statement.where(
            Medicine.medicine_category
            == medicine_category.strip().upper()
        )

    if formulary_status:
        statement = statement.where(
            Medicine.formulary_status
            == formulary_status.strip().upper()
        )

    if forecast_enabled is not None:
        statement = statement.where(
            Medicine.forecast_enabled.is_(
                forecast_enabled
            )
        )

    if stock_verified is not None:
        statement = statement.where(
            Medicine.stock_verified.is_(
                stock_verified
            )
        )

    if not include_sensitive:
        statement = statement.where(
            Medicine.sensitive_inventory.is_(
                False
            )
        )

    statement = statement.order_by(
        Medicine.medicine_category.asc(),
        Medicine.name.asc(),
        Medicine.dosage_strength.asc(),
    )

    return db.scalars(statement).all()


def get_medicine_by_id(
    db: Session,
    medicine_id: int,
):
    return db.scalar(
        select(Medicine).where(
            Medicine.id == medicine_id
        )
    )


def get_medicine_by_code(
    db: Session,
    code: str,
):
    return db.scalar(
        select(Medicine).where(
            Medicine.code == code.strip().upper()
        )
    )


def _normalize_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned or None


def _apply_safety_defaults(
    values: dict,
) -> dict:
    category = (
        values.get(
            "medicine_category"
        )
        or "GENERAL"
    ).strip().upper()

    values[
        "medicine_category"
    ] = category

    formulary_status = (
        values.get(
            "formulary_status"
        )
        or "CANDIDATE"
    ).strip().upper()

    values[
        "formulary_status"
    ] = formulary_status

    if values.get(
        "program_type"
    ):
        values[
            "program_type"
        ] = values[
            "program_type"
        ].strip().upper()

    if category == "SENSITIVE_PROGRAM":
        values[
            "sensitive_inventory"
        ] = True

        values[
            "restricted_dispensing"
        ] = True

        values[
            "requires_prescription"
        ] = True

        # Sensitive/program-managed medicines are not
        # automatically placed into ordinary demand forecasts.
        values[
            "forecast_enabled"
        ] = False

    return values


def create_medicine(
    db: Session,
    data: MedicineCreate,
):
    existing = get_medicine_by_code(
        db,
        data.code,
    )

    if existing:
        raise ValueError(
            "Medicine code already exists."
        )

    values = _apply_safety_defaults(
        data.model_dump()
    )

    medicine = Medicine(
        code=values[
            "code"
        ].strip().upper(),

        name=values[
            "name"
        ].strip(),

        generic_name=_normalize_optional_text(
            values.get(
                "generic_name"
            )
        ),

        dosage_strength=_normalize_optional_text(
            values.get(
                "dosage_strength"
            )
        ),

        dosage_form=_normalize_optional_text(
            values.get(
                "dosage_form"
            )
        ),

        medicine_category=values[
            "medicine_category"
        ],

        formulary_status=values[
            "formulary_status"
        ],

        program_type=_normalize_optional_text(
            values.get(
                "program_type"
            )
        ),

        requires_prescription=bool(
            values.get(
                "requires_prescription",
                False,
            )
        ),

        restricted_dispensing=bool(
            values.get(
                "restricted_dispensing",
                False,
            )
        ),

        sensitive_inventory=bool(
            values.get(
                "sensitive_inventory",
                False,
            )
        ),

        forecast_enabled=bool(
            values.get(
                "forecast_enabled",
                True,
            )
        ),

        stock_verified=bool(
            values.get(
                "stock_verified",
                False,
            )
        ),

        package_unit=_normalize_optional_text(
            values.get(
                "package_unit"
            )
        ),

        dispensing_unit=(
            values[
                "dispensing_unit"
            ].strip()
        ),

        units_per_package=values[
            "units_per_package"
        ],

        package_stock=values[
            "package_stock"
        ],

        loose_stock=values[
            "loose_stock"
        ],

        reorder_level=values[
            "reorder_level"
        ],

        is_active=values[
            "is_active"
        ],
    )

    db.add(medicine)
    db.commit()
    db.refresh(medicine)

    return medicine


def update_medicine(
    db: Session,
    medicine: Medicine,
    data: MedicineUpdate,
):
    update_data = data.model_dump(
        exclude_unset=True
    )

    if "code" in update_data:
        new_code = (
            update_data[
                "code"
            ]
            .strip()
            .upper()
        )

        existing = db.scalar(
            select(Medicine).where(
                Medicine.code == new_code,
                Medicine.id != medicine.id,
            )
        )

        if existing:
            raise ValueError(
                "Medicine code already exists."
            )

        update_data[
            "code"
        ] = new_code

    if "name" in update_data:
        update_data[
            "name"
        ] = (
            update_data[
                "name"
            ].strip()
        )

    for field in [
        "generic_name",
        "dosage_strength",
        "dosage_form",
        "package_unit",
    ]:
        if field in update_data:
            update_data[
                field
            ] = _normalize_optional_text(
                update_data[
                    field
                ]
            )

    if (
        "dispensing_unit"
        in update_data
        and update_data[
            "dispensing_unit"
        ]
        is not None
    ):
        update_data[
            "dispensing_unit"
        ] = (
            update_data[
                "dispensing_unit"
            ].strip()
        )

    update_data = (
        _apply_safety_defaults(
            {
                "medicine_category":
                    update_data.get(
                        "medicine_category",
                        medicine.medicine_category,
                    ),

                "formulary_status":
                    update_data.get(
                        "formulary_status",
                        medicine.formulary_status,
                    ),

                "program_type":
                    update_data.get(
                        "program_type",
                        medicine.program_type,
                    ),

                "requires_prescription":
                    update_data.get(
                        "requires_prescription",
                        medicine.requires_prescription,
                    ),

                "restricted_dispensing":
                    update_data.get(
                        "restricted_dispensing",
                        medicine.restricted_dispensing,
                    ),

                "sensitive_inventory":
                    update_data.get(
                        "sensitive_inventory",
                        medicine.sensitive_inventory,
                    ),

                "forecast_enabled":
                    update_data.get(
                        "forecast_enabled",
                        medicine.forecast_enabled,
                    ),

                **update_data,
            }
        )
    )

    for field, value in update_data.items():
        setattr(
            medicine,
            field,
            value,
        )

    db.commit()
    db.refresh(medicine)

    return medicine
