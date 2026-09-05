"""Generate reproducible synthetic development datasets for ML prototyping.

IMPORTANT
---------
The generated values are engineering-only scenario data. They are not official
DOH/LGU records, are not medically validated symptom probabilities, and must not
be used as a substitute for clinical judgment or real-world model validation.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from app.ml.config import (
    CLASSIFICATION_ROWS_PER_YEAR,
    DISEASE_CLASSES,
    END_DATE,
    RANDOM_SEED,
    REPORTS_DIR,
    START_DATE,
    SYMPTOM_CODES,
    SYNTHETIC_DIR,
    SYNTHETIC_LABEL_SOURCE,
    SYNTHETIC_SOURCE,
)


CLASSIFICATION_FILE = SYNTHETIC_DIR / "disease_classification_2021_2025.csv"
DISEASE_TIMESERIES_FILE = SYNTHETIC_DIR / "disease_timeseries_2021_2025.csv"
MEDICINE_CONSUMPTION_FILE = SYNTHETIC_DIR / "medicine_consumption_2021_2025.csv"
MANIFEST_FILE = REPORTS_DIR / "synthetic_dataset_manifest.json"


# Engineering-only scenario profiles. These values are intentionally kept in
# the synthetic generator and must not be cited as clinical probabilities.
SYMPTOM_SCENARIOS = {
    "DENGUE": {
        "FEVER": 0.94,
        "COUGH": 0.08,
        "RUNNY_NOSE": 0.05,
        "SORE_THROAT": 0.05,
        "HEADACHE": 0.72,
        "BODY_PAIN": 0.68,
        "VOMITING": 0.31,
        "DIARRHEA": 0.12,
        "ABDOMINAL_PAIN": 0.19,
        "RASH": 0.28,
        "NAUSEA": 0.37,
        "FATIGUE": 0.59,
        "DIFFICULTY_BREATHING": 0.03,
        "LOSS_OF_APPETITE": 0.48,
        "CHILLS": 0.36,
    },
    "ARI": {
        "FEVER": 0.56,
        "COUGH": 0.91,
        "RUNNY_NOSE": 0.77,
        "SORE_THROAT": 0.61,
        "HEADACHE": 0.29,
        "BODY_PAIN": 0.24,
        "VOMITING": 0.05,
        "DIARRHEA": 0.04,
        "ABDOMINAL_PAIN": 0.03,
        "RASH": 0.02,
        "NAUSEA": 0.06,
        "FATIGUE": 0.31,
        "DIFFICULTY_BREATHING": 0.13,
        "LOSS_OF_APPETITE": 0.19,
        "CHILLS": 0.16,
    },
    "ILI": {
        "FEVER": 0.91,
        "COUGH": 0.82,
        "RUNNY_NOSE": 0.51,
        "SORE_THROAT": 0.47,
        "HEADACHE": 0.66,
        "BODY_PAIN": 0.73,
        "VOMITING": 0.09,
        "DIARRHEA": 0.06,
        "ABDOMINAL_PAIN": 0.04,
        "RASH": 0.01,
        "NAUSEA": 0.12,
        "FATIGUE": 0.71,
        "DIFFICULTY_BREATHING": 0.07,
        "LOSS_OF_APPETITE": 0.32,
        "CHILLS": 0.62,
    },
    "DIARRHEA_GASTROENTERITIS": {
        "FEVER": 0.36,
        "COUGH": 0.03,
        "RUNNY_NOSE": 0.02,
        "SORE_THROAT": 0.02,
        "HEADACHE": 0.14,
        "BODY_PAIN": 0.13,
        "VOMITING": 0.58,
        "DIARRHEA": 0.95,
        "ABDOMINAL_PAIN": 0.78,
        "RASH": 0.02,
        "NAUSEA": 0.63,
        "FATIGUE": 0.38,
        "DIFFICULTY_BREATHING": 0.01,
        "LOSS_OF_APPETITE": 0.53,
        "CHILLS": 0.12,
    },
}


# Scenario-only seasonal weights. They create predictable engineering patterns
# for testing forecasting code; they are not epidemiological claims.
MONTHLY_DISEASE_WEIGHTS = {
    "DENGUE": {
        1: 0.6, 2: 0.6, 3: 0.7, 4: 0.8, 5: 1.0, 6: 1.4,
        7: 1.8, 8: 2.0, 9: 2.2, 10: 2.0, 11: 1.5, 12: 0.9,
    },
    "ARI": {
        1: 1.3, 2: 1.2, 3: 1.0, 4: 0.9, 5: 0.9, 6: 1.0,
        7: 1.1, 8: 1.2, 9: 1.2, 10: 1.3, 11: 1.4, 12: 1.4,
    },
    "ILI": {
        1: 1.8, 2: 1.6, 3: 1.3, 4: 0.9, 5: 0.8, 6: 0.8,
        7: 0.9, 8: 0.9, 9: 1.0, 10: 1.3, 11: 1.6, 12: 1.9,
    },
    "DIARRHEA_GASTROENTERITIS": {
        1: 0.9, 2: 0.9, 3: 1.0, 4: 1.4, 5: 1.7, 6: 1.5,
        7: 1.2, 8: 1.1, 9: 1.0, 10: 0.9, 11: 0.9, 12: 0.9,
    },
}


MEDICINE_SCENARIOS = (
    {
        "medicine_code": "SYN-MED-001",
        "medicine_name": "Paracetamol 500 mg Tablet",
        "base_monthly_demand": 520,
        "season_phase": 0.0,
    },
    {
        "medicine_code": "SYN-MED-002",
        "medicine_name": "Oral Rehydration Salts Sachet",
        "base_monthly_demand": 260,
        "season_phase": 1.2,
    },
    {
        "medicine_code": "SYN-MED-003",
        "medicine_name": "Ascorbic Acid 500 mg Tablet",
        "base_monthly_demand": 410,
        "season_phase": 2.1,
    },
    {
        "medicine_code": "SYN-MED-004",
        "medicine_name": "Cetirizine 10 mg Tablet",
        "base_monthly_demand": 300,
        "season_phase": 0.8,
    },
    {
        "medicine_code": "SYN-MED-005",
        "medicine_name": "Amoxicillin 500 mg Capsule",
        "base_monthly_demand": 215,
        "season_phase": 2.8,
    },
    {
        "medicine_code": "SYN-MED-006",
        "medicine_name": "Zinc Sulfate 20 mg Tablet",
        "base_monthly_demand": 175,
        "season_phase": 1.7,
    },
)


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _random_date(rng: random.Random, start: date, end: date) -> date:
    span = (end - start).days
    return start + timedelta(days=rng.randint(0, span))


def _choose_disease(rng: random.Random, month: int) -> str:
    weights = [
        MONTHLY_DISEASE_WEIGHTS[disease][month]
        for disease in DISEASE_CLASSES
    ]
    return rng.choices(DISEASE_CLASSES, weights=weights, k=1)[0]


def _sample_age(rng: random.Random) -> int:
    # Broad synthetic distribution only; not intended to reproduce population
    # demographics of Barangay Krus na Ligas.
    value = int(round(rng.triangular(0, 85, 28)))
    return max(0, min(value, 85))


def _sample_symptoms(rng: random.Random, disease: str) -> dict[str, int]:
    probabilities = SYMPTOM_SCENARIOS[disease]
    sampled = {
        code: int(rng.random() < probabilities[code])
        for code in SYMPTOM_CODES
    }

    # Ensure each synthetic record carries at least one structured symptom.
    if not any(sampled.values()):
        highest = max(probabilities, key=probabilities.get)
        sampled[highest] = 1

    return sampled


def _sample_vitals(
    rng: random.Random,
    symptoms: dict[str, int],
) -> dict[str, str | int | float]:
    if symptoms["FEVER"]:
        temperature = round(rng.uniform(37.8, 40.2), 1)
    else:
        temperature = round(rng.uniform(36.1, 37.4), 1)

    heart_rate = int(round(rng.gauss(86 if symptoms["FEVER"] else 78, 11)))
    respiratory_rate = int(round(rng.gauss(20, 4)))
    oxygen_saturation = round(rng.uniform(94.0, 100.0), 1)

    if symptoms["DIFFICULTY_BREATHING"]:
        respiratory_rate += rng.randint(3, 8)
        oxygen_saturation = round(rng.uniform(88.0, 96.0), 1)

    return {
        "temperature": max(34.0, min(temperature, 42.0)),
        "heart_rate": max(45, min(heart_rate, 170)),
        "respiratory_rate": max(8, min(respiratory_rate, 40)),
        "oxygen_saturation": max(80.0, min(oxygen_saturation, 100.0)),
    }


def generate_classification_dataset(rng: random.Random) -> list[dict[str, object]]:
    start = _parse_date(START_DATE)
    end = _parse_date(END_DATE)

    rows: list[dict[str, object]] = []
    record_number = 1

    for year in range(start.year, end.year + 1):
        year_start = max(start, date(year, 1, 1))
        year_end = min(end, date(year, 12, 31))

        for _ in range(CLASSIFICATION_ROWS_PER_YEAR):
            consultation_date = _random_date(rng, year_start, year_end)
            disease = _choose_disease(rng, consultation_date.month)
            symptoms = _sample_symptoms(rng, disease)
            vitals = _sample_vitals(rng, symptoms)

            row: dict[str, object] = {
                "synthetic_record_id": f"SYN-CLS-{record_number:06d}",
                "consultation_date": consultation_date.isoformat(),
                "age": _sample_age(rng),
                "sex": rng.choice(("F", "M")),
                **vitals,
            }

            for code in SYMPTOM_CODES:
                row[code.lower()] = symptoms[code]

            row.update(
                {
                    "disease_label": disease,
                    "label_source": SYNTHETIC_LABEL_SOURCE,
                    "data_source": SYNTHETIC_SOURCE,
                }
            )

            rows.append(row)
            record_number += 1

    rows.sort(key=lambda item: (item["consultation_date"], item["synthetic_record_id"]))
    return rows


def write_classification_dataset(rows: list[dict[str, object]]) -> None:
    fieldnames = [
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
    ]

    with CLASSIFICATION_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_disease_timeseries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    start = _parse_date(START_DATE)
    end = _parse_date(END_DATE)
    # Use Monday week-start dates that remain inside the configured
    # 2021-2025 range. The first partial days before the first Monday are
    # excluded from the weekly forecasting series.
    first_week = start + timedelta(days=(7 - start.weekday()) % 7)
    last_week = end - timedelta(days=end.weekday())

    counts: Counter[tuple[date, str]] = Counter()

    for row in rows:
        consultation_date = _parse_date(str(row["consultation_date"]))
        week_start = consultation_date - timedelta(days=consultation_date.weekday())
        counts[(week_start, str(row["disease_label"]))] += 1

    output: list[dict[str, object]] = []
    week = first_week

    while week <= last_week:
        for disease in DISEASE_CLASSES:
            output.append(
                {
                    "week_start": week.isoformat(),
                    "disease_label": disease,
                    "validated_case_count": counts[(week, disease)],
                    "validation_basis": "SYNTHETIC_WORKFLOW_STATE",
                    "data_source": SYNTHETIC_SOURCE,
                }
            )
        week += timedelta(days=7)

    return output


def write_disease_timeseries(rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "week_start",
        "disease_label",
        "validated_case_count",
        "validation_basis",
        "data_source",
    ]

    with DISEASE_TIMESERIES_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _month_starts(start: date, end: date) -> list[date]:
    current = date(start.year, start.month, 1)
    result: list[date] = []

    while current <= end:
        result.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return result


def generate_medicine_consumption(rng: random.Random) -> list[dict[str, object]]:
    start = _parse_date(START_DATE)
    end = _parse_date(END_DATE)
    months = _month_starts(start, end)

    output: list[dict[str, object]] = []

    for month_index, month_start in enumerate(months):
        year_index = month_start.year - start.year
        month_angle = (2 * math.pi * (month_start.month - 1)) / 12

        for medicine in MEDICINE_SCENARIOS:
            seasonal_factor = 1 + 0.18 * math.sin(
                month_angle + float(medicine["season_phase"])
            )
            trend_factor = 1 + 0.025 * year_index
            noise_factor = max(0.75, rng.gauss(1.0, 0.08))

            quantity = int(
                round(
                    float(medicine["base_monthly_demand"])
                    * seasonal_factor
                    * trend_factor
                    * noise_factor
                )
            )

            output.append(
                {
                    "month_start": month_start.isoformat(),
                    "medicine_code": medicine["medicine_code"],
                    "medicine_name": medicine["medicine_name"],
                    "quantity_dispensed": max(0, quantity),
                    "data_source": SYNTHETIC_SOURCE,
                }
            )

    return output


def write_medicine_consumption(rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "month_start",
        "medicine_code",
        "medicine_name",
        "quantity_dispensed",
        "data_source",
    ]

    with MEDICINE_CONSUMPTION_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(
    classification_rows: list[dict[str, object]],
    disease_timeseries_rows: list[dict[str, object]],
    medicine_rows: list[dict[str, object]],
) -> None:
    class_distribution = Counter(
        str(row["disease_label"])
        for row in classification_rows
    )

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "random_seed": RANDOM_SEED,
        "date_range": {
            "start": START_DATE,
            "end": END_DATE,
        },
        "disclaimer": (
            "Synthetic development data only. Not official DOH/LGU records, "
            "not medically validated probabilities, and not evidence of "
            "real-world predictive performance."
        ),
        "disease_classes": list(DISEASE_CLASSES),
        "symptom_codes": list(SYMPTOM_CODES),
        "files": {
            CLASSIFICATION_FILE.name: {
                "rows": len(classification_rows),
                "class_distribution": dict(sorted(class_distribution.items())),
            },
            DISEASE_TIMESERIES_FILE.name: {
                "rows": len(disease_timeseries_rows),
            },
            MEDICINE_CONSUMPTION_FILE.name: {
                "rows": len(medicine_rows),
                "medicine_count": len(MEDICINE_SCENARIOS),
            },
        },
    }

    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    rng = random.Random(RANDOM_SEED)

    classification_rows = generate_classification_dataset(rng)
    write_classification_dataset(classification_rows)

    disease_timeseries_rows = generate_disease_timeseries(classification_rows)
    write_disease_timeseries(disease_timeseries_rows)

    medicine_rows = generate_medicine_consumption(rng)
    write_medicine_consumption(medicine_rows)

    write_manifest(
        classification_rows=classification_rows,
        disease_timeseries_rows=disease_timeseries_rows,
        medicine_rows=medicine_rows,
    )

    print("Synthetic development datasets generated successfully.")
    print(f"Classification rows: {len(classification_rows)}")
    print(f"Disease time-series rows: {len(disease_timeseries_rows)}")
    print(f"Medicine consumption rows: {len(medicine_rows)}")
    print(f"Output directory: {SYNTHETIC_DIR}")


if __name__ == "__main__":
    main()
