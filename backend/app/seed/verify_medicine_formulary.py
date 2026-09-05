from collections import Counter

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.medicine import Medicine


EXPECTED_CATEGORY_COUNTS = {'ANTI_INFECTIVE': 21,
 'ANTI_THROMBOTIC': 2,
 'ANTI_ASTHMA_COPD': 8,
 'SUPPORTIVE_OTHER': 18,
 'ANTI_DIABETIC': 3,
 'ANTI_DYSLIPIDEMIA': 4,
 'ANTI_HYPERTENSIVE_CARDIOLOGY': 18,
 'NERVOUS_SYSTEM': 1,
 'SENSITIVE_PROGRAM': 11}

ALLOWED_CATEGORIES = set(
    EXPECTED_CATEGORY_COUNTS
)

CANDIDATE_PREFIXES = (
    "MED-AI-",
    "MED-AT-",
    "MED-RESP-",
    "MED-SUP-",
    "MED-DM-",
    "MED-LIP-",
    "MED-CV-",
    "MED-NS-",
    "MED-TB-",
    "MED-HIV-",
    "MED-STI-",
)


def verify_medicine_formulary():
    db = SessionLocal()

    try:
        all_rows = list(
            db.scalars(
                select(Medicine).where(
                    Medicine.code.like(
                        "MED-%"
                    )
                )
            ).all()
        )

        candidate_rows = [
            medicine
            for medicine in all_rows
            if medicine.code.startswith(
                CANDIDATE_PREFIXES
            )
        ]

        category_counts = Counter(
            medicine.medicine_category
            for medicine in candidate_rows
        )

        invalid_categories = [
            medicine
            for medicine in candidate_rows
            if medicine.medicine_category
            not in ALLOWED_CATEGORIES
        ]

        sensitive = [
            medicine
            for medicine in candidate_rows
            if medicine.sensitive_inventory
        ]

        unsafe_sensitive_forecast = [
            medicine
            for medicine in sensitive
            if medicine.forecast_enabled
        ]

        print(
            "Medicine formulary verification"
        )

        print(
            "================================"
        )

        print(
            f"Total MED-* rows: {len(all_rows)}"
        )

        print(
            f"Candidate formulary rows: "
            f"{len(candidate_rows)}"
        )

        print()

        for category in (
            EXPECTED_CATEGORY_COUNTS
        ):
            actual = category_counts.get(
                category,
                0,
            )

            expected = (
                EXPECTED_CATEGORY_COUNTS[
                    category
                ]
            )

            marker = (
                "OK"
                if actual == expected
                else "ERROR"
            )

            print(
                f"[{marker}] {category}: "
                f"{actual} / expected {expected}"
            )

        print()

        print(
            "Invalid category rows "
            f"(must be 0): "
            f"{len(invalid_categories)}"
        )

        print(
            "Sensitive medicines: "
            f"{len(sensitive)}"
        )

        print(
            "Sensitive forecast-enabled "
            f"(must be 0): "
            f"{len(unsafe_sensitive_forecast)}"
        )

        if len(candidate_rows) != 86:
            raise RuntimeError(
                "Expected exactly 86 candidate "
                "formulary rows."
            )

        if category_counts != Counter(
            EXPECTED_CATEGORY_COUNTS
        ):
            raise RuntimeError(
                "Candidate medicine category "
                "counts do not match expected values."
            )

        if invalid_categories:
            raise RuntimeError(
                "Invalid medicine_category values "
                "were found."
            )

        if unsafe_sensitive_forecast:
            raise RuntimeError(
                "Sensitive medicine forecasting "
                "safety verification failed."
            )

        print()
        print("Verification passed.")

    finally:
        db.close()


if __name__ == "__main__":
    verify_medicine_formulary()
