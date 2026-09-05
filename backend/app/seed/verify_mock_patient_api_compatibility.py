from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.patient import Patient
from app.schemas.patient import PatientResponse


MOCK_PREFIX = "MOCK-KNL-"


def verify_mock_patient_api_compatibility():
    db = SessionLocal()

    try:
        mock_patients = db.scalars(
            select(
                Patient
            ).where(
                Patient.patient_code.like(
                    f"{MOCK_PREFIX}%"
                )
            )
            .order_by(
                Patient.id.asc()
            )
        ).all()

        print(
            "MOCK PATIENT API COMPATIBILITY"
        )
        print(
            "=============================="
        )
        print(
            f"MOCK-KNL patients: "
            f"{len(mock_patients)}"
        )

        invalid_status = [
            patient
            for patient in mock_patients
            if patient.record_status
            not in {
                "ACTIVE",
                "INACTIVE",
            }
        ]

        schema_failures = []

        for patient in mock_patients:
            try:
                PatientResponse.model_validate(
                    patient
                )

            except Exception as exc:
                schema_failures.append(
                    (
                        patient.patient_code,
                        str(
                            exc
                        ),
                    )
                )

        print(
            f"Invalid record_status rows: "
            f"{len(invalid_status)}"
        )
        print(
            f"PatientResponse failures: "
            f"{len(schema_failures)}"
        )

        if invalid_status:
            raise RuntimeError(
                "Invalid record_status remains on "
                "one or more MOCK-KNL patients."
            )

        if schema_failures:
            print()
            print(
                "First schema failure:"
            )
            print(
                schema_failures[
                    0
                ][
                    0
                ]
            )
            print(
                schema_failures[
                    0
                ][
                    1
                ]
            )

            raise RuntimeError(
                "One or more MOCK-KNL patients still "
                "fail PatientResponse validation."
            )

        print()
        print(
            "Verification passed."
        )

    finally:
        db.close()


if __name__ == "__main__":
    verify_mock_patient_api_compatibility()
