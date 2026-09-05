
from __future__ import annotations
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.disease_medicine_mapping import (
    DEVELOPMENT_MAPPING_NOTICE,
    get_mapping_rule,
)
from app.models.consultation import Consultation
from app.models.consultation_medicine import ConsultationMedicine
from app.models.disease import Disease
from app.models.medicine import Medicine
from app.models.patient import Patient

MOCK_PATIENT_PREFIX = "MOCK-KNL-"
MOCK_DISPENSING_MARKER = (
    "SYNTHETIC_DEVELOPMENT_DATA | MOCK_MEDICINE_DISPENSING"
)

def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9%]+", "", str(value).lower())

def _normalized_set(values) -> set[str]:
    return {_normalize(value) for value in values if _normalize(value)}

def medicine_matches_target(
    medicine: Medicine,
    target: dict[str, Any],
) -> bool:
    """
    Conservative exact formulation matching.
    Generic-name-only matching is intentionally excluded.
    """
    allowed_names = _normalized_set(
        target.get("name_aliases", set())
    )
    if _normalize(medicine.name) not in allowed_names:
        return False

    required_strengths = _normalized_set(
        target.get("strength_aliases", set())
    )
    if required_strengths and _normalize(
        medicine.dosage_strength
    ) not in required_strengths:
        return False

    required_forms = _normalized_set(
        target.get("form_aliases", set())
    )
    if required_forms and _normalize(
        medicine.dosage_form
    ) not in required_forms:
        return False

    return True

def resolve_target_medicine(
    medicines: list[Medicine],
    *,
    target: dict[str, Any],
    sensitive_disease: bool,
) -> tuple[Medicine | None, str]:
    candidates = [
        medicine
        for medicine in medicines
        if medicine.is_active
        and medicine.stock_verified
        and medicine_matches_target(
            medicine,
            target,
        )
    ]

    if sensitive_disease:
        candidates = [
            medicine
            for medicine in candidates
            if medicine.sensitive_inventory
            and medicine.restricted_dispensing
        ]
    else:
        candidates = [
            medicine
            for medicine in candidates
            if not medicine.sensitive_inventory
        ]

    if len(candidates) == 1:
        return candidates[0], "EXACT_VERIFIED_ACTIVE"
    if len(candidates) > 1:
        return None, "AMBIGUOUS_VERIFIED_FORMULATION"
    return None, "NO_EXACT_VERIFIED_FORMULATION"

def _mock_demand_by_disease_and_medicine(
    db: Session,
) -> dict[tuple[int, int], dict[str, int]]:
    rows = db.execute(
        select(
            Consultation.disease_id,
            ConsultationMedicine.medicine_id,
            func.count(ConsultationMedicine.id),
            func.coalesce(
                func.sum(ConsultationMedicine.quantity),
                0,
            ),
        )
        .join(
            ConsultationMedicine,
            ConsultationMedicine.consultation_id == Consultation.id,
        )
        .join(
            Patient,
            Patient.id == Consultation.patient_id,
        )
        .where(
            Patient.patient_code.like(
                f"{MOCK_PATIENT_PREFIX}%"
            ),
            ConsultationMedicine.remarks.like(
                f"{MOCK_DISPENSING_MARKER}%"
            ),
        )
        .group_by(
            Consultation.disease_id,
            ConsultationMedicine.medicine_id,
        )
    ).all()

    return {
        (int(disease_id), int(medicine_id)): {
            "dispensing_records": int(row_count or 0),
            "dispensed_units": int(total_quantity or 0),
        }
        for disease_id, medicine_id, row_count, total_quantity in rows
        if disease_id is not None
    }

def list_disease_medicine_mappings(
    db: Session,
    *,
    include_sensitive: bool = False,
) -> list[dict[str, Any]]:
    diseases = list(
        db.scalars(
            select(Disease)
            .where(
                Disease.is_active.is_(True)
            )
            .order_by(Disease.name.asc())
        ).all()
    )
    medicines = list(
        db.scalars(
            select(Medicine)
            .order_by(Medicine.id.asc())
        ).all()
    )
    demand = _mock_demand_by_disease_and_medicine(db)
    result = []

    for disease in diseases:
        if disease.is_sensitive and not include_sensitive:
            continue

        rule = get_mapping_rule(
            disease_code=disease.code,
            disease_name=disease.name,
        )

        if rule is None:
            result.append({
                "disease_id": disease.id,
                "disease_code": disease.code,
                "disease_name": disease.name,
                "disease_category": disease.category,
                "is_sensitive": bool(disease.is_sensitive),
                "privacy_category": disease.privacy_category,
                "mapping_group": "UNMAPPED",
                "mapping_status": "NO_DEVELOPMENT_MAPPING_CONFIGURED",
                "mapped_medicines": [],
                "synthetic_dispensing_records": 0,
                "synthetic_dispensed_units": 0,
                "development_notice": DEVELOPMENT_MAPPING_NOTICE,
            })
            continue

        mapped = []
        total_records = 0
        total_units = 0
        matched_count = 0

        for target in rule["medicines"]:
            medicine, match_status = resolve_target_medicine(
                medicines,
                target=target,
                sensitive_disease=bool(
                    disease.is_sensitive or rule["sensitive"]
                ),
            )
            aggregate = {
                "dispensing_records": 0,
                "dispensed_units": 0,
            }
            if medicine is not None:
                matched_count += 1
                aggregate = demand.get(
                    (disease.id, medicine.id),
                    aggregate,
                )

            total_records += aggregate["dispensing_records"]
            total_units += aggregate["dispensed_units"]

            mapped.append({
                "mapping_key": target["key"],
                "target_label": target["label"],
                "match_status": match_status,
                "medicine_id": medicine.id if medicine else None,
                "medicine_code": medicine.code if medicine else None,
                "medicine_name": medicine.name if medicine else None,
                "dosage_strength": (
                    medicine.dosage_strength if medicine else None
                ),
                "dosage_form": (
                    medicine.dosage_form if medicine else None
                ),
                "stock_verified": (
                    bool(medicine.stock_verified) if medicine else False
                ),
                "forecast_enabled": (
                    bool(medicine.forecast_enabled) if medicine else False
                ),
                "sensitive_inventory": (
                    bool(medicine.sensitive_inventory) if medicine else False
                ),
                "synthetic_dispensing_records": (
                    aggregate["dispensing_records"]
                ),
                "synthetic_dispensed_units": (
                    aggregate["dispensed_units"]
                ),
            })

        if matched_count == len(mapped) and matched_count > 0:
            mapping_status = "ALL_TARGETS_EXACTLY_MATCHED"
        elif matched_count > 0:
            mapping_status = "PARTIAL_VERIFIED_MAPPING"
        else:
            mapping_status = "NO_VERIFIED_ACTIVE_FORMULATION"

        result.append({
            "disease_id": disease.id,
            "disease_code": disease.code,
            "disease_name": disease.name,
            "disease_category": disease.category,
            "is_sensitive": bool(disease.is_sensitive),
            "privacy_category": disease.privacy_category,
            "mapping_group": rule["group"],
            "mapping_status": mapping_status,
            "mapped_medicines": mapped,
            "synthetic_dispensing_records": total_records,
            "synthetic_dispensed_units": total_units,
            "development_notice": DEVELOPMENT_MAPPING_NOTICE,
        })

    return result
