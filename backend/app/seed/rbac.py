from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.permission import Permission
from app.models.role import Role


# =========================================================
# DEFAULT PERMISSIONS
# =========================================================

DEFAULT_PERMISSIONS = [
    {
        "code": "PATIENT_CREATE",
        "name": "Create Patient",
        "module": "patients",
        "description": "Create new patient records",
    },
    {
        "code": "PATIENT_VIEW",
        "name": "View Patient",
        "module": "patients",
        "description": "View patient records",
    },
    {
        "code": "PATIENT_UPDATE",
        "name": "Update Patient",
        "module": "patients",
        "description": "Update patient records",
    },
    {
        "code": "CONSULTATION_CREATE",
        "name": "Create Consultation",
        "module": "consultations",
        "description": "Create consultation records",
    },
    {
        "code": "DIAGNOSIS_CREATE",
        "name": "Create Diagnosis",
        "module": "consultations",
        "description": "Record patient diagnoses",
    },
    {
        "code": "DISEASE_PREDICT",
        "name": "Run Disease Decision Support",
        "module": "ml_decision_support",
        "description": (
            "Run the development disease "
            "classification decision-support tool"
        ),
    },
    {
        "code": "SURVEILLANCE_VIEW",
        "name": "View Disease Surveillance",
        "module": "surveillance",
        "description": "View disease surveillance data",
    },
    {
        "code": "FORECAST_VIEW",
        "name": "View Forecasts",
        "module": "forecasting",
        "description": "View disease and medicine forecasts",
    },
    {
        "code": "INVENTORY_VIEW",
        "name": "View Inventory",
        "module": "inventory",
        "description": "View medicine inventory",
    },
    {
        "code": "INVENTORY_ADJUST",
        "name": "Adjust Inventory",
        "module": "inventory",
        "description": "Create authorized inventory adjustments",
    },
    {
        "code": "REPORT_VIEW",
        "name": "View Reports",
        "module": "reports",
        "description": "View system reports",
    },
    {
        "code": "USER_MANAGE",
        "name": "Manage Users",
        "module": "administration",
        "description": "Create and manage user accounts",
    },
    {
        "code": "ROLE_MANAGE",
        "name": "Manage Roles",
        "module": "administration",
        "description": "Manage roles and permissions",
    },
    {
        "code": "AUDIT_VIEW",
        "name": "View Audit Logs",
        "module": "administration",
        "description": "View system audit logs",
    },
    {
        "code": "MEDICINE_DISPENSE",
        "name": "Dispense Medicine",
        "module": "medicine",
        "description": (
            "Record medicine dispensing "
            "transactions during a consultation"
        ),
    },
    {
        "code": "DISEASE_CASE_CREATE",
        "name": "Create Disease Case",
        "module": "disease_surveillance",
        "description": (
            "Record a disease case from "
            "an authorized consultation"
        ),
    },
    {
        "code": "DISEASE_CASE_VALIDATE",
        "name": "Validate Disease Case",
        "module": "disease_surveillance",
        "description": (
            "Validate or reject disease cases "
            "before surveillance use"
        ),
    },
    {
        "code": "SENSITIVE_DISEASE_VIEW",
        "name": "View Sensitive Disease Records",
        "module": "disease_surveillance",
        "description": (
            "View patient-identifiable "
            "sensitive disease information"
        ),
    },
]


# =========================================================
# DEFAULT ROLE-PERMISSION MATRIX
# =========================================================
#
# DISEASE_PREDICT is intentionally limited to authorized
# health-center clinical/operational roles. SYSTEM_ADMIN is
# not granted this clinical decision-support permission.
# BHW is also excluded from this Phase 4 default.
#
# Final disease-case validation remains DOCTOR-only.
# =========================================================

DEFAULT_ROLES = {
    "SYSTEM_ADMIN": [
        "PATIENT_CREATE",
        "PATIENT_VIEW",
        "PATIENT_UPDATE",
        "CONSULTATION_CREATE",
        "DIAGNOSIS_CREATE",
        "SURVEILLANCE_VIEW",
        "FORECAST_VIEW",
        "INVENTORY_VIEW",
        "INVENTORY_ADJUST",
        "REPORT_VIEW",
        "USER_MANAGE",
        "ROLE_MANAGE",
        "AUDIT_VIEW",
    ],

    "HEALTH_CENTER_ADMIN": [
        "PATIENT_CREATE",
        "PATIENT_VIEW",
        "PATIENT_UPDATE",
        "CONSULTATION_CREATE",
        "DIAGNOSIS_CREATE",
        "DISEASE_PREDICT",
        "SURVEILLANCE_VIEW",
        "FORECAST_VIEW",
        "INVENTORY_VIEW",
        "INVENTORY_ADJUST",
        "REPORT_VIEW",
        "USER_MANAGE",
        "AUDIT_VIEW",
        "MEDICINE_DISPENSE",
        "DISEASE_CASE_CREATE",
    ],

    "DOCTOR": [
        "PATIENT_VIEW",
        "PATIENT_UPDATE",
        "CONSULTATION_CREATE",
        "DIAGNOSIS_CREATE",
        "DISEASE_PREDICT",
        "SURVEILLANCE_VIEW",
        "FORECAST_VIEW",
        "INVENTORY_VIEW",
        "REPORT_VIEW",
        "MEDICINE_DISPENSE",
        "DISEASE_CASE_CREATE",
        "DISEASE_CASE_VALIDATE",
        "SENSITIVE_DISEASE_VIEW",
    ],

    "NURSE": [
        "PATIENT_CREATE",
        "PATIENT_VIEW",
        "PATIENT_UPDATE",
        "CONSULTATION_CREATE",
        "DISEASE_PREDICT",
        "SURVEILLANCE_VIEW",
        "FORECAST_VIEW",
        "INVENTORY_VIEW",
        "REPORT_VIEW",
        "MEDICINE_DISPENSE",
        "DISEASE_CASE_CREATE",
    ],

    "MIDWIFE": [
        "PATIENT_CREATE",
        "PATIENT_VIEW",
        "PATIENT_UPDATE",
        "CONSULTATION_CREATE",
        "DISEASE_PREDICT",
        "SURVEILLANCE_VIEW",
        "FORECAST_VIEW",
        "INVENTORY_VIEW",
        "REPORT_VIEW",
        "MEDICINE_DISPENSE",
        "DISEASE_CASE_CREATE",
    ],

    "BHW": [
        "PATIENT_CREATE",
        "PATIENT_VIEW",
        "PATIENT_UPDATE",
        "SURVEILLANCE_VIEW",
        "INVENTORY_VIEW",
        "MEDICINE_DISPENSE",
        "DISEASE_CASE_CREATE",
    ],
}


ROLE_DESCRIPTIONS = {
    "SYSTEM_ADMIN":
        "System Administrator",

    "HEALTH_CENTER_ADMIN":
        "Health Center Administrator",

    "DOCTOR":
        "Health Center Doctor",

    "NURSE":
        "Health Center Nurse",

    "MIDWIFE":
        "Health Center Midwife",

    "BHW":
        "Barangay Health Worker",
}


def seed_rbac():
    db = SessionLocal()

    try:
        permission_map = {}

        for permission_data in (
            DEFAULT_PERMISSIONS
        ):
            existing_permission = db.scalar(
                select(Permission).where(
                    Permission.code
                    == permission_data[
                        "code"
                    ]
                )
            )

            if existing_permission:
                permission = (
                    existing_permission
                )

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

            else:
                permission = Permission(
                    **permission_data
                )

                db.add(
                    permission
                )

                db.flush()

            permission_map[
                permission.code
            ] = permission

        for (
            role_name,
            permission_codes,
        ) in DEFAULT_ROLES.items():
            role = db.scalar(
                select(Role).where(
                    Role.name
                    == role_name
                )
            )

            if not role:
                role = Role(
                    name=role_name,
                    description=(
                        ROLE_DESCRIPTIONS[
                            role_name
                        ]
                    ),
                )

                db.add(role)
                db.flush()

            else:
                role.description = (
                    ROLE_DESCRIPTIONS[
                        role_name
                    ]
                )

            role.permissions = [
                permission_map[code]
                for code
                in permission_codes
            ]

        db.commit()

        print(
            "RBAC seed completed "
            "successfully."
        )

        print(
            "Configured roles:"
        )

        for role_name in DEFAULT_ROLES:
            print(
                f"  - {role_name}"
            )

        print(
            "Disease decision-support "
            "permission:"
        )

        for role_name in (
            "HEALTH_CENTER_ADMIN",
            "DOCTOR",
            "NURSE",
            "MIDWIFE",
        ):
            print(
                "  [YES] "
                f"DISEASE_PREDICT -> "
                f"{role_name}"
            )

        for role_name in (
            "SYSTEM_ADMIN",
            "BHW",
        ):
            print(
                "  [NO]  "
                f"DISEASE_PREDICT -> "
                f"{role_name}"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_rbac()
