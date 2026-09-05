
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.ml.services.disease_medicine_mapping_service import (
    MOCK_DISPENSING_MARKER,
)
from app.models.consultation import Consultation
from app.models.consultation_medicine import ConsultationMedicine
from app.models.patient import Patient


MOCK_PREFIX = "MOCK-KNL-"
CONDITION_VISIT_MARKER = (
    "SYNTHETIC_DEVELOPMENT_DATA | MOCK_CONDITION_VISIT"
)


def remove_phase11_2_mock_resource_data():
    db = SessionLocal()
    try:
        dispensing_ids = list(
            db.scalars(
                select(ConsultationMedicine.id)
                .where(
                    ConsultationMedicine.remarks.like(
                        f"{MOCK_DISPENSING_MARKER}%"
                    )
                )
            ).all()
        )

        if dispensing_ids:
            db.execute(
                delete(ConsultationMedicine).where(
                    ConsultationMedicine.id.in_(dispensing_ids)
                )
            )

        consultation_ids = list(
            db.scalars(
                select(Consultation.id)
                .join(
                    Patient,
                    Patient.id == Consultation.patient_id,
                )
                .where(
                    Patient.patient_code.like(
                        f"{MOCK_PREFIX}%"
                    ),
                    Consultation.notes.like(
                        f"{CONDITION_VISIT_MARKER}%"
                    ),
                )
            ).all()
        )

        if consultation_ids:
            db.execute(
                delete(Consultation).where(
                    Consultation.id.in_(consultation_ids)
                )
            )

        db.commit()

        print("PHASE 11.2 MOCK RESOURCE DATA REMOVED")
        print("=====================================")
        print(
            f"Synthetic dispensing rows removed: "
            f"{len(dispensing_ids)}"
        )
        print(
            f"Synthetic condition visits removed: "
            f"{len(consultation_ids)}"
        )
        print(
            "Existing patients, prior disease cases, "
            "live inventory stock, and non-mock records were preserved."
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    remove_phase11_2_mock_resource_data()
