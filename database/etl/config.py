# -*- coding: utf-8 -*-
"""ETL 配置：数仓库连接与调度参数。

可通过环境变量覆盖。
"""
import os

SOURCE = {
    "host": os.getenv("DW_DB_HOST", "127.0.0.1"),
    "user": os.getenv("DW_DB_USER", "root"),
    "password": os.getenv("DW_DB_PASSWORD", "root"),
    "port": int(os.getenv("DW_DB_PORT", "3306")),
    "database": os.getenv("DW_DB_NAME", "5003"),
    "charset": "utf8mb4",
}

DEFAULT_RUN_TIME = os.getenv("DW_RUN_TIME", "02:00")

# 分层执行顺序（依赖关系：ods -> dim -> dwd -> dwm -> dws -> ads）
ORDER = ["ods", "dim", "dwd", "dwm", "dws", "ads"]
