#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据存储配置管理模块
从 credentials.py 读取凭证,构建完整的配置对象
"""

import os
from credentials import (
    CACHE_PROD_PATH,
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD,
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
    DATA_STORE_MODE
)


# ============================================================
# Redis 配置
# ============================================================
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', REDIS_HOST),
    'port': int(os.getenv('REDIS_PORT', REDIS_PORT)),
    'password': os.getenv('REDIS_PASSWORD', REDIS_PASSWORD) or None,
    'db': int(os.getenv('REDIS_DB', 0)),
    'decode_responses': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'max_connections': 50,
}

# ============================================================
# MySQL 配置
# ============================================================
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', MYSQL_HOST),
    'port': int(os.getenv('MYSQL_PORT', MYSQL_PORT)),
    'user': os.getenv('MYSQL_USER', MYSQL_USER),
    'password': os.getenv('MYSQL_PASSWORD', MYSQL_PASSWORD),
    'database': os.getenv('MYSQL_DATABASE', MYSQL_DATABASE),
    'charset': 'utf8mb4',
    'pool_size': 10,
    'pool_recycle': 3600,
}

# ============================================================
# ClickHouse 配置
# ============================================================
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', CLICKHOUSE_HOST),
    'port': int(os.getenv('CLICKHOUSE_PORT', CLICKHOUSE_PORT)),
    'database': os.getenv('CLICKHOUSE_DATABASE', CLICKHOUSE_DATABASE),
    'user': os.getenv('CLICKHOUSE_USER', CLICKHOUSE_USER),
    'password': os.getenv('CLICKHOUSE_PASSWORD', CLICKHOUSE_PASSWORD),
    'send_receive_timeout': 30,
}

# ============================================================
# 数据存储配置汇总
# ============================================================
DATA_STORE_CONFIG = {
    'redis': REDIS_CONFIG,
    'mysql': MYSQL_CONFIG,
    'clickhouse': CLICKHOUSE_CONFIG,
}

# ============================================================
# 运行时配置
# ============================================================
# 数据存储模式
STORAGE_MODE = os.getenv('DATA_STORE_MODE', DATA_STORE_MODE)

# 双写模式开关 (仅在 hybrid 模式下生效)
ENABLE_DUAL_WRITE = os.getenv('ENABLE_DUAL_WRITE', 'true').lower() == 'true'

# 自动降级开关 (数据库异常时自动降级到文件模式)
ENABLE_AUTO_FALLBACK = os.getenv('ENABLE_AUTO_FALLBACK', 'true').lower() == 'true'

# ============================================================
# 文件存储路径配置
# ============================================================
PATH_HELD = os.path.join(CACHE_PROD_PATH, 'held_days.json')
PATH_MAX_PRICES = os.path.join(CACHE_PROD_PATH, 'max_prices.json')
PATH_MIN_PRICES = os.path.join(CACHE_PROD_PATH, 'min_prices.json')
PATH_TRADE_RECORDS = os.path.join(CACHE_PROD_PATH, 'trade_records.csv')
PATH_ACCOUNTS = os.path.join(CACHE_PROD_PATH, 'accounts.json')
PATH_STRATEGIES = os.path.join(CACHE_PROD_PATH, 'strategies.json')
PATH_STRATEGY_PARAMS = os.path.join(CACHE_PROD_PATH, 'strategy_params')

# ============================================================
# 配置验证
# ============================================================
def validate_config():
    """验证配置的有效性"""
    errors = []

    # 验证存储模式
    valid_modes = ['file', 'redis', 'mysql', 'clickhouse', 'hybrid']
    if STORAGE_MODE not in valid_modes:
        errors.append(f"Invalid DATA_STORE_MODE: {STORAGE_MODE}. Must be one of {valid_modes}")

    # 验证 Redis 配置
    if STORAGE_MODE in ['redis', 'hybrid']:
        if not REDIS_CONFIG['host']:
            errors.append("REDIS_HOST is required when using redis or hybrid mode")

    # 验证 MySQL 配置
    if STORAGE_MODE in ['mysql', 'hybrid']:
        if not MYSQL_CONFIG['user'] or not MYSQL_CONFIG['password']:
            errors.append("MYSQL_USER and MYSQL_PASSWORD are required when using mysql or hybrid mode")

    # 验证 ClickHouse 配置
    if STORAGE_MODE in ['clickhouse', 'hybrid']:
        if not CLICKHOUSE_CONFIG['host']:
            errors.append("CLICKHOUSE_HOST is required when using clickhouse or hybrid mode")

    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    return True


# ============================================================
# 导出配置摘要
# ============================================================
def get_config_summary():
    """获取配置摘要(用于日志和调试)"""
    return {
        'storage_mode': STORAGE_MODE,
        'redis': f"{REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}/db{REDIS_CONFIG['db']}",
        'mysql': f"{MYSQL_CONFIG['user']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}",
        'clickhouse': f"{CLICKHOUSE_CONFIG['user']}@{CLICKHOUSE_CONFIG['host']}:{CLICKHOUSE_CONFIG['port']}/{CLICKHOUSE_CONFIG['database']}",
        'dual_write': ENABLE_DUAL_WRITE,
        'auto_fallback': ENABLE_AUTO_FALLBACK,
    }


if __name__ == '__main__':
    # 命令行运行时,输出配置摘要
    import json
    print("Current Storage Configuration:")
    print(json.dumps(get_config_summary(), indent=2, ensure_ascii=False))

    try:
        validate_config()
        print("\n✓ Configuration is valid")
    except ValueError as e:
        print(f"\n✗ Configuration validation failed:\n{e}")
