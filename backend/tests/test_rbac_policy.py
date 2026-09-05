from app.seed.rbac import DEFAULT_PERMISSIONS, DEFAULT_ROLES


def roles_with(permission_code):
    return {
        role_name
        for role_name, permission_codes in DEFAULT_ROLES.items()
        if permission_code in permission_codes
    }


def test_every_role_permission_is_defined():
    defined = {
        permission["code"]
        for permission in DEFAULT_PERMISSIONS
    }

    for role_name, permission_codes in DEFAULT_ROLES.items():
        unknown = set(permission_codes) - defined
        assert unknown == set(), (
            f"{role_name} references undefined permissions: "
            f"{sorted(unknown)}"
        )


def test_medicine_dispense_policy_matrix():
    assert roles_with("MEDICINE_DISPENSE") == {
        "BHW",
        "DOCTOR",
        "HEALTH_CENTER_ADMIN",
        "MIDWIFE",
        "NURSE",
    }
    assert "SYSTEM_ADMIN" not in roles_with("MEDICINE_DISPENSE")


def test_disease_case_validation_is_doctor_only():
    assert roles_with("DISEASE_CASE_VALIDATE") == {"DOCTOR"}


def test_sensitive_disease_view_is_explicitly_restricted():
    assert roles_with("SENSITIVE_DISEASE_VIEW") == {"DOCTOR"}


def test_disease_prediction_excludes_system_admin_and_bhw():
    assert roles_with("DISEASE_PREDICT") == {
        "DOCTOR",
        "HEALTH_CENTER_ADMIN",
        "MIDWIFE",
        "NURSE",
    }


def test_user_management_is_limited_to_admin_roles():
    assert roles_with("USER_MANAGE") == {
        "HEALTH_CENTER_ADMIN",
        "SYSTEM_ADMIN",
    }
