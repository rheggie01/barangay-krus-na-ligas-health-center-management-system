from sqlalchemy import (
    delete,
    select,
)

from app.db.session import SessionLocal
from app.models.consultation import Consultation
from app.models.disease_case import DiseaseCase
from app.models.patient import Patient


MOCK_PREFIX = "MOCK-KNL-"


def remove_mock_surveillance():
    db = SessionLocal()

    try:
        mock_patient_ids = list(
            db.scalars(
                select(
                    Patient.id
                ).where(
                    Patient.patient_code.like(
                        f"{MOCK_PREFIX}%"
                    )
                )
            ).all()
        )

        if not mock_patient_ids:
            print(
                "No MOCK-KNL-* surveillance "
                "records found."
            )

            return

        db.execute(
            delete(
                DiseaseCase
            ).where(
                DiseaseCase.patient_id.in_(
                    mock_patient_ids
                )
            )
        )

        db.execute(
            delete(
                Consultation
            ).where(
                Consultation.patient_id.in_(
                    mock_patient_ids
                )
            )
        )

        db.execute(
            delete(
                Patient
            ).where(
                Patient.id.in_(
                    mock_patient_ids
                )
            )
        )

        db.commit()

        print(
            "Removed synthetic surveillance "
            f"records for {len(mock_patient_ids)} "
            "MOCK-KNL-* patients."
        )

        print(
            "Non-mock patients and records "
            "were not deleted."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    remove_mock_surveillance()
