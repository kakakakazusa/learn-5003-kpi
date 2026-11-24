# -*- coding: utf-8 -*-
"""数仓分层 ETL 同步包。

模块划分：
- config.py    连接与调度配置
- db.py        数据库连接
- source.py    ODS 源数据模拟（真实环境替换为源系统抽取）
- sync_dim.py  DIM 维度层
- sync_dwd.py  DWD 明细层
- sync_dwm.py  DWM 中间层
- sync_dws.py  DWS 汇总层
- sync_ads.py  ADS 应用层
- runner.py    调度与命令行入口
"""
from .config import ORDER

__all__ = ["ORDER"]

