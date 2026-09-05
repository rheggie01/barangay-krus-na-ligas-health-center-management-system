from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_db,
)
from app.core.security import (
    create_access_token,
    hash_password,
)
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services.auth_service import (
    authenticate_user,
)
from app.services.audit_log_service import (
    create_audit_log,
    get_request_ip,
)


router = APIRouter()


# =========================================================
# REGISTER
# =========================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    registration: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # -----------------------------------------------------
    # NORMALIZE INPUT
    # -----------------------------------------------------

    username = (
        registration.username
        .strip()
    )

    email = (
        str(registration.email)
        .strip()
        .lower()
    )

    first_name = (
        registration.first_name
        .strip()
    )

    last_name = (
        registration.last_name
        .strip()
    )


    # -----------------------------------------------------
    # PASSWORD CONFIRMATION
    # -----------------------------------------------------

    if (
        registration.password
        != registration.confirm_password
    ):
        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )


    # -----------------------------------------------------
    # USERNAME CHECK
    # -----------------------------------------------------

    existing_username = db.scalar(
        select(User).where(
            User.username == username
        )
    )

    if existing_username:
        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=(
                "Username is already "
                "registered."
            ),
        )


    # -----------------------------------------------------
    # EMAIL CHECK
    # -----------------------------------------------------

    existing_email = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_email:
        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=(
                "Email address is already "
                "registered."
            ),
        )


    # -----------------------------------------------------
    # ROLE CHECK
    # -----------------------------------------------------

    role = db.scalar(
        select(Role).where(
            Role.name ==
            registration.role_name
        )
    )

    if not role:
        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,
            detail=(
                "The selected role is not "
                "configured in the system."
            ),
        )


    # -----------------------------------------------------
    # CREATE USER
    #
    # Self-registered users start inactive.
    # An administrator must approve the account.
    # -----------------------------------------------------

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(
            registration.password
        ),
        first_name=first_name,
        last_name=last_name,

        account_status="PENDING",
        is_active=False,
    )


    # -----------------------------------------------------
    # ASSIGN ROLE
    # -----------------------------------------------------

    user.roles.append(
        role
    )


    # -----------------------------------------------------
    # SAVE USER
    # -----------------------------------------------------

    try:
        db.add(user)
        create_audit_log(
            db,
            action="REGISTER",
            module="authentication",
            record_id=None,
            subject_label_snapshot=(
                f"@{username}"
            ),
            description=(
                "User registration submitted "
                f"for username {username}."
            ),
            ip_address=get_request_ip(request),
        )
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return RegisterResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=role.name,
        is_active=user.is_active,
        message=(
            "Registration submitted successfully. "
            "Your account is awaiting "
            "administrator approval."
        ),
    )


# =========================================================
# LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        credentials.username,
        credentials.password,
    )

    if not user:
        create_audit_log(
            db,
            action="LOGIN_FAILED",
            module="authentication",
            description=(
                "Failed login attempt for "
                f"username or email {credentials.username.strip()}."
            ),
            ip_address=get_request_ip(request),
        )
        db.commit()

        raise HTTPException(
            status_code=
                status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid username or password, "
                "or the account has not yet "
                "been approved."
            ),
        )


    access_token = (
        create_access_token(
            subject=str(user.id)
        )
    )

    create_audit_log(
        db,
        action="LOGIN_SUCCESS",
        module="authentication",
        user=user,
        record_id=user.id,
        description="User signed in successfully.",
        ip_address=get_request_ip(request),
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
    )


# =========================================================
# CURRENT USER
# =========================================================

@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):
    # -----------------------------------------------------
    # ROLES
    # -----------------------------------------------------

    roles = sorted({
        role.name
        for role in current_user.roles
    })


    # -----------------------------------------------------
    # PERMISSIONS
    # -----------------------------------------------------

    permissions = sorted({
        permission.code
        for role in current_user.roles
        for permission in role.permissions
    })


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return CurrentUserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        roles=roles,
        permissions=permissions,
    )
