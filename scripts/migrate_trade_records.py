#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T061: Migrate Trade Records (CSV → ClickHouse)

迁移交易记录从 CSV 文件到 ClickHouse:
1. 读取交易记录 CSV 文件
2. 批量插入 ClickHouse (1000 行/批)
3. 输出迁移报告 (行数, 耗时)

Usage:
    python scripts/migrate_trade_records.py [--csv-file FILE] [--account-id ACCOUNT_ID] [--batch-size SIZE]
"""

import argparse
import time
import csv
import os
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.clickhouse_store import ClickHouseStore


def read_trade_csv(csv_file: str) -> List[Dict]:
    """
    读取交易记录 CSV 文件

    CSV 格式应包含列: timestamp, stock_code, stock_name, order_type, price, volume, strategy_name, remark
    """
    if not os.path.exists(csv_file):
        print(f'✗ CSV 文件不存在: {csv_file}')
        return []

    trades = []
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            # 尝试检测 CSV 格式
            reader = csv.DictReader(f)
            row_count = 0

            for row in reader:
                try:
                    # 标准化字段名 (兼容不同格式)
                    trade = {
                        'timestamp': row.get('timestamp') or row.get('时间') or row.get('成交时间'),
                        'stock_code': row.get('stock_code') or row.get('代码') or row.get('股票代码'),
                        'stock_name': row.get('stock_name') or row.get('名称') or row.get('股票名称'),
                        'order_type': row.get('order_type') or row.get('类型') or row.get('订单类型'),
                        'price': float(row.get('price') or row.get('价格') or row.get('成交价') or 0),
                        'volume': int(row.get('volume') or row.get('数量') or row.get('成交量') or 0),
                        'strategy_name': row.get('strategy_name') or row.get('策略') or row.get('策略名称') or '',
                        'remark': row.get('remark') or row.get('备注') or ''
                    }

                    # 验证必填字段
                    if not trade['timestamp'] or not trade['stock_code']:
                        print(f'  ⚠ 跳过无效行 {row_count + 1}: 缺少必填字段')
                        continue

                    trades.append(trade)
                    row_count += 1

                except Exception as e:
                    print(f'  ⚠ 解析行 {row_count + 1} 失败: {e}')
                    continue

        print(f'✓ 读取 CSV 文件: {csv_file} ({len(trades)} 条记录)')
        return trades

    except Exception as e:
        print(f'✗ 读取 CSV 文件失败: {e}')
        return []


def migrate_trade_records(
    csv_file: str,
    account_id: str,
    batch_size: int = 1000
) -> Tuple[int, int, float]:
    """
    迁移交易记录

    Args:
        csv_file: CSV 文件路径
        account_id: 账户ID
        batch_size: 批处理大小

    Returns:
        (success_count, fail_count, elapsed_time)
    """
    # 1. 读取源数据
    print(f'\n{'='*60}')
    print(f'开始迁移交易记录')
    print(f'账户ID: {account_id}')
    print(f'CSV 文件: {csv_file}')
    print(f'批处理大小: {batch_size}')
    print(f'{'='*60}\n')

    trades = read_trade_csv(csv_file)

    if not trades:
        print('✗ 没有找到有效的交易记录')
        return 0, 0, 0.0

    # 2. 连接 ClickHouse
    try:
        ch_store = ClickHouseStore()
        print(f'✓ ClickHouse 连接成功\n')
    except Exception as e:
        print(f'✗ ClickHouse 连接失败: {e}')
        return 0, len(trades), 0.0

    # 3. 批量插入
    start_time = time.time()
    success_count = 0
    fail_count = 0

    try:
        total_trades = len(trades)
        print(f'准备迁移 {total_trades} 条交易记录...\n')

        # 分批处理
        for i in range(0, total_trades, batch_size):
            batch = trades[i:i + batch_size]
            batch_success = 0

            for trade in batch:
                try:
                    # 使用 ClickHouseStore 的 record_trade 方法
                    success = ch_store.record_trade(
                        account_id=account_id,
                        timestamp=trade['timestamp'],
                        stock_code=trade['stock_code'],
                        stock_name=trade['stock_name'],
                        order_type=trade['order_type'],
                        remark=trade['remark'],
                        price=trade['price'],
                        volume=trade['volume'],
                        strategy_name=trade['strategy_name']
                    )

                    if success:
                        batch_success += 1
                    else:
                        fail_count += 1

                except Exception as e:
                    print(f'  ✗ 插入失败 {trade["stock_code"]} @ {trade["timestamp"]}: {e}')
                    fail_count += 1

            success_count += batch_success
            progress = (i + len(batch)) / total_trades * 100
            print(f'  进度: {progress:.1f}% ({i + len(batch)}/{total_trades}), 成功: {batch_success}/{len(batch)}')

    finally:
        ch_store.close()

    elapsed_time = time.time() - start_time
    return success_count, fail_count, elapsed_time


def print_migration_report(success: int, fail: int, elapsed: float):
    """打印迁移报告"""
    total = success + fail
    success_rate = (success / total * 100) if total > 0 else 0
    throughput = (success / elapsed) if elapsed > 0 else 0

    print(f'\n{'='*60}')
    print(f'迁移完成')
    print(f'{'='*60}')
    print(f'总记录数: {total}')
    print(f'成功: {success} ({success_rate:.1f}%)')
    print(f'失败: {fail}')
    print(f'耗时: {elapsed:.2f}s')
    print(f'吞吐量: {throughput:.0f} 条/秒')
    print(f'{'='*60}\n')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='迁移交易记录从 CSV 到 ClickHouse'
    )
    parser.add_argument(
        '--csv-file',
        type=str,
        required=True,
        help='交易记录 CSV 文件路径'
    )
    parser.add_argument(
        '--account-id',
        type=str,
        default='55009728',
        help='账户ID (默认: 55009728)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='批处理大小 (默认: 1000)'
    )

    args = parser.parse_args()

    # 执行迁移
    success, fail, elapsed = migrate_trade_records(
        csv_file=args.csv_file,
        account_id=args.account_id,
        batch_size=args.batch_size
    )

    # 打印报告
    print_migration_report(success, fail, elapsed)

    # 返回退出码
    exit(0 if fail == 0 else 1)


if __name__ == '__main__':
    main()
