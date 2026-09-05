import os
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# The application settings object is created at import time. These values are
# intentionally non-production placeholders so unit/policy tests never depend
# on a developer's .env file and never need to connect to the live database.
os.environ.setdefault("DATABASE_HOST", "127.0.0.1")
os.environ.setdefault("DATABASE_PORT", "3306")
os.environ.setdefault("DATABASE_NAME", "barangay_health_test")
os.environ.setdefault("DATABASE_USER", "test_user")
os.environ.setdefault("DATABASE_PASSWORD", "test_password")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "phase13-test-only-secret-key-not-for-production",
)
os.environ.setdefault("APP_ENV", "test")

# Register the RBAC association tables/classes before tests construct SQLAlchemy
# statements involving User.roles or Role.permissions. No database connection
# is opened by these imports.
import app.models.association  # noqa: E402,F401
import app.models.permission  # noqa: E402,F401
import app.models.role  # noqa: E402,F401
import app.models.user  # noqa: E402,F401
