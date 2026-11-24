# -*- coding: utf-8 -*-
"""Redis 缓存封装（取数接口缓存）。

Redis 不可用时自动降级：get 返回 None，set/clear 忽略异常。
"""
import json
import os

import redis

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
CACHE_TTL = int(os.getenv("DW_CACHE_TTL", "86400"))

_client = None


def get_client():
    global _client
    if _client is None:
        _client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    return _client


def get(key):
    try:
        value = get_client().get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


def set(key, value, ttl=CACHE_TTL):
    try:
        get_client().setex(key, ttl, json.dumps(value, ensure_ascii=False))
    except Exception:
        pass


def clear(prefix):
    try:
        client = get_client()
        keys = client.keys(f"{prefix}*")
        count = 0
        if keys:
            count = client.delete(*keys)
        return count
    except Exception:
        return 0
