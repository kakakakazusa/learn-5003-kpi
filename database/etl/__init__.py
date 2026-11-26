# -*- coding: utf-8 -*-
"""Layered warehouse ETL synchronization package.

Modules:
- config.py    connection and scheduling configuration
- db.py        database connection
- source.py    ODS source data simulation (replace with source-system extraction in production)
- sync_dim.py  DIM dimension layer
- sync_dwd.py  DWD detail layer
- sync_dwm.py  DWM intermediate layer
- sync_dws.py  DWS summary layer
- sync_ads.py  ADS application layer
- runner.py    scheduling and command-line entry point
"""
from .config import ORDER

__all__ = ["ORDER"]

