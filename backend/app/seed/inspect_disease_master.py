from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.disease import Disease


def inspect_disease_master():
    db = SessionLocal()

    try:
        rows = db.scalars(
            select(
                Disease
            )
            .order_by(
                Disease.name.asc(),
                Disease.id.asc(),
            )
        ).all()

        print(
            "DISEASE MASTER"
        )

        print(
            "=============="
        )

        for disease in rows:
            print(
                f"id={disease.id} | "
                f"code={disease.code!r} | "
                f"name={disease.name!r} | "
                f"active={disease.is_active}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    inspect_disease_master()
