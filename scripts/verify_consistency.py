#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T065: Verify Data Consistency

验证数据一致性:
1. 比较持仓数据 (Redis vs File)
2. 比较交易记录数量 (ClickHouse vs CSV)
3. 比较账户数据 (MySQL vs JSON)
4. 输出不一致报告

Exit codes:
    0 - 所有数据一致
    1 - 发现数据不一致

Usage:
    python scripts/verify_consistency.py [--account-id ACCOUNT_ID] [--cache-path PATH]
"""

import argparse
import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.redis_store import RedisStore
from storage.mysql_store import MySQLStore
from storage.clickhouse_store import ClickHouseStore
from storage.file_store import FileStore


def verify_held_days_consistency(
    account_id: str,
    cache_path: str
) -> Tuple[bool, List[str]]:
    """
    验证持仓数据一致性 (Redis vs File)

    Returns:
        (is_consistent, inconsistencies)
    """
    print(f'\n{'='*60}')
    print(f'验证持仓数据一致性 (Redis vs File)')
    print(f'{'='*60}\n')

    inconsistencies = []

    try:
        # 加载 File 数据
        file_store = FileStore(cache_path=cache_path)
        held_days_file = os.path.join(cache_path, 'held_days.json')

        if not os.path.exists(held_days_file):
            print('⚠ File 数据不存在，跳过验证')
            return True, []

        with open(held_days_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)

        # 加载 Redis 数据
        redis_store = RedisStore()
        redis_key = f'held_days:{account_id}'
        redis_data = redis_store.client.hgetall(redis_key)
        redis_data = {k.decode() if isinstance(k, bytes) else k: int(v)
                     for k, v in redis_data.items()}
        redis_store.close()

        # 比较
        all_codes = set(file_data.keys()) | set(redis_data.keys())

        for code in all_codes:
            file_days = file_data.get(code)
            redis_days = redis_data.get(code)

            if file_days != redis_days:
                inconsistencies.append(
                    f'持仓天数不一致 [{code}]: File={file_days}, Redis={redis_days}'
                )

        if inconsistencies:
            print(f'✗ 发现 {len(inconsistencies)} 处不一致:\n')
            for inc in inconsistencies[:10]:  # 只显示前10个
                print(f'  - {inc}')
            if len(inconsistencies) > 10:
                print(f'  ... 还有 {len(inconsistencies) - 10} 处不一致')
        else:
            print(f'✓ 持仓数据一致 ({len(all_codes)} 只股票)')

        return len(inconsistencies) == 0, inconsistencies

    except Exception as e:
        print(f'✗ 验证失败: {e}')
        return False, [f'验证异常: {e}']


def verify_trade_count_consistency(
    account_id: str,
    csv_file: str
) -> Tuple[bool, List[str]]:
    """
    验证交易记录数量一致性 (ClickHouse vs CSV)

    Returns:
        (is_consistent, inconsistencies)
    """
    print(f'\n{'='*60}')
    print(f'验证交易记录数量一致性 (ClickHouse vs CSV)')
    print(f'{'='*60}\n')

    inconsistencies = []

    try:
        # 读取 CSV 行数
        if not os.path.exists(csv_file):
            print('⚠ CSV 文件不存在，跳过验证')
            return True, []

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None)  # 跳过表头
            csv_count = sum(1 for _ in reader)

        # 查询 ClickHouse 行数
        ch_store = ClickHouseStore()
        query = f"SELECT COUNT(*) as count FROM {ch_store.database}.trade WHERE account_id = '{account_id}'"
        result = ch_store.client.execute(query)
        ch_count = result[0][0] if result else 0
        ch_store.close()

        # 比较
        if csv_count != ch_count:
            inconsistencies.append(
                f'交易记录数量不一致: CSV={csv_count}, ClickHouse={ch_count}'
            )
            print(f'✗ 交易记录数量不一致')
            print(f'  CSV: {csv_count} 条')
            print(f'  ClickHouse: {ch_count} 条')
            print(f'  差异: {abs(csv_count - ch_count)} 条')
        else:
            print(f'✓ 交易记录数量一致 ({csv_count} 条)')

        return len(inconsistencies) == 0, inconsistencies

    except Exception as e:
        print(f'✗ 验证失败: {e}')
        return False, [f'验证异常: {e}']


def verify_account_consistency(
    account_id: str
) -> Tuple[bool, List[str]]:
    """
    验证账户数据一致性 (MySQL vs credentials.py)

    Returns:
        (is_consistent, inconsistencies)
    """
    print(f'\n{'='*60}')
    print(f'验证账户数据一致性 (MySQL vs credentials.py)')
    print(f'{'='*60}\n')

    inconsistencies = []

    try:
        # 从 credentials.py 获取账户ID
        from tools import credentials
        expected_account_id = getattr(credentials, 'ACCOUNT_ID', None) or \
                             getattr(credentials, 'account_id', None)

        if not expected_account_id:
            print('⚠ credentials.py 中没有定义账户ID，跳过验证')
            return True, []

        # 从 MySQL 查询账户
        mysql_store = MySQLStore()
        account = mysql_store.get_account(account_id)
        mysql_store.close()

        if not account:
            inconsistencies.append(f'账户不存在于 MySQL: {account_id}')
            print(f'✗ 账户不存在于 MySQL: {account_id}')
        else:
            # 验证账户ID匹配
            if account['account_id'] != expected_account_id:
                inconsistencies.append(
                    f'账户ID不一致: credentials.py={expected_account_id}, MySQL={account["account_id"]}'
                )
                print(f'✗ 账户ID不一致')
            else:
                print(f'✓ 账户数据一致')
                print(f'  账户ID: {account["account_id"]}')
                print(f'  账户名称: {account.get("account_name", "未知")}')
                print(f'  当前资金: {account.get("current_capital", 0):,.2f}')

        return len(inconsistencies) == 0, inconsistencies

    except Exception as e:
        print(f'✗ 验证失败: {e}')
        return False, [f'验证异常: {e}']


def print_verification_report(
    results: Dict[str, Tuple[bool, List[str]]]
):
    """打印验证报告"""
    print(f'\n{'='*60}')
    print(f'验证报告')
    print(f'{'='*60}\n')

    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r[0])
    total_inconsistencies = sum(len(r[1]) for r in results.values())

    print(f'总检查项: {total_checks}')
    print(f'通过: {passed_checks}')
    print(f'失败: {total_checks - passed_checks}')
    print(f'不一致总数: {total_inconsistencies}')

    if total_inconsistencies > 0:
        print(f'\n详细不一致列表:')
        for check_name, (consistent, inconsistencies) in results.items():
            if not consistent:
                print(f'\n  [{check_name}]:')
                for inc in inconsistencies:
                    print(f'    - {inc}')

    print(f'\n{'='*60}')
    print(f'结果: {'✓ 所有数据一致' if total_inconsistencies == 0 else '✗ 发现数据不一致'}')
    print(f'{'='*60}\n')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='验证数据一致性 (Redis/MySQL/ClickHouse vs File)'
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
        '--trade-csv',
        type=str,
        default='storage/trade_records.csv',
        help='交易记录 CSV 文件路径 (默认: storage/trade_records.csv)'
    )

    args = parser.parse_args()

    # 执行验证
    results = {}

    # 1. 验证持仓数据
    results['held_days'] = verify_held_days_consistency(
        account_id=args.account_id,
        cache_path=args.cache_path
    )

    # 2. 验证交易记录
    results['trade_records'] = verify_trade_count_consistency(
        account_id=args.account_id,
        csv_file=args.trade_csv
    )

    # 3. 验证账户数据
    results['accounts'] = verify_account_consistency(
        account_id=args.account_id
    )

    # 打印报告
    print_verification_report(results)

    # 返回退出码
    all_consistent = all(r[0] for r in results.values())
    exit(0 if all_consistent else 1)


if __name__ == '__main__':
    main()
