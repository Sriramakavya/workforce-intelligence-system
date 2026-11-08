# Database schema and relationships

The generator exports CSV tables and the pipeline loads the same records into `outputs/workforce_intelligence.sqlite`.

- Role 1:N Employee.
- Employee N:M Skill through EmployeeSkill (bridge table; one employee-skill pair per row).
- Project 1:N DemandPlan; Role 1:N DemandPlan; Skill 1:N DemandPlan.
- Employee 1:N Allocation; Project 1:N Allocation.
- Employee 1:N Availability; Skill 1:N Training.
- DemandPlan 1:1 GapAnalysis in this generated snapshot.
- Allocation 1:N AllocationEvent, preserving append-only event history.

Relationships are optional on the many side: an employee may have zero or many skill profiles, allocations, or availability periods; a skill may have zero or many employee profiles, demand rows, or training options; a project may have zero or many demand/allocation rows. Each generated EmployeeSkill, DemandPlan, Allocation, Availability, Training, and AllocationEvent row must reference its parent. Training is an optional planning option for a skill gap; an employee training-enrollment entity is outside this prototype.

Effective dates are represented by Employee.hire_date, EmployeeSkill.last_verified_date/expiry_date, Project.start_date/end_date, and weekly period fields on DemandPlan, Allocation, and Availability. Training duration is measured in weeks.

Every entity has a primary key. All foreign keys are validated before the pipeline completes. The SQLite export creates indexes on `(employee_id, period)` for Allocation and `(project_id, period)` for DemandPlan. CSV remains the portable source export. Ground-truth labels are kept in a separate folder and are not inserted into the feature tables.

The CSV/SQLite prototype does not implement multi-user transactional writes, access control, or a production event broker. Those are deployment extensions, not claimed capabilities.
