#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T066: Export Database to Files

导出数据库数据到文件 (用于备份回滚):
1. Redis → JSON
2. ClickHouse → CSV
3. MySQL → JSON

Usage:
    python scripts/export_to_file.py --output DIR [--account-id ACCOUNT_ID]
"""

import argparse
import json
import csv
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.redis_store import RedisStore
from storage.mysql_store import MySQLStore
from storage.clickhouse_store import ClickHouseStore


def export_redis_to_json(account_id: str, output_dir: str) -> int:
    """导出 Redis 数据到 JSON"""
    print(f'\n导出 Redis 数据...')

    try:
        redis_store = RedisStore()

        # 导出持仓天数
        held_days_key = f'held_days:{account_id}'
        held_days = redis_store.client.hgetall(held_days_key)
        held_days = {k.decode() if isinstance(k, bytes) else k: int(v)
                    for k, v in held_days.items()}

        # 导出最高价
        max_prices_key = f'max_prices:{account_id}'
        max_prices = redis_store.client.hgetall(max_prices_key)
        max_prices = {k.decode() if isinstance(k, bytes) else k: float(v)
                     for k, v in max_prices.items()}

        # 导出最低价
        min_prices_key = f'min_prices:{account_id}'
        min_prices = redis_store.client.hgetall(min_prices_key)
        min_prices = {k.decode() if isinstance(k, bytes) else k: float(v)
                     for k, v in min_prices.items()}

        redis_store.close()

        # 保存到文件
        with open(os.path.join(output_dir, 'held_days.json'), 'w', encoding='utf-8') as f:
            json.dump(held_days, f, indent=2, ensure_ascii=False)

        with open(os.path.join(output_dir, 'max_prices.json'), 'w', encoding='utf-8') as f:
            json.dump(max_prices, f, indent=2, ensure_ascii=False)

        with open(os.path.join(output_dir, 'min_prices.json'), 'w', encoding='utf-8') as f:
            json.dump(min_prices, f, indent=2, ensure_ascii=False)

        total = len(held_days) + len(max_prices) + len(min_prices)
        print(f'  ✓ Redis: {total} 条记录')
        return total

    except Exception as e:
        print(f'  ✗ Redis 导出失败: {e}')
        return 0


def export_clickhouse_to_csv(account_id: str, output_dir: str) -> int:
    """导出 ClickHouse 数据到 CSV"""
    print(f'\n导出 ClickHouse 数据...')

    try:
        ch_store = ClickHouseStore()

        # 导出交易记录
        df = ch_store.query_trades(account_id=account_id)
        trade_file = os.path.join(output_dir, 'trade_records.csv')
        df.to_csv(trade_file, index=False, encoding='utf-8-sig')

        ch_store.close()

        print(f'  ✓ ClickHouse: {len(df)} 条交易记录')
        return len(df)

    except Exception as e:
        print(f'  ✗ ClickHouse 导出失败: {e}')
        return 0


def export_mysql_to_json(output_dir: str) -> int:
    """导出 MySQL 数据到 JSON"""
    print(f'\n导出 MySQL 数据...')

    try:
        mysql_store = MySQLStore()

        # 导出所有账户
        from storage.mysql_store import Account, Strategy, StrategyParam
        session = mysql_store.Session()

        accounts = session.query(Account).all()
        accounts_data = [
            {
                'account_id': acc.account_id,
                'account_name': acc.account_name,
                'account_type': acc.account_type,
                'initial_capital': float(acc.initial_capital),
                'current_capital': float(acc.current_capital),
                'is_active': acc.is_active
            }
            for acc in accounts
        ]

        # 导出所有策略
        strategies = session.query(Strategy).all()
        strategies_data = [
            {
                'strategy_code': strat.strategy_code,
                'strategy_name': strat.strategy_name,
                'description': strat.description
            }
            for strat in strategies
        ]

        # 导出策略参数
        params = session.query(StrategyParam).filter_by(is_active=True).all()
        params_data = [
            {
                'strategy_code': p.strategy_code,
                'version': p.version,
                'params': json.loads(p.params) if p.params else {},
                'remark': p.remark
            }
            for p in params
        ]

        session.close()
        mysql_store.close()

        # 保存到文件
        with open(os.path.join(output_dir, 'accounts.json'), 'w', encoding='utf-8') as f:
            json.dump(accounts_data, f, indent=2, ensure_ascii=False)

        with open(os.path.join(output_dir, 'strategies.json'), 'w', encoding='utf-8') as f:
            json.dump(strategies_data, f, indent=2, ensure_ascii=False)

        with open(os.path.join(output_dir, 'strategy_params.json'), 'w', encoding='utf-8') as f:
            json.dump(params_data, f, indent=2, ensure_ascii=False)

        total = len(accounts_data) + len(strategies_data) + len(params_data)
        print(f'  ✓ MySQL: {len(accounts_data)} 账户, {len(strategies_data)} 策略, {len(params_data)} 参数版本')
        return total

    except Exception as e:
        print(f'  ✗ MySQL 导出失败: {e}')
        return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='导出数据库数据到文件 (用于备份回滚)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='输出目录'
    )
    parser.add_argument(
        '--account-id',
        type=str,
        default='55009728',
        help='账户ID (默认: 55009728)'
    )

    args = parser.parse_args()

    # 创建输出目录
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    print(f'\n{'='*60}')
    print(f'开始导出数据')
    print(f'输出目录: {output_dir}')
    print(f'{'='*60}')

    # 执行导出
    redis_count = export_redis_to_json(args.account_id, output_dir)
    ch_count = export_clickhouse_to_csv(args.account_id, output_dir)
    mysql_count = export_mysql_to_json(output_dir)

    # 打印总结
    print(f'\n{'='*60}')
    print(f'导出完成')
    print(f'{'='*60}')
    print(f'总记录数: {redis_count + ch_count + mysql_count}')
    print(f'  Redis: {redis_count}')
    print(f'  ClickHouse: {ch_count}')
    print(f'  MySQL: {mysql_count}')
    print(f'{'='*60}\n')

    exit(0)


if __name__ == '__main__':
    main()
