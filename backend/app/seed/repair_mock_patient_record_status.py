from sqlalchemy import func, select, update

from app.db.session import SessionLocal
from app.models.patient import Patient


MOCK_PREFIX = "MOCK-KNL-"


def repair_mock_patient_record_status():
    db = SessionLocal()

    try:
        total_mock = db.scalar(
            select(
                func.count(
                    Patient.id
                )
            ).where(
                Patient.patient_code.like(
                    f"{MOCK_PREFIX}%"
                )
            )
        )

        invalid_mock = db.scalar(
            select(
                func.count(
                    Patient.id
                )
            ).where(
                Patient.patient_code.like(
                    f"{MOCK_PREFIX}%"
                ),
                Patient.record_status.notin_(
                    [
                        "ACTIVE",
                        "INACTIVE",
                    ]
                ),
            )
        )

        print(
            "MOCK PATIENT RECORD-STATUS REPAIR"
        )
        print(
            "================================="
        )
        print(
            f"MOCK-KNL patients: {total_mock}"
        )
        print(
            f"Invalid record_status rows: {invalid_mock}"
        )

        if not invalid_mock:
            print()
            print(
                "No repair needed."
            )
            return

        result = db.execute(
            update(
                Patient
            )
            .where(
                Patient.patient_code.like(
                    f"{MOCK_PREFIX}%"
                ),
                Patient.record_status.notin_(
                    [
                        "ACTIVE",
                        "INACTIVE",
                    ]
                ),
            )
            .values(
                record_status="ACTIVE"
            )
        )

        db.commit()

        remaining_invalid = db.scalar(
            select(
                func.count(
                    Patient.id
                )
            ).where(
                Patient.patient_code.like(
                    f"{MOCK_PREFIX}%"
                ),
                Patient.record_status.notin_(
                    [
                        "ACTIVE",
                        "INACTIVE",
                    ]
                ),
            )
        )

        print(
            f"Rows repaired: {result.rowcount}"
        )
        print(
            f"Remaining invalid rows: "
            f"{remaining_invalid}"
        )

        if remaining_invalid:
            raise RuntimeError(
                "Some MOCK-KNL patient record_status "
                "values are still invalid."
            )

        print()
        print(
            "Repair complete."
        )
        print(
            "MOCK-KNL-* still identifies synthetic "
            "development patients; record_status now "
            "uses the valid operational value ACTIVE."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    repair_mock_patient_record_status()
