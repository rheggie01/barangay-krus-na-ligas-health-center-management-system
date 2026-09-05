from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.consultation import Consultation
from app.models.disease import Disease
from app.models.disease_case import DiseaseCase
from app.models.patient import Patient


MARKER = "SENSITIVE_MOCK_V1"
MOCK_PREFIX = "MOCK-KNL-"

EXPECTED = {
    "TB": 120,
    "HIV": 60,
    "SYPHILIS": 75,
    "GONORRHEA": 80,
    "GENITAL_HERPES": 65,
}

ALIASES = {
    "TB": {
        "codes": {
            "TB",
            "TUBERCULOSIS",
            "PTB",
        },
        "names": {
            "tuberculosis",
            "tuberculosis (tb)",
            "pulmonary tuberculosis",
        },
    },

    "HIV": {
        "codes": {
            "HIV",
        },
        "names": {
            "hiv",
            "hiv infection",
            "human immunodeficiency virus (hiv)",
        },
    },

    "SYPHILIS": {
        "codes": {
            "SYPHILIS",
            "SYPH",
        },
        "names": {
            "syphilis",
        },
    },

    "GONORRHEA": {
        "codes": {
            "GONORRHEA",
            "GC",
        },
        "names": {
            "gonorrhea",
            "gonorrhoea",
        },
    },

    "GENITAL_HERPES": {
        "codes": {
            "GENITAL_HERPES",
            "HSV_GENITAL",
            "HSV",
        },
        "names": {
            "genital herpes",
            "genital herpes simplex",
        },
    },
}


def verify_sensitive_mock_surveillance():
    db = SessionLocal()

    try:
        rows = db.execute(
            select(
                Disease.code,
                Disease.name,
                Disease.is_sensitive,
                Disease.privacy_category,
                func.count(DiseaseCase.id),
            )
            .join(
                DiseaseCase,
                DiseaseCase.disease_id == Disease.id,
            )
            .join(
                Consultation,
                Consultation.id == DiseaseCase.consultation_id,
            )
            .join(
                Patient,
                Patient.id == DiseaseCase.patient_id,
            )
            .where(
                Consultation.notes.like(f"%{MARKER}%"),
                Patient.patient_code.like(f"{MOCK_PREFIX}%"),
                DiseaseCase.validation_status == "VALIDATED",
            )
            .group_by(
                Disease.id,
                Disease.code,
                Disease.name,
                Disease.is_sensitive,
                Disease.privacy_category,
            )
            .order_by(Disease.name.asc())
        ).all()

        total = sum(int(row[4]) for row in rows)

        print("SENSITIVE MOCK SURVEILLANCE VERIFICATION")
        print("=======================================")
        print(f"Total validated sensitive mock cases: {total}")
        print()

        normalized_rows = []

        for code, name, is_sensitive, privacy_category, count in rows:
            normalized_code = (
                str(
                    code
                    or ""
                )
                .strip()
                .upper()
            )

            normalized_name = (
                str(
                    name
                    or ""
                )
                .strip()
                .lower()
            )

            normalized_rows.append(
                (
                    normalized_code,
                    normalized_name,
                    int(
                        count
                    ),
                )
            )

            print(
                f"{code!r} / {name!r}: {count} | "
                f"sensitive={is_sensitive} | privacy={privacy_category}"
            )

            if not is_sensitive:
                raise RuntimeError(
                    f"Disease {name} is not marked sensitive."
                )

            if not privacy_category or privacy_category == "STANDARD":
                raise RuntimeError(
                    f"Disease {name} does not have a restricted privacy category."
                )

        for expected_class, expected_count in EXPECTED.items():
            aliases = ALIASES[
                expected_class
            ]

            actual = sum(
                count
                for (
                    code,
                    name,
                    count,
                ) in normalized_rows
                if (
                    code
                    in aliases[
                        "codes"
                    ]
                )
                or
                (
                    name
                    in aliases[
                        "names"
                    ]
                )
            )

            if actual != expected_count:
                raise RuntimeError(
                    f"{expected_class}: expected "
                    f"{expected_count}, found {actual}."
                )

        if total != sum(EXPECTED.values()):
            raise RuntimeError(
                "Unexpected total sensitive mock case count."
            )

        print()
        print("Verification passed.")
        print(
            "Synthetic development records only; not official prevalence data."
        )

    finally:
        db.close()


if __name__ == "__main__":
    verify_sensitive_mock_surveillance()
