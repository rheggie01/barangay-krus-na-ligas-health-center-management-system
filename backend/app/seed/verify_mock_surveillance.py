from sqlalchemy import (
    func,
    inspect,
    select,
)

from app.db.session import SessionLocal
from app.models.consultation import Consultation
from app.models.disease import Disease
from app.models.disease_case import DiseaseCase
from app.models.patient import Patient


MOCK_PREFIX = "MOCK-KNL-"


def _patient_has_column(
    column_name: str,
) -> bool:
    return column_name in {
        attribute.key
        for attribute
        in inspect(
            Patient
        ).column_attrs
    }


def verify_mock_surveillance():
    db = SessionLocal()

    try:
        mock_patient_ids = list(
            db.scalars(
                select(
                    Patient.id
                ).where(
                    Patient.patient_code.like(
                        f"{MOCK_PREFIX}%"
                    )
                )
            ).all()
        )

        patient_count = len(
            mock_patient_ids
        )

        if not mock_patient_ids:
            raise RuntimeError(
                "No MOCK-KNL-* patients found."
            )

        consultation_count = db.scalar(
            select(
                func.count(
                    Consultation.id
                )
            ).where(
                Consultation.patient_id.in_(
                    mock_patient_ids
                )
            )
        )

        validated_case_count = db.scalar(
            select(
                func.count(
                    DiseaseCase.id
                )
            ).where(
                DiseaseCase.patient_id.in_(
                    mock_patient_ids
                ),
                DiseaseCase.validation_status
                == "VALIDATED",
            )
        )

        missing_street = db.scalar(
            select(
                func.count(
                    Patient.id
                )
            ).where(
                Patient.id.in_(
                    mock_patient_ids
                ),
                (
                    Patient.street.is_(
                        None
                    )
                    |
                    (
                        func.trim(
                            Patient.street
                        )
                        == ""
                    )
                ),
            )
        )

        missing_address = 0

        if _patient_has_column(
            "address"
        ):
            missing_address = db.scalar(
                select(
                    func.count(
                        Patient.id
                    )
                ).where(
                    Patient.id.in_(
                        mock_patient_ids
                    ),
                    (
                        Patient.address.is_(
                            None
                        )
                        |
                        (
                            func.trim(
                                Patient.address
                            )
                            == ""
                        )
                    ),
                )
            )

        has_latitude = (
            _patient_has_column(
                "latitude"
            )
        )

        has_longitude = (
            _patient_has_column(
                "longitude"
            )
        )

        missing_coordinates = None

        if (
            has_latitude
            and has_longitude
        ):
            missing_coordinates = db.scalar(
                select(
                    func.count(
                        Patient.id
                    )
                ).where(
                    Patient.id.in_(
                        mock_patient_ids
                    ),
                    (
                        Patient.latitude.is_(
                            None
                        )
                        |
                        Patient.longitude.is_(
                            None
                        )
                    ),
                )
            )

        rows = db.execute(
            select(
                Disease.code,
                Disease.name,
                func.count(
                    DiseaseCase.id
                ),
            )
            .join(
                DiseaseCase,
                DiseaseCase.disease_id
                == Disease.id,
            )
            .where(
                DiseaseCase.patient_id.in_(
                    mock_patient_ids
                ),
                DiseaseCase.validation_status
                == "VALIDATED",
            )
            .group_by(
                Disease.code,
                Disease.name,
            )
            .order_by(
                Disease.name.asc()
            )
        ).all()

        disease_counts = {
            (
                code,
                name,
            ):
                count
            for (
                code,
                name,
                count,
            ) in rows
        }

        street_rows = db.execute(
            select(
                Patient.street,
                func.count(
                    DiseaseCase.id
                ),
            )
            .join(
                DiseaseCase,
                DiseaseCase.patient_id
                == Patient.id,
            )
            .where(
                Patient.id.in_(
                    mock_patient_ids
                ),
                DiseaseCase.validation_status
                == "VALIDATED",
            )
            .group_by(
                Patient.street
            )
            .order_by(
                func.count(
                    DiseaseCase.id
                ).desc()
            )
        ).all()

        print(
            "MOCK SURVEILLANCE VERIFICATION"
        )

        print(
            "================================"
        )

        print(
            f"Mock patients: "
            f"{patient_count}"
        )

        print(
            f"Mock consultations: "
            f"{consultation_count}"
        )

        print(
            "Validated mock disease cases: "
            f"{validated_case_count}"
        )

        print()

        print(
            "Patient model compatibility:"
        )

        print(
            "  latitude column: "
            + (
                "YES"
                if has_latitude
                else "NO (street reference mapping will be used)"
            )
        )

        print(
            "  longitude column: "
            + (
                "YES"
                if has_longitude
                else "NO (street reference mapping will be used)"
            )
        )

        print()

        print(
            "Completeness checks:"
        )

        print(
            f"  Missing street: "
            f"{missing_street}"
        )

        if _patient_has_column(
            "address"
        ):
            print(
                f"  Missing full address: "
                f"{missing_address}"
            )

        else:
            print(
                "  Full address column: "
                "NOT PRESENT IN CURRENT MODEL"
            )

        if (
            has_latitude
            and has_longitude
        ):
            print(
                f"  Missing coordinates: "
                f"{missing_coordinates}"
            )

        else:
            print(
                "  Coordinate completeness: "
                "N/A - current model uses "
                "street-level surveillance mapping"
            )

        print()

        print(
            "Disease counts:"
        )

        for (
            code,
            name,
        ), count in disease_counts.items():
            print(
                f"  {code!r} / "
                f"{name!r}: "
                f"{count}"
            )

        print()

        print(
            "Top streets:"
        )

        for (
            street,
            count,
        ) in street_rows[
            :10
        ]:
            print(
                f"  {street}: {count}"
            )

        if patient_count < 1500:
            raise RuntimeError(
                "Expected at least 1500 "
                "mock patients."
            )

        if consultation_count < 1500:
            raise RuntimeError(
                "Expected at least 1500 "
                "mock consultations."
            )

        if validated_case_count < 1500:
            raise RuntimeError(
                "Expected at least 1500 "
                "validated mock disease cases."
            )

        if missing_street:
            raise RuntimeError(
                "Mock patient street completeness "
                "verification failed."
            )

        if (
            _patient_has_column(
                "address"
            )
            and missing_address
        ):
            raise RuntimeError(
                "Mock patient address completeness "
                "verification failed."
            )

        if (
            has_latitude
            and has_longitude
            and missing_coordinates
        ):
            raise RuntimeError(
                "Mock patient coordinate completeness "
                "verification failed."
            )

        normalized_rows = {
            (
                str(code or "")
                .strip()
                .upper(),
                str(name or "")
                .strip()
                .lower(),
            )
            for (
                code,
                name,
            ) in disease_counts
        }

        # The project database can legitimately reuse legacy
        # Disease master codes/names. For example:
        #
        #   code='ARI'
        #   name='Acute Respiratory Infection'
        #
        # instead of:
        #
        #   name='Acute Respiratory Infection (ARI)'
        #
        # The verifier therefore accepts safe aliases for the
        # four synthetic development classes instead of
        # requiring one exact display name.
        expected_classes = {
            "DENGUE": {
                "codes": {
                    "DENGUE",
                    "DENG",
                },

                "names": {
                    "dengue",
                },
            },

            "ARI": {
                "codes": {
                    "ARI",
                },

                "names": {
                    "acute respiratory infection",
                    "acute respiratory infection (ari)",
                },
            },

            "ILI": {
                "codes": {
                    "ILI",
                },

                "names": {
                    "influenza-like illness",
                    "influenza-like illness (ili)",
                },
            },

            "DIARRHEA_GASTROENTERITIS": {
                "codes": {
                    "DIARRHEA_GASTROENTERITIS",
                    "GE",
                },

                "names": {
                    "diarrhea / gastroenteritis",
                    "diarrhea/gastroenteritis",
                    "gastroenteritis",
                },
            },
        }

        missing_classes = []

        for (
            class_name,
            aliases,
        ) in expected_classes.items():
            matched = any(
                (
                    row_code
                    in aliases[
                        "codes"
                    ]
                )
                or
                (
                    row_name
                    in aliases[
                        "names"
                    ]
                )
                for (
                    row_code,
                    row_name,
                ) in normalized_rows
            )

            if not matched:
                missing_classes.append(
                    class_name
                )

        if missing_classes:
            raise RuntimeError(
                "Missing synthetic disease classes: "
                + ", ".join(
                    missing_classes
                )
            )

        print()

        print(
            "Verification passed."
        )

        print(
            "Synthetic development dataset only; "
            "not official epidemiological evidence."
        )

    finally:
        db.close()


if __name__ == "__main__":
    verify_mock_surveillance()
