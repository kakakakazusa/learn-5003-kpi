# idata KPI 看板 · 屏幕录像口播稿（中英对照）
# idata KPI Dashboard — Screen Recording Script (EN / 中文)

**目标时长 / Runtime:** 6:40（口播 5:35 + 约 65 秒操作停顿）；中文版约 6:50
**英文 807 词（145 wpm ≈ 5:35）· 中文 1,428 字（约 250 字/分钟 ≈ 5:45）**
**要凑到 7:00 以上？** 第 4 节有两个可插入片段，各加 35–40 秒
**形式 / Format:** 一镜到底，录屏 + 旁白，无幻灯片

> 录制时读哪一版？英文旁白就用 `DEMO_SCRIPT_EN.md`（纯英文，不被中文打断）。这一份用于准备、审阅、或需要中文字幕/中文讲解的场合。

---

## 0. 观众看完应能回答 / What the viewer must be able to answer

1. 这个应用做什么，给谁用 / What the application does and who it is for
2. 界面怎么组织，两块看板各是什么 / How the interface is organised, what the two boards mean
3. 从点击到出图之间发生了什么 / What happens between a click and a rendered chart
4. 数据怎么从源系统走到屏幕上的数字 / How data travels from source systems to the numbers on screen
5. 后端在每个请求里做什么，依赖挂掉时会怎样 / What the backend does per request, and what happens when a dependency fails

每一段只对应其中一条。**超时就砍第 2 段，永远不要砍第 4 段。**

---

## 1. 录制前检查 / Pre-flight checklist

| # | 检查项 | 怎么做 |
|---|---|---|
| 1 | MySQL 3306 在跑 | `mysql -u root -p -e "SELECT 1"` |
| 2 | 数仓有数据 | `curl http://127.0.0.1:8000/api/dw/health` → 每张表计数 > 0 |
| 3 | 接口 8000 在跑 | `cd backend && python app.py` |
| 4 | 前端 5173 在跑 | `cd frontend && npm run dev` |
| 5 | 演示用的缓存键是冷的 | `curl -X POST http://127.0.0.1:8000/api/dw/cache/clear` |

> ⚠️ **写这份稿子时三个服务全部没启动**（3306 / 8000 / 5173 实测都不通）。开录前务必确认都在监听，否则第 3、4 段没有画面可拍。

数仓是空的就先重建（约 30 秒）：

```bash
python -m database.etl.runner --once
```

**画面设置 / Screen setup**

- 1920×1080，浏览器 100–110%，隐藏书签栏，只留一个标签页
- 终端字号 ≥ 16pt，清掉滚动记录，窗口高度要能放下完整 JSON
- 关闭通知（Windows：专注助手 → 仅闹钟）
- 打开光标高亮，否则点击在压缩后会糊掉
- **说话时鼠标别动**：移动 → 点击 → 再开口

**第 4 段的冷缓存技巧：** 清完缓存后，第一次调用必须用一个界面还没加载过的组合——用 `org_type=team&period_type=quarter`。这样第一次是真 miss、第二次是真 hit，时间差是真的，不是演的。

---

## 2. 镜头表 / Shot list

| 段 | 时间 | 画面 | 英文词数 | 纯口播 | 目的 |
|---|---|---|---|---|---|
| 0 | 0:00–0:30 | 部门看板已渲染，画面静止 | 72 | 0:30 | 立问题 + 预告议程 |
| 1 | 0:30–1:35 | 侧边栏、筛选栏、四张图、公式浮层 | 147 | 1:01 | 界面导览 |
| 2 | 1:35–2:45 | 切维度、切粒度、明细弹窗、项目看板 | 146 | 1:00 | 查询执行 |
| 3 | 2:45–4:20 | 终端跑 ETL · MySQL 看 ADS 表 | 171 | 1:11 | 数据流 |
| 4 | 4:20–6:00 | 终端：health、两次计时 curl、清缓存 | 189 | 1:18 | 后端运维 |
| 5 | 6:00–6:40 | 回到看板，缓慢平移 | 82 | 0:34 | 收束 |

---

## 3. 脚本 / Script

每段先英文、后中文，内容一一对应。`[SCREEN]` 是动作提示，不用念。

---

### 第 0 段 · 开场 / SEGMENT 0 · Cold open — 0:00–0:30

**[SCREEN]** 浏览器全屏停在 Department Board，图表已渲染完。手离开鼠标。

**SAY · EN**

> This is idata — an internal KPI dashboard for engineering delivery. It answers two questions a delivery organisation argues about: are we landing our committed requirements, and how fast do we recover when something breaks.
>
> Behind this screen: a Vue front end, a Flask API, and a MySQL warehouse with six modelling layers.
>
> Next seven minutes: the interface, how a query executes, how data flows, and what the backend does on every request.

**SAY · 中文**

> 这是 idata，一个面向研发交付的内部 KPI 看板。它回答交付组织最常争论的两个问题：承诺的需求有没有落地，出了故障多快能恢复。
>
> 这个界面的背后是一套 Vue 前端、一个 Flask 接口服务，和一个做了六层建模的 MySQL 数仓。
>
> 接下来七分钟，我讲四件事：界面、一次查询是怎么执行的、数据怎么流动、以及后端在每个请求里做了什么。

---

### 第 1 段 · 界面导览 / SEGMENT 1 · Interface tour — 0:30–1:35

**[SCREEN]** 光标移到左侧导航，逐个悬停，然后移到筛选栏。

**SAY · EN**

> Start with the layout. The left rail holds two views, and the distinction matters.
>
> **Department board** is the organisational cut — the same metrics sliced by department, team, or domain. **Project board** is the delivery cut, filtered by project. Same numbers, two different questions.
>
> Both share one filter bar: the org dimension, and the time grain — week through year. Everything below is driven by those two values.
>
> Four charts on one time axis. Top two are requirement metrics: completion rate, and on-time delivery rate. Bottom two are incident metrics: resolution rate, and average first-response time.

**SAY · 中文**

> 先看布局。左侧只有两个视图，这个区分很关键。
>
> **部门看板**是组织维度的切法——同样的指标，按部门、团队、领域拆开看。**项目看板**是交付维度的切法，按项目过滤。同一批数字，回答两个不同的问题。
>
> 两块看板共用一条筛选栏：组织维度，和时间粒度——从周到年。下面所有内容只由这两个值驱动。
>
> 四张图共用一条时间轴。上面两张是需求类指标：完成率、准时交付率。下面两张是故障类指标：解决率、平均首次响应时长。

**[SCREEN]** 悬停第一张图右上角的 `?`，然后沿 x 轴移动，停下。

**SAY · EN**

> Two details. Every card carries a question mark. Hover it and you get the exact formula — numerator, denominator, unit. Nobody has to guess what a number means.
>
> And the axis is bounded: future periods are dropped, twelve periods kept at month grain, four at quarter. Scrolling into empty future months is just noise.

**SAY · 中文**

> 两个细节。每张卡片右上角都有一个问号，悬停就能看到准确公式——分子、分母、单位。没有人需要猜一个数字是什么意思。
>
> 另外，坐标轴是有边界的：未来周期会被丢掉，月粒度保留最近十二期，季度保留四期。滚进一堆还没有数据的未来月份，只是噪音。

---

### 第 2 段 · 查询执行 / SEGMENT 2 · Query execution — 1:35–2:45

**[SCREEN]** Organization dimension 下拉从 "Department" 切到 "Team"，等重绘完成再开口。

**SAY · EN**

> Let's execute a query. Dimension from department to team.
>
> Every chart re-renders. That's a watcher on filter state — no reload. Same colours, finer lines: now you're looking at teams inside departments.
>
> Time grain to quarter. Twelve points collapse to four, and the lines smooth out — same daily aggregates, coarser period.

**SAY · 中文**

> 我们来执行一次查询。维度从部门切到团队。
>
> 所有图表重新渲染。这是筛选状态上的 watcher 触发的，没有刷新页面。颜色不变，线更细了——现在看的是部门内部的团队。
>
> 时间粒度切到季度。十二个点收敛成四个，曲线变平滑——数据还是那批日汇总，只是换了更粗的周期。

**[SCREEN]** 悬停一个数据点，点击打开明细面板。

**SAY · EN**

> Hover a point for the exact value. Click it: not just the percentage, but the count and the denominator behind it. If a number looks wrong in a review, this is where you settle it — one click, no query console.

**SAY · 中文**

> 悬停看具体数值，点击打开明细：不只是百分比，还有背后的计数和分母。评审时如果觉得某个数不对，就在这里当场对清楚——一次点击，不用开查询窗口。

**[SCREEN]** 关掉面板，切到 Project Board，停在 "All Projects"，点开一个明细。

**SAY · EN**

> The project board works the same way. One difference: "all projects" is not an average of percentages. The API returns counts, and the front end recomputes the ratio from summed numerators and denominators — otherwise a three-requirement project would weigh the same as a thirty-requirement one.

**SAY · 中文**

> 项目看板逻辑一样，只有一处差别：屏幕上的 "All Projects" 不是各项目百分比的平均。接口返回的是计数，前端用求和后的分子分母重新算比率——否则一个只有三条需求的项目，会跟一个有三十条需求的项目等权。

**[SCREEN]** 从下拉里选一个具体项目。

**SAY · EN**

> Pick one project and the view narrows to a single series.

**SAY · 中文**

> 选单个项目，视图就收窄成一条线。

---

### 第 3 段 · 数据流 / SEGMENT 3 · Data flow — 2:45–4:20

**[SCREEN]** 切到终端，清屏，慢慢敲命令，回车。

```bash
python -m database.etl.runner --once
```

**SAY · EN**

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

**SAY · 中文**

> 那这些数字从哪来？看板上没有一个值是写死的。接口读的是预聚合表，这些表由这条流水线产出。
>
> 六层。**ODS** 落地源系统的原始抽取——HR、项目管理、故障系统——带批次号、加载时间、操作类型这些审计字段。任何一行都能追回产生它的那次加载。
>
> **DIM** 存一致性维度。组织和项目维度会缓慢变化，所以历史是版本化的，而不是被覆盖。
>
> **DWD** 做清洗，并且把派生标记只算一次：是否准时、用了几天、多少分钟首次响应。
>
> 然后是三层汇总。**DWM** 汇总到员工和项目的日粒度。**DWS** 汇总到组织的日粒度。**ADS** 把所有东西透视成周期级表——每个维度、每个周期一行，计数和比率都有。
>
> 每一层都是先清空目标表再全量写入，所以整个任务是幂等的：可以反复跑，固定随机种子可复现。

**[SCREEN]** 切到 MySQL 客户端。

```sql
SHOW TABLES;
SELECT org_type, period_type, period_value, pr_assign_cnt, pr_complete_cnt, pr_completion_rate
FROM ads_pr_kpi
WHERE org_type = 'department' AND period_type = 'month'
ORDER BY period_value DESC LIMIT 5;
```

**SAY · EN**

> And here's the table the dashboard reads. Counts and rates already computed. The API doesn't calculate a KPI per request — it reads a row. That's why the board stays fast as history grows.

**SAY · 中文**

> 这就是看板真正读的那张表。计数和比率都已经算好了。接口不会在每次请求里算 KPI——它只读一行。这就是历史数据增长、看板依然快的原因。

---

### 第 4 段 · 后端运维 / SEGMENT 4 · Backend operations — 4:20–6:00

**[SCREEN]** 回到终端。

```bash
curl -s http://127.0.0.1:8000/api/dw/health | head -c 400
```

**SAY · EN**

> Now the backend, from outside. Health endpoint: it counts rows in all twenty-three warehouse tables. First thing I check when a chart looks stale — if a layer is empty, the problem is upstream.

**SAY · 中文**

> 现在从外部看后端。健康检查接口：它会数一遍数仓里全部二十三张表的行数。图表看着不对时，我第一个查的就是这里——如果某一层是空的，问题在上游。

**[SCREEN]** 第一次计时调用——这是冷的那次。

```bash
curl -s -o /dev/null -w "time: %{time_total}s\n" \
  "http://127.0.0.1:8000/api/dw/board?org_type=team&period_type=quarter"
```

**SAY · EN**

> Now a real query. Org type, period type — a combination this browser session hasn't loaded, so it's a genuine cold call.
>
> There's the time. The API went to MySQL, assembled the response, and wrote it into Redis on the way out.

**SAY · 中文**

> 现在发一次真实查询。组织类型、周期类型——我特意选了这个浏览器会话还没加载过的组合，所以这是一次真正的冷调用。
>
> 这是耗时。接口去了 MySQL，组装响应，返回的路上把结果写进 Redis。

**[SCREEN]** 原样再跑一次，指着时间值。

**SAY · EN**

> Same command again — and watch the time. That came from cache. The key is the endpoint plus every query parameter, under a `dw:` prefix, twenty-four hours by default.
>
> But after an ETL run the cache still holds the old answer. So invalidation is explicit: this wipes every `dw:` key and reports how many it removed. Reload, and you're on fresh numbers.

**SAY · 中文**

> 同一条命令再跑一次——看这个时间。这次来自缓存。缓存的键是接口加全部查询参数，统一 `dw:` 前缀，默认二十四小时。
>
> 但 ETL 跑过之后，缓存里还是旧答案。所以失效是显式的：这个接口会清掉所有 `dw:` 开头的键，并告诉你清了多少条。刷新页面，拿到的就是新数据。

**[SCREEN]** 第三次调用。

```bash
curl -s -X POST http://127.0.0.1:8000/api/dw/cache/clear
```

**SAY · EN**

> Two properties to finish on. Every response shares one envelope — code, message, data — so the front end has one error path, not twelve; a database failure returns a 503 with a rollback, not a stack trace.
>
> And the cache swallows its own failures: if Redis is down, calls fall through to MySQL. Slower, still correct.

**SAY · 中文**

> 最后两点。所有响应共用一个封套——code、message、data——所以前端只需要处理一条错误路径，而不是十二条；数据库出问题会返回 503 并回滚事务，而不是把堆栈抛到浏览器。
>
> 另外，缓存会吞掉自己的失败：Redis 挂了，请求会直接落回 MySQL。变慢，但依然正确。

---

### 第 5 段 · 收束 / SEGMENT 5 · Synthesis and close — 6:00–6:40

**[SCREEN]** 回到 Department Board。从侧边栏缓慢平移到图表，停手再开口。

**SAY · EN**

> To close. Two views over one warehouse: organisational accountability, and project delivery.
>
> Metrics are computed once upstream and read many times. That separation keeps the interface instant, and means a KPI definition can change in exactly one place.
>
> Contracts are uniform, so the front end stays thin. Caching degrades quietly instead of failing loudly.
>
> The pipeline is idempotent, the warehouse is plain MySQL, and the whole thing runs on a laptop before moving to a scheduled job.
>
> That's idata. Thanks for watching.

**SAY · 中文**

> 最后收一下。一块数仓，两个视图：组织的责任归属，和项目的交付情况。
>
> 指标在上游只算一次，被读取很多次。这个分离让界面保持即时，也意味着一个 KPI 的定义只需要改一个地方。
>
> 契约统一，前端就能保持很薄。缓存失效时安静降级，而不是大声报错。
>
> 流水线是幂等的，数仓就是一个普通的 MySQL 库，整套东西能跑在笔记本上，之后切成定时任务也不需要改应用代码。
>
> 这就是 idata，谢谢观看。

---

## 4. 时长调控 / Pacing control

| 情况 / Situation | 怎么调 / Adjustment |
|---|---|
| 超过 7:15 | 砍掉第 2 段"全部项目不等于百分比平均"那句（−30 秒），明细弹窗保留 |
| 严重超时 | 第 2 段项目看板整段不要（−40 秒），在第 5 段用一句话带过 |
| 要凑到 7:00 以上（推荐） | 停掉 MySQL，请求 `/api/dw/board`，展示 503 封套（+40 秒）。最有说服力的可选素材 |
| 要凑到 7:00 以上（更安静） | 在 `dim_department` 里给同一个部门看两行、`effective_date` 不同、只有一个 `is_current = 1`（+35 秒） |

---

## 5. 翻车应急话术 / If something fails on camera

别沉默调试。把失败讲出来——听起来是从容，不是 bug。

| 故障 | 说这句，然后继续走 |
|---|---|
| 图表一直转圈 | "The board is waiting on the API — let me check the health endpoint, which counts rows in every warehouse table."<br>看板在等接口，我查一下健康检查——它会数每张数仓表的行数。 |
| `/api/dw/health` 返回 503 | "That's the error envelope I mentioned — a 503 with a rollback, not a stack trace."<br>这就是我说的那个错误封套——503 加回滚，不是堆栈。 |
| 图表空白 | "Empty rather than wrong — no data for this combination, and the UI says so instead of drawing a flat line at zero."<br>是空，不是错——这个组合没数据，界面如实说，而不是画一条零线。 |
| ETL 中途失败 | "Layers run in dependency order, so a failure here stops the chain rather than corrupting downstream tables. Re-running is safe."<br>分层按依赖顺序跑，这里失败会中断整条链，不会污染下游表。重跑是安全的。 |
| Redis 连接被拒 | "Cache is optional by design — the call falls through to MySQL. Slower, still correct."<br>缓存本来就是可选的，请求会落回 MySQL。变慢，依然正确。 |

---

## 6. 界面标签 / UI labels

界面已改为英文。光标停在元素上时按屏幕原文念，中文旁白里保留原来的中文叫法。

| 屏幕原文（英文） | 英文旁白 | 中文旁白 |
|---|---|---|
| Department Board | the Department Board | 部门看板 |
| Project Board | the Project Board | 项目看板 |
| Organization dimension | the organization dimension | 组织维度 |
| Period | the period | 时间粒度 |
| Clear Cache | Clear Cache | 刷新缓存 |
| All Projects | All Projects | 全部项目 |
| PR Completion Rate / Requirement Completion Rate | completion rate | 需求完成率 |
| PR On-time Delivery Rate / On-time Delivery Rate | on-time delivery rate | 准时交付率 |
| EC Resolution Rate | incident resolution rate | 故障解决率 |
| EC Avg. Response Time | average response time | 平均响应时长 |
| Metric Details | the detail panel | 指标明细 |

---

## 7. 可选书面摘要 / Optional written abstract

如果还要交一段书面说明，直接用下面的版本（英文 ~110 词，中文 ~180 字）。

**EN**

> **idata — KPI Analytics Dashboard.** idata is a full-stack delivery-analytics platform that reports two families of KPIs — requirement delivery and incident response — across two independent dimensions: organisational structure (department, team, domain) and project. A Vue 3 and ECharts front end consumes a Flask REST API; the API reads only pre-aggregated ADS tables from a MySQL warehouse modelled in six layers, from raw ODS extracts through conformed dimensions, cleaned facts, and daily rollups at employee, project and organisation grain. Because KPIs are computed once upstream rather than per request, the dashboard stays responsive as history grows, and metric definitions live in a single place. Redis caching is optional and degrades silently, so the system runs correctly with or without it.

**中文**

> **idata — KPI 分析看板。** idata 是一个全栈交付分析平台，围绕需求交付与故障响应两类 KPI，在两个相互独立的维度上呈现：组织结构（部门、团队、领域）与项目。Vue 3 与 ECharts 前端消费 Flask REST 接口；接口只读取 MySQL 数仓中预聚合的 ADS 表，该数仓按六层建模，从 ODS 原始抽取、一致性维度、清洗后的事实表，一直到员工、项目、组织三个粒度的日汇总。由于 KPI 在上游一次计算而非每次请求计算，看板在历史数据增长时依然响应迅速，指标定义也只存在于一处。Redis 缓存为可选组件并支持静默降级，因此有缓存或无缓存系统都能正确运行。

---

## 8. 命令卡 / Command card

```bash
# 1. 重建数仓（幂等，约 30 秒）
python -m database.etl.runner --once

# 2. 接口
cd backend && python app.py

# 3. 前端
cd frontend && npm run dev

# 4. 开录前检查
curl -s http://127.0.0.1:8000/api/dw/health | head -c 300
curl -s -X POST http://127.0.0.1:8000/api/dw/cache/clear
```

```bash
# 第 4 段：先冷后热
curl -s -o /dev/null -w "time: %{time_total}s\n" \
  "http://127.0.0.1:8000/api/dw/board?org_type=team&period_type=quarter"
```
