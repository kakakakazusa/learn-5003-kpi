# Employee Directory KPI Map

Employee KPIs are measured in two areas: **PR (project requirements)** and **EC (incidents)**.

## 1. PR (project requirements)

Measures the efficiency and quality with which employees take on and complete project requirements.

| Metric | Definition | Formula | Target direction |
|---|---|---|---|
| Requirements Assigned | Number of project requirements assigned within the period | COUNT(pr_id) | Higher is better |
| Requirements Completed | Number of requirements completed within the period | COUNT(pr_done) | Higher is better |
| Requirement Completion Rate | Ratio of completed requirements to assigned requirements | Completed / Assigned x 100% | ≥100% |
| On-time Delivery Rate | Share of requirements delivered by the planned milestone | On-time Deliveries / Requirements Due x 100% | Higher is better |
| Avg. Processing Time | Average time from assignment to completion for a requirement | SUM(duration) / Completed | Lower is better |
| Rework Rate | Share of delivered requirements that need rework | Reworked / Delivered x 100% | Lower is better |
| Requirement Work-Hours Ratio | Share of effective work hours spent on project requirements | Requirement work hours / Effective work hours x 100% | Set by position |

## 2. EC (incidents)

Measures employees' response speed and resolution quality when handling incidents.

| Metric | Definition | Formula | Target direction |
|---|---|---|---|
| Incidents Found | Number of incidents found within the period | COUNT(ec_id) | Reference value |
| Incidents Resolved | Number of incidents resolved within the period | COUNT(ec_resolved) | Higher is better |
| Incident Resolution Rate | Ratio of resolved incidents to found incidents | Resolved / Found x 100% | ≥100% |
| Avg. Response Time | Average time from incident occurrence to first response | SUM(response time) / Incidents | Lower is better |
| Avg. Resolution Time | Average time from incident discovery to resolution | SUM(resolution time) / Resolved | Lower is better |
| Incident Recurrence Rate | Share of resolved incidents that recur | Recurring / Resolved x 100% | Lower is better |
| Severe Incidents | Number of P0/P1 incidents within the period | COUNT(severe incidents) | Lower is better |

## 3. Status rules

| Status | Rule |
|---|---|
| Achieved | Achievement rate ≥100% |
| Near target | Achievement rate ≥90% and <100% |
| Needs improvement | Achievement rate <90% |

For "lower is better" metrics (processing time, rework rate, recurrence rate, severe incidents), use the inverse rule: target value / actual value x 100%.

## 4. Analytical dimensions

- Organization: Team, Domain, Department, Employee
- Time: Week, Month, Quarter, Half-year, Year
- Comparison: actual vs. target, current period vs. previous period, employee vs. team average

## 5. Data fields

PR fields: pr_id, pr_name, employee_id, assign_date, due_date, complete_date, status, rework_flag, work_hours

EC fields: ec_id, ec_title, employee_id, severity, found_at, first_response_at, resolved_at, status, recur_flag
