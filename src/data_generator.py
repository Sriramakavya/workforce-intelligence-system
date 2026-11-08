"""Deterministic synthetic workforce data generator."""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import hashlib
import pandas as pd
import numpy as np

SEED = 20261022
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TRUTH = ROOT / "data" / "ground_truth"

ROLE_NAMES = ["Software Engineer", "Data Scientist", "Data Engineer", "QA Engineer",
              "DevOps Engineer", "Business Analyst", "Product Manager", "ML Engineer"]
SKILL_NAMES = ["Python", "Java", "SQL", "React", "AWS", "Docker", "Kubernetes",
               "Machine Learning", "Statistics", "Pandas", "FastAPI", "Testing",
               "Communication", "Agile", "Data Visualization", "Spark"]
PROJECT_NAMES = ["Customer Platform", "Analytics Modernization", "Cloud Migration",
                 "Fraud Detection", "Mobile Application", "Data Warehouse",
                 "AI Support Assistant", "Payments Upgrade"]

def make_id(prefix: str, n: int, width: int = 6) -> str:
    return f"{prefix}-{n:0{width}d}"

def generate(scale: str = "starter", seed: int = SEED, output_dir: Path = RAW):
    """Generate starter or full data. Full scale: 5,000 employees, 300 skills, 500 projects."""
    rng = np.random.default_rng(seed)
    if scale == "full":
        n_emp, n_skill, n_project = 5000, 300, 500
    else:
        n_emp, n_skill, n_project = 250, 40, 30

    output_dir.mkdir(parents=True, exist_ok=True)
    TRUTH.mkdir(parents=True, exist_ok=True)

    roles = pd.DataFrame([
        {"role_id": make_id("ROLE", i+1, 4), "role_name": name,
         "department": ["Engineering", "Data", "Operations", "Business"][i % 4],
         "active": True}
        for i, name in enumerate(ROLE_NAMES)
    ])

    skill_rows = []
    for i in range(n_skill):
        name = SKILL_NAMES[i] if i < len(SKILL_NAMES) else f"Specialized Skill {i+1:03d}"
        skill_rows.append({"skill_id": make_id("SKL", i+1), "skill_name": name,
                           "category": ["Technical", "Data", "Cloud", "Soft Skill"][i % 4],
                           "validity_months": int(rng.choice([12, 18, 24, 36]))})
    skills = pd.DataFrame(skill_rows)

    employees = []
    for i in range(n_emp):
        role = roles.iloc[int(rng.integers(0, len(roles)))]
        fte = float(rng.choice([0.5, 0.75, 1.0], p=[0.08, 0.12, 0.80]))
        employees.append({
            "employee_id": make_id("EMP", i+1), "employee_name": f"Employee {i+1:05d}",
            "role_id": role.role_id, "fte": fte, "hire_date": str(pd.Timestamp("2021-01-01") + pd.Timedelta(days=int(rng.integers(0, 1800)))).split()[0],
            "employment_status": "Active", "location": str(rng.choice(["Hyderabad", "Bengaluru", "Chennai", "Pune"]))
        })
    employees = pd.DataFrame(employees)

    employee_skills = []
    for emp in employees.itertuples(index=False):
        chosen = rng.choice(skills.skill_id.to_numpy(), size=min(6, n_skill), replace=False)
        for sid in chosen:
            employee_skills.append({
                "employee_skill_id": make_id("ES", len(employee_skills)+1),
                "employee_id": emp.employee_id, "skill_id": sid,
                "proficiency": int(rng.integers(1, 6)),
                "last_verified_date": str(pd.Timestamp("2026-11-01") - pd.Timedelta(days=int(rng.integers(0, 1000)))).split()[0],
                "status": "Verified"
            })
    employee_skills = pd.DataFrame(employee_skills)
    validity_lookup = dict(zip(skills.skill_id, skills.validity_months))
    employee_skills["expiry_date"] = [
        (pd.Timestamp(d) + pd.DateOffset(months=int(validity_lookup[sid]))).date().isoformat()
        for d, sid in zip(employee_skills.last_verified_date, employee_skills.skill_id)
    ]

    projects = []
    for i in range(n_project):
        start = pd.Timestamp("2026-01-01") + pd.Timedelta(days=int(rng.integers(0, 300)))
        projects.append({
            "project_id": f"PRJ-2026-{i+1:06d}", "project_name": f"{PROJECT_NAMES[i % len(PROJECT_NAMES)]} {i+1}",
            "start_date": str(start.date()), "end_date": str((start + pd.Timedelta(days=int(rng.integers(120, 500)))).date()),
            "project_status": "Active", "priority": str(rng.choice(["Low", "Medium", "High"], p=[0.2, 0.5, 0.3]))
        })
    projects = pd.DataFrame(projects)

    demand_rows = []
    for p in projects.itertuples(index=False):
        for week in range(1, 53):
            role = roles.iloc[int(rng.integers(0, len(roles)))]
            skill = skills.iloc[int(rng.integers(0, len(skills)))]
            demand_rows.append({
                "demand_id": f"DEM-{p.project_id}-2026W{week:02d}",
                "project_id": p.project_id, "role_id": role.role_id, "skill_id": skill.skill_id,
                "period": f"2026W{week:02d}", "required_fte": round(float(rng.uniform(0.5, 4.0)), 2),
                "minimum_proficiency": int(rng.integers(2, 5)), "status": "Approved"
            })
    demand = pd.DataFrame(demand_rows)

    allocations = []
    for i in range(max(n_emp, int(n_emp * 1.4))):
        emp = employees.iloc[int(rng.integers(0, n_emp))]
        proj = projects.iloc[int(rng.integers(0, n_project))]
        week = int(rng.integers(1, 53))
        allocations.append({
            "allocation_id": f"ALLOC-2026-{i+1:06d}", "employee_id": emp.employee_id,
            "project_id": proj.project_id, "period": f"2026W{week:02d}",
            "allocated_fte": round(float(rng.uniform(0.1, 0.8)), 2),
            "allocation_status": "Confirmed"
        })
    allocations = pd.DataFrame(allocations)

    availability = []
    for emp in employees.itertuples(index=False):
        for week in range(1, 53):
            leave = float(rng.choice([0, 0, 0, 0.2, 0.4, 0.6]))
            capacity = round(emp.fte * (1 - leave), 2)
            availability.append({
                "availability_id": make_id("AV", len(availability)+1),
                "employee_id": emp.employee_id, "period": f"2026W{week:02d}",
                "fte_capacity": capacity, "leave_fte": round(emp.fte * leave, 2)
            })
    availability = pd.DataFrame(availability)

    training = pd.DataFrame([{
        "training_id": make_id("TRN", i+1), "skill_id": skills.iloc[i % n_skill].skill_id,
        "training_name": f"{skills.iloc[i % n_skill].skill_name} Upskilling",
        "duration_weeks": int(rng.integers(2, 9)), "cost_usd": int(rng.integers(200, 2000)),
        "status": "Available"
    } for i in range(min(n_skill, 100))])

    # Required deliberate edge cases; records are tagged, not silently corrupted.
    anomaly_truth = []
    if len(allocations):
        allocations.loc[0, "allocated_fte"] = 1.5
        anomaly_truth.append({"record_type": "Allocation", "record_id": allocations.loc[0, "allocation_id"],
                              "issue_type": "ALLOCATION_EXCEEDS_AVAILABILITY",
                              "expected_decision": "Flag allocation for manager review"})
        employee_skills.loc[0, "last_verified_date"] = "2023-01-01"
        anomaly_truth.append({"record_type": "EmployeeSkill", "record_id": employee_skills.loc[0, "employee_skill_id"],
                              "issue_type": "STALE_SKILL_TREATED_CURRENT",
                              "expected_decision": "Require re-verification before matching"})
        demand.loc[1, ["project_id", "role_id", "skill_id", "period"]] = demand.loc[0, ["project_id", "role_id", "skill_id", "period"]]
        anomaly_truth.append({"record_type": "DemandPlan", "record_id": demand.loc[1, "demand_id"],
                              "issue_type": "DEMAND_DOUBLE_COUNTED",
                              "expected_decision": "Detect duplicate demand key and exclude duplicate"})
        if len(allocations) > 1:
            allocations.loc[1, "employee_id"] = allocations.loc[0, "employee_id"]
            other_projects = projects.loc[projects.project_id != allocations.loc[0, "project_id"], "project_id"]
            allocations.loc[1, "project_id"] = other_projects.iloc[0]
            allocations.loc[1, "period"] = allocations.loc[0, "period"]
            anomaly_truth.append({"record_type": "Allocation", "record_id": allocations.loc[1, "allocation_id"],
                                  "issue_type": "OVERLAPPING_PROJECT_ALLOCATION",
                                  "expected_decision": "Flag overlapping employee assignments"})

    employee_skills["expiry_date"] = [
        (pd.Timestamp(d) + pd.DateOffset(months=int(validity_lookup[sid]))).date().isoformat()
        for d, sid in zip(employee_skills.last_verified_date, employee_skills.skill_id)
    ]

    # Derive gap records from role + skill + proficiency + skill expiry.
    # Pre-aggregate by role/skill/proficiency to keep full-scale generation efficient.
    gap_rows = []
    es = employee_skills.merge(employees[["employee_id", "role_id"]], on="employee_id", how="left")
    es = es[pd.to_datetime(es.expiry_date) >= pd.Timestamp("2026-11-08")]
    prof = es.groupby(["role_id", "skill_id", "proficiency"]).employee_id.nunique().unstack(fill_value=0)
    prof = prof.reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
    cumulative = prof.iloc[:, ::-1].cumsum(axis=1).iloc[:, ::-1]
    eligible_lookup = {}
    for threshold in range(1, 6):
        for (role_id, skill_id), count in cumulative[threshold].items():
            eligible_lookup[(role_id, skill_id, threshold)] = int(count)
    for i, row in enumerate(demand.itertuples(index=False), start=1):
        available_count = eligible_lookup.get((row.role_id, row.skill_id, row.minimum_proficiency), 0)
        needed = max(1, int(np.ceil(row.required_fte)))
        gap_rows.append({
            "gap_id": make_id("GAP", i), "demand_id": row.demand_id,
            "project_id": row.project_id, "role_id": row.role_id, "skill_id": row.skill_id,
            "required_fte": row.required_fte, "available_employee_count": available_count,
            "gap_count": max(0, needed - available_count),
            "gap_status": "Gap" if needed > available_count else "Covered"
        })
    gaps = pd.DataFrame(gap_rows)

    # Append-only event history: creation is recorded as an event; source rows remain intact.
    allocation_events = pd.DataFrame([{
        "event_id": make_id("EVT", i+1), "allocation_id": row.allocation_id,
        "event_type": "CREATED", "event_date": "2026-11-08",
        "previous_status": "", "new_status": row.allocation_status,
        "event_note": "Synthetic allocation creation event"
    } for i, row in enumerate(allocations.itertuples(index=False))])

    tables = {
        "Employee": employees, "Role": roles, "Skill": skills,
        "EmployeeSkill": employee_skills, "Project": projects,
        "DemandPlan": demand, "Allocation": allocations,
        "Availability": availability, "Training": training, "GapAnalysis": gaps,
        "AllocationEvent": allocation_events
    }
    for name, df in tables.items():
        df.to_csv(output_dir / f"{name.lower()}.csv", index=False)
    truth_path = TRUTH / "ground_truth.csv"
    pd.DataFrame(anomaly_truth).to_csv(truth_path, index=False)
    manifest = {"seed": seed, "scale": scale, "generated_at_fixed_reference_date": "2026-11-08",
                "generated_tables": {k: len(v) for k, v in tables.items()},
                "ground_truth_rows": len(anomaly_truth),
                "period_coverage": "2026W01-2026W52",
                "provenance": "Fully synthetic data; no external personal or company data used"}
    (output_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2))
    checksums = {}
    for path in sorted(output_dir.glob("*.csv")):
        checksums[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output_dir / "checksums.json").write_text(json.dumps(checksums, indent=2))
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", choices=["starter", "full"], default="starter")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    print(json.dumps(generate(args.scale, args.seed), indent=2))
