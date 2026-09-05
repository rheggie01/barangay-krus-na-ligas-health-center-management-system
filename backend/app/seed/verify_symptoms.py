from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.symptom import Symptom


def verify_symptoms() -> None:
    db = SessionLocal()

    try:
        symptoms = db.scalars(
            select(Symptom)
            .order_by(
                Symptom.name.asc()
            )
        ).all()

        if not symptoms:
            raise RuntimeError(
                "No structured symptoms "
                "were found in the database."
            )

        inactive = [
            symptom.code
            for symptom in symptoms
            if not symptom.is_active
        ]

        if inactive:
            raise RuntimeError(
                "Inactive symptom(s) found: "
                + ", ".join(inactive)
            )

        print(
            "Structured symptom "
            "verification passed."
        )

        print(
            f"Active symptoms: "
            f"{len(symptoms)}"
        )

        for symptom in symptoms:
            print(
                f"  - {symptom.code}: "
                f"{symptom.name}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    verify_symptoms()
