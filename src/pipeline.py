"""Run analytics, export measurable outputs, and create a local SQLite seed database."""
from pathlib import Path
import argparse, json, sqlite3, hashlib
import pandas as pd
from src.data_generator import generate, RAW, ROOT
from src.analytics import load_tables, utilization_report, skill_gap_report, forecast_demand, forecast_segmented_demand, detect_anomalies, recommendations
from src.validation import validate

OUT = ROOT / "outputs"

def run(scale="starter", seed=20261022):
    manifest = generate(scale, seed)
    tables = load_tables()
    OUT.mkdir(exist_ok=True)
    util = utilization_report(tables)
    gaps = skill_gap_report(tables)
    forecast, metrics = forecast_demand(tables)
    segmented_forecast = forecast_segmented_demand(tables)
    anomalies = detect_anomalies(tables)
    recs = recommendations(tables)
    util.to_csv(OUT / "utilization_report.csv", index=False)
    gaps.to_csv(OUT / "skill_gap_report.csv", index=False)
    forecast.to_csv(OUT / "demand_forecast.csv", index=False)
    segmented_forecast.to_csv(OUT / "segmented_demand_forecast.csv", index=False)
    anomalies.to_csv(OUT / "detected_anomalies.csv", index=False)
    recs.to_csv(OUT / "recommendations.csv", index=False)
    validation = validate(RAW)
    validation.to_csv(OUT / "validation_report.csv", index=False)
    (OUT / "forecast_metrics.json").write_text(json.dumps(metrics, indent=2))
    summary = {
        "seed": seed, "scale": scale, "employees": len(tables["employee"]),
        "projects": len(tables["project"]), "skills": len(tables["skill"]),
        "demand_rows": len(tables["demandplan"]),
        "project_role_forecast_rows": len(segmented_forecast),
        "employee_periods": len(util),
        "overallocated_employee_periods": int((util.utilization_status == "Overallocated").sum()),
        "high_utilization_employee_periods": int((util.utilization_status == "High utilization").sum()),
        "skill_gap_rows": int((gaps.gap_count > 0).sum()),
        "detected_anomaly_rows": len(anomalies),
        "validation_passed": int(validation.passed.sum()),
        "validation_total": len(validation), "forecast_metrics": metrics,
        "generator_manifest": manifest
    }
    (OUT / "run_summary.json").write_text(json.dumps(summary, indent=2))
    # Local relational seed database; CSV remains the portable interchange format.
    db_path = OUT / "workforce_intelligence.sqlite"
    if db_path.exists(): db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        for name, df in tables.items():
            df.to_sql(name.lower(), conn, index=False, if_exists="replace")
        conn.execute("CREATE INDEX idx_allocation_employee_period ON allocation(employee_id, period)")
        conn.execute("CREATE INDEX idx_demand_project_period ON demandplan(project_id, period)")
    # Hash all generated inputs and outputs (except the hash file itself).
    files = sorted(list(RAW.glob("*.csv")) + list(OUT.glob("*.csv")) + list(OUT.glob("*.json")))
    hashes = {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.name != "checksums.json"}
    (OUT / "checksums.json").write_text(json.dumps(hashes, indent=2))
    print(json.dumps(summary, indent=2))
    if not validation.passed.all():
        raise SystemExit("Validation failed. Inspect outputs/validation_report.csv")
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=["starter", "full"], default="starter")
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    run(args.scale, args.seed)
