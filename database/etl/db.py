# -*- coding: utf-8 -*-
"""Database connection."""
import pymysql

from . import config


def get_conn():
    return pymysql.connect(**config.SOURCE, autocommit=False)
