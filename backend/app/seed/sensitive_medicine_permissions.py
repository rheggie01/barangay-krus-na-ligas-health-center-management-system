from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.permission import Permission
from app.models.role import Role


PERMISSIONS = [
    {
        "code":
            "SENSITIVE_MEDICINE_VIEW",

        "name":
            "View Sensitive Program Medicines",

        "module":
            "medicine",

        "description":
            (
                "View sensitive/program-managed "
                "medicine inventory records"
            ),
    },
    {
        "code":
            "SENSITIVE_MEDICINE_DISPENSE",

        "name":
            "Dispense Sensitive Program Medicines",

        "module":
            "medicine",

        "description":
            (
                "Dispense restricted sensitive/"
                "program-managed medicines"
            ),
    },
]


ROLE_PERMISSION_MATRIX = {
    # Inventory/program oversight.
    "HEALTH_CENTER_ADMIN": {
        "SENSITIVE_MEDICINE_VIEW",
    },

    # Conservative default: restricted clinical dispensing
    # is doctor-only unless the health center formally
    # authorizes additional personnel.
    "DOCTOR": {
        "SENSITIVE_MEDICINE_VIEW",
        "SENSITIVE_MEDICINE_DISPENSE",
    },
}


def seed_sensitive_medicine_permissions():
    db = SessionLocal()

    try:
        permission_map = {}

        for permission_data in PERMISSIONS:
            permission = db.scalar(
                select(Permission).where(
                    Permission.code
                    == permission_data[
                        "code"
                    ]
                )
            )

            if permission is None:
                permission = Permission(
                    **permission_data
                )

                db.add(
                    permission
                )

                db.flush()

            else:
                permission.name = (
                    permission_data[
                        "name"
                    ]
                )

                permission.module = (
                    permission_data[
                        "module"
                    ]
                )

                permission.description = (
                    permission_data[
                        "description"
                    ]
                )

            permission_map[
                permission.code
            ] = permission

        for (
            role_name,
            permission_codes,
        ) in ROLE_PERMISSION_MATRIX.items():
            role = db.scalar(
                select(Role).where(
                    Role.name
                    == role_name
                )
            )

            if role is None:
                raise RuntimeError(
                    "Required role does not "
                    f"exist: {role_name}. "
                    "Run the normal RBAC seed first."
                )

            existing_codes = {
                permission.code
                for permission
                in role.permissions
            }

            for permission_code in (
                permission_codes
            ):
                if (
                    permission_code
                    not in existing_codes
                ):
                    role.permissions.append(
                        permission_map[
                            permission_code
                        ]
                    )

        db.commit()

        print(
            "Sensitive medicine permission "
            "setup complete."
        )

        print(
            "  HEALTH_CENTER_ADMIN: "
            "SENSITIVE_MEDICINE_VIEW"
        )

        print(
            "  DOCTOR: "
            "SENSITIVE_MEDICINE_VIEW + "
            "SENSITIVE_MEDICINE_DISPENSE"
        )

        print(
            "  SYSTEM_ADMIN / NURSE / "
            "MIDWIFE / BHW: no restricted "
            "sensitive medicine permission "
            "by default."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_sensitive_medicine_permissions()
