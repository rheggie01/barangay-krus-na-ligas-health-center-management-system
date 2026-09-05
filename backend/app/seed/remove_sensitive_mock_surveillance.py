from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.consultation import Consultation
from app.models.disease_case import DiseaseCase


MARKER = "SENSITIVE_MOCK_V1"


def remove_sensitive_mock_surveillance():
    db = SessionLocal()

    try:
        consultation_ids = list(
            db.scalars(
                select(Consultation.id).where(
                    Consultation.notes.like(
                        f"%{MARKER}%"
                    )
                )
            ).all()
        )

        if not consultation_ids:
            print("No SENSITIVE_MOCK_V1 records found.")
            return

        db.execute(
            delete(DiseaseCase).where(
                DiseaseCase.consultation_id.in_(consultation_ids)
            )
        )

        db.execute(
            delete(Consultation).where(
                Consultation.id.in_(consultation_ids)
            )
        )

        db.commit()

        print(
            f"Removed {len(consultation_ids)} sensitive mock consultations."
        )
        print("Disease master records were preserved.")
        print("General MOCK-KNL-* surveillance records were preserved.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    remove_sensitive_mock_surveillance()
