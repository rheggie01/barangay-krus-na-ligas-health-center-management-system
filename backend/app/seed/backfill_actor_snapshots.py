from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.consultation import Consultation
from app.models.consultation_medicine import ConsultationMedicine
from app.models.disease_case import DiseaseCase
from app.models.inventory_transaction import InventoryTransaction
from app.models.patient_history import PatientMedicalHistory
from app.models.user import User
from app.services.actor_snapshot_service import snapshot_user


def _fill_pair(
    row,
    actor,
    name_field: str,
    role_field: str,
) -> bool:
    changed = False

    if not getattr(row, name_field):
        setattr(row, name_field, actor["display_name"])
        changed = True

    if not getattr(row, role_field):
        setattr(row, role_field, actor["role_names"])
        changed = True

    return changed


def backfill_actor_snapshots():
    db = SessionLocal()

    try:
        users = list(
            db.scalars(
                select(User).options(
                    selectinload(User.roles)
                )
            ).all()
        )

        actors = {
            user.id: snapshot_user(user)
            for user in users
        }

        counts = {
            "audit_logs": 0,
            "inventory_transactions": 0,
            "consultations": 0,
            "consultation_medicines": 0,
            "disease_cases_recorded": 0,
            "disease_cases_validated": 0,
            "patient_histories": 0,
        }

        for row in db.scalars(select(AuditLog)).all():
            actor = actors.get(row.user_id)

            if not actor:
                continue

            changed = False

            if not row.actor_username_snapshot:
                row.actor_username_snapshot = actor["username"]
                changed = True

            if not row.actor_name_snapshot:
                row.actor_name_snapshot = actor["display_name"]
                changed = True

            if not row.role_names:
                row.role_names = actor["role_names"]
                changed = True

            if changed:
                counts["audit_logs"] += 1

        for row in db.scalars(
            select(InventoryTransaction)
        ).all():
            actor = actors.get(row.recorded_by)

            if actor and _fill_pair(
                row,
                actor,
                "recorded_by_name_snapshot",
                "recorded_by_role_snapshot",
            ):
                counts["inventory_transactions"] += 1

        for row in db.scalars(
            select(Consultation)
        ).all():
            actor = actors.get(row.recorded_by)

            if actor and _fill_pair(
                row,
                actor,
                "recorded_by_name_snapshot",
                "recorded_by_role_snapshot",
            ):
                counts["consultations"] += 1

        for row in db.scalars(
            select(ConsultationMedicine)
        ).all():
            actor = actors.get(row.dispensed_by)

            if actor and _fill_pair(
                row,
                actor,
                "dispensed_by_name_snapshot",
                "dispensed_by_role_snapshot",
            ):
                counts["consultation_medicines"] += 1

        for row in db.scalars(
            select(DiseaseCase)
        ).all():
            recorder = actors.get(row.recorded_by)

            if recorder and _fill_pair(
                row,
                recorder,
                "recorded_by_name_snapshot",
                "recorded_by_role_snapshot",
            ):
                counts["disease_cases_recorded"] += 1

            validator = actors.get(row.validated_by)

            if validator and _fill_pair(
                row,
                validator,
                "validated_by_name_snapshot",
                "validated_by_role_snapshot",
            ):
                counts["disease_cases_validated"] += 1

        for row in db.scalars(
            select(PatientMedicalHistory)
        ).all():
            actor = actors.get(row.recorded_by)

            if actor and _fill_pair(
                row,
                actor,
                "recorded_by_name_snapshot",
                "recorded_by_role_snapshot",
            ):
                counts["patient_histories"] += 1

        db.commit()

        print("ACTOR SNAPSHOT BACKFILL COMPLETE")
        print("================================")

        for key, value in counts.items():
            print(f"{key}: {value}")

        print()
        print("IMPORTANT LEGACY NOTE:")
        print(
            "Records created before immutable snapshots existed "
            "are backfilled using the user's CURRENT stored "
            "name/role. This improves continuity but does not "
            "prove that the same role/name applied historically."
        )
        print(
            "All NEW records after this phase capture actor "
            "name/role snapshots at action time."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    backfill_actor_snapshots()
