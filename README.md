# Workforce Intelligence & Demand Forecasting System

A reproducible, synthetic-data prototype for workforce demand forecasting, role/skill gap analysis, capacity and utilization monitoring, exception detection, and hiring/training recommendations.

## What this project does

1. Generates master data and dependent records for Employee, Role, Skill, EmployeeSkill, Project, DemandPlan, Allocation, Availability, Training, and GapAnalysis, plus append-only AllocationEvent records.
2. Creates 52 weekly demand periods (one year) and supports both a starter dataset and the requested full-scale dataset.
3. Calculates employee-week capacity and utilization after leave and part-time FTE.
4. Matches skill demand to employee role, skill, minimum proficiency, and unexpired skill profiles (expiry is derived from each skill validity period).
5. Forecasts aggregate weekly FTE demand and produces separate next-12-week forecasts by project and role. The aggregate baseline is evaluated using a time-ordered holdout, MAE, RMSE, and a naive baseline; segmented forecasts also report holdout MAE/RMSE.
6. Detects four labelled edge cases and produces traceable recommendations.
7. Exports CSV, JSON, a local SQLite database, validation results, checksums, and a run summary.

## Requirements

- Python 3.10 or newer (tested with Python 3.11)
- Git
- VS Code recommended

All dependencies are free/open-source and run locally. No API key, cloud service, or external dataset is required.

## Windows setup (VS Code)

Open the extracted project folder in VS Code. Choose Terminal → New Terminal and run:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `py -3.11` is unavailable, use `python -m venv .venv` with an installed Python 3.10+ version.

## Run the complete starter workflow

```powershell
python main.py --scale starter
```

This generates the starter dataset, validates it, runs analytics, exports reports, and builds `outputs/workforce_intelligence.sqlite`.

## Generate full challenge volume

```powershell
python main.py --scale full
```

Full mode generates 5,000 employees, 300 skills, 500 projects and 52 weekly periods of demand (12 months). It also creates the dependent tables. Use starter mode first to verify setup; full mode uses more memory and takes longer.

Default seed is `20261022`. To specify it explicitly:

```powershell
python main.py --scale starter --seed 20261022
```

You can also run individual steps:

```powershell
python -m src.data_generator --scale starter --seed 20261022
python -m src.validation
python -m src.pipeline --scale starter --seed 20261022
python -m src.reproducibility --scale starter --seed 20261022
```

The reproducibility command generates the same scale twice and writes `outputs/reproducibility_report.json` after comparing row counts, CSV hashes, and the separate ground-truth file.

## Run automated tests

```powershell
pytest -q
```

Tests cover primary/foreign key validation, required entities, event references, anomaly detection, capacity outputs, and forecast evaluation.

## Launch the dashboard

After generating data:

```powershell
streamlit run app/dashboard.py
```

The dashboard shows workforce counts, employee-week utilization, demand forecast and holdout metrics, skill gaps, recommended actions, and detected exceptions.

## Output files

- `data/raw/*.csv`: generated entity tables, `source_manifest.json`, and generator checksums.
- `data/ground_truth/ground_truth.csv`: separate labels for the four deliberately injected anomaly classes. This file is never loaded as an analytics feature.
- `outputs/utilization_report.csv`: capacity, allocated FTE, balance and utilization per employee-week.
- `outputs/skill_gap_report.csv`: demand-to-skill gap details.
- `outputs/demand_forecast.csv`: next 12 weekly aggregate FTE forecasts.
- `outputs/segmented_demand_forecast.csv`: next 12 weekly forecasts by project and role, with segment holdout MAE/RMSE.
- `outputs/forecast_metrics.json`: time-based holdout MAE/RMSE and naive MAE.
- `outputs/detected_anomalies.csv`: exception type and record ID.
- `outputs/recommendations.csv`: hiring/training/cross-training rule and assumption.
- `outputs/validation_report.csv`: structural and business-key validation results.
- `outputs/run_summary.json`: measurable run summary.
- `outputs/workforce_intelligence.sqlite`: local relational seed database.
- `outputs/checksums.json`: SHA-256 hashes for generated input and output artifacts.
- `outputs/reproducibility_report.json`: result of the two-run fixed-seed comparison.

## Reproducibility check

Run the same command twice with the same seed. Compare `data/raw/checksums.json` and `outputs/checksums.json`. Identical inputs and configuration should produce identical CSV content and hashes. The generator uses a fixed reference date and fixed seed; it does not rely on the machine's current date.

## Business rules and assumptions

See `docs/assumptions.md`, `docs/data_dictionary.md`, and `docs/database_schema.md`. Important formulas:

- Available capacity = employee contractual FTE - leave FTE.
- Utilization = allocated FTE / available capacity (when capacity is zero, utilization is reported as zero and the zero-capacity condition should be reviewed separately).
- Skill match requires role match, skill match, proficiency at or above demand minimum, and verification within 365 days of the fixed reference date.
- Skill gap count = max(0, ceil(required FTE) - eligible employee count). This is a transparent proxy measured in people, not a full optimization model.
- Forecast model = linear regression on weekly aggregate FTE; the last eight observed weeks (or a smaller-data fallback) are held out in time order. MAE and RMSE are compared with a last-observation naive baseline.
- Duplicate demand business keys are excluded from the aggregate forecast, flagged as exceptions, and retained in the raw input with unique immutable demand IDs.

## AI use and individual work disclosure

AI assistance was used to help plan, draft, debug, and document parts of this project. The candidate must review and understand the code, rerun the checks, make their own final decisions, and be able to explain the design, assumptions, dependencies, and limitations. `PROMPT_HISTORY.md` is provided as a prompt log; add every additional prompt used in any AI tool before submission. AI responses do not need to be included according to the candidate FAQ.

## Limitations and next steps

This is a synthetic-data prototype, not a production staffing system. The forecast is a simple baseline and should be compared with additional models on real historical holdouts. Gap count is a people-count proxy; a production system should solve role/skill/FTE matching with employee availability, proficiency expiry by skill, geography, project dates, and allocation constraints. SQLite is a local seed/export database, not a multi-user transactional service. Access control, approval workflows, full lifecycle transitions, and human review are future work.

## Lawful data provenance

No external employee or company data is used. All records are generated synthetically for this challenge; no personal information, confidential data, or external dataset is redistributed.

## Full-scale generated artifact bundle

`artifacts/full_scale_bundle.zip` contains the full-scale 5,000-employee export, all entity CSVs, ground-truth labels, analytics/validation reports, run and reproducibility summaries, and the full-scale SQLite database. The normal project folder retains the smaller starter dataset so a reviewer can run the application quickly. Recreate the full-scale bundle by running `python main.py --scale full` and exporting the generated `data/` and `outputs/` artifacts.
