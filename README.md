# idata · KPI 数据分析看板

Vue 3 + ECharts 前端、Flask + SQLAlchemy 后端、MySQL 数仓的前后端分离 KPI 分析平台。数据不是写死的演示数据，而是通过一套 `ODS → DIM → DWD → DWM → DWS → ADS` 分层 ETL 从源数据加工而来，接口只读 ADS 层结果。

**技术栈**

| 层 | 选型 |
|---|---|
| 前端 | Vue 3.5、Vite 6、ECharts 5（按需引入） |
| 后端 | Flask 3.0、Flask-SQLAlchemy 3.1、SQLAlchemy 2.0、PyMySQL |
| 数据库 | MySQL 8（数仓库 `5003`，utf8mb4） |
| 缓存 | Redis（可选，不可用自动降级） |
| 数仓 | 6 层分层建模，23 张表 |

## 功能

**部门看板**（组织维度：部门 / 团队 / 领域）

- PR 需求完成率：各组织多序列趋势对比
- PR 准时交付率
- EC 故障解决率
- EC 平均响应时长（分钟）

**项目看板**（项目维度，可与组织维度并列切换）

- 需求完成率、准时交付率
- EC 故障解决率、EC 平均响应时长
- 支持"全部项目"聚合视图与单项目下钻

**交互细节**

- 时间粒度切换：周 / 月 / 季度 / 半年 / 年
- 点击任意数据点弹出明细面板，显示分子、分母与比率，口径可追溯
- 每个图表右上角 `?` 悬浮显示指标公式
- "刷新缓存"按钮清空 Redis 中 `dw:` 前缀的缓存后重新取数
- 周期自动过滤未来值（如当前 2026-11 不展示 2026-12），并按粒度截断最近 N 期（周/月 12 期，季/半年/年 4 期）
- 加载态、错误横幅 + 重试、空数据占位、窄屏适配

## 架构

**数据加工链**

```
源系统（模拟 HR / PM / ITSM）
  └─► ODS ─► DIM ─► DWD ─► DWM ─► DWS ─► ADS     全部落在 MySQL 数仓 `5003`
      └────────────── database/etl/runner.py ──────────────┘
```

**请求链路**

```
浏览器 ─► Vue 3 + ECharts ─► /api（Vite 代理 / Nginx 反代）─► Flask
                                                               ├─► 数仓 ADS 表（dw bind）
                                                               └─► Redis 缓存（可选）
```

后端只挂载一个实际承载数据的 bind：

- **`dw` bind**：数仓库（`DW_DATABASE_URL`，默认 `5003`），23 张表全部在此，服务 `/api/dw/*` 看板接口
- **默认 bind**：不含任何模型，仅作 Flask-SQLAlchemy 的占位；显式配置 `DATABASE_URL` 时才指向其他库，否则与数仓库同源

## 目录结构

```
demo/
├── frontend/                       # Vue 3 + Vite，开发端口 5173
│   ├── src/
│   │   ├── App.vue                 # 侧边栏 + 顶栏 + 双视图切换
│   │   ├── api/index.js            # 统一请求层（fetch 封装 + 错误映射 + qs 拼接）
│   │   ├── composables/useDw.js    # 取数状态、周期计算与截断、watch 自动重载
│   │   ├── components/
│   │   │   ├── DepartmentBoard.vue # 部门看板（4 张对比图 + 明细弹窗）
│   │   │   ├── ProjectBoard.vue    # 项目看板（4 张趋势图 + 明细弹窗）
│   │   │   └── TrendChart.vue      # ECharts 封装（line/bar、百分比轴、点击事件）
│   │   ├── main.js
│   │   └── style.css               # 全局样式与响应式布局
│   ├── vite.config.js              # 5173 端口 + /api 代理 + 分包策略
│   └── package.json
│
├── backend/                        # Flask，开发端口 8000
│   ├── app.py                      # 应用工厂：双 bind、CORS、错误处理、init-db
│   ├── extensions.py               # SQLAlchemy 实例（独立存放避免循环导入）
│   ├── dw_models.py                # 数仓 23 张表模型（dw bind）
│   ├── cache.py                    # Redis 封装，异常静默降级
│   ├── routes/
│   │   └── dw.py                   # /api/dw/* 看板接口
│   ├── requirements.txt
│   └── .env.example
│
└── database/
    ├── etl/                        # 分层 ETL（pymysql 直连，非 ORM）
    │   ├── config.py               # 连接配置与分层执行顺序
    │   ├── db.py                   # 连接工厂
    │   ├── source.py               # ODS：模拟 HR/PM/ITSM 源数据（固定随机种子）
    │   ├── sync_dim.py             # DIM：SCD2 维度
    │   ├── sync_dwd.py             # DWD：事实表清洗
    │   ├── sync_dwm.py             # DWM：员工/项目日汇总
    │   ├── sync_dws.py             # DWS：组织日汇总
    │   ├── sync_ads.py             # ADS：组织/项目 × 周期 KPI
    │   └── runner.py               # 命令行入口与定时调度
    ├── 数据库设计文档.md            # 分层方案与建表 DDL
    └── 项目数据设计文档.md          # 项目维度的补充设计
```

## 快速开始

**前置依赖**：Python 3.10+、Node.js 18+、MySQL 8（utf8mb4）；Redis 可选。

### 1. 创建数据库

```sql
CREATE DATABASE `5003` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 配置后端环境变量

```bash
cd backend
cp .env.example .env        # Windows: Copy-Item .env.example .env
```

编辑 `.env`，确认数仓库连接串（默认 bind 无需配置，未设置时与它同源）：

```dotenv
DW_DATABASE_URL=mysql+pymysql://root:your_password@127.0.0.1:3306/5003?charset=utf8mb4
```

### 3. 建表并灌数据

```bash
# 仍在 backend/ 目录，先装依赖
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # PowerShell；macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 建表：create_all 会同时作用于默认库和 dw 库，共 23 张数仓表
flask --app app init-db

# 执行全量 ETL（回到仓库根目录，避免模块导入问题）
cd ..
python -m database.etl.runner --once
```

ETL 会模拟近 365 天的 HR / 需求 / 故障数据，逐层写入 `5003`，随机种子固定（`20251124`），重复执行结果可复现。

### 4. 启动后端

```bash
cd backend
python app.py                # http://127.0.0.1:8000
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

开发期 Vite 把 `/api` 代理到 `http://127.0.0.1:8000`，浏览器视角同源，无需额外配置 CORS。

## 环境变量

`backend/.env`（模板见 `backend/.env.example`）：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DATABASE_URL` | 默认 bind（占位，无模型）；不设置时与 `DW_DATABASE_URL` 同源 | 同 `DW_DATABASE_URL` |
| `DW_DATABASE_URL` | 数仓库连接串（`dw` bind） | `mysql+pymysql://root:root@127.0.0.1:3306/5003` |
| `PORT` | 后端监听端口 | `8000` |
| `SECRET_KEY` | Flask 密钥 | `dev-only-secret` |
| `CORS_ORIGINS` | 允许来源，逗号分隔 | `*` |
| `FLASK_DEBUG` | 设为 `1` 开启调试 | `0` |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | 缓存连接 | `127.0.0.1` / `6379` / `0` |
| `DW_CACHE_TTL` | 缓存过期秒数 | `86400` |

ETL 不走 `.env`，直接读环境变量（未设置则用括号内默认值）：`DW_DB_HOST`（`127.0.0.1`）、`DW_DB_USER`（`root`）、`DW_DB_PASSWORD`（`root`）、`DW_DB_PORT`（`3306`）、`DW_DB_NAME`（`5003`）、`DW_RUN_TIME`（`02:00`）。

`frontend/.env.development` / `.env.production`：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `VITE_API_BASE_URL` | API 前缀 | `/api` |

## API

所有响应统一为 `{ "code": 0, "message": "ok", "data": ... }`，`code` 非 0 即失败；HTTP 状态码同时反映错误（400 / 404 / 500 / 503）。

**组织维度（部门看板）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查，验证业务库可达 |
| GET | `/api/dw/health` | 数仓各表行数 |
| GET | `/api/dw/meta` | 组织维度、周期枚举与维度清单 |
| GET | `/api/dw/board` | 组织看板，返回 PR + EC 合并指标 |
| GET | `/api/dw/kpi/pr` | PR 需求 KPI 明细 |
| GET | `/api/dw/kpi/ec` | EC 故障 KPI 明细 |

**项目维度（项目看板）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/dw/project/meta` | 项目清单 |
| GET | `/api/dw/project/board` | 项目 PR 趋势数据 |
| GET | `/api/dw/project/ec` | 项目 EC 趋势数据 |
| GET | `/api/dw/project/kpi` | 项目 PR KPI 明细（支持单项目过滤） |

**其他**

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/dw/cache/clear` | 清空 `dw:` 前缀缓存，返回清除条数 |

**查询参数**

- `org_type`：`department` / `team` / `domain` / `employee`（前端看板不展示 `employee`）
- `period_type`：`week` / `month` / `quarter` / `halfyear` / `year`
- `period_value`：如 `2026-11`、`2026-Q4`、`2026-H2`、`2026-W46`、`2026`
- `org_id` / `project_id`：按维度主键过滤

```bash
curl "http://127.0.0.1:8000/api/dw/board?org_type=department&period_type=month"
```

## 指标口径

| 指标 | 公式 | 说明 |
|---|---|---|
| 需求完成率 | 需求完成数 ÷ 需求承接数 | 承接按 `assign_date`、完成按 `complete_date` 分别聚合后合并 |
| 准时交付率 | 准时交付数 ÷ 应交付数 | 应交付取当期已完成需求（`complete_date` 非空），准时指 `complete_date <= due_date` |
| 平均处理时长 | 处理天数总和 ÷ 完成数 | 单位：天，`process_days = complete_date - assign_date` |
| 返工率 | 返工数 ÷ 完成数 | 源数据 `rework_flag` |
| 故障解决率 | 故障解决数 ÷ 故障发现数 | 发现按 `found_at`、解决按 `resolved_at` |
| 平均响应时长 | 响应时长总和 ÷ 故障数 | 单位：分钟，`first_response_at - found_at` |
| 平均解决时长 | 解决时长总和 ÷ 解决数 | 单位：分钟 |
| 复发率 | 复发数 ÷ 解决数 | 源数据 `recur_flag` |

`pr_work_hours_ratio`（工时占比）字段已预留，ETL 当前写入 `NULL`。

## 数据模型

数仓 23 张表，模型定义见 `backend/dw_models.py`：

| 层 | 表 | 说明 |
|---|---|---|
| ODS | `ods_hr_employee`、`ods_pm_pr`、`ods_itsm_ec`、`ods_pm_project` | 源系统落地，含 ETL 审计字段（`etl_load_time` / `etl_batch_id` / `etl_operation`） |
| DIM | `dim_employee`、`dim_department`、`dim_team`、`dim_domain`、`dim_project`、`dim_date`、`dim_severity` | 组织/项目维度为 SCD2（`is_current` + 生效失效区间），`dim_date` 为日期维 |
| DWD | `dwd_pr_fact`、`dwd_ec_fact` | 事实表，含 `is_on_time`、`process_days`、`response_minutes` 等派生列 |
| DWM | `dwm_pr_emp_1d`、`dwm_ec_emp_1d`、`dwm_pr_project_1d`、`dwm_ec_project_1d` | 员工 / 项目 × 日粒度汇总 |
| DWS | `dws_pr_org_1d`、`dws_ec_org_1d` | 组织（部门/团队/领域/员工）× 日粒度汇总 |
| ADS | `ads_pr_kpi`、`ads_ec_kpi`、`ads_pr_project_kpi`、`ads_ec_project_kpi` | 组织/项目 × 周期 KPI，接口直接查询这一层 |

建表 DDL 见 `database/数据库设计文档.md`（分层方案 + 17 张核心表）与 `database/项目数据设计文档.md`（项目维度补充）；最省事的做法是直接 `flask --app app init-db`，由 ORM 完整生成 23 张表（含文档尚未收录的 `dwm_ec_project_1d`、`ads_ec_project_kpi`）。

### ETL 使用

```bash
python -m database.etl.runner --once                # 全量跑一遍（ods→dim→dwd→dwm→dws→ads）
python -m database.etl.runner --once --layer ads    # 只重跑某一层
python -m database.etl.runner --schedule            # 常驻进程，每日 02:00 执行
python -m database.etl.runner --schedule --time 03:30
```

每层执行前先 `DELETE` 目标表再全量写入，因此可反复执行；层间强依赖，改上游需按 `ORDER` 顺序重跑下游。

## 缓存策略

- 所有 `/api/dw/*` 读接口按「接口名 + 全部查询参数」拼 Redis key，前缀 `dw:`，默认 TTL 24 小时
- `cache.py` 对 Redis 异常全部静默吞掉：连不上就当作未命中，接口照常回源，**本地不装 Redis 也能跑**
- ETL 重跑后数据会变，需要主动 `POST /api/dw/cache/clear` 或点前端"刷新缓存"按钮

## 构建与部署

```bash
cd frontend
npm run build                # 产物在 frontend/dist，按 vue / charts 分包
```

Nginx 同域部署（前端静态资源 + `/api` 反代，避免跨域）：

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

后端生产环境用 WSGI 服务器，关闭 `FLASK_DEBUG`，并把 `CORS_ORIGINS` 收紧到实际域名：

```bash
pip install waitress
waitress-serve --host 127.0.0.1 --port 8000 app:create_app
```

## 已知限制

- `source.py` 是模拟数据源，接真实系统需替换该模块的抽取逻辑
- 只读接口，无鉴权与写操作（除清缓存）
- `pr_work_hours_ratio` 尚未计算

## 文档

- `database/数据库设计文档.md` —— 数仓分层方案、表结构与 DDL
- `database/项目数据设计文档.md` —— 项目维度建模与接口映射
- `database/员工目录-KPI指标地图.md` —— 指标与组织维度的对照关系
