from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.inventory_transaction import InventoryTransaction
from app.models.user import User
from app.services.actor_snapshot_service import snapshot_user


def backfill_actor_snapshots():
    db = SessionLocal()

    try:
        users = list(
            db.scalars(
                select(User)
                .options(selectinload(User.roles))
            ).all()
        )

        actors = {
            user.id:
                snapshot_user(user)
            for user in users
        }

        counts = {
            "audit_logs": 0,
            "inventory_transactions": 0,
        }

        for row in db.scalars(
            select(AuditLog)
        ).all():
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

            if (
                actor
                and not row.recorded_by_name_snapshot
            ):
                row.recorded_by_name_snapshot = actor["display_name"]
                row.recorded_by_role_snapshot = actor["role_names"]
                counts["inventory_transactions"] += 1

        db.commit()

        print("ACTOR SNAPSHOT BACKFILL COMPLETE")
        print("================================")

        for key, value in counts.items():
            print(f"{key}: {value}")

        print()
        print("IMPORTANT LEGACY NOTE:")
        print(
            "Existing rows were backfilled using the user's "
            "CURRENT name/role because historical actor snapshots "
            "did not exist previously."
        )
        print(
            "All NEW audit and inventory transaction rows created "
            "after this patch capture immutable actor snapshots."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    backfill_actor_snapshots()
