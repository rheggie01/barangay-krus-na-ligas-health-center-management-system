
from __future__ import annotations

import argparse
import random
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select

from app.db.session import SessionLocal
from app.ml.disease_medicine_mapping import get_mapping_rule
from app.ml.services.disease_medicine_mapping_service import (
    MOCK_DISPENSING_MARKER,
    resolve_target_medicine,
)
from app.models.consultation import Consultation
from app.models.consultation_medicine import ConsultationMedicine
from app.models.disease import Disease
from app.models.medicine import Medicine
from app.models.patient import Patient


LOCAL_TZ = ZoneInfo("Asia/Manila")
MOCK_PREFIX = "MOCK-KNL-"
RANDOM_SEED = 202609051345


def _latest_completed_month_end() -> date:
    today = datetime.now(LOCAL_TZ).date()
    current_month_start = date(
        today.year,
        today.month,
        1,
    )
    return current_month_start - timedelta(days=1)


def _remove_existing(db) -> int:
    ids = list(
        db.scalars(
            select(ConsultationMedicine.id)
            .where(
                ConsultationMedicine.remarks.like(
                    f"{MOCK_DISPENSING_MARKER}%"
                )
            )
        ).all()
    )
    if ids:
        db.execute(
            delete(ConsultationMedicine).where(
                ConsultationMedicine.id.in_(ids)
            )
        )
        db.flush()
    return len(ids)


def seed_mock_medicine_dispensings(
    *,
    replace: bool,
):
    db = SessionLocal()
    rng = random.Random(RANDOM_SEED)

    try:
        if replace:
            print(
                f"[CLEANUP] Removed "
                f"{_remove_existing(db)} previous synthetic "
                "medicine dispensing rows."
            )
        else:
            existing = db.scalar(
                select(func.count(ConsultationMedicine.id))
                .where(
                    ConsultationMedicine.remarks.like(
                        f"{MOCK_DISPENSING_MARKER}%"
                    )
                )
            )
            if existing:
                raise RuntimeError(
                    "Synthetic medicine dispensing rows already "
                    "exist. Use --replace to rebuild."
                )

        completed_through = _latest_completed_month_end()

        consultations = list(
            db.execute(
                select(Consultation, Disease)
                .join(
                    Patient,
                    Patient.id == Consultation.patient_id,
                )
                .join(
                    Disease,
                    Disease.id == Consultation.disease_id,
                )
                .where(
                    Patient.patient_code.like(
                        f"{MOCK_PREFIX}%"
                    ),
                    Consultation.consultation_date <= datetime.combine(
                        completed_through,
                        time.max,
                    ),
                )
                .order_by(
                    Consultation.consultation_date.asc(),
                    Consultation.id.asc(),
                )
            ).all()
        )

        medicines = list(
            db.scalars(
                select(Medicine)
                .order_by(Medicine.id.asc())
            ).all()
        )

        created = 0
        consultations_with_dispensing = 0
        no_verified_match = 0
        unmapped = 0
        by_medicine = {}

        print("ALL-DISEASE MOCK MEDICINE DISPENSING")
        print("====================================")
        print(f"Mock consultations scanned: {len(consultations)}")
        print(f"Completed through: {completed_through}")
        print()

        for consultation, disease in consultations:
            rule = get_mapping_rule(
                disease_code=disease.code,
                disease_name=disease.name,
            )
            if rule is None:
                unmapped += 1
                continue

            resolved_targets = []
            for target in rule["medicines"]:
                medicine, _ = resolve_target_medicine(
                    medicines,
                    target=target,
                    sensitive_disease=bool(
                        disease.is_sensitive
                        or rule["sensitive"]
                    ),
                )
                if medicine is not None:
                    resolved_targets.append(
                        (target, medicine)
                    )

            if not resolved_targets:
                no_verified_match += 1
                continue

            selected = [
                (target, medicine)
                for target, medicine in resolved_targets
                if rng.random()
                <= float(target["selection_probability"])
            ]

            # Technical-demand simulation: ensure one row when a
            # verified mapped formulation exists. This is not a
            # prescribing rule.
            if not selected:
                selected = [
                    rng.choice(resolved_targets)
                ]

            consultations_with_dispensing += 1

            for target, medicine in selected:
                q_min, q_max = target["quantity_range"]
                quantity = rng.randint(
                    int(q_min),
                    int(q_max),
                )

                db.add(
                    ConsultationMedicine(
                        consultation_id=consultation.id,
                        medicine_id=medicine.id,
                        quantity=quantity,
                        stock_unit="LOOSE",
                        dosage_instruction=None,
                        remarks=(
                            f"{MOCK_DISPENSING_MARKER} | "
                            f"DISEASE={disease.code} | "
                            f"MAP={target['key']} | "
                            "ARTIFICIAL INVENTORY-DEMAND UNITS | "
                            "NOT A CLINICAL PRESCRIPTION"
                        ),
                        dispensed_by=consultation.recorded_by,
                        dispensed_at=(
                            consultation.consultation_date
                            + timedelta(
                                minutes=30 + rng.randint(0, 90)
                            )
                        ),
                    )
                )

                created += 1
                by_medicine[medicine.name] = (
                    by_medicine.get(medicine.name, 0)
                    + quantity
                )

            if created and created % 500 == 0:
                db.flush()

        db.commit()

        print("SEED COMPLETE")
        print("=============")
        print(f"Synthetic dispensing rows: {created}")
        print(
            "Consultations with at least one synthetic "
            f"dispensing: {consultations_with_dispensing}"
        )
        print(
            "Mapped consultations with no exact verified "
            f"formulation: {no_verified_match}"
        )
        print(
            "Consultations with no configured mapping: "
            f"{unmapped}"
        )
        print()
        print("Top synthetic medicine-demand totals:")
        for name, total in sorted(
            by_medicine.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:15]:
            print(f"  {name}: {total} units")

        print()
        print("IMPORTANT:")
        print("- Current live stock was NOT decremented.")
        print("- No inventory transaction was created.")
        print("- Candidate medicines were NOT auto-verified.")
        print("- Rows are synthetic historical demand only.")
        print(
            "- Quantities are artificial inventory-demand "
            "units, not patient dosing instructions."
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
    seed_mock_medicine_dispensings(
        replace=args.replace,
    )
