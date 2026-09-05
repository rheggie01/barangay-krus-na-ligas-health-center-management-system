
from __future__ import annotations

from sqlalchemy import select

from app.db.session import SessionLocal
from app.ml.disease_medicine_mapping import get_mapping_rule
from app.ml.services.disease_medicine_mapping_service import (
    MOCK_DISPENSING_MARKER,
    medicine_matches_target,
)
from app.models.consultation import Consultation
from app.models.consultation_medicine import ConsultationMedicine
from app.models.disease import Disease
from app.models.medicine import Medicine
from app.models.patient import Patient


MOCK_PREFIX = "MOCK-KNL-"


def verify_all_disease_mock_medicine_demand():
    db = SessionLocal()
    try:
        rows = db.execute(
            select(
                ConsultationMedicine,
                Consultation,
                Disease,
                Medicine,
            )
            .join(
                Consultation,
                Consultation.id
                == ConsultationMedicine.consultation_id,
            )
            .join(
                Disease,
                Disease.id
                == Consultation.disease_id,
            )
            .join(
                Medicine,
                Medicine.id
                == ConsultationMedicine.medicine_id,
            )
            .join(
                Patient,
                Patient.id
                == Consultation.patient_id,
            )
            .where(
                Patient.patient_code.like(
                    f"{MOCK_PREFIX}%"
                ),
                ConsultationMedicine.remarks.like(
                    f"{MOCK_DISPENSING_MARKER}%"
                ),
            )
        ).all()

        print("ALL-DISEASE MOCK MEDICINE DEMAND VERIFICATION")
        print("============================================")
        print(f"Synthetic dispensing rows: {len(rows)}")

        if not rows:
            raise RuntimeError(
                "No synthetic medicine dispensing rows found."
            )

        invalid = []
        sensitive_failures = []
        mapping_failures = []
        disease_counts = {}
        medicine_units = {}

        for dispensing, consultation, disease, medicine in rows:
            if not medicine.is_active or not medicine.stock_verified:
                invalid.append(dispensing.id)

            if disease.is_sensitive and (
                not medicine.sensitive_inventory
                or not medicine.restricted_dispensing
            ):
                sensitive_failures.append(dispensing.id)

            rule = get_mapping_rule(
                disease_code=disease.code,
                disease_name=disease.name,
            )

            if (
                rule is None
                or not any(
                    medicine_matches_target(
                        medicine,
                        target,
                    )
                    for target in rule["medicines"]
                )
            ):
                mapping_failures.append(dispensing.id)

            disease_counts[disease.name] = (
                disease_counts.get(disease.name, 0) + 1
            )
            medicine_units[medicine.name] = (
                medicine_units.get(medicine.name, 0)
                + int(dispensing.quantity or 0)
            )

        print(
            "Invalid inactive/unverified medicine rows: "
            f"{len(invalid)}"
        )
        print(
            "Sensitive inventory safety failures: "
            f"{len(sensitive_failures)}"
        )
        print(
            "Disease-medicine mapping failures: "
            f"{len(mapping_failures)}"
        )
        print()
        print("Diseases with synthetic medicine demand:")
        for name, count in sorted(disease_counts.items()):
            print(f"  {name}: {count} dispensing rows")

        print()
        print("Top medicine demand:")
        for name, units in sorted(
            medicine_units.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:15]:
            print(f"  {name}: {units} units")

        if invalid:
            raise RuntimeError(
                "Synthetic demand used inactive/unverified medicines."
            )
        if sensitive_failures:
            raise RuntimeError(
                "Sensitive synthetic dispensing safety check failed."
            )
        if mapping_failures:
            raise RuntimeError(
                "Synthetic demand contains rows outside "
                "the configured disease-medicine mapping."
            )

        print()
        print("Verification passed.")
        print(
            "Synthetic development demand only; not actual "
            "dispensing history or a treatment protocol."
        )
    finally:
        db.close()


if __name__ == "__main__":
    verify_all_disease_mock_medicine_demand()
