# Project Data Design Document (PR Project Requirements + EC Incident Topics)

This document supplements `DATABASE_DESIGN.md` and describes the layered data design of the **project dimension**. The project dimension covers two topics: **PR (project requirements)** and **EC (incidents)**.

## 1. Dimension positioning

The project dimension and the organization dimension are two parallel top-level analytical dimensions; a project is **not** subordinate to a department (organization).

```text
Analytical dimensions
├── Organization dimension org
│   ├── employee    Employee
│   ├── team        Team
│   ├── domain      Domain
│   └── department  Department   ← Department Board
└── Project dimension project      ← Project Board (parallel to the organization dimension)
```

- **Department Board**: uses the organization dimension, drilling down by `employee / team / domain / department` to display PR and EC.
- **Project Board**: uses the project dimension, analyzing by `project` independently to display PR and EC.

At the code level (both front end and back end), the two are parallel first-class dimensions: the front-end left navigation lists "Department Board / Project Board" side by side; the back end has separate APIs and separate tables for each, without sharing the `org_type` enum.

## 2. Layered architecture

`project_id` is used as the unique identifier of a project (no surrogate key). Both PR and EC join the project dimension through `project_id`.

```text
Business systems → ODS → DWD → DIM → DWM → ADS
```

| Layer | Table | Description |
|---|---|---|
| ODS | `ods_pm_project` (new) | Project master data landing |
| ODS | `ods_pm_pr` (existing) | PR requirements, already has `project_id` |
| ODS | `ods_itsm_ec` (extended) | EC incidents, `project_id` added |
| DIM | `dim_project` (new) | Project dimension |
| DWD | `dwd_pr_fact` (existing) | Already has `project_id` |
| DWD | `dwd_ec_fact` (extended) | `project_id` added |
| DWM | `dwm_pr_project_1d` (new) | Project x day PR summary |
| DWM | `dwm_ec_project_1d` (new) | Project x day EC summary |
| ADS | `ads_pr_project_kpi` (new) | Project x period PR KPIs |
| ADS | `ads_ec_project_kpi` (new) | Project x period EC KPIs |

> Note: the organization chain is DWD → DWM → DWS → ADS (it needs to roll up across employees). In the project chain, DWM is already at the final analytical grain of "project x day", so no further rollup is needed; therefore no separate DWS project table is defined and DWM aggregates directly into ADS.

## 3. Table design

### 3.1 ods_pm_project (project master data)

Source: project management system

| Column | Type | Description |
|---|---|---|
| project_id | bigint | Project ID (business primary key) |
| project_name | varchar(128) | Project name |
| project_status | varchar(16) | Status (In Progress / Completed / Closed) |
| owner_employee_id | bigint | Project owner ID |
| start_date | date | Start date |
| end_date | date | Planned end date |
| + ETL metadata columns | | |

Load strategy: full daily load.

### 3.2 dim_project (project dimension)

| Column | Type | Description |
|---|---|---|
| project_id | bigint | Project ID (primary key, unique identifier) |
| project_name | varchar(128) | Project name |
| project_status | varchar(16) | Project status |
| owner_employee_id | bigint | Project owner ID |
| start_date | date | Start date |
| end_date | date | Planned end date |

### 3.3 dwd_pr_fact / dwd_ec_fact (existing/extended)

Both detail fact tables contain `project_id` and join directly to `dim_project.project_id`; no new surrogate key is added.

`dwd_ec_fact` adds a `project_id` column on top of the design in `DATABASE_DESIGN.md`.

### 3.4 dwm_pr_project_1d (PR project daily summary)

| Column | Type | Description |
|---|---|---|
| stat_date | date | Statistic date |
| project_id | bigint | Project ID |
| pr_assign_cnt | int | Requirements Assigned |
| pr_complete_cnt | int | Requirements Completed |
| pr_due_cnt | int | Requirements Due |
| pr_on_time_cnt | int | On-time Deliveries |
| pr_rework_cnt | int | Reworked Requirements |
| pr_process_days_sum | int | Total Processing Time (days) |
| pr_work_hours_sum | decimal(12,2) | Total Work Hours |
| Primary key | | (stat_date, project_id) |

### 3.5 dwm_ec_project_1d (EC project daily summary)

| Column | Type | Description |
|---|---|---|
| stat_date | date | Statistic date |
| project_id | bigint | Project ID |
| ec_found_cnt | int | Incidents Found |
| ec_resolved_cnt | int | Incidents Resolved |
| ec_recur_cnt | int | Recurring Incidents |
| ec_severe_cnt | int | Severe Incidents |
| ec_response_minutes_sum | int | Total Response Time (min) |
| ec_resolve_minutes_sum | int | Total Resolution Time (min) |
| Primary key | | (stat_date, project_id) |

### 3.6 ads_pr_project_kpi (PR project period KPIs)

| Column | Type | Description |
|---|---|---|
| period_type | varchar(16) | Period type (week/month/quarter/halfyear/year) |
| period_value | varchar(32) | Period value |
| project_id | bigint | Project ID |
| pr_assign_cnt | int | Requirements Assigned |
| pr_complete_cnt | int | Requirements Completed |
| pr_due_cnt | int | Requirements Due |
| pr_on_time_cnt | int | On-time Deliveries |
| pr_process_days_sum | int | Total Processing Time (days) |
| pr_rework_cnt | int | Reworked Requirements |
| pr_completion_rate | decimal(8,4) | Requirement Completion Rate |
| pr_on_time_rate | decimal(8,4) | On-time Delivery Rate |
| pr_avg_process_days | decimal(8,2) | Avg. Processing Time (days) |
| pr_rework_rate | decimal(8,4) | Rework Rate |
| pr_work_hours_ratio | decimal(8,4) | Requirement Work-Hours Ratio |
| Primary key | | (period_type, period_value, project_id) |

### 3.7 ads_ec_project_kpi (EC project period KPIs)

| Column | Type | Description |
|---|---|---|
| period_type | varchar(16) | Period type |
| period_value | varchar(32) | Period value |
| project_id | bigint | Project ID |
| ec_found_cnt | int | Incidents Found |
| ec_resolved_cnt | int | Incidents Resolved |
| ec_response_minutes_sum | int | Total Response Time (min) |
| ec_resolve_minutes_sum | int | Total Resolution Time (min) |
| ec_recur_cnt | int | Recurring Incidents |
| ec_resolution_rate | decimal(8,4) | Incident Resolution Rate |
| ec_avg_response_minutes | decimal(8,2) | Avg. Response Time (min) |
| ec_avg_resolve_minutes | decimal(8,2) | Avg. Resolution Time (min) |
| ec_recur_rate | decimal(8,4) | Recurrence Rate |
| ec_severe_cnt | int | Severe Incidents |
| Primary key | | (period_type, period_value, project_id) |

## 4. Project-dimension KPIs

### PR (project requirements)

| KPI | Metric definition | Source field |
|---|---|---|
| Requirements Assigned | SUM | pr_assign_cnt |
| Requirements Completed | SUM | pr_complete_cnt |
| Requirement Completion Rate | Completed / Assigned | pr_completion_rate |
| On-time Delivery Rate | On-time / Requirements Due | pr_on_time_rate |
| Avg. Processing Time | Total Processing Time / Completed | pr_avg_process_days |
| Rework Rate | Reworked / Completed | pr_rework_rate |
| Requirement Work-Hours Ratio | Requirement work hours / Effective work hours | `pr_work_hours_ratio` (left null when effective work hours are unavailable) |

### EC (incidents)

| KPI | Metric definition | Source field |
|---|---|---|
| Incidents Found | SUM | ec_found_cnt |
| Incidents Resolved | SUM | ec_resolved_cnt |
| Incident Resolution Rate | Resolved / Found | ec_resolution_rate |
| Avg. Response Time | Total Response Time / Incidents | ec_avg_response_minutes |
| Avg. Resolution Time | Total Resolution Time / Resolved | ec_avg_resolve_minutes |
| Incident Recurrence Rate | Recurring / Resolved | ec_recur_rate |
| Severe Incidents | SUM | ec_severe_cnt |

## 5. Table-creation SQL (MySQL 5.7, utf8mb4)

```sql
-- Project master data (ODS)
CREATE TABLE ods_pm_project (
  project_id        BIGINT        NOT NULL,
  project_name      VARCHAR(128)  NULL,
  project_status    VARCHAR(16)   NULL,
  owner_employee_id BIGINT        NULL,
  start_date        DATE          NULL,
  end_date          DATE          NULL,
  etl_load_time     DATETIME      NOT NULL,
  etl_source        VARCHAR(32)   NOT NULL,
  etl_batch_id      VARCHAR(64)   NULL,
  etl_operation     CHAR(1)       NOT NULL,
  data_date         DATE          NOT NULL,
  PRIMARY KEY (project_id, data_date),
  KEY idx_data_date (data_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='project master data (ODS)';

-- Project dimension (DIM)
CREATE TABLE dim_project (
  project_id        BIGINT        NOT NULL,
  project_name      VARCHAR(128)  NOT NULL,
  project_status    VARCHAR(16)   NULL,
  owner_employee_id BIGINT        NULL,
  start_date        DATE          NULL,
  end_date          DATE          NULL,
  PRIMARY KEY (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='project dimension';

-- PR project daily summary (DWM)
CREATE TABLE dwm_pr_project_1d (
  stat_date           DATE          NOT NULL,
  project_id          BIGINT        NOT NULL,
  pr_assign_cnt       INT           NOT NULL DEFAULT 0,
  pr_complete_cnt     INT           NOT NULL DEFAULT 0,
  pr_due_cnt          INT           NOT NULL DEFAULT 0,
  pr_on_time_cnt      INT           NOT NULL DEFAULT 0,
  pr_rework_cnt       INT           NOT NULL DEFAULT 0,
  pr_process_days_sum INT           NOT NULL DEFAULT 0,
  pr_work_hours_sum   DECIMAL(12,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (stat_date, project_id),
  KEY idx_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='PR project daily summary (DWM)';

-- EC project daily summary (DWM)
CREATE TABLE dwm_ec_project_1d (
  stat_date               DATE   NOT NULL,
  project_id              BIGINT NOT NULL,
  ec_found_cnt            INT    NOT NULL DEFAULT 0,
  ec_resolved_cnt         INT    NOT NULL DEFAULT 0,
  ec_recur_cnt            INT    NOT NULL DEFAULT 0,
  ec_severe_cnt           INT    NOT NULL DEFAULT 0,
  ec_response_minutes_sum INT    NOT NULL DEFAULT 0,
  ec_resolve_minutes_sum  INT    NOT NULL DEFAULT 0,
  PRIMARY KEY (stat_date, project_id),
  KEY idx_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='EC project daily summary (DWM)';

-- PR project period KPIs (ADS)
CREATE TABLE ads_pr_project_kpi (
  period_type         VARCHAR(16)   NOT NULL,
  period_value        VARCHAR(32)   NOT NULL,
  project_id          BIGINT        NOT NULL,
  pr_assign_cnt       INT           NOT NULL DEFAULT 0,
  pr_complete_cnt     INT           NOT NULL DEFAULT 0,
  pr_due_cnt          INT           NOT NULL DEFAULT 0,
  pr_on_time_cnt      INT           NOT NULL DEFAULT 0,
  pr_process_days_sum INT           NOT NULL DEFAULT 0,
  pr_rework_cnt       INT           NOT NULL DEFAULT 0,
  pr_completion_rate  DECIMAL(8,4)  NULL,
  pr_on_time_rate     DECIMAL(8,4)  NULL,
  pr_avg_process_days DECIMAL(8,2)  NULL,
  pr_rework_rate      DECIMAL(8,4)  NULL,
  pr_work_hours_ratio DECIMAL(8,4)  NULL,
  PRIMARY KEY (period_type, period_value, project_id),
  KEY idx_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='PR project period KPIs (ADS)';

-- EC project period KPIs (ADS)
CREATE TABLE ads_ec_project_kpi (
  period_type             VARCHAR(16)   NOT NULL,
  period_value            VARCHAR(32)   NOT NULL,
  project_id              BIGINT        NOT NULL,
  ec_found_cnt            INT           NOT NULL DEFAULT 0,
  ec_resolved_cnt         INT           NOT NULL DEFAULT 0,
  ec_response_minutes_sum INT           NOT NULL DEFAULT 0,
  ec_resolve_minutes_sum  INT           NOT NULL DEFAULT 0,
  ec_recur_cnt            INT           NOT NULL DEFAULT 0,
  ec_resolution_rate      DECIMAL(8,4)  NULL,
  ec_avg_response_minutes DECIMAL(8,2)  NULL,
  ec_avg_resolve_minutes  DECIMAL(8,2)  NULL,
  ec_recur_rate           DECIMAL(8,4)  NULL,
  ec_severe_cnt           INT           NOT NULL DEFAULT 0,
  PRIMARY KEY (period_type, period_value, project_id),
  KEY idx_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='EC project period KPIs (ADS)';
```

## 6. Front-end/back-end API mapping (parallel relationship)

The organization dimension and the project dimension use separate APIs and are never mixed:

| Dimension | API | Key parameters |
|---|---|---|
| Organization dimension | `GET /api/dw/kpi/pr` | `org_type` ∈ employee / team / domain / department |
| Organization dimension | `GET /api/dw/kpi/ec` | `org_type` same as above |
| Organization dimension | `GET /api/dw/board` | `org_type` same as above |
| Project dimension | `GET /api/dw/project/meta` | — |
| Project dimension | `GET /api/dw/project/kpi` | `period_type`, `period_value`, `project_id` |
| Project dimension | `GET /api/dw/project/ec` | `period_type`, `period_value`, `project_id` |
| Project dimension | `GET /api/dw/project/board` | `period_type` |

Front end:

- Department Board: organization dimension dropdown (Team / Domain / Department) + period
- Project Board: project dimension + period, calling the PR and EC project APIs separately

The back-end `routes/dw.py` does not add `project` to `ORG_TYPE_LABELS`; instead it adds separate project routes and a `project` name mapping (`dim_project.project_name`).

## 7. Implementation status

- Tables created: `ods_pm_project`, `dim_project`, `dwm_pr_project_1d`, `ads_pr_project_kpi`, `dwm_ec_project_1d`, `ads_ec_project_kpi` ✅
- `ods_itsm_ec` and `dwd_ec_fact` extended with `project_id` ✅
- Back-end `dw_models.py` has the corresponding new models ✅
- Back-end `routes/dw.py` has added `/api/dw/project/meta`, `/project/kpi`, `/project/ec` and `/project/board` ✅
- ETL supports PR and EC synchronization for the project dimension ✅
- Front-end Project Board is wired to the dedicated project-dimension APIs ✅
