#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Storage Module - 统一数据存储接口"""

from typing import Optional, Dict
from storage.base_store import BaseDataStore
from storage.file_store import FileStore
from storage.redis_store import RedisStore
from storage.mysql_store import MySQLStore
from storage.clickhouse_store import ClickHouseStore
from storage.hybrid_store import HybridStore


def create_data_store(mode: str = 'file', config: Optional[Dict] = None) -> BaseDataStore:
    """工厂函数: 创建数据存储实例"""
    valid_modes = ['file', 'redis', 'mysql', 'clickhouse', 'hybrid']
    if mode not in valid_modes:
        raise ValueError(f"Invalid storage mode: '{mode}'. Must be one of {valid_modes}")
    
    config = config or {}
    
    if mode == 'file':
        cache_path = config.get('cache_path')
        return FileStore(cache_path) if cache_path else FileStore()
    elif mode == 'redis':
        return RedisStore(
            host=config.get('host'), port=config.get('port'),
            password=config.get('password'), db=config.get('db')
        )
    elif mode == 'mysql':
        return MySQLStore(
            host=config.get('host'), port=config.get('port'),
            user=config.get('user'), password=config.get('password'),
            database=config.get('database')
        )
    elif mode == 'clickhouse':
        return ClickHouseStore(
            host=config.get('host'), port=config.get('port'),
            database=config.get('database'), user=config.get('user'),
            password=config.get('password')
        )
    elif mode == 'hybrid':
        return HybridStore(
            cache_path=config.get('cache_path'),
            enable_redis=config.get('enable_redis', True),
            enable_mysql=config.get('enable_mysql', True),
            enable_clickhouse=config.get('enable_clickhouse', True),
            enable_dual_write=config.get('enable_dual_write', True),
            enable_auto_fallback=config.get('enable_auto_fallback', True)
        )


__all__ = [
    'BaseDataStore', 'FileStore', 'RedisStore', 'MySQLStore',
    'ClickHouseStore', 'HybridStore', 'create_data_store'
]
