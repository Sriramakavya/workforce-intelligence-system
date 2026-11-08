# Data dictionary

All records are synthetic. Dates use ISO `YYYY-MM-DD`; periods use `2026W01`–`2026W52`; FTE is a fraction of one full-time equivalent. Required means non-null in generated baseline data. IDs are immutable and unique within their entity. Parent IDs must exist in the referenced parent table.

| Entity / field | Type | Required | Allowed values / units | Unique | Validation |
|---|---|---:|---|---:|---|
| Employee.employee_id | string | Yes | `EMP-000001` | Yes | Immutable primary key |
| Employee.employee_name | string | Yes | Synthetic display name | No | Non-empty |
| Employee.role_id | string | Yes | Role ID | No | FK to Role |
| Employee.fte | decimal | Yes | 0.5, 0.75, 1.0 FTE | No | 0 < FTE <= 1 |
| Employee.hire_date | date | Yes | ISO date | No | Valid date |
| Employee.employment_status | enum | Yes | Active, OnLeave, Exited | No | Lifecycle enum; baseline Active |
| Employee.location | string | Yes | Hyderabad, Bengaluru, Chennai, Pune | No | Non-empty |
| Role.role_id | string | Yes | ROLE-0001 etc. | Yes | Primary key |
| Role.role_name | string | Yes | Role taxonomy | Yes | Non-empty |
| Role.department | string | Yes | Engineering, Data, Operations, Business | No | Controlled taxonomy |
| Role.active | boolean | Yes | true/false | No | Boolean |
| Skill.skill_id | string | Yes | `SKL-000001` | Yes | Primary key |
| Skill.skill_name | string | Yes | Skill taxonomy | Yes | Non-empty |
| Skill.category | enum | Yes | Technical, Data, Cloud, Soft Skill | No | Controlled taxonomy |
| Skill.validity_months | integer | Yes | 12, 18, 24, 36 months | No | Positive integer; drives skill expiry |
| EmployeeSkill.employee_skill_id | string | Yes | ES-000001 | Yes | Primary key |
| EmployeeSkill.employee_id | string | Yes | Employee ID | No | FK to Employee |
| EmployeeSkill.skill_id | string | Yes | Skill ID | No | FK to Skill |
| EmployeeSkill.proficiency | integer | Yes | 1–5 scale | No | Inclusive range 1..5 |
| EmployeeSkill.last_verified_date | date | Yes | ISO date | No | Valid date; source date for expiry calculation |
| EmployeeSkill.expiry_date | date | Yes | ISO date | No | Derived as last_verified_date + Skill.validity_months; valid date |
| EmployeeSkill.status | enum | Yes | Verified, Pending, Expired | No | Controlled lifecycle value |
| Project.project_id | string | Yes | `PRJ-2026-000001` | Yes | Primary key |
| Project.project_name | string | Yes | Synthetic project name | No | Non-empty |
| Project.start_date / end_date | date | Yes | ISO dates | No | start <= end |
| Project.project_status | enum | Yes | Planned, Active, OnHold, Completed | No | Controlled lifecycle; baseline Active |
| Project.priority | enum | Yes | Low, Medium, High | No | Controlled enum |
| DemandPlan.demand_id | string | Yes | `DEM-<project-id>-2026W01` | Yes | Primary key; not the business-combination key |
| DemandPlan.project_id / role_id / skill_id | string | Yes | Parent IDs | No | FKs to Project, Role, Skill |
| DemandPlan.period | string | Yes | 2026W01–2026W52 | No | ISO week convention |
| DemandPlan.required_fte | decimal | Yes | FTE | No | >= 0 |
| DemandPlan.minimum_proficiency | integer | Yes | 1–5 | No | Inclusive range 1..5 |
| DemandPlan.status | enum | Yes | Draft, Approved, Cancelled | No | Controlled lifecycle; baseline Approved |
| Allocation.allocation_id | string | Yes | `ALLOC-2026-000001` | Yes | Primary key |
| Allocation.employee_id / project_id | string | Yes | Parent IDs | No | FKs to Employee and Project |
| Allocation.period | string | Yes | 2026W01–2026W52 | No | Week key |
| Allocation.allocated_fte | decimal | Yes | FTE | No | >= 0; can intentionally exceed capacity for labelled test |
| Allocation.allocation_status | enum | Yes | Proposed, Confirmed, Cancelled | No | Controlled lifecycle; baseline Confirmed |
| Availability.availability_id | string | Yes | AV-000001 | Yes | Primary key |
| Availability.employee_id | string | Yes | Employee ID | No | FK to Employee |
| Availability.period | string | Yes | 2026W01–2026W52 | No | Week key; employee-period unique |
| Availability.fte_capacity / leave_fte | decimal | Yes | FTE | No | Non-negative; capacity = contractual FTE - leave |
| Training.training_id | string | Yes | TRN-000001 | Yes | Primary key |
| Training.skill_id | string | Yes | Skill ID | No | FK to Skill |
| Training.training_name | string | Yes | Text | No | Non-empty |
| Training.duration_weeks | integer | Yes | Weeks | No | > 0 |
| Training.cost_usd | integer | Yes | USD | No | >= 0; synthetic estimate |
| Training.status | enum | Yes | Available, Planned, Completed | No | Controlled lifecycle; baseline Available |
| GapAnalysis.gap_id | string | Yes | GAP-000001 | Yes | Primary key |
| GapAnalysis.demand_id / project_id / role_id / skill_id | string | Yes | Parent IDs | No | FKs to demand, project, role, skill |
| GapAnalysis.required_fte | decimal | Yes | FTE | No | Derived from DemandPlan |
| GapAnalysis.available_employee_count | integer | Yes | Employees | No | Derived from eligible current skill profiles |
| GapAnalysis.gap_count | integer | Yes | People | No | max(0, ceil(required_fte) - eligible employee count) |
| GapAnalysis.gap_status | enum | Yes | Gap, Covered | No | Derived from gap_count |
| AllocationEvent.event_id | string | Yes | EVT-000001 | Yes | Primary key; append-only event |
| AllocationEvent.allocation_id | string | Yes | Allocation ID | No | FK to Allocation |
| AllocationEvent.event_type | enum | Yes | CREATED, STATUS_CHANGED | No | Event type |
| AllocationEvent.event_date | date | Yes | ISO date | No | Valid date |
| AllocationEvent.previous_status / new_status | string | Yes | Status values; previous may be empty on creation | No | Lifecycle transition context |
| AllocationEvent.event_note | string | Yes | Text | No | Audit explanation |

## Bridge tables and cardinality

- Employee 1:N EmployeeSkill and Skill 1:N EmployeeSkill form Employee N:M Skill.
- Project 1:N DemandPlan; Role 1:N DemandPlan; Skill 1:N DemandPlan.
- Employee 1:N Allocation and Project 1:N Allocation.
- Employee 1:N Availability; Skill 1:N Training.
- DemandPlan 1:1 GapAnalysis in the baseline output (a gap row per demand row).
- Allocation 1:N AllocationEvent. Events preserve change history; current allocation rows are not overwritten to represent historical transitions.

## Data quality notes

The four required anomaly cases are deliberate and labelled in `data/ground_truth/ground_truth.csv`. The demand anomaly repeats a business key while retaining unique immutable `demand_id` values. This distinction allows primary-key integrity and anomaly detection to be tested independently. Ground-truth labels are never joined into analytics features.
