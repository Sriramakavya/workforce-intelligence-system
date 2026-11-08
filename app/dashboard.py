from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
import plotly.express as px
from src.data_generator import generate, RAW
from src.analytics import load_tables, utilization_report, skill_gap_report, forecast_demand, forecast_segmented_demand, detect_anomalies, recommendations

st.set_page_config(page_title="Workforce Intelligence", layout="wide")
st.title("Workforce Intelligence & Demand Forecasting")
st.caption("Synthetic workforce planning prototype | Fixed seed: 20261022 | Reference date: 2026-11-08")
if not (RAW / "employee.csv").exists():
    st.warning("No generated data found. Creating starter dataset.")
    generate("starter")
t = load_tables()
util = utilization_report(t)
gaps = skill_gap_report(t)
forecast, metrics = forecast_demand(t)
segmented_forecast = forecast_segmented_demand(t)
anomalies = detect_anomalies(t)
recs = recommendations(t)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Employees", f"{len(t['employee']):,}")
c2.metric("Projects", f"{len(t['project']):,}")
c3.metric("Demand skill gaps", f"{int((gaps.gap_count > 0).sum()):,}")
c4.metric("Detected exception rows", f"{len(anomalies):,}")

st.subheader("Utilization and capacity")
status = util.groupby("utilization_status", as_index=False).size()
st.plotly_chart(px.bar(status, x="utilization_status", y="size", title="Employee-week utilization status"), use_container_width=True)
st.dataframe(util.sort_values("utilization", ascending=False).head(25), use_container_width=True)

st.subheader("Demand forecast")
if not forecast.empty:
    st.plotly_chart(px.line(forecast, x="week_num", y="forecast_fte", markers=True, title="Next 12 weeks: total required FTE"), use_container_width=True)
    a, b, c = st.columns(3)
    a.metric("Holdout MAE", metrics["mae"])
    b.metric("Holdout RMSE", metrics["rmse"])
    c.metric("Naive baseline MAE", metrics["naive_mae"])
    st.caption(f"Time-based holdout: {metrics['holdout_weeks']} final weeks. Compare model MAE with naive baseline MAE.")

if not segmented_forecast.empty:
    st.subheader("Forecast by project and role")
    project_tab, role_tab = st.tabs(["Projects", "Roles"])
    with project_tab:
        project_view = segmented_forecast[segmented_forecast.entity_type == "project"]
        st.dataframe(project_view.sort_values("forecast_fte", ascending=False).head(30), use_container_width=True)
    with role_tab:
        role_view = segmented_forecast[segmented_forecast.entity_type == "role"]
        st.dataframe(role_view.sort_values("forecast_fte", ascending=False).head(30), use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Skill gap analysis")
    st.dataframe(gaps.sort_values("gap_count", ascending=False).head(30), use_container_width=True)
with right:
    st.subheader("Hiring and training recommendations")
    st.dataframe(recs[["project_id", "skill_name", "gap_count", "recommended_action", "assumption"]].head(30), use_container_width=True)

st.subheader("Detected exceptions")
st.dataframe(anomalies, use_container_width=True)
st.subheader("Ground truth labels")
st.caption("Known injected cases are stored separately in data/ground_truth/ground_truth.csv and are not loaded as model features.")
st.caption("Forecast and recommendations are transparent baseline heuristics, not production decisions. Review assumptions before acting.")
