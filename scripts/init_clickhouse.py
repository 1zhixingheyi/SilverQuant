#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ClickHouse 数据库初始化脚本
创建 trade 和 daily_kline 表
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickhouse_driver import Client
from storage.config import CLICKHOUSE_CONFIG


def init_clickhouse(host=None, port=None, database=None, user=None, password=None):
    """
    初始化 ClickHouse 数据库和表结构

    Args:
        host: ClickHouse 主机地址 (默认从 config.py 读取)
        port: ClickHouse 端口 (默认从 config.py 读取)
        database: 数据库名称 (默认从 config.py 读取)
        user: 用户名 (默认从 config.py 读取)
        password: 密码 (默认从 config.py 读取)
    """
    # 使用配置文件中的默认值
    host = host or CLICKHOUSE_CONFIG['host']
    port = port or CLICKHOUSE_CONFIG['port']
    database = database or CLICKHOUSE_CONFIG['database']
    user = user or CLICKHOUSE_CONFIG.get('user', 'default')
    password = password or CLICKHOUSE_CONFIG.get('password', '')

    try:
        # 连接 ClickHouse (创建数据库时不指定database)
        client = Client(host=host, port=port, user=user, password=password)
        print(f"✓ 成功连接到 ClickHouse {host}:{port}")

        # 创建数据库
        client.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        print(f"✓ 数据库 '{database}' 已创建")

        # 切换到目标数据库
        client = Client(host=host, port=port, database=database, user=user, password=password)

        # ============================================================
        # 创建 trade 表 (交易记录)
        # ============================================================
        trade_table_sql = """
        CREATE TABLE IF NOT EXISTS trade (
            id UInt64,
            timestamp DateTime,
            date Date,
            account_id String,
            stock_code String,
            stock_name String,
            order_type String,
            remark String,
            price Decimal(10, 3),
            volume UInt32,
            amount Decimal(20, 2),
            strategy_name String
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (account_id, stock_code, timestamp)
        SETTINGS index_granularity = 8192
        """

        client.execute(trade_table_sql)
        print("✓ 表 'trade' 已创建 (分区: 按月, 排序: account_id, stock_code, timestamp)")

        # ============================================================
        # 创建 daily_kline 表 (K线数据)
        # ============================================================
        kline_table_sql = """
        CREATE TABLE IF NOT EXISTS daily_kline (
            id UInt64,
            stock_code String,
            date Date,
            datetime UInt32,
            open Decimal(10, 3),
            high Decimal(10, 3),
            low Decimal(10, 3),
            close Decimal(10, 3),
            volume UInt64,
            amount Decimal(20, 2)
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(date)
        ORDER BY (stock_code, date)
        SETTINGS index_granularity = 8192
        """

        client.execute(kline_table_sql)
        print("✓ 表 'daily_kline' 已创建 (分区: 按月, 排序: stock_code, date)")

        # ============================================================
        # 验证表已创建
        # ============================================================
        tables = client.execute(f"SHOW TABLES FROM {database}")
        table_names = [table[0] for table in tables]

        print(f"\n✓ 初始化完成! 数据库 '{database}' 包含以下表:")
        for table_name in table_names:
            row_count = client.execute(f"SELECT COUNT(*) FROM {table_name}")[0][0]
            print(f"  - {table_name}: {row_count} 行")

        # ============================================================
        # 插入测试数据 (可选)
        # ============================================================
        # 插入一条测试交易记录
        test_trade_sql = """
        INSERT INTO trade (id, timestamp, date, account_id, stock_code, stock_name,
                          order_type, remark, price, volume, amount, strategy_name)
        VALUES (1, now(), today(), '55009728', 'SH600000', '浦发银行',
               'buy_trade', '测试买入', 10.50, 1000, 10500.00, 'wencai_v1')
        """
        client.execute(test_trade_sql)
        print("\n✓ 插入测试交易记录")

        # 插入一条测试K线数据
        test_kline_sql = """
        INSERT INTO daily_kline (id, stock_code, date, datetime, open, high, low, close, volume, amount)
        VALUES (1, 'SH600000', today(), toUInt32(toYYYYMMDD(today())),
               10.50, 10.80, 10.40, 10.65, 1000000, 10650000.00)
        """
        client.execute(test_kline_sql)
        print("✓ 插入测试K线数据")

        print("\n========================================")
        print("ClickHouse 初始化成功!")
        print("========================================")

        return True

    except Exception as e:
        print(f"✗ ClickHouse 初始化失败: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    # 从命令行参数读取配置
    import argparse

    parser = argparse.ArgumentParser(description='初始化 ClickHouse 数据库')
    parser.add_argument('--host', default='localhost', help='ClickHouse 主机地址')
    parser.add_argument('--port', type=int, default=9000, help='ClickHouse 端口')
    parser.add_argument('--database', default='silverquant', help='数据库名称')

    args = parser.parse_args()

    success = init_clickhouse(host=args.host, port=args.port, database=args.database)

    sys.exit(0 if success else 1)
