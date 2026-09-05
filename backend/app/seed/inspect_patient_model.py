from sqlalchemy import inspect

from app.models.patient import Patient


def inspect_patient_model():
    columns = [
        attribute.key
        for attribute
        in inspect(
            Patient
        ).column_attrs
    ]

    print(
        "CURRENT PATIENT MODEL COLUMNS"
    )

    print(
        "============================="
    )

    for column in columns:
        print(
            f"  {column}"
        )


if __name__ == "__main__":
    inspect_patient_model()
