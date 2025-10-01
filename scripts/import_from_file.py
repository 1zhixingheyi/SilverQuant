#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T067: Import Files to Database

从文件导入数据到数据库 (用于灾难恢复):
1. JSON → Redis
2. CSV → ClickHouse
3. JSON → MySQL

Usage:
    python scripts/import_from_file.py --input DIR [--account-id ACCOUNT_ID] [--verify]
"""

import argparse
import json
import csv
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.redis_store import RedisStore
from storage.mysql_store import MySQLStore
from storage.clickhouse_store import ClickHouseStore


def import_json_to_redis(account_id: str, input_dir: str) -> int:
    """从 JSON 导入数据到 Redis"""
    print(f'\n导入数据到 Redis...')

    try:
        redis_store = RedisStore()
        count = 0

        # 导入持仓天数
        held_file = os.path.join(input_dir, 'held_days.json')
        if os.path.exists(held_file):
            with open(held_file, 'r', encoding='utf-8') as f:
                held_days = json.load(f)

            key = f'held_days:{account_id}'
            pipe = redis_store.client.pipeline()
            for code, days in held_days.items():
                pipe.hset(key, code, int(days))
            pipe.execute()
            count += len(held_days)

        redis_store.close()
        print(f'  ✓ Redis: {count} 条记录')
        return count

    except Exception as e:
        print(f'  ✗ Redis 导入失败: {e}')
        return 0


def import_csv_to_clickhouse(account_id: str, input_dir: str) -> int:
    """从 CSV 导入数据到 ClickHouse"""
    print(f'\n导入数据到 ClickHouse...')

    try:
        ch_store = ClickHouseStore()

        trade_file = os.path.join(input_dir, 'trade_records.csv')
        if not os.path.exists(trade_file):
            print(f'  ⚠ 文件不存在: {trade_file}')
            return 0

        count = 0
        with open(trade_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ch_store.record_trade(
                    account_id=account_id,
                    timestamp=row['timestamp'],
                    stock_code=row['stock_code'],
                    stock_name=row['stock_name'],
                    order_type=row['order_type'],
                    remark=row.get('remark', ''),
                    price=float(row['price']),
                    volume=int(row['volume']),
                    strategy_name=row.get('strategy_name', '')
                )
                count += 1

        ch_store.close()
        print(f'  ✓ ClickHouse: {count} 条记录')
        return count

    except Exception as e:
        print(f'  ✗ ClickHouse 导入失败: {e}')
        return 0


def import_json_to_mysql(input_dir: str) -> int:
    """从 JSON 导入数据到 MySQL"""
    print(f'\n导入数据到 MySQL...')

    try:
        mysql_store = MySQLStore()
        count = 0

        # 导入账户
        accounts_file = os.path.join(input_dir, 'accounts.json')
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r', encoding='utf-8') as f:
                accounts = json.load(f)

            for acc in accounts:
                if not mysql_store.get_account(acc['account_id']):
                    mysql_store.create_account(
                        account_id=acc['account_id'],
                        account_name=acc['account_name'],
                        account_type=acc['account_type'],
                        initial_capital=acc['initial_capital'],
                        current_capital=acc['current_capital']
                    )
                    count += 1

        mysql_store.close()
        print(f'  ✓ MySQL: {count} 条记录')
        return count

    except Exception as e:
        print(f'  ✗ MySQL 导入失败: {e}')
        return 0


def main():
    parser = argparse.ArgumentParser(description='从文件导入数据到数据库')
    parser.add_argument('--input', type=str, required=True, help='输入目录')
    parser.add_argument('--account-id', type=str, default='55009728', help='账户ID')
    parser.add_argument('--verify', action='store_true', help='导入后验证')

    args = parser.parse_args()

    print(f'\n{'='*60}')
    print(f'开始导入数据')
    print(f'输入目录: {args.input}')
    print(f'{'='*60}')

    redis_count = import_json_to_redis(args.account_id, args.input)
    ch_count = import_csv_to_clickhouse(args.account_id, args.input)
    mysql_count = import_json_to_mysql(args.input)

    print(f'\n{'='*60}')
    print(f'导入完成')
    print(f'总记录数: {redis_count + ch_count + mysql_count}')
    print(f'{'='*60}\n')

    if args.verify:
        print('执行验证...')
        os.system(f'python scripts/verify_consistency.py --account-id {args.account_id}')

    exit(0)


if __name__ == '__main__':
    main()
