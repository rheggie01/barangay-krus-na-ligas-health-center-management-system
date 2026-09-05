
from __future__ import annotations

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.disease import Disease


CONDITIONS = [
    ("HTN","Hypertension","NON_COMMUNICABLE","Non-communicable"),
    ("T2DM","Type 2 Diabetes Mellitus","NON_COMMUNICABLE","Non-communicable"),
    ("DYSLIPIDEMIA","Dyslipidemia","NON_COMMUNICABLE","Non-communicable"),
    ("ASTHMA","Asthma","RESPIRATORY","Non-communicable"),
    ("COPD","Chronic Obstructive Pulmonary Disease","RESPIRATORY","Non-communicable"),
    ("UTI","Urinary Tract Infection","OTHER_CONDITION","Clinical condition"),
    ("PNEUMONIA","Pneumonia / Bacterial Respiratory Infection","RESPIRATORY","Respiratory"),
    ("HELMINTHIASIS","Helminthiasis","OTHER_CONDITION","Parasitic"),
    ("FUNGAL_INFECTION","Fungal Infection / Candidiasis","OTHER_CONDITION","Clinical condition"),
    ("GERD_DYSPEPSIA","GERD / Dyspepsia","OTHER_CONDITION","Non-communicable"),
    ("GOUT","Gout","OTHER_CONDITION","Non-communicable"),
    ("IRON_DEF_ANEMIA","Iron Deficiency Anemia","OTHER_CONDITION","Non-communicable"),
    ("ALLERGIC_RHINITIS","Allergic Rhinitis","OTHER_CONDITION","Non-communicable"),
    ("IHD_ANGINA","Ischemic Heart Disease / Angina","CARDIOVASCULAR","Non-communicable"),
]


def seed_expanded_condition_master():
    db = SessionLocal()
    try:
        created = 0
        reused = 0

        for code, name, category, transmission in CONDITIONS:
            by_code = db.scalar(
                select(Disease).where(
                    Disease.code == code
                )
            )
            by_name = db.scalar(
                select(Disease).where(
                    func.lower(
                        func.trim(Disease.name)
                    ) == name.lower()
                )
            )

            if (
                by_code is not None
                and by_name is not None
                and by_code.id != by_name.id
            ):
                raise RuntimeError(
                    f"Ambiguous disease master mapping: {code} / {name}."
                )

            existing = by_code or by_name
            if existing is not None:
                reused += 1
                print(
                    f"[REUSE] {code} -> "
                    f"{existing.code!r} / {existing.name!r}"
                )
                continue

            db.add(
                Disease(
                    code=code,
                    name=name,
                    category=category,
                    transmission_type=transmission,
                    description=(
                        "Synthetic development condition master "
                        "entry for workflow and resource-allocation testing."
                    ),
                    is_communicable=False,
                    is_reportable=False,
                    is_sensitive=False,
                    privacy_category="STANDARD",
                    is_active=True,
                )
            )
            db.flush()
            created += 1
            print(f"[CREATED] {code} -> {name}")

        db.commit()

        print()
        print("EXPANDED CONDITION MASTER COMPLETE")
        print("==================================")
        print(f"Created: {created}")
        print(f"Reused: {reused}")
        print("Development configuration only.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_expanded_condition_master()
