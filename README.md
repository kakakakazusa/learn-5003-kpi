# 拾数 · 数据分析平台

Vue 3 + ECharts 前端、Flask + SQLAlchemy 后端、MySQL 数据库的前后端分离经营分析仪表盘。

```
demo/
├── frontend/                 # Vue 3 + Vite，开发端口 5173
│   ├── src/App.vue           # 仪表盘页面与图表
│   ├── src/api/index.js      # 统一请求层
│   └── src/style.css         # 全局样式与响应式布局
└── backend/                  # Flask，开发端口 8000
    ├── app.py                # 应用工厂、模型、接口
    ├── seed.py               # 演示数据（幂等，可 --reset）
    └── requirements.txt
```

## 功能

- 核心指标：销售额、订单数、平均客单价、覆盖地区数，含环比变化。
- 销售趋势：销售额折线 + 订单数双轴，顶部下拉框支持按月、季度、半年、年度分组。
- 品类占比：环形图展示各品类销售额。
- 区域排行：横向条形图展示地区销售表现。
- 近期记录：按日期倒序展示最近 8 条销售明细。
- 加载、错误、重试、空数据占位与窄屏适配。

## 快速开始（SQLite，零依赖）

默认未设置 `DATABASE_URL` 时使用 SQLite，数据库文件位于 `backend/instance/analytics.db`，便于本地直接跑通。

### 1. 启动后端

```powershell
cd backend
python -m venv .venv                 # 首次创建
.\.venv\Scripts\Activate.ps1         # PowerShell
pip install -r requirements.txt
flask --app app init-db              # 建表
python seed.py                       # 写入近 180 天演示数据
python app.py                        # http://127.0.0.1:8000
```

重新生成演示数据：

```powershell
python seed.py --reset
```

### 2. 启动前端

```powershell
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

开发期 Vite 将 `/api` 代理到 `http://127.0.0.1:8000`，浏览器视角同源，后端无需额外 CORS 配置。

## 切换 MySQL

1. 创建数据库（要求 `utf8mb4`）：

```sql
CREATE DATABASE analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. 复制环境变量模板并填入连接信息：

```powershell
cd backend
Copy-Item .env.example .env
```

编辑 `backend/.env`，启用 MySQL 连接串：

```dotenv
DATABASE_URL=mysql+pymysql://root:your_password@127.0.0.1:3306/analytics?charset=utf8mb4
```

3. 初始化并重新灌入数据：

```powershell
flask --app app init-db
python seed.py
python app.py
```

切换到 MySQL 后，`pool_pre_ping` 会自动启用，避免空闲连接失效。ORM 查询不依赖具体方言，SQLite 与 MySQL 行为一致。

## 环境变量

`backend/.env`（模板见 `backend/.env.example`）：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy 连接串 | `sqlite:///analytics.db` |
| `PORT` | 后端端口 | `8000` |
| `SECRET_KEY` | Flask 密钥 | `dev-only-secret` |
| `CORS_ORIGINS` | 允许的前端来源，逗号分隔 | `*` |
| `FLASK_DEBUG` | 设为 `1` 开启调试 | `0` |

`frontend/.env.development` / `.env.production`：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `VITE_API_BASE_URL` | API 前缀 | `/api` |

## 接口

所有响应统一为 `{ "code": 0, "message": "ok", "data": ... }`，`code` 非 0 即为失败。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查，验证数据库可达 |
| GET | `/api/analytics/overview?period=month` | 仪表盘聚合数据，`period` 支持 `week` / `month` / `quarter` / `halfyear` / `year` |
| GET | `/api/dw/health` | 数仓库（5003）各表行数 |
| GET | `/api/dw/meta` | 组织维度、周期类型枚举与维度清单 |
| GET | `/api/dw/kpi/pr` | PR 项目需求 KPI，按 org_type / period_type / period_value / org_id 过滤 |
| GET | `/api/dw/kpi/ec` | EC 故障 KPI，按 org_type / period_type / period_value / org_id 过滤 |
| GET | `/api/dw/board` | 组织看板，org_type + period_type 返回 PR/EC 合并指标 |

`overview` 返回结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "start_date": "2026-10-25",
    "end_date": "2026-11-23",
    "metrics": {
      "revenue": 1234567.89,
      "revenue_change": 8.4,
      "orders": 3210,
      "orders_change": 3.1,
      "average_order_value": 384.6,
      "average_order_value_change": 5.2,
      "regions": 5
    },
    "trend": [{ "date": "2026-10-25", "revenue": 42000.0, "orders": 110 }],
    "categories": [{ "name": "数码科技", "revenue": 500000.0, "orders": 1200 }],
    "regions": [{ "name": "华东", "revenue": 300000.0, "orders": 800 }],
    "recent": [
      {
        "date": "2026-11-23",
        "category": "数码科技",
        "region": "华东",
        "revenue": 28560.0,
        "orders": 32
      }
    ]
  }
}
```

- 趋势数据按天补齐，无成交日期补 0。
- 环比对比的是紧邻的、等长的上一周期。
- 当前仅提供只读分析接口。

## 数据模型

表 `sales_records`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | INTEGER PK | 自增主键 |
| `sale_date` | DATE | 销售日期，索引 |
| `category` | VARCHAR(80) | 商品品类，索引 |
| `region` | VARCHAR(80) | 销售地区，索引 |
| `revenue` | NUMERIC(12,2) | 销售额 |
| `order_count` | INTEGER | 订单数 |

演示数据覆盖近 180 天、4 个品类、5 个地区，随机种子固定，可重复生成。

## 构建与部署

```powershell
cd frontend
npm run build                        # 产物在 frontend/dist
```

Nginx 同域部署示例：

```nginx
server {
    listen 80;
    server_name example.com;

    root /var/www/shishu/dist;
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

后端生产环境建议使用 WSGI 服务器（Windows 可用 `waitress`），并关闭 `FLASK_DEBUG`：

```powershell
pip install waitress
waitress-serve --host 127.0.0.1 --port 8000 app:create_app
```
