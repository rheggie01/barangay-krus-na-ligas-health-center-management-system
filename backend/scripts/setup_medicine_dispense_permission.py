from sqlalchemy import (
    MetaData,
    Table,
    delete,
    insert,
    select,
)

from app.db.session import SessionLocal


# =========================================================
# PERMISSION CONFIGURATION
# =========================================================

PERMISSION_CODE = "MEDICINE_DISPENSE"

PERMISSION_NAME = "Dispense Medicine"

PERMISSION_MODULE = "INVENTORY"

PERMISSION_DESCRIPTION = (
    "Allows authorized health-center staff "
    "to dispense medicine to registered patients."
)


# =========================================================
# ROLES ALLOWED TO DISPENSE
# =========================================================

ALLOWED_ROLE_NAMES = {
    "HEALTH_CENTER_ADMIN",
    "DOCTOR",
    "NURSE",
    "MIDWIFE",
    "BHW",
}


# =========================================================
# ROLES NOT ALLOWED TO DISPENSE
# =========================================================

DENIED_ROLE_NAMES = {
    "SYSTEM_ADMIN",
}


# =========================================================
# FIND FOREIGN KEY COLUMN
# =========================================================

def find_foreign_key_column(
    table: Table,
    target_table_name: str,
):
    """
    Finds the column inside an association table
    that points to the requested target table.

    Example:

    role_permissions.role_id
        -> roles.id

    role_permissions.permission_id
        -> permissions.id
    """

    for column in table.columns:
        for foreign_key in column.foreign_keys:
            if (
                foreign_key.column.table.name
                == target_table_name
            ):
                return column

    raise RuntimeError(
        f"Unable to find foreign key from "
        f"'{table.name}' to "
        f"'{target_table_name}'."
    )


# =========================================================
# GET OR CREATE PERMISSION
# =========================================================

def get_or_create_permission(
    db,
    permissions_table: Table,
) -> int:
    permission_id = db.scalar(
        select(
            permissions_table.c.id
        ).where(
            permissions_table.c.code
            == PERMISSION_CODE
        )
    )

    if permission_id:
        print(
            f"[OK] Permission already exists: "
            f"{PERMISSION_CODE}"
        )

        # Keep existing permission information
        # synchronized with the current configuration.
        db.execute(
            permissions_table.update()
            .where(
                permissions_table.c.id
                == permission_id
            )
            .values(
                name=PERMISSION_NAME,
                module=PERMISSION_MODULE,
                description=(
                    PERMISSION_DESCRIPTION
                ),
            )
        )

        return int(
            permission_id
        )

    result = db.execute(
        insert(
            permissions_table
        ).values(
            code=PERMISSION_CODE,
            name=PERMISSION_NAME,
            module=PERMISSION_MODULE,
            description=(
                PERMISSION_DESCRIPTION
            ),
        )
    )

    permission_id = (
        result.inserted_primary_key[0]
        if result.inserted_primary_key
        else None
    )

    if not permission_id:
        permission_id = db.scalar(
            select(
                permissions_table.c.id
            ).where(
                permissions_table.c.code
                == PERMISSION_CODE
            )
        )

    if not permission_id:
        raise RuntimeError(
            "Unable to create "
            "MEDICINE_DISPENSE permission."
        )

    print(
        f"[CREATED] Permission: "
        f"{PERMISSION_CODE}"
    )

    return int(
        permission_id
    )


# =========================================================
# GET ROLE
# =========================================================

def get_role_id(
    db,
    roles_table: Table,
    role_name: str,
):
    return db.scalar(
        select(
            roles_table.c.id
        ).where(
            roles_table.c.name
            == role_name
        )
    )


# =========================================================
# CHECK ROLE PERMISSION
# =========================================================

def role_has_permission(
    db,
    role_permissions_table: Table,
    role_id_column,
    permission_id_column,
    role_id: int,
    permission_id: int,
) -> bool:
    existing = db.scalar(
        select(
            role_id_column
        ).where(
            role_id_column
            == role_id,
            permission_id_column
            == permission_id,
        )
    )

    return existing is not None


# =========================================================
# ASSIGN PERMISSION
# =========================================================

def assign_permission(
    db,
    role_permissions_table: Table,
    role_id_column,
    permission_id_column,
    role_name: str,
    role_id: int,
    permission_id: int,
):
    if role_has_permission(
        db=db,
        role_permissions_table=(
            role_permissions_table
        ),
        role_id_column=(
            role_id_column
        ),
        permission_id_column=(
            permission_id_column
        ),
        role_id=role_id,
        permission_id=permission_id,
    ):
        print(
            f"[OK] {role_name} already has "
            f"{PERMISSION_CODE}"
        )

        return

    db.execute(
        insert(
            role_permissions_table
        ).values(
            {
                role_id_column.name:
                    role_id,

                permission_id_column.name:
                    permission_id,
            }
        )
    )

    print(
        f"[ASSIGNED] {PERMISSION_CODE} "
        f"-> {role_name}"
    )


# =========================================================
# REMOVE PERMISSION
# =========================================================

def remove_permission(
    db,
    role_permissions_table: Table,
    role_id_column,
    permission_id_column,
    role_name: str,
    role_id: int,
    permission_id: int,
):
    if not role_has_permission(
        db=db,
        role_permissions_table=(
            role_permissions_table
        ),
        role_id_column=(
            role_id_column
        ),
        permission_id_column=(
            permission_id_column
        ),
        role_id=role_id,
        permission_id=permission_id,
    ):
        print(
            f"[OK] {role_name} does not have "
            f"{PERMISSION_CODE}"
        )

        return

    db.execute(
        delete(
            role_permissions_table
        ).where(
            role_id_column
            == role_id,

            permission_id_column
            == permission_id,
        )
    )

    print(
        f"[REMOVED] {PERMISSION_CODE} "
        f"from {role_name}"
    )


# =========================================================
# MAIN SETUP
# =========================================================

def setup_medicine_dispense_permission():
    db = SessionLocal()

    try:
        bind = db.get_bind()

        metadata = MetaData()


        # -------------------------------------------------
        # REFLECT EXISTING DATABASE TABLES
        #
        # Ginagamit natin ang existing tables mismo para
        # hindi tayo manghula kung saang Python association
        # model naka-declare ang role_permissions.
        # -------------------------------------------------

        roles_table = Table(
            "roles",
            metadata,
            autoload_with=bind,
        )

        permissions_table = Table(
            "permissions",
            metadata,
            autoload_with=bind,
        )

        role_permissions_table = Table(
            "role_permissions",
            metadata,
            autoload_with=bind,
        )


        # -------------------------------------------------
        # FIND ASSOCIATION COLUMNS
        # -------------------------------------------------

        role_id_column = (
            find_foreign_key_column(
                role_permissions_table,
                "roles",
            )
        )

        permission_id_column = (
            find_foreign_key_column(
                role_permissions_table,
                "permissions",
            )
        )


        # -------------------------------------------------
        # CREATE / GET PERMISSION
        # -------------------------------------------------

        permission_id = (
            get_or_create_permission(
                db=db,
                permissions_table=(
                    permissions_table
                ),
            )
        )


        # -------------------------------------------------
        # ASSIGN TO OPERATIONAL ROLES
        # -------------------------------------------------

        print()
        print(
            "Assigning medicine dispensing permission..."
        )
        print()


        for role_name in sorted(
            ALLOWED_ROLE_NAMES
        ):
            role_id = get_role_id(
                db=db,
                roles_table=roles_table,
                role_name=role_name,
            )

            if not role_id:
                print(
                    f"[WARNING] Role not found: "
                    f"{role_name}"
                )

                continue

            assign_permission(
                db=db,

                role_permissions_table=(
                    role_permissions_table
                ),

                role_id_column=(
                    role_id_column
                ),

                permission_id_column=(
                    permission_id_column
                ),

                role_name=role_name,

                role_id=int(
                    role_id
                ),

                permission_id=(
                    permission_id
                ),
            )


        # -------------------------------------------------
        # REMOVE FROM DENIED ROLES
        # -------------------------------------------------

        print()
        print(
            "Checking restricted roles..."
        )
        print()


        for role_name in sorted(
            DENIED_ROLE_NAMES
        ):
            role_id = get_role_id(
                db=db,
                roles_table=roles_table,
                role_name=role_name,
            )

            if not role_id:
                print(
                    f"[WARNING] Role not found: "
                    f"{role_name}"
                )

                continue

            remove_permission(
                db=db,

                role_permissions_table=(
                    role_permissions_table
                ),

                role_id_column=(
                    role_id_column
                ),

                permission_id_column=(
                    permission_id_column
                ),

                role_name=role_name,

                role_id=int(
                    role_id
                ),

                permission_id=(
                    permission_id
                ),
            )


        # -------------------------------------------------
        # COMMIT EVERYTHING
        # -------------------------------------------------

        db.commit()


        print()
        print("=" * 60)
        print(
            "MEDICINE DISPENSE PERMISSION SETUP COMPLETE"
        )
        print("=" * 60)

        print()

        print(
            "Allowed:"
        )

        for role_name in sorted(
            ALLOWED_ROLE_NAMES
        ):
            print(
                f"  [YES] {role_name}"
            )

        print()

        print(
            "Not allowed:"
        )

        for role_name in sorted(
            DENIED_ROLE_NAMES
        ):
            print(
                f"  [NO]  {role_name}"
            )

        print()

    except Exception as exc:
        db.rollback()

        print()
        print(
            "Medicine dispense permission "
            "setup FAILED."
        )

        print(
            f"Reason: {exc}"
        )

        raise

    finally:
        db.close()


# =========================================================
# SCRIPT ENTRY POINT
# =========================================================

if __name__ == "__main__":
    setup_medicine_dispense_permission()