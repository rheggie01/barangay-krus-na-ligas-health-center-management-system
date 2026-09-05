from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.models.disease import Disease
from app.schemas.disease import (
    DiseaseCreate,
    DiseaseUpdate,
)


# =========================================================
# GET ALL DISEASES
# =========================================================

def get_diseases(
    db: Session,
):
    return db.scalars(
        select(Disease)
        .order_by(
            Disease.name
        )
    ).all()


# =========================================================
# GET ACTIVE DISEASES
# =========================================================

def get_active_diseases(
    db: Session,
):
    return db.scalars(
        select(Disease)
        .where(
            Disease.is_active.is_(True)
        )
        .order_by(
            Disease.name
        )
    ).all()


# =========================================================
# GET DISEASE BY ID
# =========================================================

def get_disease_by_id(
    db: Session,
    disease_id: int,
):
    return db.scalar(
        select(Disease).where(
            Disease.id ==
            disease_id
        )
    )


# =========================================================
# CREATE DISEASE
# =========================================================

def create_disease(
    db: Session,
    data: DiseaseCreate,
):
    code = (
        data.code
        .strip()
        .upper()
    )

    name = (
        data.name
        .strip()
    )

    existing = db.scalar(
        select(Disease).where(
            or_(
                Disease.code ==
                code,

                Disease.name ==
                name,
            )
        )
    )

    if existing:
        raise ValueError(
            "Disease code or name already exists."
        )

    disease = Disease(
        code=code,

        name=name,

        category=(
            data.category.strip()
            if data.category
            else None
        ),

        transmission_type=(
            data.transmission_type.strip()
            if data.transmission_type
            else None
        ),

        description=(
            data.description.strip()
            if data.description
            else None
        ),

        is_communicable=(
            data.is_communicable
        ),

        is_reportable=(
            data.is_reportable
        ),

        is_sensitive=(
            data.is_sensitive
        ),

        privacy_category=(
            data.privacy_category
            .strip()
            .upper()
        ),

        is_active=True,
    )

    try:
        db.add(
            disease
        )

        db.commit()

        db.refresh(
            disease
        )

    except Exception:
        db.rollback()
        raise

    return disease


# =========================================================
# UPDATE DISEASE
# =========================================================

def update_disease(
    db: Session,
    disease: Disease,
    data: DiseaseUpdate,
):
    update_data = data.model_dump(
        exclude_unset=True
    )


    # -----------------------------------------------------
    # CLEAN CODE
    # -----------------------------------------------------

    if (
        "code" in update_data
        and update_data["code"]
        is not None
    ):
        update_data["code"] = (
            update_data["code"]
            .strip()
            .upper()
        )


    # -----------------------------------------------------
    # CLEAN NAME
    # -----------------------------------------------------

    if (
        "name" in update_data
        and update_data["name"]
        is not None
    ):
        update_data["name"] = (
            update_data["name"]
            .strip()
        )


    # -----------------------------------------------------
    # CLEAN OPTIONAL TEXT FIELDS
    # -----------------------------------------------------

    for field in (
        "category",
        "transmission_type",
        "description",
    ):
        if (
            field in update_data
            and update_data[field]
            is not None
        ):
            cleaned = (
                update_data[field]
                .strip()
            )

            update_data[field] = (
                cleaned
                if cleaned
                else None
            )


    # -----------------------------------------------------
    # CLEAN PRIVACY CATEGORY
    # -----------------------------------------------------

    if (
        "privacy_category"
        in update_data
        and update_data[
            "privacy_category"
        ]
        is not None
    ):
        update_data[
            "privacy_category"
        ] = (
            update_data[
                "privacy_category"
            ]
            .strip()
            .upper()
        )


    # -----------------------------------------------------
    # CHECK DUPLICATE CODE OR NAME
    # -----------------------------------------------------

    new_code = update_data.get(
        "code",
        disease.code,
    )

    new_name = update_data.get(
        "name",
        disease.name,
    )

    existing = db.scalar(
        select(Disease).where(
            Disease.id !=
            disease.id,

            or_(
                Disease.code ==
                new_code,

                Disease.name ==
                new_name,
            ),
        )
    )

    if existing:
        raise ValueError(
            "Disease code or name already exists."
        )


    # -----------------------------------------------------
    # APPLY CHANGES
    # -----------------------------------------------------

    for field, value in (
        update_data.items()
    ):
        setattr(
            disease,
            field,
            value,
        )


    # -----------------------------------------------------
    # SAVE CHANGES
    # -----------------------------------------------------

    try:
        db.commit()

        db.refresh(
            disease
        )

    except Exception:
        db.rollback()
        raise


    return disease