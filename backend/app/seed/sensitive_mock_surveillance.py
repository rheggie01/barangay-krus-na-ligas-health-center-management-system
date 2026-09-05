from __future__ import annotations

import argparse
import random
from datetime import date, datetime, time, timedelta

from sqlalchemy import delete, func, or_, select

from app.db.session import SessionLocal
from app.models.consultation import Consultation
from app.models.disease import Disease
from app.models.disease_case import DiseaseCase
from app.models.patient import Patient
from app.models.user import User


try:
    from app.models.symptom import Symptom

    STRUCTURED_SYMPTOMS_AVAILABLE = True

except ImportError:
    Symptom = None
    STRUCTURED_SYMPTOMS_AVAILABLE = False


MOCK_PATIENT_PREFIX = "MOCK-KNL-"
SENSITIVE_MOCK_MARKER = "SENSITIVE_MOCK_V1"
DATA_LABEL = "SYNTHETIC_DEVELOPMENT_DATA"
RANDOM_SEED = 20260905
START_DATE = date(2021, 1, 1)
END_DATE = date(2026, 8, 30)


SENSITIVE_DISEASES = {
    "TB": {
        "name": "Tuberculosis (TB)",
        "aliases": {
            "codes": {"TB", "TUBERCULOSIS", "PTB"},
            "names": {
                "tuberculosis",
                "tuberculosis (tb)",
                "pulmonary tuberculosis",
            },
        },
        "category": "PROGRAM_MANAGED_COMMUNICABLE",
        "transmission_type": "Airborne / respiratory",
        "privacy_category": "PROGRAM_SENSITIVE",
        "is_reportable": True,
        "target_cases": 120,
        "chief_complaint": "Persistent respiratory symptoms and program evaluation",
        "symptoms_text": "Persistent cough, fatigue, fever, reduced appetite",
        "structured_codes": ["COUGH", "FEVER", "FATIGUE", "LOSS_OF_APPETITE"],
        "temperature": (36.8, 38.4),
    },
    "HIV": {
        "name": "HIV Infection",
        "aliases": {
            "codes": {"HIV"},
            "names": {
                "hiv",
                "hiv infection",
                "human immunodeficiency virus (hiv)",
            },
        },
        "category": "SENSITIVE_PROGRAM",
        "transmission_type": "Blood / sexual / perinatal",
        "privacy_category": "HIGHLY_SENSITIVE",
        "is_reportable": True,
        "target_cases": 60,
        "chief_complaint": "Confidential program consultation and follow-up",
        "symptoms_text": "Fatigue with nonspecific constitutional symptoms",
        "structured_codes": ["FATIGUE", "FEVER", "LOSS_OF_APPETITE"],
        "temperature": (36.5, 38.1),
    },
    "SYPHILIS": {
        "name": "Syphilis",
        "aliases": {
            "codes": {"SYPHILIS", "SYPH"},
            "names": {"syphilis"},
        },
        "category": "SEXUALLY_TRANSMITTED_INFECTION",
        "transmission_type": "Sexual / perinatal",
        "privacy_category": "HIGHLY_SENSITIVE",
        "is_reportable": False,
        "target_cases": 75,
        "chief_complaint": "Confidential STI evaluation",
        "symptoms_text": "Localized lesion with possible rash; synthetic development record",
        "structured_codes": ["RASH", "FEVER"],
        "temperature": (36.4, 37.9),
    },
    "GONORRHEA": {
        "name": "Gonorrhea",
        "aliases": {
            "codes": {"GONORRHEA", "GC"},
            "names": {"gonorrhea", "gonorrhoea"},
        },
        "category": "SEXUALLY_TRANSMITTED_INFECTION",
        "transmission_type": "Sexual / perinatal",
        "privacy_category": "HIGHLY_SENSITIVE",
        "is_reportable": False,
        "target_cases": 80,
        "chief_complaint": "Confidential STI evaluation",
        "symptoms_text": "Genitourinary discomfort and discharge; synthetic development record",
        "structured_codes": [],
        "temperature": (36.4, 37.8),
    },
    "GENITAL_HERPES": {
        "name": "Genital Herpes",
        "aliases": {
            "codes": {"GENITAL_HERPES", "HSV_GENITAL"},
            "names": {"genital herpes", "genital herpes simplex"},
        },
        "category": "SEXUALLY_TRANSMITTED_INFECTION",
        "transmission_type": "Sexual / direct contact",
        "privacy_category": "HIGHLY_SENSITIVE",
        "is_reportable": False,
        "target_cases": 65,
        "chief_complaint": "Confidential STI evaluation",
        "symptoms_text": "Localized painful vesicular lesions; synthetic development record",
        "structured_codes": [],
        "temperature": (36.4, 37.8),
    },
}


EXPECTED_TOTAL = sum(
    definition["target_cases"]
    for definition in SENSITIVE_DISEASES.values()
)


def _has_permission(user: User, code: str) -> bool:
    return any(
        permission.code == code
        for role in user.roles
        for permission in role.permissions
    )


def _find_validator(db):
    users = db.scalars(
        select(User).where(
            User.is_active.is_(True)
        )
    ).all()

    for user in users:
        if _has_permission(
            user,
            "DISEASE_CASE_VALIDATE",
        ):
            return user

    for user in users:
        if any(
            role.name == "DOCTOR"
            for role in user.roles
        ):
            return user

    raise RuntimeError(
        "No active disease-case validator / doctor was found."
    )


def _find_recorder(db, fallback: User):
    users = db.scalars(
        select(User).where(
            User.is_active.is_(True)
        )
    ).all()

    preferred_roles = [
        "NURSE",
        "MIDWIFE",
        "BHW",
        "DOCTOR",
    ]

    for role_name in preferred_roles:
        for user in users:
            if any(
                role.name == role_name
                for role in user.roles
            ):
                return user

    return fallback


def _ensure_sensitive_disease(db, code: str, definition: dict):
    aliases = definition["aliases"]

    normalized_codes = {
        value.strip().upper()
        for value in aliases["codes"]
    } | {code.strip().upper()}

    normalized_names = {
        value.strip().lower()
        for value in aliases["names"]
    } | {definition["name"].strip().lower()}

    candidates = db.scalars(
        select(Disease).where(
            or_(
                func.upper(
                    func.trim(Disease.code)
                ).in_(normalized_codes),
                func.lower(
                    func.trim(Disease.name)
                ).in_(normalized_names),
            )
        )
    ).all()

    unique_candidates = {
        disease.id: disease
        for disease in candidates
    }

    if len(unique_candidates) > 1:
        details = ", ".join(
            f"id={item.id}, code={item.code!r}, name={item.name!r}"
            for item in unique_candidates.values()
        )
        raise RuntimeError(
            f"Ambiguous disease master mapping for {code}: {details}"
        )

    if unique_candidates:
        disease = next(
            iter(unique_candidates.values())
        )
        action = "REUSE"
    else:
        disease = Disease(
            code=code,
            name=definition["name"],
            category=definition["category"],
            transmission_type=definition["transmission_type"],
            description=(
                "Sensitive/program disease master entry used by the "
                "health-center surveillance workflow."
            ),
            is_communicable=True,
            is_reportable=definition["is_reportable"],
            is_sensitive=True,
            privacy_category=definition["privacy_category"],
            is_active=True,
        )
        db.add(disease)
        db.flush()
        action = "CREATED"

    # Privacy hardening is intentional for these conditions.
    disease.is_sensitive = True
    disease.privacy_category = definition["privacy_category"]
    disease.is_active = True

    if not disease.category:
        disease.category = definition["category"]

    if not disease.transmission_type:
        disease.transmission_type = definition["transmission_type"]

    if not disease.description:
        disease.description = (
            "Sensitive/program disease master entry used by the "
            "health-center surveillance workflow."
        )

    print(
        f"[{action}] {code} -> id={disease.id}, "
        f"code={disease.code!r}, name={disease.name!r}, "
        f"privacy={disease.privacy_category}"
    )

    return disease


def _load_symptom_map(db):
    if not STRUCTURED_SYMPTOMS_AVAILABLE:
        return {}

    required_codes = {
        code
        for definition in SENSITIVE_DISEASES.values()
        for code in definition["structured_codes"]
    }

    if not required_codes:
        return {}

    symptoms = db.scalars(
        select(Symptom).where(
            Symptom.code.in_(required_codes),
            Symptom.is_active.is_(True),
        )
    ).all()

    return {
        symptom.code: symptom
        for symptom in symptoms
    }


def _age_on(reference: date, birth_date: date) -> int:
    return (
        reference.year
        - birth_date.year
        - (
            (reference.month, reference.day)
            < (birth_date.month, birth_date.day)
        )
    )


def _adult_mock_patients(db):
    patients = db.scalars(
        select(Patient).where(
            Patient.patient_code.like(
                f"{MOCK_PATIENT_PREFIX}%"
            )
        )
    ).all()

    adults = [
        patient
        for patient in patients
        if _age_on(
            END_DATE,
            patient.date_of_birth,
        ) >= 18
    ]

    if len(adults) < EXPECTED_TOTAL:
        raise RuntimeError(
            f"Need at least {EXPECTED_TOTAL} adult MOCK-KNL-* patients; "
            f"found only {len(adults)}."
        )

    return adults


def _random_case_date(rng: random.Random, patient: Patient) -> date:
    adult_date = date(
        patient.date_of_birth.year + 18,
        patient.date_of_birth.month,
        min(patient.date_of_birth.day, 28),
    )

    minimum = max(
        START_DATE,
        adult_date,
    )

    day_span = (END_DATE - minimum).days

    if day_span <= 0:
        return END_DATE

    return minimum + timedelta(
        days=rng.randint(0, day_span)
    )


def _bounded(rng, low, high, digits=1):
    return round(
        rng.uniform(low, high),
        digits,
    )


def _remove_existing_sensitive_mock(db):
    consultation_ids = list(
        db.scalars(
            select(Consultation.id).where(
                Consultation.notes.like(
                    f"%{SENSITIVE_MOCK_MARKER}%"
                )
            )
        ).all()
    )

    if not consultation_ids:
        return (0, 0)

    case_count = db.scalar(
        select(
            func.count(DiseaseCase.id)
        ).where(
            DiseaseCase.consultation_id.in_(
                consultation_ids
            )
        )
    ) or 0

    db.execute(
        delete(DiseaseCase).where(
            DiseaseCase.consultation_id.in_(
                consultation_ids
            )
        )
    )

    db.execute(
        delete(Consultation).where(
            Consultation.id.in_(
                consultation_ids
            )
        )
    )

    db.flush()

    return (
        len(consultation_ids),
        int(case_count),
    )


def _create_sensitive_case(
    *,
    db,
    rng,
    patient,
    disease,
    disease_code,
    definition,
    recorder,
    validator,
    symptom_map,
):
    case_date = _random_case_date(
        rng,
        patient,
    )

    encounter_time = datetime.combine(
        case_date,
        time(
            hour=rng.randint(8, 16),
            minute=rng.choice([0, 10, 20, 30, 40, 50]),
        ),
    )

    temp_low, temp_high = definition["temperature"]

    consultation = Consultation(
        patient_id=patient.id,
        disease_id=disease.id,
        consultation_date=encounter_time,
        chief_complaint=definition["chief_complaint"],
        symptoms=definition["symptoms_text"],
        temperature=_bounded(rng, temp_low, temp_high),
        systolic_bp=rng.randint(100, 138),
        diastolic_bp=rng.randint(65, 88),
        heart_rate=rng.randint(68, 108),
        respiratory_rate=rng.randint(16, 24),
        oxygen_saturation=_bounded(rng, 95.0, 100.0),
        weight_kg=_bounded(rng, 45.0, 92.0),
        height_cm=_bounded(rng, 148.0, 182.0),
        assessment=(
            f"{DATA_LABEL} | TEST RECORD ONLY | "
            f"restricted mock {disease_code} surveillance scenario."
        ),
        diagnosis=disease.name,
        treatment_plan=(
            "TEST RECORD ONLY. No real medication, treatment, or "
            "clinical instruction is represented by this synthetic record."
        ),
        notes=(
            f"{SENSITIVE_MOCK_MARKER} | {DATA_LABEL} | "
            "TEST RECORD ONLY | NOT OFFICIAL BARANGAY HEALTH DATA"
        ),
        recorded_by=recorder.id,
    )

    if hasattr(
        consultation,
        "structured_symptoms",
    ):
        consultation.structured_symptoms = [
            symptom_map[code]
            for code in definition["structured_codes"]
            if code in symptom_map
        ]

    db.add(consultation)
    db.flush()

    disease_case = DiseaseCase(
        patient_id=patient.id,
        consultation_id=consultation.id,
        disease_id=disease.id,
        case_status="CONFIRMED",
        onset_date=(
            case_date
            - timedelta(days=rng.randint(0, 14))
        ),
        case_date=case_date,
        remarks=(
            f"{SENSITIVE_MOCK_MARKER} | {DATA_LABEL} | "
            "TEST RECORD ONLY | RESTRICTED SENSITIVE PROGRAM DATA"
        ),
        validation_status="VALIDATED",
        validated_by=validator.id,
        validated_at=(
            encounter_time
            + timedelta(hours=2)
        ),
        recorded_by=recorder.id,
    )

    db.add(disease_case)


def seed_sensitive_mock_surveillance(replace: bool = False):
    rng = random.Random(RANDOM_SEED)
    db = SessionLocal()

    try:
        existing_count = db.scalar(
            select(
                func.count(Consultation.id)
            ).where(
                Consultation.notes.like(
                    f"%{SENSITIVE_MOCK_MARKER}%"
                )
            )
        ) or 0

        if existing_count and not replace:
            raise RuntimeError(
                "Sensitive mock cases already exist. Use --replace "
                "to rebuild only SENSITIVE_MOCK_V1 records."
            )

        if replace:
            removed_consultations, removed_cases = (
                _remove_existing_sensitive_mock(db)
            )
            print(
                f"[CLEANUP] Removed {removed_consultations} sensitive "
                f"mock consultations and {removed_cases} disease cases."
            )

        disease_map = {
            code: _ensure_sensitive_disease(
                db,
                code,
                definition,
            )
            for code, definition in SENSITIVE_DISEASES.items()
        }

        validator = _find_validator(db)
        recorder = _find_recorder(db, validator)
        symptom_map = _load_symptom_map(db)
        patients = _adult_mock_patients(db)

        rng.shuffle(patients)

        print("=" * 60)
        print("SENSITIVE / PROGRAM MOCK SURVEILLANCE SEED")
        print("=" * 60)
        print(f"Available adult mock patients: {len(patients)}")
        print(f"Sensitive cases requested: {EXPECTED_TOTAL}")
        print(f"Date range: {START_DATE} to {END_DATE}")
        print(f"Recorder: {recorder.username}")
        print(f"Validator: {validator.username}")
        print("Street-level sensitive mapping: DISABLED BY API POLICY")
        print()

        cursor = 0
        created = 0

        for code, definition in SENSITIVE_DISEASES.items():
            target = definition["target_cases"]
            selected = patients[cursor:cursor + target]
            cursor += target

            for patient in selected:
                _create_sensitive_case(
                    db=db,
                    rng=rng,
                    patient=patient,
                    disease=disease_map[code],
                    disease_code=code,
                    definition=definition,
                    recorder=recorder,
                    validator=validator,
                    symptom_map=symptom_map,
                )
                created += 1

            db.commit()
            print(
                f"[CREATED] {code}: {target} validated synthetic cases"
            )

        print()
        print("=" * 60)
        print("SEED COMPLETE")
        print("=" * 60)
        print(f"Sensitive mock cases created: {created}")
        print("General surveillance data was not deleted or rewritten.")
        print("No medicine dispensing records were fabricated.")
        print()
        print(
            "[IMPORTANT] Synthetic development data only. "
            "These counts do not represent actual Krus na Ligas prevalence."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Seed restricted synthetic TB/HIV/STI surveillance cases "
            "onto the existing MOCK-KNL-* development patients."
        )
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        help=(
            "Remove and rebuild only SENSITIVE_MOCK_V1 consultations/cases."
        ),
    )

    args = parser.parse_args()

    seed_sensitive_mock_surveillance(
        replace=args.replace
    )


if __name__ == "__main__":
    main()
