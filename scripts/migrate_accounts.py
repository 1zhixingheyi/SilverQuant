#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T063: Migrate Accounts (credentials.py → MySQL)

迁移账户配置从 credentials.py 到 MySQL:
1. 读取 credentials.py 中的账户配置
2. INSERT INTO MySQL account 表 (幂等性: 先检查存在性)
3. 输出迁移报告

Usage:
    python scripts/migrate_accounts.py [--dry-run]
"""

import argparse
import time
from pathlib import Path
from typing import List, Dict, Tuple

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.mysql_store import MySQLStore
from tools import credentials


def extract_accounts_from_credentials() -> List[Dict]:
    """从 credentials.py 提取账户信息"""
    accounts = []

    # 检查常见的账户配置变量
    account_configs = [
        {
            'account_id': getattr(credentials, 'ACCOUNT_ID', None) or getattr(credentials, 'account_id', None),
            'account_name': '主账户',
            'account_type': 'simulation',  # 模拟账户
            'initial_capital': 1000000.0,
            'current_capital': 1000000.0,
            'is_active': True
        }
    ]

    # 过滤有效账户
    for acc in account_configs:
        if acc['account_id']:
            accounts.append(acc)

    return accounts


def migrate_accounts(dry_run: bool = False) -> Tuple[int, int, float]:
    """
    迁移账户数据

    Args:
        dry_run: 是否仅模拟运行 (不实际插入数据)

    Returns:
        (success_count, skip_count, elapsed_time)
    """
    # 1. 提取账户配置
    print(f'\n{'='*60}')
    print(f'开始迁移账户配置')
    print(f'模式: {'仅模拟' if dry_run else '实际执行'}')
    print(f'{'='*60}\n')

    accounts = extract_accounts_from_credentials()

    if not accounts:
        print('✗ 没有找到账户配置')
        print('  提示: 请确保 credentials.py 中定义了 ACCOUNT_ID 或 account_id')
        return 0, 0, 0.0

    print(f'找到 {len(accounts)} 个账户配置:\n')
    for acc in accounts:
        print(f'  - 账户ID: {acc["account_id"]}')
        print(f'    账户名称: {acc["account_name"]}')
        print(f'    账户类型: {acc["account_type"]}')
        print(f'    初始资金: {acc["initial_capital"]:,.2f}')

    if dry_run:
        print(f'\n✓ 模拟运行完成 (未实际写入数据)')
        return len(accounts), 0, 0.0

    # 2. 连接 MySQL
    try:
        mysql_store = MySQLStore()
        print(f'\n✓ MySQL 连接成功\n')
    except Exception as e:
        print(f'✗ MySQL 连接失败: {e}')
        return 0, 0, 0.0

    # 3. 插入账户 (幂等性)
    start_time = time.time()
    success_count = 0
    skip_count = 0

    try:
        for acc in accounts:
            account_id = acc['account_id']

            # 检查账户是否已存在
            existing = mysql_store.get_account(account_id)

            if existing:
                print(f'  ⚠ 账户已存在，跳过: {account_id}')
                skip_count += 1
                continue

            # 创建新账户
            try:
                result = mysql_store.create_account(
                    account_id=account_id,
                    account_name=acc['account_name'],
                    account_type=acc['account_type'],
                    initial_capital=acc['initial_capital'],
                    current_capital=acc['current_capital']
                )

                if result:
                    print(f'  ✓ 账户创建成功: {account_id}')
                    success_count += 1
                else:
                    print(f'  ✗ 账户创建失败: {account_id}')

            except Exception as e:
                print(f'  ✗ 账户创建异常 {account_id}: {e}')

    finally:
        mysql_store.close()

    elapsed_time = time.time() - start_time
    return success_count, skip_count, elapsed_time


def print_migration_report(success: int, skip: int, elapsed: float):
    """打印迁移报告"""
    total = success + skip

    print(f'\n{'='*60}')
    print(f'迁移完成')
    print(f'{'='*60}')
    print(f'总账户数: {total}')
    print(f'成功创建: {success}')
    print(f'跳过(已存在): {skip}')
    print(f'耗时: {elapsed:.2f}s')
    print(f'{'='*60}\n')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='迁移账户配置从 credentials.py 到 MySQL'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅模拟运行，不实际插入数据'
    )

    args = parser.parse_args()

    # 执行迁移
    success, skip, elapsed = migrate_accounts(dry_run=args.dry_run)

    # 打印报告
    if not args.dry_run:
        print_migration_report(success, skip, elapsed)

    # 返回退出码
    exit(0)


if __name__ == '__main__':
    main()
