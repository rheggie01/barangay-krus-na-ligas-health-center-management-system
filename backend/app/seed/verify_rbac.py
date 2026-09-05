from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.role import Role
from app.seed.rbac import DEFAULT_ROLES


def verify_rbac() -> int:
    db = SessionLocal()

    try:
        roles = list(
            db.scalars(
                select(Role).options(
                    selectinload(Role.permissions)
                )
            ).all()
        )
        actual = {
            role.name: {
                permission.code
                for permission in role.permissions
            }
            for role in roles
        }

        problems: list[str] = []

        for role_name, expected_codes in DEFAULT_ROLES.items():
            expected = set(expected_codes)
            current = actual.get(role_name)

            if current is None:
                problems.append(f"Missing role: {role_name}")
                continue

            missing = expected - current
            unexpected = current - expected

            if missing:
                problems.append(
                    f"{role_name} missing: {', '.join(sorted(missing))}"
                )

            if unexpected:
                problems.append(
                    f"{role_name} unexpected: {', '.join(sorted(unexpected))}"
                )

        if problems:
            print("RBAC verification failed:")
            for problem in problems:
                print(f"  - {problem}")
            return 1

        print("RBAC verification passed.")
        return 0

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(verify_rbac())
