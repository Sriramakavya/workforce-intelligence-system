# Assumptions, methodology and limitations

1. All people, projects, skills, allocations, availability and training records are synthetic. No external personal or company data is used.
2. Reference date for deterministic recency checks is 2026-11-08. The fixed random seed defaults to 20261022.
3. Employee FTE is contractual capacity (0.5, 0.75 or 1.0). Weekly capacity is contractual FTE minus leave FTE.
4. Utilization = total confirmed allocated FTE for employee-week / available FTE capacity. A ratio above 1 is an over-allocation; 0.8 or above is high utilization.
5. Skill proficiency uses a 1–5 scale. EmployeeSkill.expiry_date is derived from last_verified_date plus the Skill.validity_months policy. A profile is eligible only while expiry_date is on or after the fixed reference date.
6. Demand is weekly FTE by project, role and skill. Demand forecast aggregates approved demand into total weekly FTE.
7. Eligible skill coverage requires matching employee role, matching skill, proficiency >= demand minimum and unexpired skill profile. Gap count = max(0, ceil(required_fte) - eligible employee count). This is a simplified people-count proxy, not a full FTE optimization model.
8. Forecast uses a linear-regression baseline. The last eight (or a small-data minimum) weeks form a time-ordered holdout. MAE and RMSE are reported and compared with a last-observation naive baseline. The final forecast model is refit on all observed weeks.
9. Hiring/training recommendations are rules: if training exists for the skill, recommend training; otherwise larger gaps recommend hiring; smaller gaps recommend cross-training or hiring. Recommendations cite their assumption in the output.
10. Four deliberate anomalies are labelled separately: allocation exceeds availability, stale skill treated as current, duplicate demand business key, and overlapping project allocation.
11. AllocationEvent records are append-only synthetic creation events. The prototype does not yet simulate a full multi-state lifecycle or user-authored audit events.
12. CSV exports and SQLite seed database are local prototype persistence. No hosted service, authentication, or access control is provided.
13. Forecasting and recommendation logic is illustrative and must not be used for real staffing decisions without stakeholder review and historical backtesting.
