# Phase 2 — Synthetic Development Data + Validation

This folder prepares **development-only** datasets for the capstone ML and forecasting pipeline.

## Important data statement

The generated datasets are **synthetic development data**. They are **not** official Department of Health (DOH), Quezon City LGU, City Health Department, or Barangay Krus na Ligas patient records. The scenario probabilities used by the generator are engineering values for pipeline testing only and are **not medically validated probabilities**.

Any model metrics produced from these datasets must be described as **developmental/technical testing results only**, not real-world clinical accuracy.

## Prototype disease classes

- `DENGUE`
- `ARI`
- `ILI`
- `DIARRHEA_GASTROENTERITIS`

These are provisional prototype classes and should be revised if the authorized health-center dataset or health-professional validation requires a different scope.

## Generated datasets

### 1. `disease_classification_2021_2025.csv`

One synthetic consultation-style row per observation, with:

- synthetic record identifier only
- consultation date
- age and sex
- selected vital-sign fields
- 15 binary structured symptom features
- synthetic disease class label
- explicit synthetic source labels

No patient name, contact information, address, patient code, or location coordinates are included.

### 2. `disease_timeseries_2021_2025.csv`

Weekly synthetic case counts by disease class. This is intended for ARIMA/SARIMA pipeline development.

The `validated_case_count` name mirrors the intended production pipeline, where only authorized `VALIDATED` disease cases should be aggregated. In this synthetic file, `validation_basis=SYNTHETIC_WORKFLOW_STATE` makes clear that no real clinical validation occurred.

### 3. `medicine_consumption_2021_2025.csv`

Monthly synthetic medicine-dispensing demand for forecasting-pipeline development. Medicine names/codes are synthetic examples and do not represent treatment recommendations.

## Commands

Run from the `backend` directory:

```powershell
python -m app.ml.data.generate_synthetic_data
python -m app.ml.data.validate_dataset
```

Expected generation output:

```text
Synthetic development datasets generated successfully.
Classification rows: 6000
Disease time-series rows: 1044
Medicine consumption rows: 360
```

The exact disease time-series row count can vary slightly only if the configured date range changes.

Expected validation result:

```text
[PASS] disease_classification_2021_2025.csv
[PASS] disease_timeseries_2021_2025.csv
[PASS] medicine_consumption_2021_2025.csv
Dataset validation passed.
```

## Validation checks

The validator checks:

- required columns
- explicit synthetic-source labels
- duplicate synthetic record IDs
- date ranges and weekly/monthly date structure
- age ranges
- allowed sex values
- broad technical vital-sign bounds
- symptom values restricted to `0/1`
- allowed disease labels
- nonnegative case/dispensing quantities
- forbidden PII column names
- basic class-distribution warnings
- complete 60-month medicine series

These checks are **data engineering validation**, not clinical validation.

## Output folders

```text
app/ml/datasets/
├── synthetic/   # generator output
├── validated/   # copies written only after validation passes
└── reports/
    ├── synthetic_dataset_manifest.json
    └── dataset_validation_report.json
```

## Next phase

After this phase passes, build the classification training pipeline:

```text
Validated synthetic classification dataset
        ↓
Train/test split
        ↓
Preprocessing pipeline
        ↓
Logistic Regression + Random Forest
        ↓
Accuracy / Precision / Recall / F1 / Confusion Matrix
        ↓
Compare models
        ↓
Save selected development model + metadata
```

The selected development model must remain clearly labeled as synthetic-data trained until it is retrained and appropriately validated on authorized real-world data.
