"""Validate synthetic development datasets before ML training/forecasting."""

from __future__ import annotations

import csv
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from app.ml.config import (
    DISEASE_CLASSES,
    END_DATE,
    FORBIDDEN_PII_COLUMNS,
    REPORTS_DIR,
    START_DATE,
    SYMPTOM_CODES,
    SYNTHETIC_DIR,
    SYNTHETIC_LABEL_SOURCE,
    SYNTHETIC_SOURCE,
    VALIDATED_DIR,
)


CLASSIFICATION_FILE = SYNTHETIC_DIR / "disease_classification_2021_2025.csv"
DISEASE_TIMESERIES_FILE = SYNTHETIC_DIR / "disease_timeseries_2021_2025.csv"
MEDICINE_CONSUMPTION_FILE = SYNTHETIC_DIR / "medicine_consumption_2021_2025.csv"
VALIDATION_REPORT = REPORTS_DIR / "dataset_validation_report.json"


class ValidationResult:
    def __init__(self, dataset_name: str) -> None:
        self.dataset_name = dataset_name
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.metrics: dict[str, object] = {}

    @property
    def passed(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset": self.dataset_name,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    return fieldnames, rows


def _check_required_columns(
    result: ValidationResult,
    fieldnames: list[str],
    required: set[str],
) -> None:
    missing = sorted(required - set(fieldnames))
    if missing:
        result.errors.append(
            "Missing required column(s): " + ", ".join(missing)
        )


def _check_forbidden_pii(
    result: ValidationResult,
    fieldnames: list[str],
) -> None:
    present = sorted(FORBIDDEN_PII_COLUMNS.intersection(fieldnames))
    if present:
        result.errors.append(
            "Forbidden PII column(s) present: " + ", ".join(present)
        )


def _parse_iso_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def _validate_classification() -> ValidationResult:
    result = ValidationResult(CLASSIFICATION_FILE.name)

    required = {
        "synthetic_record_id",
        "consultation_date",
        "age",
        "sex",
        "temperature",
        "heart_rate",
        "respiratory_rate",
        "oxygen_saturation",
        *[code.lower() for code in SYMPTOM_CODES],
        "disease_label",
        "label_source",
        "data_source",
    }

    try:
        fieldnames, rows = _read_csv(CLASSIFICATION_FILE)
    except FileNotFoundError:
        result.errors.append(f"File not found: {CLASSIFICATION_FILE}")
        return result

    _check_required_columns(result, fieldnames, required)
    _check_forbidden_pii(result, fieldnames)

    if result.errors:
        return result

    seen_ids: set[str] = set()
    duplicates = 0
    invalid_dates = 0
    invalid_ages = 0
    invalid_sex = 0
    invalid_vitals = 0
    invalid_symptoms = 0
    invalid_labels = 0
    invalid_sources = 0
    class_counts: Counter[str] = Counter()

    start = _parse_iso_date(START_DATE)
    end = _parse_iso_date(END_DATE)

    for line_number, row in enumerate(rows, start=2):
        record_id = row["synthetic_record_id"].strip()
        if record_id in seen_ids:
            duplicates += 1
        seen_ids.add(record_id)

        try:
            consultation_date = _parse_iso_date(row["consultation_date"])
            if not (start <= consultation_date <= end):
                invalid_dates += 1
        except ValueError:
            invalid_dates += 1

        try:
            age = int(row["age"])
            if not 0 <= age <= 100:
                invalid_ages += 1
        except ValueError:
            invalid_ages += 1

        if row["sex"] not in {"F", "M"}:
            invalid_sex += 1

        try:
            temperature = float(row["temperature"])
            heart_rate = int(row["heart_rate"])
            respiratory_rate = int(row["respiratory_rate"])
            oxygen_saturation = float(row["oxygen_saturation"])

            if not (
                34.0 <= temperature <= 42.5
                and 35 <= heart_rate <= 200
                and 6 <= respiratory_rate <= 50
                and 70.0 <= oxygen_saturation <= 100.0
            ):
                invalid_vitals += 1
        except ValueError:
            invalid_vitals += 1

        for code in SYMPTOM_CODES:
            if row[code.lower()] not in {"0", "1"}:
                invalid_symptoms += 1
                break

        label = row["disease_label"]
        class_counts[label] += 1
        if label not in DISEASE_CLASSES:
            invalid_labels += 1

        if (
            row["data_source"] != SYNTHETIC_SOURCE
            or row["label_source"] != SYNTHETIC_LABEL_SOURCE
        ):
            invalid_sources += 1

    checks = {
        "duplicate_record_ids": duplicates,
        "invalid_dates": invalid_dates,
        "invalid_ages": invalid_ages,
        "invalid_sex_values": invalid_sex,
        "invalid_vitals": invalid_vitals,
        "invalid_symptom_rows": invalid_symptoms,
        "invalid_disease_labels": invalid_labels,
        "invalid_source_labels": invalid_sources,
    }

    for label, count in checks.items():
        if count:
            result.errors.append(f"{label}: {count}")

    missing_classes = sorted(set(DISEASE_CLASSES) - set(class_counts))
    if missing_classes:
        result.errors.append(
            "Missing disease class(es): " + ", ".join(missing_classes)
        )

    if class_counts:
        smallest = min(class_counts.values())
        largest = max(class_counts.values())
        imbalance_ratio = round(largest / smallest, 3) if smallest else None
        if imbalance_ratio and imbalance_ratio > 3.0:
            result.warnings.append(
                f"Class imbalance ratio is {imbalance_ratio}; review before training."
            )
    else:
        imbalance_ratio = None

    result.metrics = {
        "row_count": len(rows),
        "unique_record_ids": len(seen_ids),
        "class_distribution": dict(sorted(class_counts.items())),
        "class_imbalance_ratio": imbalance_ratio,
        **checks,
    }

    return result


def _validate_disease_timeseries() -> ValidationResult:
    result = ValidationResult(DISEASE_TIMESERIES_FILE.name)

    required = {
        "week_start",
        "disease_label",
        "validated_case_count",
        "validation_basis",
        "data_source",
    }

    try:
        fieldnames, rows = _read_csv(DISEASE_TIMESERIES_FILE)
    except FileNotFoundError:
        result.errors.append(f"File not found: {DISEASE_TIMESERIES_FILE}")
        return result

    _check_required_columns(result, fieldnames, required)
    _check_forbidden_pii(result, fieldnames)

    if result.errors:
        return result

    seen_keys: set[tuple[str, str]] = set()
    duplicate_keys = 0
    invalid_dates = 0
    invalid_counts = 0
    invalid_labels = 0
    invalid_sources = 0
    class_counts: Counter[str] = Counter()
    weeks_by_disease: defaultdict[str, set[str]] = defaultdict(set)

    start = _parse_iso_date(START_DATE)
    end = _parse_iso_date(END_DATE)

    for row in rows:
        key = (row["week_start"], row["disease_label"])
        if key in seen_keys:
            duplicate_keys += 1
        seen_keys.add(key)

        try:
            parsed = _parse_iso_date(row["week_start"])
            if (
                parsed.weekday() != 0
                or not (start <= parsed <= end)
            ):
                invalid_dates += 1
        except ValueError:
            invalid_dates += 1

        try:
            count = int(row["validated_case_count"])
            if count < 0:
                invalid_counts += 1
        except ValueError:
            invalid_counts += 1

        disease = row["disease_label"]
        class_counts[disease] += 1
        weeks_by_disease[disease].add(row["week_start"])

        if disease not in DISEASE_CLASSES:
            invalid_labels += 1

        if (
            row["data_source"] != SYNTHETIC_SOURCE
            or row["validation_basis"] != "SYNTHETIC_WORKFLOW_STATE"
        ):
            invalid_sources += 1

    checks = {
        "duplicate_week_disease_keys": duplicate_keys,
        "invalid_week_start_values": invalid_dates,
        "invalid_case_counts": invalid_counts,
        "invalid_disease_labels": invalid_labels,
        "invalid_source_labels": invalid_sources,
    }

    for label, count in checks.items():
        if count:
            result.errors.append(f"{label}: {count}")

    week_counts = {
        disease: len(weeks_by_disease[disease])
        for disease in DISEASE_CLASSES
    }

    if len(set(week_counts.values())) > 1:
        result.warnings.append(
            "Disease classes do not all have the same number of weekly observations."
        )

    result.metrics = {
        "row_count": len(rows),
        "weekly_observations_by_disease": week_counts,
        **checks,
    }

    return result


def _validate_medicine_consumption() -> ValidationResult:
    result = ValidationResult(MEDICINE_CONSUMPTION_FILE.name)

    required = {
        "month_start",
        "medicine_code",
        "medicine_name",
        "quantity_dispensed",
        "data_source",
    }

    try:
        fieldnames, rows = _read_csv(MEDICINE_CONSUMPTION_FILE)
    except FileNotFoundError:
        result.errors.append(f"File not found: {MEDICINE_CONSUMPTION_FILE}")
        return result

    _check_required_columns(result, fieldnames, required)
    _check_forbidden_pii(result, fieldnames)

    if result.errors:
        return result

    seen_keys: set[tuple[str, str]] = set()
    duplicate_keys = 0
    invalid_dates = 0
    invalid_quantities = 0
    invalid_sources = 0
    months_by_medicine: defaultdict[str, set[str]] = defaultdict(set)

    start = _parse_iso_date(START_DATE)
    end = _parse_iso_date(END_DATE)

    for row in rows:
        key = (row["month_start"], row["medicine_code"])
        if key in seen_keys:
            duplicate_keys += 1
        seen_keys.add(key)

        try:
            parsed = _parse_iso_date(row["month_start"])
            if (
                parsed.day != 1
                or not (start <= parsed <= end)
            ):
                invalid_dates += 1
        except ValueError:
            invalid_dates += 1

        try:
            quantity = int(row["quantity_dispensed"])
            if quantity < 0:
                invalid_quantities += 1
        except ValueError:
            invalid_quantities += 1

        if row["data_source"] != SYNTHETIC_SOURCE:
            invalid_sources += 1

        months_by_medicine[row["medicine_code"]].add(row["month_start"])

    checks = {
        "duplicate_month_medicine_keys": duplicate_keys,
        "invalid_month_start_values": invalid_dates,
        "invalid_quantities": invalid_quantities,
        "invalid_source_labels": invalid_sources,
    }

    for label, count in checks.items():
        if count:
            result.errors.append(f"{label}: {count}")

    month_counts = {
        medicine: len(months)
        for medicine, months in sorted(months_by_medicine.items())
    }

    expected_months = 60
    incomplete = {
        medicine: count
        for medicine, count in month_counts.items()
        if count != expected_months
    }

    if incomplete:
        result.warnings.append(
            "Expected 60 monthly observations per synthetic medicine; "
            f"found incomplete series: {incomplete}"
        )

    result.metrics = {
        "row_count": len(rows),
        "medicine_count": len(month_counts),
        "monthly_observations_by_medicine": month_counts,
        **checks,
    }

    return result


def _copy_validated_files() -> None:
    VALIDATED_DIR.mkdir(parents=True, exist_ok=True)

    for source in (
        CLASSIFICATION_FILE,
        DISEASE_TIMESERIES_FILE,
        MEDICINE_CONSUMPTION_FILE,
    ):
        shutil.copy2(
            source,
            VALIDATED_DIR / source.name,
        )


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    results = [
        _validate_classification(),
        _validate_disease_timeseries(),
        _validate_medicine_consumption(),
    ]

    overall_passed = all(result.passed for result in results)

    report = {
        "validated_at": datetime.now().isoformat(timespec="seconds"),
        "overall_passed": overall_passed,
        "disclaimer": (
            "Validation here checks engineering/schema/data-quality rules only. "
            "It is not clinical or epidemiological validation."
        ),
        "datasets": [result.to_dict() for result in results],
    }

    VALIDATION_REPORT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.dataset_name}")

        for warning in result.warnings:
            print(f"  WARNING: {warning}")

        for error in result.errors:
            print(f"  ERROR: {error}")

    print(f"Validation report: {VALIDATION_REPORT}")

    if overall_passed:
        _copy_validated_files()
        print(f"Validated copies written to: {VALIDATED_DIR}")
        print("Dataset validation passed.")
        return

    print("Dataset validation failed.")
    sys.exit(1)


if __name__ == "__main__":
    main()
