# -*- coding: utf-8 -*-
"""ETL scheduling and command-line entry point.

Usage:
    python -m database.etl.runner --once              # Run one full sync immediately
    python -m database.etl.runner --layer dws         # Sync only the specified layer
    python -m database.etl.runner --schedule          # Enter the scheduled loop, running daily at 02:00
    python -m database.etl.runner --once --time 03:30 # Specify the daily run time
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
        raise SystemExit("Unknown layer: %s, available: %s" % (layer, ["all"] + config.ORDER))


def run_once(layer):
    conn = get_conn()
    try:
        run_layer(conn, layer)
    finally:
        conn.close()


def schedule(layer, run_time):
    hh, mm = [int(x) for x in run_time.split(":")]
    print("Scheduled task started: daily %s sync of layer %s" % (run_time, layer))
    while True:
        now = datetime.now()
        next_run = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        wait = (next_run - now).total_seconds()
        print("Next run: %s (in %.0f seconds)" % (next_run.strftime("%Y-%m-%d %H:%M:%S"), wait))
        time.sleep(wait)
        try:
            run_once(layer)
            print("Sync complete: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as exc:  # noqa: BLE001
            print("Sync failed: %s" % exc, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Layered warehouse scheduled sync script")
    parser.add_argument("--layer", default="all", help="Layer to sync: all/ods/dim/dwd/dwm/dws/ads")
    parser.add_argument("--once", action="store_true", help="Run once immediately")
    parser.add_argument("--schedule", action="store_true", help="Enter the scheduled loop")
    parser.add_argument("--time", default=config.DEFAULT_RUN_TIME, help="Daily run time HH:MM")
    args = parser.parse_args()

    if args.schedule:
        schedule(args.layer, args.time)
    elif args.once:
        run_once(args.layer)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
