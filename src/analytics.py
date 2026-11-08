"""Transparent workforce planning analytics and evaluation."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

TABLES = ["employee", "role", "skill", "employeeskill", "project", "demandplan",
          "allocation", "availability", "training", "gapanalysis", "allocationevent"]

def load_tables(data_dir=RAW):
    return {name: pd.read_csv(Path(data_dir) / f"{name}.csv") for name in TABLES
            if (Path(data_dir) / f"{name}.csv").exists()}

def utilization_report(t):
    a, v = t["allocation"], t["availability"]
    allocated = a.groupby(["employee_id", "period"], as_index=False).allocated_fte.sum()
    result = v.merge(allocated, on=["employee_id", "period"], how="left")
    result["allocated_fte"] = result.allocated_fte.fillna(0)
    result["utilization"] = np.divide(result.allocated_fte, result.fte_capacity,
        out=np.zeros(len(result), dtype=float), where=result.fte_capacity.to_numpy() > 0)
    result["capacity_balance_fte"] = result.fte_capacity - result.allocated_fte
    result["utilization_status"] = np.select(
        [result.utilization > 1.000001, result.utilization >= .8],
        ["Overallocated", "High utilization"], default="Available")
    return result

def skill_gap_report(t):
    gaps = t["gapanalysis"].merge(t["skill"][["skill_id", "skill_name"]], on="skill_id", how="left")
    return gaps.merge(t["project"][["project_id", "project_name"]], on="project_id", how="left")

def forecast_demand(t, periods=12):
    """Fit on earlier weeks and report holdout metrics before refitting all history."""
    demand = t["demandplan"].drop_duplicates(
        ["project_id", "role_id", "skill_id", "period"], keep="first").copy()
    demand["week_num"] = demand.period.str.extract(r"W(\d+)").astype(int)
    weekly = demand.groupby("week_num", as_index=False).required_fte.sum().sort_values("week_num")
    if len(weekly) < 6:
        return pd.DataFrame(columns=["week_num", "forecast_fte"]), {"mae": None, "rmse": None, "holdout_weeks": 0}
    holdout_n = min(8, max(2, len(weekly) // 5))
    train, test = weekly.iloc[:-holdout_n], weekly.iloc[-holdout_n:]
    model = LinearRegression().fit(train[["week_num"]], train.required_fte)
    pred = np.clip(model.predict(test[["week_num"]]), 0, None)
    baseline = np.repeat(train.required_fte.iloc[-1], len(test))
    metrics = {"mae": round(float(mean_absolute_error(test.required_fte, pred)), 4),
               "rmse": round(float(np.sqrt(mean_squared_error(test.required_fte, pred))), 4),
               "naive_mae": round(float(mean_absolute_error(test.required_fte, baseline)), 4),
               "holdout_weeks": int(len(test))}
    final_model = LinearRegression().fit(weekly[["week_num"]], weekly.required_fte)
    future = pd.DataFrame({"week_num": range(int(weekly.week_num.max())+1,
                                               int(weekly.week_num.max())+1+periods)})
    future["forecast_fte"] = np.clip(final_model.predict(future[["week_num"]]), 0, None).round(2)
    return future, metrics

def detect_anomalies(t):
    a, v = t["allocation"], t["availability"]
    av = a.merge(v[["employee_id", "period", "fte_capacity"]], on=["employee_id", "period"], how="left")
    over = av[av.allocated_fte > av.fte_capacity]
    d = t["demandplan"]
    dup = d[d.duplicated(["project_id", "role_id", "skill_id", "period"], keep=False)]
    overlaps = a[a.duplicated(["employee_id", "period"], keep=False)]
    es = t["employeeskill"].copy()
    es["last_verified_date"] = pd.to_datetime(es.last_verified_date, errors="coerce")
    stale = es[es.last_verified_date < pd.Timestamp("2025-11-08")]
    rows = []
    for df, issue, key in [(over, "ALLOCATION_EXCEEDS_AVAILABILITY", "allocation_id"),
                           (dup, "DEMAND_DOUBLE_COUNTED", "demand_id"),
                           (overlaps, "OVERLAPPING_PROJECT_ALLOCATION", "allocation_id"),
                           (stale, "STALE_SKILL_TREATED_CURRENT", "employee_skill_id")]:
        for rid in df[key].astype(str).tolist():
            rows.append({"issue_type": issue, "record_id": rid})
    return pd.DataFrame(rows, columns=["issue_type", "record_id"])

def recommendations(t):
    gaps = skill_gap_report(t)
    result = gaps[gaps.gap_count > 0].copy()
    training_skills = set(t["training"].skill_id) if "training" in t else set()
    result["recommended_action"] = np.where(
        result.skill_id.isin(training_skills), "Train existing employees",
        np.where(result.gap_count >= 2, "Hire for skill gap", "Cross-train or hire"))
    result["assumption"] = "Gap is derived from demand FTE rounded up minus eligible verified skill-profile coverage; see methodology."
    return result

def forecast_segmented_demand(t, periods=12):
    """Forecast weekly FTE separately for each project and each role."""
    demand = t["demandplan"].drop_duplicates(
        ["project_id", "role_id", "skill_id", "period"], keep="first").copy()
    demand["week_num"] = demand.period.str.extract(r"W(\d+)").astype(int)
    rows = []
    for dimension, entity_type in [("project_id", "project"), ("role_id", "role")]:
        for entity_id, group in demand.groupby(dimension):
            weekly = group.groupby("week_num", as_index=False).required_fte.sum().sort_values("week_num")
            if len(weekly) < 6:
                continue
            holdout_n = min(8, max(2, len(weekly) // 5))
            train, test = weekly.iloc[:-holdout_n], weekly.iloc[-holdout_n:]
            model = LinearRegression().fit(train[["week_num"]], train.required_fte)
            pred = np.clip(model.predict(test[["week_num"]]), 0, None)
            mae = float(mean_absolute_error(test.required_fte, pred))
            rmse = float(np.sqrt(mean_squared_error(test.required_fte, pred)))
            final_model = LinearRegression().fit(weekly[["week_num"]], weekly.required_fte)
            future = pd.DataFrame({"week_num": range(int(weekly.week_num.max()) + 1,
                                                       int(weekly.week_num.max()) + 1 + periods)})
            future["forecast_fte"] = np.clip(final_model.predict(future[["week_num"]]), 0, None)
            for r in future.itertuples(index=False):
                rows.append({"entity_type": entity_type, "entity_id": entity_id,
                             "week_num": int(r.week_num), "forecast_fte": round(float(r.forecast_fte), 2),
                             "holdout_mae": round(mae, 4), "holdout_rmse": round(rmse, 4)})
    result = pd.DataFrame(rows)
    if not result.empty:
        project_names = t["project"][["project_id", "project_name"]].rename(
            columns={"project_id": "entity_id", "project_name": "entity_name"})
        role_names = t["role"][["role_id", "role_name"]].rename(
            columns={"role_id": "entity_id", "role_name": "entity_name"})
        names = pd.concat([project_names, role_names], ignore_index=True)
        result = result.merge(names, on="entity_id", how="left")
        result["period"] = result.week_num.map(lambda w: f"2026W{w:02d}" if w <= 52 else f"2027W{w-52:02d}")
    return result
