#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T062: Migrate K-line Data (CSV → ClickHouse)

迁移K线数据从 CSV 文件到 ClickHouse:
1. 扫描股票 CSV 文件目录
2. 批量插入 ClickHouse (10000 行/批)
3. 显示进度条 (使用 tqdm)
4. 输出迁移报告

Usage:
    python scripts/migrate_kline.py [--data-dir DIR] [--pattern PATTERN] [--batch-size SIZE]
"""

import argparse
import time
import os
import csv
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import glob

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage.clickhouse_store import ClickHouseStore

# 尝试导入 tqdm，如果没有则使用简单进度
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print('⚠ tqdm 未安装，将使用简单进度显示')
    print('  提示: pip install tqdm')


def find_kline_files(data_dir: str, pattern: str = '*.csv') -> List[str]:
    """查找K线数据文件"""
    if not os.path.exists(data_dir):
        print(f'✗ 数据目录不存在: {data_dir}')
        return []

    search_pattern = os.path.join(data_dir, pattern)
    files = glob.glob(search_pattern)

    print(f'✓ 找到 {len(files)} 个K线数据文件')
    return files


def extract_stock_code_from_filename(filename: str) -> str:
    """从文件名提取股票代码"""
    # 支持常见格式: SH600000.csv, 600000_daily.csv, etc.
    basename = os.path.basename(filename)
    name_without_ext = os.path.splitext(basename)[0]

    # 尝试匹配常见模式
    import re

    # 模式1: SH600000 或 SZ000001
    match = re.match(r'(SH|SZ)\d{6}', name_without_ext)
    if match:
        return match.group(0)

    # 模式2: 600000_daily 或 000001_kline
    match = re.match(r'(\d{6})', name_without_ext)
    if match:
        # 猜测市场 (6开头为上海，0/3开头为深圳)
        code = match.group(1)
        if code.startswith('6'):
            return f'SH{code}'
        elif code.startswith(('0', '3')):
            return f'SZ{code}'
        return code

    # 无法识别，返回文件名
    return name_without_ext


def read_kline_csv(csv_file: str, stock_code: str) -> List[Dict]:
    """
    读取K线 CSV 文件

    CSV 格式应包含列: date, open, high, low, close, volume, amount
    """
    klines = []
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # 标准化字段名
                    kline = {
                        'stock_code': stock_code,
                        'date': row.get('date') or row.get('日期') or row.get('交易日期'),
                        'open': float(row.get('open') or row.get('开盘') or row.get('开盘价') or 0),
                        'high': float(row.get('high') or row.get('最高') or row.get('最高价') or 0),
                        'low': float(row.get('low') or row.get('最低') or row.get('最低价') or 0),
                        'close': float(row.get('close') or row.get('收盘') or row.get('收盘价') or 0),
                        'volume': int(float(row.get('volume') or row.get('成交量') or row.get('量') or 0)),
                        'amount': float(row.get('amount') or row.get('成交额') or row.get('额') or 0)
                    }

                    # 验证必填字段
                    if not kline['date'] or kline['close'] == 0:
                        continue

                    klines.append(kline)

                except Exception:
                    continue

        return klines

    except Exception as e:
        print(f'  ✗ 读取文件失败 {csv_file}: {e}')
        return []


def migrate_kline_data(
    data_dir: str,
    pattern: str = '*.csv',
    batch_size: int = 10000
) -> Tuple[int, int, int, float]:
    """
    迁移K线数据

    Args:
        data_dir: 数据目录
        pattern: 文件匹配模式
        batch_size: 批处理大小

    Returns:
        (files_processed, success_rows, fail_rows, elapsed_time)
    """
    # 1. 查找文件
    print(f'\n{'='*60}')
    print(f'开始迁移K线数据')
    print(f'数据目录: {data_dir}')
    print(f'文件模式: {pattern}')
    print(f'批处理大小: {batch_size}')
    print(f'{'='*60}\n')

    files = find_kline_files(data_dir, pattern)

    if not files:
        print('✗ 没有找到K线数据文件')
        return 0, 0, 0, 0.0

    # 2. 连接 ClickHouse
    try:
        ch_store = ClickHouseStore()
        print(f'✓ ClickHouse 连接成功\n')
    except Exception as e:
        print(f'✗ ClickHouse 连接失败: {e}')
        return 0, 0, len(files), 0.0

    # 3. 逐文件迁移
    start_time = time.time()
    files_processed = 0
    total_success = 0
    total_fail = 0

    # 使用 tqdm 或简单进度
    file_iterator = tqdm(files, desc='迁移K线文件', unit='file') if HAS_TQDM else files

    try:
        for csv_file in file_iterator:
            # 提取股票代码
            stock_code = extract_stock_code_from_filename(csv_file)

            # 读取K线数据
            klines = read_kline_csv(csv_file, stock_code)

            if not klines:
                if not HAS_TQDM:
                    print(f'  ⚠ 跳过空文件: {os.path.basename(csv_file)}')
                continue

            # 批量插入
            success_count = 0
            for i in range(0, len(klines), batch_size):
                batch = klines[i:i + batch_size]

                try:
                    # 准备批量插入数据
                    insert_query = f"""
                        INSERT INTO {ch_store.database}.daily_kline
                        (date, stock_code, open, high, low, close, volume, amount)
                        VALUES
                    """

                    values = []
                    for kline in batch:
                        values.append((
                            kline['date'],
                            kline['stock_code'],
                            kline['open'],
                            kline['high'],
                            kline['low'],
                            kline['close'],
                            kline['volume'],
                            kline['amount']
                        ))

                    ch_store.client.execute(insert_query, values)
                    success_count += len(batch)

                except Exception as e:
                    if not HAS_TQDM:
                        print(f'  ✗ 批量插入失败: {e}')
                    total_fail += len(batch)

            total_success += success_count
            files_processed += 1

            if not HAS_TQDM:
                print(f'  ✓ {stock_code}: {success_count} 条记录 ({files_processed}/{len(files)})')

    finally:
        ch_store.close()

    elapsed_time = time.time() - start_time
    return files_processed, total_success, total_fail, elapsed_time


def print_migration_report(files: int, success: int, fail: int, elapsed: float):
    """打印迁移报告"""
    total_rows = success + fail
    success_rate = (success / total_rows * 100) if total_rows > 0 else 0
    throughput = (success / elapsed) if elapsed > 0 else 0

    print(f'\n{'='*60}')
    print(f'迁移完成')
    print(f'{'='*60}')
    print(f'处理文件数: {files}')
    print(f'总行数: {total_rows}')
    print(f'成功: {success} ({success_rate:.1f}%)')
    print(f'失败: {fail}')
    print(f'耗时: {elapsed:.2f}s')
    print(f'吞吐量: {throughput:.0f} 条/秒')
    print(f'{'='*60}\n')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='迁移K线数据从 CSV 到 ClickHouse'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data/stock_kline',
        help='K线数据目录 (默认: data/stock_kline)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.csv',
        help='文件匹配模式 (默认: *.csv)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10000,
        help='批处理大小 (默认: 10000)'
    )

    args = parser.parse_args()

    # 执行迁移
    files, success, fail, elapsed = migrate_kline_data(
        data_dir=args.data_dir,
        pattern=args.pattern,
        batch_size=args.batch_size
    )

    # 打印报告
    print_migration_report(files, success, fail, elapsed)

    # 返回退出码
    exit(0 if fail == 0 else 1)


if __name__ == '__main__':
    main()
