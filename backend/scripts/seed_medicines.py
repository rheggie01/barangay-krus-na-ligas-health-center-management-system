from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.medicine import Medicine


MEDICINES = [
    {
        "code": "MED-001",
        "name": "Urine Pregnancy Test",
        "generic_name": None,
        "dosage_strength": None,
        "dosage_form": "Test Kit",
        "package_unit": None,
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 0,
        "loose_stock": 100,
    },
    {
        "code": "MED-002",
        "name": "Ferrous Sulfate",
        "generic_name": "Ferrous Sulfate",
        "dosage_strength": None,
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "tablet",
        "units_per_package": None,
        "package_stock": 19,
        "loose_stock": 0,
    },
    {
        "code": "MED-003",
        "name": "Amoxicillin + Ambroxol",
        "generic_name": "Amoxicillin + Ambroxol",
        "dosage_strength": "500 mg",
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 8,
        "loose_stock": 0,
    },
    {
        "code": "MED-004",
        "name": "Mefenamic Acid",
        "generic_name": "Mefenamic Acid",
        "dosage_strength": "500 mg",
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 2,
        "loose_stock": 0,
    },
    {
        "code": "MED-005",
        "name": "Albendazole",
        "generic_name": "Albendazole",
        "dosage_strength": None,
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 20,
        "loose_stock": 0,
    },
    {
        "code": "MED-006",
        "name": "Celecoxib",
        "generic_name": "Celecoxib",
        "dosage_strength": "400 mg",
        "dosage_form": "Capsule",
        "package_unit": "box",
        "dispensing_unit": "capsule",
        "units_per_package": None,
        "package_stock": 9,
        "loose_stock": 0,
    },
    {
        "code": "MED-007",
        "name": "Retinol Palmitate",
        "generic_name": "Vitamin A",
        "dosage_strength": None,
        "dosage_form": "Liquid",
        "package_unit": "bottle",
        "dispensing_unit": "bottle",
        "units_per_package": 1,
        "package_stock": 5,
        "loose_stock": 0,
    },
    {
        "code": "MED-008",
        "name": "Chlorhexidine",
        "generic_name": "Chlorhexidine",
        "dosage_strength": "500 mg",
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 7,
        "loose_stock": 0,
    },
    {
        "code": "MED-009",
        "name": "Dicycloverine Hydrochloride",
        "generic_name": "Dicycloverine Hydrochloride",
        "dosage_strength": "10 mg",
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 1,
        "loose_stock": 0,
    },
    {
        "code": "MED-010",
        "name": "Cinnarizine",
        "generic_name": "Cinnarizine",
        "dosage_strength": "25 mg",
        "dosage_form": "Tablet",
        "package_unit": None,
        "dispensing_unit": "tablet",
        "units_per_package": None,
        "package_stock": 0,
        "loose_stock": 100,
    },
    {
        "code": "MED-011",
        "name": "Ascorbic Acid",
        "generic_name": "Vitamin C",
        "dosage_strength": "500 mg",
        "dosage_form": "Tablet",
        "package_unit": "box",
        "dispensing_unit": "tablet",
        "units_per_package": None,
        "package_stock": 13,
        "loose_stock": 0,
    },
    {
        "code": "MED-012",
        "name": "Cefuroxime",
        "generic_name": "Cefuroxime",
        "dosage_strength": "250 mg",
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 4,
        "loose_stock": 0,
    },
    {
        "code": "MED-013",
        "name": "Multivitamins",
        "generic_name": "Multivitamins",
        "dosage_strength": None,
        "dosage_form": "Pediatric Drops / Syrup",
        "package_unit": "box",
        "dispensing_unit": "bottle",
        "units_per_package": None,
        "package_stock": 6,
        "loose_stock": 0,
    },
    {
        "code": "MED-014",
        "name": "Amoxicillin",
        "generic_name": "Amoxicillin",
        "dosage_strength": None,
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 18,
        "loose_stock": 0,
    },
    {
        "code": "MED-015",
        "name": "Vitex Negundo",
        "generic_name": "Lagundi Leaf",
        "dosage_strength": None,
        "dosage_form": "Syrup",
        "package_unit": "box",
        "dispensing_unit": "bottle",
        "units_per_package": None,
        "package_stock": 4,
        "loose_stock": 0,
    },
    {
        "code": "MED-016",
        "name": "Salbutamol",
        "generic_name": "Salbutamol",
        "dosage_strength": None,
        "dosage_form": "Nebule",
        "package_unit": "box",
        "dispensing_unit": "nebule",
        "units_per_package": None,
        "package_stock": 72,
        "loose_stock": 0,
    },
    {
        "code": "MED-017",
        "name": "Salbutamol Sulfate",
        "generic_name": "Salbutamol Sulfate",
        "dosage_strength": None,
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 3,
        "loose_stock": 0,
    },
    {
        "code": "MED-018",
        "name": "Gliclazide",
        "generic_name": "Gliclazide",
        "dosage_strength": "30 mg",
        "dosage_form": "Tablet",
        "package_unit": "box",
        "dispensing_unit": "tablet",
        "units_per_package": None,
        "package_stock": 14,
        "loose_stock": 0,
    },
    {
        "code": "MED-019",
        "name": "Phenylpropanolamine Hydrochloride",
        "generic_name": "Phenylpropanolamine Hydrochloride",
        "dosage_strength": None,
        "dosage_form": "Syrup",
        "package_unit": "box",
        "dispensing_unit": "bottle",
        "units_per_package": None,
        "package_stock": 19,
        "loose_stock": 0,
    },
    {
        "code": "MED-020",
        "name": "Paracetamol Combination",
        "generic_name": "Paracetamol",
        "dosage_strength": "500 mg",
        "dosage_form": "Tablet",
        "package_unit": "box",
        "dispensing_unit": "tablet",
        "units_per_package": None,
        "package_stock": 5,
        "loose_stock": 0,
    },
    {
        "code": "MED-021",
        "name": "Tranexamic Acid",
        "generic_name": "Tranexamic Acid",
        "dosage_strength": "500 mg",
        "dosage_form": "Capsule",
        "package_unit": "box",
        "dispensing_unit": "capsule",
        "units_per_package": None,
        "package_stock": 1,
        "loose_stock": 0,
    },
    {
        "code": "MED-022",
        "name": "Lagundi Leaf",
        "generic_name": "Vitex Negundo",
        "dosage_strength": "300 mg",
        "dosage_form": "Tablet",
        "package_unit": "box",
        "dispensing_unit": "tablet",
        "units_per_package": None,
        "package_stock": 2,
        "loose_stock": 0,
    },
    {
        "code": "MED-023",
        "name": "Aluminum Hydroxide + Magnesium Hydroxide",
        "generic_name": "Aluminum Hydroxide + Magnesium Hydroxide",
        "dosage_strength": "200 mg / 200 mg",
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 5,
        "loose_stock": 0,
    },
    {
        "code": "MED-024",
        "name": "Cotrimoxazole",
        "generic_name": "Cotrimoxazole",
        "dosage_strength": "400 mg",
        "dosage_form": None,
        "package_unit": "box",
        "dispensing_unit": "piece",
        "units_per_package": None,
        "package_stock": 7,
        "loose_stock": 0,
    },
]


def seed_medicines():
    db = SessionLocal()

    try:
        for data in MEDICINES:
            existing = db.scalar(
                select(Medicine).where(
                    Medicine.code == data["code"]
                )
            )

            if existing:
                print(
                    f"Skipping {data['code']} "
                    f"- already exists"
                )
                continue

            medicine = Medicine(
                **data,
                reorder_level=10,
                is_active=True,
            )

            db.add(medicine)

        db.commit()

        print("Medicine seed completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_medicines()