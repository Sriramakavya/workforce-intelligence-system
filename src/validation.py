"""Integrity checks. Intentional business anomalies are reported separately from structural failures."""
from pathlib import Path
import pandas as pd

PRIMARY_KEYS = {
    "employee": "employee_id", "role": "role_id", "skill": "skill_id",
    "employeeskill": "employee_skill_id", "project": "project_id",
    "demandplan": "demand_id", "allocation": "allocation_id",
    "availability": "availability_id", "training": "training_id",
    "gapanalysis": "gap_id", "allocationevent": "event_id"
}
RELATIONS = [
    ("employee", "role_id", "role", "role_id"),
    ("employeeskill", "employee_id", "employee", "employee_id"),
    ("employeeskill", "skill_id", "skill", "skill_id"),
    ("demandplan", "project_id", "project", "project_id"),
    ("demandplan", "role_id", "role", "role_id"),
    ("demandplan", "skill_id", "skill", "skill_id"),
    ("allocation", "employee_id", "employee", "employee_id"),
    ("allocation", "project_id", "project", "project_id"),
    ("availability", "employee_id", "employee", "employee_id"),
    ("training", "skill_id", "skill", "skill_id"),
    ("gapanalysis", "demand_id", "demandplan", "demand_id"),
    ("gapanalysis", "project_id", "project", "project_id"),
    ("gapanalysis", "role_id", "role", "role_id"),
    ("gapanalysis", "skill_id", "skill", "skill_id"),
    ("allocationevent", "allocation_id", "allocation", "allocation_id"),
]

def validate(data_dir):
    p = Path(data_dir)
    tables = {x.stem: pd.read_csv(x) for x in p.glob("*.csv")}
    checks = []
    def add(name, passed, detail):
        checks.append({"check": name, "passed": bool(passed), "detail": str(detail)})
    for table, key in PRIMARY_KEYS.items():
        df = tables.get(table)
        good = df is not None and key in df and df[key].notna().all() and not df[key].duplicated().any()
        add(f"{table} primary key unique and non-null", good, f"{len(df) if df is not None else 0} rows")
    for child, fk, parent, pk in RELATIONS:
        if child not in tables or parent not in tables or fk not in tables[child] or pk not in tables[parent]:
            add(f"{child}.{fk} foreign key", False, "table or column missing")
        else:
            missing = int((~tables[child][fk].isin(tables[parent][pk])).sum())
            add(f"{child}.{fk} foreign key", missing == 0, f"{missing} invalid references")
    for table, col in [("employee", "fte"), ("availability", "fte_capacity"),
                       ("availability", "leave_fte"), ("allocation", "allocated_fte"),
                       ("demandplan", "required_fte"), ("training", "duration_weeks"),
                       ("training", "cost_usd")]:
        df = tables.get(table)
        ok = df is not None and col in df and pd.to_numeric(df[col], errors="coerce").notna().all() and (df[col] >= 0).all()
        add(f"{table}.{col} numeric non-negative", ok, "range checked")
    if "employeeskill" in tables:
        es = tables["employeeskill"]
        add("employee skill proficiency 1-5", es.proficiency.between(1, 5).all(), "scale 1 to 5")
        add("employee skill expiry dates valid", pd.to_datetime(es.expiry_date, errors="coerce").notna().all(), "expiry derived from skill validity months")
        add("employee-skill pair unique", not es.duplicated(["employee_id", "skill_id"]).any(), "bridge uniqueness")
    if "availability" in tables and "employee" in tables:
        av = tables["availability"].merge(tables["employee"][["employee_id", "fte"]], on="employee_id", how="left")
        ok = (av.fte_capacity + av.leave_fte - av.fte).abs().max() < 1e-8
        add("availability capacity reconciles to contractual FTE", ok, "fte_capacity + leave_fte = employee FTE")
        add("availability employee-period unique", not av.duplicated(["employee_id", "period"]).any(), "one row per employee-week")
    if "project" in tables:
        pr = tables["project"]
        add("project dates ordered", (pd.to_datetime(pr.end_date) >= pd.to_datetime(pr.start_date)).all(), "start_date <= end_date")
    if "demandplan" in tables:
        d = tables["demandplan"]
        duplicate_rows = int(d.duplicated(["project_id", "role_id", "skill_id", "period"], keep=False).sum())
        truth_path = p.parent / "ground_truth" / "ground_truth.csv"
        labelled = False
        if truth_path.exists():
            truth = pd.read_csv(truth_path)
            labelled = "DEMAND_DOUBLE_COUNTED" in set(truth.get("issue_type", []))
        add("demand duplicate business keys are labelled", duplicate_rows == 0 or labelled,
            f"{duplicate_rows} duplicate rows; ground-truth label present={labelled}")
        add("demand period values valid", d.period.astype(str).str.fullmatch(r"2026W(0[1-9]|[1-4][0-9]|5[0-2])").all(), "2026W01 through 2026W52")
    if "allocation" in tables:
        a = tables["allocation"]
        add("allocation period values valid", a.period.astype(str).str.fullmatch(r"2026W(0[1-9]|[1-4][0-9]|5[0-2])").all(), "2026W01 through 2026W52")
    return pd.DataFrame(checks)

if __name__ == "__main__":
    from src.data_generator import RAW
    result = validate(RAW)
    out = Path(__file__).resolve().parents[1] / "outputs" / "validation_report.csv"
    out.parent.mkdir(exist_ok=True)
    result.to_csv(out, index=False)
    print(result.to_string(index=False))
    print(f"\nPassed: {int(result.passed.sum())}/{len(result)}")
    if not result.passed.all():
        raise SystemExit(1)
