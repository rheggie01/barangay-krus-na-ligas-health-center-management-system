from getpass import getpass

from sqlalchemy import or_, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.role import Role
from app.models.user import User


def create_admin():
    db = SessionLocal()

    try:
        print("\nCreate Administrator Account")
        print("----------------------------")

        username = input("Username: ").strip()
        email = input("Email: ").strip().lower()
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()

        password = getpass("Password: ")
        confirm_password = getpass("Confirm password: ")

        if not username:
            print("Username is required.")
            return

        if not email:
            print("Email is required.")
            return

        if not first_name or not last_name:
            print("First name and last name are required.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        if len(password) < 8:
            print("Password must be at least 8 characters long.")
            return

        existing_user = db.scalar(
            select(User).where(
                or_(
                    User.username == username,
                    User.email == email,
                )
            )
        )

        if existing_user:
            print(
                "A user with that username or email already exists."
            )
            return

        admin_role = db.scalar(
            select(Role).where(
                Role.name == "SYSTEM_ADMIN"
            )
        )

        if not admin_role:
            print(
                "SYSTEM_ADMIN role was not found. "
                "Run the RBAC seed first."
            )
            return

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        user.roles.append(admin_role)

        db.add(user)
        db.commit()
        db.refresh(user)

        print("\nAdministrator created successfully.")
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()