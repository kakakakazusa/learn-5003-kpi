# -*- coding: utf-8 -*-
"""数据库连接。"""
import pymysql

from . import config


def get_conn():
    return pymysql.connect(**config.SOURCE, autocommit=False)
