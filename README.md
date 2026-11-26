# idata · KPI Data Analytics Dashboard

A front-end/back-end separated KPI analytics platform with a Vue 3 + ECharts front end, a Flask + SQLAlchemy back end, and a MySQL warehouse. The data is not hardcoded demo data; it is processed from source data through a layered `ODS → DIM → DWD → DWM → DWS → ADS` ETL pipeline, and the APIs only read ADS layer results.

**Tech stack**

| Layer | Choice |
|---|---|
| Front end | Vue 3.5, Vite 6, ECharts 5 (on-demand imports) |
| Back end | Flask 3.0, Flask-SQLAlchemy 3.1, SQLAlchemy 2.0, PyMySQL |
| Database | MySQL 8 (warehouse `5003`, utf8mb4) |
| Cache | Redis (optional, automatically falls back when unavailable) |
| Warehouse | 6 layered models, 23 tables |

## Features

**Department Board** (organization dimension: department / team / domain)

- PR Completion Rate: multi-series trend comparison by organization
- PR On-time Delivery Rate
- EC Resolution Rate
- EC Avg. Response Time (min)

**Project Board** (project dimension, switchable side by side with the organization dimension)

- Completion Rate, On-time Delivery Rate
- EC Resolution Rate, EC Avg. Response Time
- Supports an "All Projects" aggregate view and drill-down into a single project

**Interaction details**

- Time granularity switching: Week / Month / Quarter / Half-year / Year
- Click any data point to open a details panel showing the numerator, denominator and rate, with traceable metric definitions
- Hover over the `?` in the top-right corner of each chart to view the metric formula
- The "Clear Cache" button clears `dw:`-prefixed keys in Redis and then re-fetches data
- Periods automatically filter out future values (e.g. when the current period is 2026-11, 2026-12 is not shown) and trim to the last N periods by granularity (12 periods for week/month, 4 for quarter/half-year/year)
- Loading state, error banner + Retry, empty-data placeholder, narrow-screen adaptation

## Architecture

**Data processing chain**

```
Source systems (simulated HR / PM / ITSM)
  └─► ODS ─► DIM ─► DWD ─► DWM ─► DWS ─► ADS     All land in the MySQL warehouse `5003`
      └────────────── database/etl/runner.py ──────────────┘
```

**Request flow**

```
Browser ─► Vue 3 + ECharts ─► /api (Vite proxy / Nginx reverse proxy) ─► Flask
                                                               ├─► Warehouse ADS tables (dw bind)
                                                               └─► Redis cache (optional)
```

The back end mounts only one bind that actually carries data:

- **`dw` bind**: the warehouse (`DW_DATABASE_URL`, default `5003`), all 23 tables live here, serving the `/api/dw/*` dashboard APIs
- **Default bind**: contains no models and serves only as a Flask-SQLAlchemy placeholder; it points to another database only when `DATABASE_URL` is explicitly configured, otherwise it shares the same source as the warehouse

## Directory structure

```
demo/
├── frontend/                       # Vue 3 + Vite, dev port 5173
│   ├── src/
│   │   ├── App.vue                 # sidebar + top bar + dual-view switching
│   │   ├── api/index.js            # unified request layer (fetch wrapper + error mapping + qs concatenation)
│   │   ├── composables/useDw.js    # data-fetch state, period calculation and trimming, watch-based auto-reload
│   │   ├── components/
│   │   │   ├── DepartmentBoard.vue # Department Board (4 comparison charts + details modal)
│   │   │   ├── ProjectBoard.vue    # Project Board (4 trend charts + details modal)
│   │   │   └── TrendChart.vue      # ECharts wrapper (line/bar, percentage axis, click events)
│   │   ├── main.js
│   │   └── style.css               # global styles and responsive layout
│   ├── vite.config.js              # port 5173 + /api proxy + chunk-splitting strategy
│   └── package.json
│
├── backend/                        # Flask, dev port 8000
│   ├── app.py                      # application factory: dual bind, CORS, error handling, init-db
│   ├── extensions.py               # SQLAlchemy instance (kept separate to avoid circular imports)
│   ├── dw_models.py                # models for the 23 warehouse tables (dw bind)
│   ├── cache.py                    # Redis wrapper, silently falls back on exceptions
│   ├── routes/
│   │   └── dw.py                   # /api/dw/* dashboard APIs
│   ├── requirements.txt
│   └── .env.example
│
└── database/
    ├── etl/                        # layered ETL (direct pymysql, not ORM)
    │   ├── config.py               # connection config and layer execution order
    │   ├── db.py                   # connection factory
    │   ├── source.py               # ODS: simulated HR/PM/ITSM source data (fixed random seed)
    │   ├── sync_dim.py             # DIM: SCD2 dimensions
    │   ├── sync_dwd.py             # DWD: fact table cleaning
    │   ├── sync_dwm.py             # DWM: employee/project daily summaries
    │   ├── sync_dws.py             # DWS: organization daily summaries
    │   ├── sync_ads.py             # ADS: organization/project x period KPIs
    │   ├── runner.py               # CLI entry point and scheduled execution
    │   └── test_etl.py             # end-to-end integration tests (separate test database, dropped after the run)
    ├── DATABASE_DESIGN.md          # layering scheme and table-creation DDL
    └── PROJECT_DATA_DESIGN.md      # supplementary design for the project dimension
```

## Quick start

**Prerequisites**: Python 3.10+, Node.js 18+, MySQL 8 (utf8mb4); Redis is optional.

### 1. Create the database

```sql
CREATE DATABASE `5003` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Configure back-end environment variables

```bash
cd backend
cp .env.example .env        # Windows: Copy-Item .env.example .env
```

Edit `.env` and confirm the warehouse connection string (the default bind needs no configuration; when unset it shares the same source):

```dotenv
DW_DATABASE_URL=mysql+pymysql://root:your_password@127.0.0.1:3306/5003?charset=utf8mb4
```

### 3. Create tables and load data

```bash
# Still in the backend/ directory, install dependencies first
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # PowerShell; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Create tables: create_all applies to both the default and dw databases, 23 warehouse tables in total
flask --app app init-db

# Run the full ETL (return to the repository root to avoid module import issues)
cd ..
python -m database.etl.runner --once
```

The ETL simulates nearly 365 days of HR / requirement / incident data and writes it layer by layer into `5003`; the random seed is fixed (`20251124`), so repeated runs are reproducible.

### 4. Start the back end

```bash
cd backend
python app.py                # http://127.0.0.1:8000
```

### 5. Start the front end

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

During development Vite proxies `/api` to `http://127.0.0.1:8000`; from the browser's perspective this is same-origin, so no extra CORS configuration is needed.

## Environment variables

`backend/.env` (see `backend/.env.example` for the template):

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Default bind (placeholder, no models); when unset, shares the same source as `DW_DATABASE_URL` | Same as `DW_DATABASE_URL` |
| `DW_DATABASE_URL` | Warehouse connection string (`dw` bind) | `mysql+pymysql://root:root@127.0.0.1:3306/5003` |
| `PORT` | Back-end listening port | `8000` |
| `SECRET_KEY` | Flask secret key | `dev-only-secret` |
| `CORS_ORIGINS` | Allowed origins, comma-separated | `*` |
| `FLASK_DEBUG` | Set to `1` to enable debug mode | `0` |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | Cache connection | `127.0.0.1` / `6379` / `0` |
| `DW_CACHE_TTL` | Cache TTL in seconds | `86400` |

The ETL does not use `.env`; it reads environment variables directly (using the values in parentheses when unset): `DW_DB_HOST` (`127.0.0.1`), `DW_DB_USER` (`root`), `DW_DB_PASSWORD` (`root`), `DW_DB_PORT` (`3306`), `DW_DB_NAME` (`5003`), `DW_RUN_TIME` (`02:00`).

`frontend/.env.development` / `.env.production`:

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | API prefix | `/api` |

## API

All responses use the shape `{ "code": 0, "message": "ok", "data": ... }`; a non-zero `code` indicates failure, and HTTP status codes also reflect errors (400 / 404 / 500 / 503).

**Organization dimension (Department Board)**

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check, verifies the business database is reachable |
| GET | `/api/dw/health` | Row counts of all warehouse tables |
| GET | `/api/dw/meta` | Organization dimensions, period enums and dimension list |
| GET | `/api/dw/board` | Organization dashboard, returns merged PR + EC metrics |
| GET | `/api/dw/kpi/pr` | PR requirement KPI details |
| GET | `/api/dw/kpi/ec` | EC incident KPI details |

**Project dimension (Project Board)**

| Method | Path | Description |
|---|---|---|
| GET | `/api/dw/project/meta` | Project list |
| GET | `/api/dw/project/board` | Project PR trend data |
| GET | `/api/dw/project/ec` | Project EC trend data |
| GET | `/api/dw/project/kpi` | Project PR KPI details (supports single-project filtering) |

**Other**

| Method | Path | Description |
|---|---|---|
| POST | `/api/dw/cache/clear` | Clears `dw:`-prefixed cache entries and returns the number removed |

**Query parameters**

- `org_type`: `department` / `team` / `domain` / `employee` (`employee` is not shown in the front-end boards)
- `period_type`: `week` / `month` / `quarter` / `halfyear` / `year`
- `period_value`: e.g. `2026-11`, `2026-Q4`, `2026-H2`, `2026-W46`, `2026`
- `org_id` / `project_id`: filter by dimension primary key

```bash
curl "http://127.0.0.1:8000/api/dw/board?org_type=department&period_type=month"
```

## Metric definitions

| Metric | Formula | Description |
|---|---|---|
| Requirement Completion Rate | Requirements Completed / Requirements Assigned | assigned is aggregated by `assign_date` and completed by `complete_date`, then merged |
| On-time Delivery Rate | On-time Deliveries / Requirements Due | requirements due is taken as requirements completed in the current period (`complete_date` is not null); on-time means `complete_date <= due_date` |
| Avg. Processing Time | Total Processing Days / Requirements Completed | unit: days, `process_days = complete_date - assign_date` |
| Rework Rate | Reworked Requirements / Requirements Completed | source field `rework_flag` |
| Incident Resolution Rate | Incidents Resolved / Incidents Found | found is based on `found_at`, resolved on `resolved_at` |
| Avg. Response Time | Total Response Time / Incidents | unit: min, `first_response_at - found_at` |
| Avg. Resolution Time | Total Resolution Time / Incidents Resolved | unit: min |
| Recurrence Rate | Recurring Incidents / Incidents Resolved | source field `recur_flag` |

The `pr_work_hours_ratio` (work-hours ratio) field is reserved; the ETL currently writes `NULL`.

## Data model

The warehouse has 23 tables; model definitions are in `backend/dw_models.py`:

| Layer | Tables | Description |
|---|---|---|
| ODS | `ods_hr_employee`, `ods_pm_pr`, `ods_itsm_ec`, `ods_pm_project` | Source-system landing, with ETL audit fields (`etl_load_time` / `etl_batch_id` / `etl_operation`) |
| DIM | `dim_employee`, `dim_department`, `dim_team`, `dim_domain`, `dim_project`, `dim_date`, `dim_severity` | Organization/project dimensions use SCD2 (`is_current` + effective/expiry range); `dim_date` is the date dimension |
| DWD | `dwd_pr_fact`, `dwd_ec_fact` | Fact tables with derived columns such as `is_on_time`, `process_days` and `response_minutes` |
| DWM | `dwm_pr_emp_1d`, `dwm_ec_emp_1d`, `dwm_pr_project_1d`, `dwm_ec_project_1d` | Employee / project x daily-grain summaries |
| DWS | `dws_pr_org_1d`, `dws_ec_org_1d` | Organization (department/team/domain/employee) x daily-grain summaries |
| ADS | `ads_pr_kpi`, `ads_ec_kpi`, `ads_pr_project_kpi`, `ads_ec_project_kpi` | Organization/project x period KPIs; APIs query this layer directly |

Table-creation DDL is in `database/DATABASE_DESIGN.md` (layering scheme + 17 core tables) and `database/PROJECT_DATA_DESIGN.md` (project-dimension supplement); the simplest approach is to run `flask --app app init-db` and let the ORM generate all 23 tables (including `dwm_ec_project_1d` and `ads_ec_project_kpi`, which are not yet documented).

### ETL usage

```bash
python -m database.etl.runner --once                # run the full pipeline once (ods→dim→dwd→dwm→dws→ads)
python -m database.etl.runner --once --layer ads    # re-run only one layer
python -m database.etl.runner --schedule            # long-running process, executes daily at 02:00
python -m database.etl.runner --schedule --time 03:30
```

Before each layer runs, it first `DELETE`s the target table and then performs a full load, so it can be run repeatedly; layers are strongly dependent, so after changing an upstream layer you must re-run downstream layers in `ORDER` sequence.

## Caching strategy

- All `/api/dw/*` read endpoints build a Redis key from "endpoint name + all query parameters", prefixed with `dw:`, with a default TTL of 24 hours
- `cache.py` silently swallows all Redis exceptions: if it cannot connect, the request is treated as a cache miss and the endpoint falls back to the source as usual, so it runs fine without Redis installed locally
- Data changes after an ETL re-run, so you need to call `POST /api/dw/cache/clear` or click the front-end "Clear Cache" button

## Testing

`database/etl/test_etl.py` is the end-to-end integration test for the warehouse pipeline. It creates tables in a **separate test database** `dw_etl_test`, runs the whole chain (ODS → DIM → DWD → DWM → DWS → ADS), verifies each layer, and drops the database automatically afterwards; it **never reads or writes the production database `5003`**.

```bash
cd D:/code/codex_start/demo
backend/.venv/Scripts/python.exe database/etl/test_etl.py -v        # show results one by one
backend/.venv/Scripts/python.exe database/etl/test_etl.py --keep    # keep the test database for inspection
```

Prerequisites: MySQL is running and the `DW_DB_*` settings in `database/etl/config.py` are connectable. When MySQL is unavailable, the tests **skip automatically** rather than failing.

| Case | Contract verified |
|---|---|
| 01 | ODS source data volume (18 employees / 20 projects / PR and EC non-empty) |
| 02 | `dim_date` covers three years and includes today |
| 03 | DWD `is_on_time` and `process_days` can be recomputed from raw ODS dates |
| 04 | DWD `response_minutes` and `resolve_minutes` equal the differences of ODS timestamps |
| 05 | DWS department/team/domain summaries equal the sum of employee-level values for each day |
| 06 | ADS completion rate, on-time rate and average processing days can be recomputed from numerators and denominators |
| 07 | ADS covers 5 period types x 4 organization dimensions |
| 08 | Row counts remain unchanged after re-running DIM→ADS (idempotent) |
| 09 | DWS work-hour summaries equal the sum of completed-requirement work hours in DWD |

The test database name can be overridden with `DW_TEST_DB`.

## Build and deployment

```bash
cd frontend
npm run build                # output goes to frontend/dist, split into vue / charts chunks
```

Same-origin deployment with Nginx (front-end static assets + `/api` reverse proxy, avoiding cross-origin issues):

```nginx
server {
    listen 80;
    server_name example.com;

    root /var/www/idata/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

In production, run the back end with a WSGI server, turn off `FLASK_DEBUG`, and tighten `CORS_ORIGINS` to the actual domain:

```bash
pip install waitress
waitress-serve --host 127.0.0.1 --port 8000 app:create_app
```

## Known limitations

- `source.py` is a simulated data source; connecting real systems requires replacing this module's extraction logic
- Read-only APIs, no authentication and no write operations (except clearing the cache)
- `pr_work_hours_ratio` is not yet calculated

## Documentation

- `database/DATABASE_DESIGN.md` — warehouse layering scheme, table structures and DDL
- `database/PROJECT_DATA_DESIGN.md` — project-dimension modeling and API mapping
- `database/EMPLOYEE_DIRECTORY_KPI_MAP.md` — mapping between metrics and organization dimensions
