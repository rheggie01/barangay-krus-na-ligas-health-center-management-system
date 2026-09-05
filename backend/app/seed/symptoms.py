from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.symptom import Symptom


# =========================================================
# DEFAULT STRUCTURED SYMPTOMS
# =========================================================

DEFAULT_SYMPTOMS = [
    {
        "code": "FEVER",
        "name": "Fever",
    },
    {
        "code": "COUGH",
        "name": "Cough",
    },
    {
        "code": "RUNNY_NOSE",
        "name": "Colds / Runny Nose",
    },
    {
        "code": "SORE_THROAT",
        "name": "Sore Throat",
    },
    {
        "code": "HEADACHE",
        "name": "Headache",
    },
    {
        "code": "BODY_PAIN",
        "name": "Body Pain",
    },
    {
        "code": "VOMITING",
        "name": "Vomiting",
    },
    {
        "code": "DIARRHEA",
        "name": "Diarrhea",
    },
    {
        "code": "ABDOMINAL_PAIN",
        "name": "Abdominal Pain",
    },
    {
        "code": "RASH",
        "name": "Rash",
    },
    {
        "code": "NAUSEA",
        "name": "Nausea",
    },
    {
        "code": "FATIGUE",
        "name": "Weakness / Fatigue",
    },
    {
        "code": "DIFFICULTY_BREATHING",
        "name": "Difficulty Breathing",
    },
    {
        "code": "LOSS_OF_APPETITE",
        "name": "Loss of Appetite",
    },
    {
        "code": "CHILLS",
        "name": "Chills",
    },
]


# =========================================================
# SEED STRUCTURED SYMPTOMS
# =========================================================

def seed_symptoms() -> None:
    db = SessionLocal()

    try:
        created_count = 0
        updated_count = 0

        for symptom_data in DEFAULT_SYMPTOMS:
            existing_symptom = db.scalar(
                select(Symptom).where(
                    Symptom.code
                    == symptom_data["code"]
                )
            )

            if existing_symptom:
                existing_symptom.name = (
                    symptom_data["name"]
                )
                existing_symptom.is_active = True

                updated_count += 1
                continue

            symptom = Symptom(
                code=symptom_data["code"],
                name=symptom_data["name"],
                is_active=True,
            )

            db.add(symptom)
            created_count += 1

        db.commit()

        print(
            "Structured symptom seed "
            "completed successfully."
        )

        print(
            f"Created: {created_count}"
        )

        print(
            f"Updated/reactivated: "
            f"{updated_count}"
        )

        print("Configured symptoms:")

        for symptom_data in DEFAULT_SYMPTOMS:
            print(
                f"  - "
                f"{symptom_data['code']}: "
                f"{symptom_data['name']}"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_symptoms()
