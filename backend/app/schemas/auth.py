from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


# =========================================================
# LOGIN
# =========================================================

class LoginRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


# =========================================================
# TOKEN
# =========================================================

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# =========================================================
# CURRENT USER
# =========================================================

class CurrentUserResponse(BaseModel):
    id: int

    username: str
    email: EmailStr

    first_name: str
    last_name: str

    is_active: bool

    roles: list[str]
    permissions: list[str]


# =========================================================
# REGISTRATION REQUEST
# =========================================================

class RegisterRequest(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    email: EmailStr

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=128,
    )

    role_name: str

    privacy_accepted: bool


    # -----------------------------------------------------
    # NAME VALIDATION
    # -----------------------------------------------------

    @field_validator(
        "first_name",
        "last_name",
    )
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "This field cannot be empty."
            )

        return cleaned


    # -----------------------------------------------------
    # USERNAME VALIDATION
    # -----------------------------------------------------

    @field_validator("username")
    @classmethod
    def clean_username(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Username cannot be empty."
            )

        return cleaned


    # -----------------------------------------------------
    # ROLE VALIDATION
    # -----------------------------------------------------

    @field_validator("role_name")
    @classmethod
    def validate_role(
        cls,
        value: str,
    ) -> str:

        cleaned = value.strip().upper()

        allowed_roles = {
            "BHW",
            "HEALTH_CENTER_ADMIN",
            "DOCTOR",
            "NURSE",
            "MIDWIFE",
        }

        if cleaned not in allowed_roles:
            raise ValueError(
                "Invalid role selected."
            )

        return cleaned


    # -----------------------------------------------------
    # DATA PRIVACY VALIDATION
    # -----------------------------------------------------

    @field_validator("privacy_accepted")
    @classmethod
    def validate_privacy(
        cls,
        value: bool,
    ) -> bool:

        if not value:
            raise ValueError(
                "You must acknowledge "
                "the Data Privacy Act."
            )

        return value


    # -----------------------------------------------------
    # PASSWORD CONFIRMATION
    # -----------------------------------------------------

    @model_validator(mode="after")
    def validate_password_match(self):

        if self.password != self.confirm_password:
            raise ValueError(
                "Passwords do not match."
            )

        return self


# =========================================================
# REGISTRATION RESPONSE
# =========================================================

class RegisterResponse(BaseModel):
    id: int

    username: str
    email: EmailStr

    first_name: str
    last_name: str

    role: str

    is_active: bool

    message: str