#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T060: Migrate Held Days Data (JSON → Redis)

迁移持仓数据从 JSON 文件到 Redis:
1. 读取 held_days.json, max_prices.json, min_prices.json
2. 批量写入 Redis (使用 Pipeline, 每批 100 个键)
3. 输出迁移报告 (成功/失败数量, 耗时)

Usage:
    python scripts/migrate_held_days.py [--account-id ACCOUNT_ID] [--cache-path PATH] [--batch-size SIZE]
"""

import argparse
import time
import json
import os
from pathlib import Path
from typing import Dict, Tuple

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.redis_store import RedisStore


def load_json_file(file_path: str) -> Dict:
    """加载 JSON 文件"""
    if not os.path.exists(file_path):
        print(f'⚠ 文件不存在: {file_path}')
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f'✓ 加载文件: {file_path} ({len(data)} 条记录)')
            return data
    except Exception as e:
        print(f'✗ 加载文件失败 {file_path}: {e}')
        return {}


def migrate_held_days(
    cache_path: str,
    account_id: str,
    batch_size: int = 100
) -> Tuple[int, int, float]:
    """
    迁移持仓天数数据

    Args:
        cache_path: 缓存文件目录
        account_id: 账户ID
        batch_size: 批处理大小

    Returns:
        (success_count, fail_count, elapsed_time)
    """
    # 1. 加载源数据
    print(f'\n{'='*60}')
    print(f'开始迁移持仓数据')
    print(f'账户ID: {account_id}')
    print(f'缓存路径: {cache_path}')
    print(f'批处理大小: {batch_size}')
    print(f'{'='*60}\n')

    held_days_file = os.path.join(cache_path, 'held_days.json')
    max_prices_file = os.path.join(cache_path, 'max_prices.json')
    min_prices_file = os.path.join(cache_path, 'min_prices.json')

    held_days = load_json_file(held_days_file)
    max_prices = load_json_file(max_prices_file)
    min_prices = load_json_file(min_prices_file)

    if not held_days and not max_prices and not min_prices:
        print('✗ 没有找到任何数据文件')
        return 0, 0, 0.0

    # 2. 连接 Redis
    try:
        redis_store = RedisStore()
        print(f'✓ Redis 连接成功')
    except Exception as e:
        print(f'✗ Redis 连接失败: {e}')
        return 0, len(held_days) + len(max_prices) + len(min_prices), 0.0

    # 3. 批量写入
    start_time = time.time()
    success_count = 0
    fail_count = 0

    try:
        # 准备所有数据
        all_operations = []

        # 持仓天数
        for code, days in held_days.items():
            all_operations.append(('held_days', code, days))

        # 最高价
        for code, price in max_prices.items():
            all_operations.append(('max_price', code, price))

        # 最低价
        for code, price in min_prices.items():
            all_operations.append(('min_price', code, price))

        total_ops = len(all_operations)
        print(f'\n准备迁移 {total_ops} 条记录...\n')

        # 分批处理
        for i in range(0, total_ops, batch_size):
            batch = all_operations[i:i + batch_size]
            pipeline = redis_store.client.pipeline()

            for op_type, code, value in batch:
                try:
                    if op_type == 'held_days':
                        key = f'held_days:{account_id}'
                        pipeline.hset(key, code, int(value))
                    elif op_type == 'max_price':
                        key = f'max_prices:{account_id}'
                        pipeline.hset(key, code, float(value))
                    elif op_type == 'min_price':
                        key = f'min_prices:{account_id}'
                        pipeline.hset(key, code, float(value))
                except Exception as e:
                    print(f'  ✗ 准备操作失败 {code}: {e}')
                    fail_count += 1

            # 执行批处理
            try:
                pipeline.execute()
                batch_success = len(batch) - fail_count
                success_count += batch_success

                progress = (i + len(batch)) / total_ops * 100
                print(f'  进度: {progress:.1f}% ({i + len(batch)}/{total_ops})')
            except Exception as e:
                print(f'  ✗ 批处理执行失败: {e}')
                fail_count += len(batch)

    finally:
        redis_store.close()

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
        description='迁移持仓数据从 JSON 到 Redis'
    )
    parser.add_argument(
        '--account-id',
        type=str,
        default='55009728',
        help='账户ID (默认: 55009728)'
    )
    parser.add_argument(
        '--cache-path',
        type=str,
        default='storage',
        help='缓存文件目录 (默认: storage)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='批处理大小 (默认: 100)'
    )

    args = parser.parse_args()

    # 执行迁移
    success, fail, elapsed = migrate_held_days(
        cache_path=args.cache_path,
        account_id=args.account_id,
        batch_size=args.batch_size
    )

    # 打印报告
    print_migration_report(success, fail, elapsed)

    # 返回退出码
    exit(0 if fail == 0 else 1)


if __name__ == '__main__':
    main()
