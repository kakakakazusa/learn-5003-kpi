# idata KPI Dashboard — Screen Recording Script (English)

**Target runtime:** 6:40 (5:35 speech + ~65 s of on-screen actions)
**Speaking pace:** ~145 wpm · **Spoken words:** 807
**Need 7:00+?** Add one optional insert from §4 — both are scripted there.
**Deliverable:** one continuous take, screen + voice-over, no slides

---

## 0. What the viewer must be able to answer afterwards

1. What the application does and who it is for
2. How the interface is organised, and what the two boards mean
3. What happens between a click and a rendered chart
4. How data travels from source systems to the numbers on screen
5. What the backend does on every request — and what happens when a dependency fails

Each segment maps to exactly one of those. If you are running long, cut from Segment 2, never from Segment 4.

---

## 1. Pre-flight checklist

Run this **before** you start recording. Nothing kills a demo faster than a spinner on camera.

| # | Check | How |
|---|---|---|
| 1 | MySQL is up on 3306 | `mysql -u root -p -e "SELECT 1"` |
| 2 | Warehouse is populated | `curl http://127.0.0.1:8000/api/dw/health` → every count > 0 |
| 3 | API is up on 8000 | `cd backend && python app.py` |
| 4 | UI is up on 5173 | `cd frontend && npm run dev` |
| 5 | Cache cleared for the demo call | `curl -X POST http://127.0.0.1:8000/api/dw/cache/clear` |

> **The services were all down when this script was written.** Confirm 3306 / 8000 / 5173 are listening right before you record, otherwise Segments 3 and 4 have nothing to show.

If the warehouse is empty, rebuild it first (~30 s):

```bash
python -m database.etl.runner --once
```

**Screen setup**

- 1920×1080, browser at 100–110 % zoom, bookmarks bar hidden, one tab only
- Terminal: font ≥ 16 pt, scrollback cleared, window tall enough for a full JSON response
- Notifications off (Windows: Focus assist → Alarms only)
- Cursor highlight on, so clicks survive video compression
- Keep the mouse still while speaking — move, click, then talk

**Cold-cache trick for Segment 4:** after clearing the cache, the first call must use a filter combination the UI has not loaded yet — use `org_type=team&period_type=quarter`. Your first curl is then a genuine miss and the second a genuine hit, so the timing difference is real rather than staged.

---

## 2. Shot list

| Segment | Time | On screen | Words | Speaking time | Purpose |
|---|---|---|---|---|---|
| 0 | 0:00–0:30 | Dashboard, department board loaded | 72 | 0:30 | Frame the problem and the agenda |
| 1 | 0:30–1:35 | Sidebar, filter bar, four charts, formula tooltip | 147 | 1:01 | Interface tour |
| 2 | 1:35–2:45 | Dimension switch, grain switch, detail panel, project board | 146 | 1:00 | Query execution |
| 3 | 2:45–4:20 | Terminal: ETL run · MySQL: ADS table | 171 | 1:11 | Data flow |
| 4 | 4:20–6:00 | Terminal: health, timed curl ×2, cache clear | 189 | 1:18 | Backend operations |
| 5 | 6:00–6:40 | Back to dashboard, slow pan | 82 | 0:34 | Synthesis and close |

---

## 3. Script

Read the **SAY** blocks as written — they are timed to the word count. **[SCREEN]** notes are actions, not narration.

---

### SEGMENT 0 · Cold open — 0:00–0:30

**[SCREEN]** Browser full screen on the department board, charts already rendered. Don't touch the mouse.

**SAY**

> This is idata — an internal KPI dashboard for engineering delivery. It answers two questions a delivery organisation argues about: are we landing our committed requirements, and how fast do we recover when something breaks.
>
> Behind this screen: a Vue front end, a Flask API, and a MySQL warehouse with six modelling layers.
>
> Next seven minutes: the interface, how a query executes, how data flows, and what the backend does on every request.

---

### SEGMENT 1 · Interface tour — 0:30–1:35

**[SCREEN]** Cursor to the left rail, hover each nav item, then move to the filter bar.

**SAY**

> Start with the layout. The left rail holds two views, and the distinction matters.
>
> **Department board** is the organisational cut — the same metrics sliced by department, team, or domain. **Project board** is the delivery cut, filtered by project. Same numbers, two different questions.
>
> Both share one filter bar: the org dimension, and the time grain — week through year. Everything below is driven by those two values.
>
> Four charts on one time axis. Top two are requirement metrics: completion rate, and on-time delivery rate. Bottom two are incident metrics: resolution rate, and average first-response time.

**[SCREEN]** Hover the `?` on the first chart, then trace the x-axis and stop.

**SAY**

> Two details. Every card carries a question mark. Hover it and you get the exact formula — numerator, denominator, unit. Nobody has to guess what a number means.
>
> And the axis is bounded: future periods are dropped, twelve periods kept at month grain, four at quarter. Scrolling into empty future months is just noise.

---

### SEGMENT 2 · Query execution — 1:35–2:45

**[SCREEN]** Switch the dimension dropdown from department to team. Pause for the re-render.

**SAY**

> Let's execute a query. Dimension from department to team.
>
> Every chart re-renders. That's a watcher on filter state — no reload. Same colours, finer lines: now you're looking at teams inside departments.
>
> Time grain to quarter. Twelve points collapse to four, and the lines smooth out — same daily aggregates, coarser period.

**[SCREEN]** Hover a point, click it to open the detail panel.

**SAY**

> Hover a point for the exact value. Click it: not just the percentage, but the count and the denominator behind it. If a number looks wrong in a review, this is where you settle it — one click, no query console.

**[SCREEN]** Close the panel. Switch to the Project Board, leave it on "All Projects", open a detail panel there.

**SAY**

> The project board works the same way. One difference: "all projects" is not an average of percentages. The API returns counts, and the front end recomputes the ratio from summed numerators and denominators — otherwise a three-requirement project would weigh the same as a thirty-requirement one.

**[SCREEN]** Pick one project from the dropdown.

**SAY**

> Pick one project and the view narrows to a single series.

---

### SEGMENT 3 · Data flow — 2:45–4:20

**[SCREEN]** Terminal. Clear the screen, type the command slowly, run it.

```bash
python -m database.etl.runner --once
```

**SAY**

> So where do those numbers come from? Nothing is hard-coded. The API reads pre-aggregated tables, built by this pipeline.
>
> Six layers. **ODS** lands raw extracts — HR, project management, the incident system — with audit columns for batch, load time, and operation. Any row traces back to the load that produced it.
>
> **DIM** holds conformed dimensions. Organisation and project dimensions change slowly, so history is versioned, not overwritten.
>
> **DWD** is where cleaning happens, and where derived flags are computed once: on time or not, days taken, minutes to first response.
>
> Then three rollups. **DWM** to employee and project per day. **DWS** to organisation per day. **ADS** pivots it all into period-level tables — one row per dimension, per period, carrying counts and rates.
>
> Every layer truncates and reloads, so the job is idempotent: safe to re-run, reproducible from a fixed seed.

**[SCREEN]** Switch to the MySQL client.

```sql
SHOW TABLES;
SELECT org_type, period_type, period_value, pr_assign_cnt, pr_complete_cnt, pr_completion_rate
FROM ads_pr_kpi
WHERE org_type = 'department' AND period_type = 'month'
ORDER BY period_value DESC LIMIT 5;
```

**SAY**

> And here's the table the dashboard reads. Counts and rates already computed. The API doesn't calculate a KPI per request — it reads a row. That's why the board stays fast as history grows.

---

### SEGMENT 4 · Backend operations — 4:20–6:00

**[SCREEN]** Back to the terminal.

```bash
curl -s http://127.0.0.1:8000/api/dw/health | head -c 400
```

**SAY**

> Now the backend, from outside. Health endpoint: it counts rows in all twenty-three warehouse tables. First thing I check when a chart looks stale — if a layer is empty, the problem is upstream.

**[SCREEN]** First timed call — the cold one.

```bash
curl -s -o /dev/null -w "time: %{time_total}s\n" \
  "http://127.0.0.1:8000/api/dw/board?org_type=team&period_type=quarter"
```

**SAY**

> Now a real query. Org type, period type — a combination this browser session hasn't loaded, so it's a genuine cold call.
>
> There's the time. The API went to MySQL, assembled the response, and wrote it into Redis on the way out.

**[SCREEN]** Run the identical command again. Point at the time value.

**SAY**

> Same command again — and watch the time. That came from cache. The key is the endpoint plus every query parameter, under a `dw:` prefix, twenty-four hours by default.
>
> But after an ETL run the cache still holds the old answer. So invalidation is explicit: this wipes every `dw:` key and reports how many it removed. Reload, and you're on fresh numbers.

**[SCREEN]** Third call.

```bash
curl -s -X POST http://127.0.0.1:8000/api/dw/cache/clear
```

**SAY**

> Two properties to finish on. Every response shares one envelope — code, message, data — so the front end has one error path, not twelve; a database failure returns a 503 with a rollback, not a stack trace.
>
> And the cache swallows its own failures: if Redis is down, calls fall through to MySQL. Slower, still correct.

---

### SEGMENT 5 · Synthesis and close — 6:00–6:40

**[SCREEN]** Back to the department board. Pan slowly from sidebar to charts. Stop moving before you speak.

**SAY**

> To close. Two views over one warehouse: organisational accountability, and project delivery.
>
> Metrics are computed once upstream and read many times. That separation keeps the interface instant, and means a KPI definition can change in exactly one place.
>
> Contracts are uniform, so the front end stays thin. Caching degrades quietly instead of failing loudly.
>
> The pipeline is idempotent, the warehouse is plain MySQL, and the whole thing runs on a laptop before moving to a scheduled job.
>
> That's idata. Thanks for watching.

---

## 4. Pacing control

| Situation | Adjustment |
|---|---|
| Overrunning past 7:15 | Cut the "all projects" weighting explanation in Segment 2 (−30 s). Keep the detail panel. |
| Overrunning badly | Drop the project-board half of Segment 2 entirely (−40 s) and cover it in one sentence during Segment 5. |
| Need 7:00+ (recommended) | Stop MySQL, hit `/api/dw/board`, show the 503 envelope (+40 s). Strongest optional material — it proves the error contract. |
| Need 7:00+, quieter option | Show two rows for one department in `dim_department` with different `effective_date`, only one with `is_current = 1` (+35 s). |

---

## 5. If something fails on camera

Never debug silently. Narrate the failure — it reads as composure, not as a bug.

| Failure | Say this, then move on |
|---|---|
| Chart stuck loading | "The board is waiting on the API — let me check the health endpoint, which counts rows in every warehouse table." |
| `/api/dw/health` returns 503 | "That's the error envelope I mentioned — a 503 with a rollback, not a stack trace. The warehouse is unreachable, so everything downstream correctly refuses to serve." |
| Empty charts | "Empty rather than wrong — no data for this combination, and the UI says so instead of drawing a flat line at zero." |
| ETL fails mid-run | "Layers run in dependency order, so a failure here stops the chain rather than corrupting downstream tables. Re-running is safe — every layer truncates and reloads." |
| Redis connection refused | "Cache is optional by design — the call falls through to MySQL. Slower, still correct." |

---

## 6. UI labels

The interface is in English. Use these exact labels when you refer to an on-screen element.

| On screen | In narration |
|---|---|
| Department Board | the Department Board |
| Project Board | the Project Board |
| Organization dimension | the organization dimension |
| Period | the period |
| Clear Cache | Clear Cache |
| All Projects | All Projects |
| PR Completion Rate / Requirement Completion Rate | completion rate |
| PR On-time Delivery Rate / On-time Delivery Rate | on-time delivery rate |
| EC Resolution Rate | incident resolution rate |
| EC Avg. Response Time | average response time |
| Metric Details | the detail panel |

---

## 7. Optional written abstract

If the submission also needs a short written summary, use this verbatim (~110 words).

> **idata — KPI Analytics Dashboard.** idata is a full-stack delivery-analytics platform that reports two families of KPIs — requirement delivery and incident response — across two independent dimensions: organisational structure (department, team, domain) and project. A Vue 3 and ECharts front end consumes a Flask REST API; the API reads only pre-aggregated ADS tables from a MySQL warehouse modelled in six layers, from raw ODS extracts through conformed dimensions, cleaned facts, and daily rollups at employee, project and organisation grain. Because KPIs are computed once upstream rather than per request, the dashboard stays responsive as history grows, and metric definitions live in a single place. Redis caching is optional and degrades silently, so the system runs correctly with or without it.

---

## 8. Command card

```bash
# 1. rebuild the warehouse (idempotent, ~30 s)
python -m database.etl.runner --once

# 2. API
cd backend && python app.py

# 3. UI
cd frontend && npm run dev

# 4. pre-recording checks
curl -s http://127.0.0.1:8000/api/dw/health | head -c 300
curl -s -X POST http://127.0.0.1:8000/api/dw/cache/clear
```

```bash
# Segment 4 — cold call, then warm call
curl -s -o /dev/null -w "time: %{time_total}s\n" \
  "http://127.0.0.1:8000/api/dw/board?org_type=team&period_type=quarter"
```
