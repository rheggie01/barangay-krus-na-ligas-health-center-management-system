from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
)


class PatientRepository:
    """
    Database access layer for patient records.
    """

    # =====================================================
    # GET ALL PATIENTS
    # =====================================================

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[Patient]:
        statement = (
            select(Patient)
            .order_by(
                Patient.id.desc()
            )
        )

        result = db.scalars(
            statement
        ).all()

        return list(result)


    # =====================================================
    # GET PATIENT BY ID
    # =====================================================

    @staticmethod
    def get_by_id(
        db: Session,
        patient_id: int,
    ) -> Patient | None:
        statement = (
            select(Patient)
            .where(
                Patient.id == patient_id
            )
        )

        return db.scalar(
            statement
        )


    # =====================================================
    # GET PATIENT BY CODE
    # =====================================================

    @staticmethod
    def get_by_patient_code(
        db: Session,
        patient_code: str,
    ) -> Patient | None:
        statement = (
            select(Patient)
            .where(
                Patient.patient_code ==
                patient_code
            )
        )

        return db.scalar(
            statement
        )


    # =====================================================
    # CREATE PATIENT
    # =====================================================

    @staticmethod
    def create(
        db: Session,
        *,
        patient_code: str,
        patient_data: PatientCreate,
    ) -> Patient:
        data = (
            patient_data.model_dump()
        )

        patient = Patient(
            patient_code=patient_code,
            **data,
        )

        db.add(patient)
        db.commit()
        db.refresh(patient)

        return patient


    # =====================================================
    # UPDATE PATIENT
    # =====================================================

    @staticmethod
    def update(
        db: Session,
        *,
        patient: Patient,
        patient_data: PatientUpdate,
    ) -> Patient:
        # Only update values actually provided
        # by the frontend.
        #
        # Because "suffix" exists in PatientUpdate,
        # values such as "Jr." and "III" will also
        # be included here automatically.

        update_data = (
            patient_data.model_dump(
                exclude_unset=True
            )
        )

        for field, value in update_data.items():
            setattr(
                patient,
                field,
                value,
            )

        db.add(patient)
        db.commit()
        db.refresh(patient)

        return patient


    # =====================================================
    # DELETE PATIENT
    # =====================================================

    @staticmethod
    def delete(
        db: Session,
        *,
        patient: Patient,
    ) -> None:
        db.delete(patient)
        db.commit()