def test_phase11_2_imports():
    print(
        "PHASE 11.2 ML IMPORT TEST"
    )
    print(
        "========================="
    )

    from app.ml.disease_medicine_mapping import (
        DISEASE_MEDICINE_RULES,
    )

    from app.ml.services.disease_medicine_mapping_service import (
        list_disease_medicine_mappings,
    )

    print(
        "app.ml.disease_medicine_mapping: OK"
    )

    print(
        "app.ml.services."
        "disease_medicine_mapping_service: OK"
    )

    print(
        f"Configured mapping rules: "
        f"{len(DISEASE_MEDICINE_RULES)}"
    )

    print()
    print(
        "Import verification passed."
    )


if __name__ == "__main__":
    test_phase11_2_imports()
