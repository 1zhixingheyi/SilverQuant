#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T064: Migrate Strategies (JSON → MySQL)

迁移策略配置从 JSON 文件到 MySQL:
1. 读取策略配置 JSON 文件
2. INSERT INTO MySQL strategy + strategy_param 表 (初始 version=1)
3. 输出迁移报告

Usage:
    python scripts/migrate_strategies.py [--config-file FILE] [--dry-run]
"""

import argparse
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.mysql_store import MySQLStore


def load_strategy_config(config_file: str) -> List[Dict]:
    """
    加载策略配置文件

    配置格式示例:
    {
        "strategies": [
            {
                "strategy_code": "wencai_v1",
                "strategy_name": "问财策略V1",
                "description": "基于问财选股的策略",
                "parameters": {
                    "param1": "value1",
                    "param2": 100
                }
            }
        ]
    }
    """
    if not os.path.exists(config_file):
        print(f'✗ 配置文件不存在: {config_file}')
        return []

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        strategies = config.get('strategies', [])
        print(f'✓ 读取配置文件: {config_file} ({len(strategies)} 个策略)')
        return strategies

    except Exception as e:
        print(f'✗ 读取配置文件失败: {e}')
        return []


def create_default_strategies() -> List[Dict]:
    """创建默认策略配置 (如果没有配置文件)"""
    return [
        {
            'strategy_code': 'wencai_v1',
            'strategy_name': '问财策略V1',
            'description': '基于问财选股的策略，每日更新持仓',
            'parameters': {
                'query': '涨幅大于5%',
                'max_positions': 10,
                'buy_ratio': 0.1
            }
        },
        {
            'strategy_code': 'technical_v1',
            'strategy_name': '技术指标策略V1',
            'description': '基于技术指标的策略',
            'parameters': {
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26
            }
        }
    ]


def migrate_strategies(config_file: str = None, dry_run: bool = False) -> Tuple[int, int, float]:
    """
    迁移策略数据

    Args:
        config_file: 配置文件路径 (如果为 None，使用默认配置)
        dry_run: 是否仅模拟运行

    Returns:
        (success_count, skip_count, elapsed_time)
    """
    # 1. 加载策略配置
    print(f'\n{'='*60}')
    print(f'开始迁移策略配置')
    print(f'模式: {'仅模拟' if dry_run else '实际执行'}')
    print(f'{'='*60}\n')

    if config_file:
        strategies = load_strategy_config(config_file)
    else:
        print('未指定配置文件，使用默认策略配置')
        strategies = create_default_strategies()

    if not strategies:
        print('✗ 没有找到策略配置')
        return 0, 0, 0.0

    print(f'\n找到 {len(strategies)} 个策略:\n')
    for strat in strategies:
        print(f'  - 策略代码: {strat["strategy_code"]}')
        print(f'    策略名称: {strat["strategy_name"]}')
        print(f'    描述: {strat.get("description", "无")}')
        print(f'    参数数量: {len(strat.get("parameters", {}))}')
        print()

    if dry_run:
        print(f'✓ 模拟运行完成 (未实际写入数据)')
        return len(strategies), 0, 0.0

    # 2. 连接 MySQL
    try:
        mysql_store = MySQLStore()
        print(f'✓ MySQL 连接成功\n')
    except Exception as e:
        print(f'✗ MySQL 连接失败: {e}')
        return 0, 0, 0.0

    # 3. 插入策略 (幂等性)
    start_time = time.time()
    success_count = 0
    skip_count = 0

    try:
        for strat in strategies:
            strategy_code = strat['strategy_code']

            # 检查策略是否已存在
            existing = mysql_store.get_strategy_params(strategy_code)

            if existing:
                print(f'  ⚠ 策略已存在，跳过: {strategy_code}')
                skip_count += 1
                continue

            # 创建新策略
            try:
                result = mysql_store.create_strategy(
                    strategy_code=strategy_code,
                    strategy_name=strat['strategy_name'],
                    description=strat.get('description', '')
                )

                if result:
                    # 保存策略参数 (初始版本=1)
                    params = strat.get('parameters', {})
                    if params:
                        mysql_store.save_strategy_params(
                            strategy_code=strategy_code,
                            params=params,
                            version=1,
                            remark='初始版本'
                        )

                    print(f'  ✓ 策略创建成功: {strategy_code} (版本 1)')
                    success_count += 1
                else:
                    print(f'  ✗ 策略创建失败: {strategy_code}')

            except Exception as e:
                print(f'  ✗ 策略创建异常 {strategy_code}: {e}')

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
    print(f'总策略数: {total}')
    print(f'成功创建: {success}')
    print(f'跳过(已存在): {skip}')
    print(f'耗时: {elapsed:.2f}s')
    print(f'{'='*60}\n')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='迁移策略配置从 JSON 到 MySQL'
    )
    parser.add_argument(
        '--config-file',
        type=str,
        help='策略配置 JSON 文件路径 (可选)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅模拟运行，不实际插入数据'
    )

    args = parser.parse_args()

    # 执行迁移
    success, skip, elapsed = migrate_strategies(
        config_file=args.config_file,
        dry_run=args.dry_run
    )

    # 打印报告
    if not args.dry_run:
        print_migration_report(success, skip, elapsed)

    # 返回退出码
    exit(0)


if __name__ == '__main__':
    main()
