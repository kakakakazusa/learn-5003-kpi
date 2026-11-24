# -*- coding: utf-8 -*-
"""ETL 调度与命令行入口。

用法：
    python -m database.etl.runner --once              # 立即执行一次全量同步
    python -m database.etl.runner --layer dws         # 只同步指定层
    python -m database.etl.runner --schedule          # 进入定时循环，每日 02:00 执行
    python -m database.etl.runner --once --time 03:30 # 指定每日执行时间
"""
import argparse
import sys
import time
from datetime import datetime, timedelta

from . import config
from .db import get_conn
from .source import load_source
from .sync_dim import sync as sync_dim
from .sync_dwd import sync as sync_dwd
from .sync_dwm import sync as sync_dwm
from .sync_dws import sync as sync_dws
from .sync_ads import sync as sync_ads

LAYERS = {
    "ods": load_source,
    "dim": sync_dim,
    "dwd": sync_dwd,
    "dwm": sync_dwm,
    "dws": sync_dws,
    "ads": sync_ads,
}


def run_layer(conn, layer):
    if layer == "all":
        for name in config.ORDER:
            LAYERS[name](conn)
    elif layer in LAYERS:
        LAYERS[layer](conn)
    else:
        raise SystemExit("未知层：%s，可选 %s" % (layer, ["all"] + config.ORDER))


def run_once(layer):
    conn = get_conn()
    try:
        run_layer(conn, layer)
    finally:
        conn.close()


def schedule(layer, run_time):
    hh, mm = [int(x) for x in run_time.split(":")]
    print("定时任务已启动：每日 %s 同步层 %s" % (run_time, layer))
    while True:
        now = datetime.now()
        next_run = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        wait = (next_run - now).total_seconds()
        print("下次执行：%s（%.0f 秒后）" % (next_run.strftime("%Y-%m-%d %H:%M:%S"), wait))
        time.sleep(wait)
        try:
            run_once(layer)
            print("同步完成：%s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as exc:  # noqa: BLE001
            print("同步失败：%s" % exc, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="数仓分层定时同步脚本")
    parser.add_argument("--layer", default="all", help="同步层：all/ods/dim/dwd/dwm/dws/ads")
    parser.add_argument("--once", action="store_true", help="立即执行一次")
    parser.add_argument("--schedule", action="store_true", help="进入定时循环")
    parser.add_argument("--time", default=config.DEFAULT_RUN_TIME, help="每日执行时间 HH:MM")
    args = parser.parse_args()

    if args.schedule:
        schedule(args.layer, args.time)
    elif args.once:
        run_once(args.layer)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
