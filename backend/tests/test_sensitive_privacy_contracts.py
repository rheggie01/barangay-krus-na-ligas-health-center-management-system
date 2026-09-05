from app.schemas.surveillance import (
    DiseaseCaseCountResponse,
    DiseaseStreetCountResponse,
    DiseaseWeeklyComparisonResponse,
)


IDENTIFYING_OR_FINE_GRAINED_FIELDS = {
    "patient_id",
    "patient_name",
    "first_name",
    "last_name",
    "birth_date",
    "phone",
    "email",
    "address",
    "latitude",
    "longitude",
    "household_id",
    "medical_record_number",
}


def test_sensitive_case_count_schema_is_aggregate_only():
    fields = set(
        DiseaseCaseCountResponse.model_fields
    )

    assert fields == {
        "disease_id",
        "code",
        "name",
        "case_count",
    }
    assert (
        fields
        & IDENTIFYING_OR_FINE_GRAINED_FIELDS
        == set()
    )


def test_sensitive_weekly_comparison_schema_is_aggregate_only():
    fields = set(
        DiseaseWeeklyComparisonResponse.model_fields
    )

    assert fields == {
        "disease_id",
        "code",
        "name",
        "current_week_cases",
        "previous_week_cases",
        "difference",
        "percentage_change",
        "trend",
    }
    assert (
        fields
        & IDENTIFYING_OR_FINE_GRAINED_FIELDS
        == set()
    )


def test_street_schema_contains_no_patient_identity_fields():
    fields = set(
        DiseaseStreetCountResponse.model_fields
    )

    assert "street" in fields
    assert "patient_id" not in fields
    assert "patient_name" not in fields
    assert "first_name" not in fields
    assert "last_name" not in fields


def test_aggregate_sensitive_contract_has_no_street_field():
    count_fields = set(
        DiseaseCaseCountResponse.model_fields
    )
    weekly_fields = set(
        DiseaseWeeklyComparisonResponse.model_fields
    )

    assert "street" not in count_fields
    assert "street" not in weekly_fields
    assert "address" not in count_fields
    assert "address" not in weekly_fields
