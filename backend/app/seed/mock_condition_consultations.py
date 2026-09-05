
from __future__ import annotations

import argparse
import random
from datetime import date, datetime, time, timedelta

from sqlalchemy import delete, func, select

from app.db.session import SessionLocal
from app.models.consultation import Consultation
from app.models.disease import Disease
from app.models.patient import Patient
from app.models.user import User


MOCK_PREFIX = "MOCK-KNL-"
MARKER = "SYNTHETIC_DEVELOPMENT_DATA | MOCK_CONDITION_VISIT"
RANDOM_SEED = 202609051122
START_DATE = date(2021, 1, 1)
END_DATE = date(2026, 8, 31)

# Development scenario sizes only; not prevalence estimates.
VISIT_PLAN = {
    "HTN": (380, 2, 4, 30),
    "T2DM": (240, 2, 4, 30),
    "DYSLIPIDEMIA": (220, 1, 3, 30),
    "ASTHMA": (210, 1, 3, 5),
    "COPD": (80, 1, 3, 40),
    "UTI": (170, 1, 2, 5),
    "PNEUMONIA": (130, 1, 2, 1),
    "HELMINTHIASIS": (110, 1, 2, 5),
    "FUNGAL_INFECTION": (110, 1, 2, 5),
    "GERD_DYSPEPSIA": (180, 1, 3, 18),
    "GOUT": (85, 1, 2, 25),
    "IRON_DEF_ANEMIA": (145, 1, 3, 10),
    "ALLERGIC_RHINITIS": (180, 1, 3, 5),
    "IHD_ANGINA": (70, 1, 3, 40),
}


def _age_on(patient: Patient, value: date) -> int:
    dob = patient.date_of_birth
    return (
        value.year
        - dob.year
        - ((value.month, value.day) < (dob.month, dob.day))
    )


def _random_date(
    rng: random.Random,
    patient: Patient,
) -> date | None:
    minimum = max(
        START_DATE,
        patient.date_of_birth + timedelta(days=30),
    )
    if minimum > END_DATE:
        return None

    return minimum + timedelta(
        days=rng.randint(
            0,
            (END_DATE - minimum).days,
        )
    )


def _find_recorder(db) -> User:
    users = db.scalars(
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.id.asc())
    ).all()

    for preferred in ["NURSE", "MIDWIFE", "DOCTOR", "BHW"]:
        for user in users:
            if preferred in {role.name for role in user.roles}:
                return user

    if users:
        return users[0]

    raise RuntimeError("No active user found.")


def _remove_existing(db) -> int:
    ids = list(
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
                    f"{MARKER}%"
                ),
            )
        ).all()
    )

    if ids:
        db.execute(
            delete(Consultation).where(
                Consultation.id.in_(ids)
            )
        )
        db.flush()

    return len(ids)


def seed_mock_condition_consultations(
    *,
    replace: bool,
):
    db = SessionLocal()
    rng = random.Random(RANDOM_SEED)

    try:
        if replace:
            print(
                f"[CLEANUP] Removed "
                f"{_remove_existing(db)} previous mock condition visits."
            )
        else:
            existing = db.scalar(
                select(func.count(Consultation.id))
                .join(
                    Patient,
                    Patient.id == Consultation.patient_id,
                )
                .where(
                    Patient.patient_code.like(
                        f"{MOCK_PREFIX}%"
                    ),
                    Consultation.notes.like(
                        f"{MARKER}%"
                    ),
                )
            )
            if existing:
                raise RuntimeError(
                    "Mock condition visits already exist. Use --replace."
                )

        patients = list(
            db.scalars(
                select(Patient)
                .where(
                    Patient.patient_code.like(
                        f"{MOCK_PREFIX}%"
                    ),
                    Patient.record_status == "ACTIVE",
                )
                .order_by(Patient.id.asc())
            ).all()
        )

        if len(patients) < 1500:
            raise RuntimeError(
                "Expected the existing 1,500 MOCK-KNL-* patients."
            )

        diseases = {
            disease.code: disease
            for disease in db.scalars(
                select(Disease).where(
                    Disease.code.in_(list(VISIT_PLAN))
                )
            ).all()
        }

        missing = [
            code for code in VISIT_PLAN
            if code not in diseases
        ]
        if missing:
            raise RuntimeError(
                "Missing expanded condition rows: "
                + ", ".join(missing)
                + ". Run expanded_condition_master first."
            )

        recorder = _find_recorder(db)
        reference_date = date(2026, 9, 5)
        created = 0

        print("MOCK CONDITION CONSULTATION SEED")
        print("================================")
        print(f"Mock patient pool: {len(patients)}")
        print(f"Recorder: {recorder.username}")
        print()

        for disease_code, plan in VISIT_PLAN.items():
            patient_count, visits_min, visits_max, minimum_age = plan
            disease = diseases[disease_code]
            eligible = [
                patient
                for patient in patients
                if _age_on(patient, reference_date) >= minimum_age
            ]
            selected = rng.sample(
                eligible,
                k=min(patient_count, len(eligible)),
            )
            disease_created = 0

            for patient in selected:
                used_dates = set()

                for _ in range(
                    rng.randint(visits_min, visits_max)
                ):
                    visit_date = _random_date(rng, patient)
                    if visit_date is None:
                        continue

                    attempts = 0
                    while visit_date in used_dates and attempts < 20:
                        visit_date = _random_date(rng, patient)
                        attempts += 1

                    if (
                        visit_date is None
                        or visit_date in used_dates
                        or _age_on(patient, visit_date) < minimum_age
                    ):
                        continue

                    used_dates.add(visit_date)

                    db.add(
                        Consultation(
                            patient_id=patient.id,
                            disease_id=disease.id,
                            consultation_date=datetime.combine(
                                visit_date,
                                time(
                                    hour=rng.randint(8, 16),
                                    minute=rng.choice(
                                        [0,10,20,30,40,50]
                                    ),
                                ),
                            ),
                            chief_complaint=(
                                f"Development follow-up / consultation "
                                f"for {disease.name}"
                            ),
                            symptoms=(
                                "Synthetic development condition visit."
                            ),
                            assessment=(
                                f"{MARKER} | {disease_code}. "
                                "Not a real clinical assessment."
                            ),
                            diagnosis=disease.name,
                            treatment_plan=(
                                "TEST RECORD ONLY. No real patient "
                                "treatment or prescription represented."
                            ),
                            notes=(
                                f"{MARKER} | {disease_code} | "
                                "NOT OFFICIAL HEALTH-CENTER DATA"
                            ),
                            recorded_by=recorder.id,
                        )
                    )
                    created += 1
                    disease_created += 1

            db.flush()
            print(
                f"[CREATED] {disease_code}: "
                f"{disease_created} visits"
            )

        db.commit()

        print()
        print("MOCK CONDITION CONSULTATIONS COMPLETE")
        print("=====================================")
        print(f"Total condition visits created: {created}")
        print(
            "No DiseaseCase rows were created for these "
            "expanded condition visits, so communicable "
            "surveillance totals are not silently changed."
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    seed_mock_condition_consultations(
        replace=args.replace,
    )
