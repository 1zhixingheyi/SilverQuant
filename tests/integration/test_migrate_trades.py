#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T019: Integration Test - Migrate Trades (CSV → ClickHouse)

验证交易记录迁移流程:
1. 从 CSV 文件读取交易记录
2. 迁移到 ClickHouse
3. 验证行数匹配和数据完整性
"""

import pytest
import tempfile
import csv
import os
from datetime import datetime, timedelta
from storage.clickhouse_store import ClickHouseStore


class TestMigrateTrades:
    """交易记录迁移集成测试"""

    @pytest.fixture
    def temp_csv_file(self):
        """创建临时 CSV 文件"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.csv',
            encoding='utf-8',
            newline=''
        )
        temp_file.close()  # 关闭文件句柄以避免 Windows 文件锁问题
        yield temp_file.name
        # 清理临时文件
        try:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        except PermissionError:
            pass  # Windows 文件锁问题，忽略清理失败

    @pytest.fixture
    def sample_trade_records(self):
        """示例交易记录数据"""
        base_date = datetime(2024, 1, 1)
        return [
            {
                'date': (base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                'account_id': 'test_55009728',
                'code': f'SH60000{i % 10}',
                'direction': 'buy' if i % 2 == 0 else 'sell',
                'price': 10.0 + i * 0.5,
                'volume': 100 * (i + 1),
                'amount': (10.0 + i * 0.5) * 100 * (i + 1),
                'commission': 5.0 + i * 0.1
            }
            for i in range(20)
        ]

    def test_migrate_trades_to_clickhouse(self, temp_csv_file, sample_trade_records):
        """测试迁移交易记录到 ClickHouse"""
        account_id = 'test_migrate_55009728'

        # 1. 创建测试 CSV 文件
        with open(temp_csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['date', 'account_id', 'code', 'name', 'direction', 'price',
                         'volume', 'amount', 'remark']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # 转换为 CSV 格式
            for record in sample_trade_records:
                writer.writerow({
                    'date': record['date'],
                    'account_id': account_id,
                    'code': record['code'],
                    'name': '测试股票',
                    'direction': 'buy_trade' if record['direction'] == 'buy' else 'sell_trade',
                    'price': record['price'],
                    'volume': record['volume'],
                    'amount': record['amount'],
                    'remark': '迁移测试'
                })

        # 2. 读取 CSV 并迁移到 ClickHouse
        ch_store = ClickHouseStore()

        try:
            # 读取 CSV 文件
            with open(temp_csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                csv_records = list(reader)

            # 使用 record_trade() 逐条插入
            success_count = 0
            for record in csv_records:
                # 构造时间戳 (date + 默认时间)
                timestamp = f"{record['date']} 09:30:00"

                success = ch_store.record_trade(
                    account_id=record['account_id'],
                    timestamp=timestamp,
                    stock_code=record['code'],
                    stock_name=record['name'],
                    order_type=record['direction'],
                    remark=record['remark'],
                    price=float(record['price']),
                    volume=int(record['volume']),
                    strategy_name='test_migration'
                )

                if success:
                    success_count += 1

            assert success_count == len(csv_records), \
                f'插入失败: 成功 {success_count}/{len(csv_records)} 条'

            # 3. 验证行数匹配
            df = ch_store.query_trades(account_id=account_id)
            actual_count = len(df)

            assert actual_count == len(sample_trade_records), \
                f'行数不匹配: CSV有 {len(sample_trade_records)} 条, ClickHouse有 {actual_count} 条'

            # 4. 验证数据完整性 (检查几条关键记录)
            for i in [0, 5, 10]:
                expected = sample_trade_records[i]
                expected_date = expected['date']
                expected_code = expected['code']

                # 从查询结果中查找匹配记录
                matched = df[
                    (df['date'].astype(str) == expected_date) &
                    (df['stock_code'] == expected_code)
                ]

                assert len(matched) > 0, f'未找到记录: {expected_code} on {expected_date}'

                record = matched.iloc[0]
                assert abs(record['price'] - float(expected['price'])) < 0.01, \
                    f'价格不匹配: {record["price"]} != {expected["price"]}'
                assert record['volume'] == int(expected['volume']), \
                    f'数量不匹配: {record["volume"]} != {expected["volume"]}'

            print(f'\n✓ 成功迁移 {len(sample_trade_records)} 条交易记录到 ClickHouse')
            print(f'✓ 数据完整性验证通过')

        finally:
            # 清理测试数据
            try:
                ch_store.client.execute(
                    f"ALTER TABLE {ch_store.database}.trade DELETE WHERE account_id = '{account_id}'"
                )
            except Exception as e:
                print(f'清理测试数据失败: {e}')
            ch_store.close()

    def test_verify_trade_row_count(self, temp_csv_file):
        """测试迁移后行数验证和查询功能"""
        account_id = 'test_count_55009728'

        # 准备少量测试数据
        test_records = [
            {
                'timestamp': '2024-01-01 09:30:00',
                'code': 'SH600000',
                'name': '浦发银行',
                'direction': 'buy_trade',
                'price': 10.0,
                'volume': 100
            },
            {
                'timestamp': '2024-01-02 10:00:00',
                'code': 'SZ000001',
                'name': '平安银行',
                'direction': 'sell_trade',
                'price': 15.0,
                'volume': 200
            },
            {
                'timestamp': '2024-01-03 14:30:00',
                'code': 'SH600000',
                'name': '浦发银行',
                'direction': 'sell_trade',
                'price': 11.0,
                'volume': 100
            }
        ]

        ch_store = ClickHouseStore()

        try:
            # 插入测试数据
            success_count = 0
            for record in test_records:
                success = ch_store.record_trade(
                    account_id=account_id,
                    timestamp=record['timestamp'],
                    stock_code=record['code'],
                    stock_name=record['name'],
                    order_type=record['direction'],
                    remark='row count test',
                    price=record['price'],
                    volume=record['volume'],
                    strategy_name='test'
                )
                if success:
                    success_count += 1

            assert success_count == 3, f'插入失败: {success_count}/3'

            # 验证总行数
            df = ch_store.query_trades(account_id=account_id)
            total_count = len(df)
            assert total_count == 3, f'总行数不匹配: {total_count} != 3'

            # 验证按代码分组的行数
            code_counts = df['stock_code'].value_counts().sort_index()
            assert len(code_counts) == 2, '应该有2个不同的股票代码'
            assert code_counts['SH600000'] == 2, f'SH600000 数量错误: {code_counts.get("SH600000")}'
            assert code_counts['SZ000001'] == 1, f'SZ000001 数量错误: {code_counts.get("SZ000001")}'

            # 验证日期范围
            df['date'] = df['date'].astype(str)
            min_date = df['date'].min()
            max_date = df['date'].max()
            assert min_date == '2024-01-01', f'最小日期错误: {min_date}'
            assert max_date == '2024-01-03', f'最大日期错误: {max_date}'

            print(f'\n✓ 行数验证通过: 共 {total_count} 条记录')
            print(f'✓ 分组查询验证通过')
            print(f'✓ 日期范围查询验证通过')

        finally:
            # 清理测试数据
            try:
                ch_store.client.execute(
                    f"ALTER TABLE {ch_store.database}.trade DELETE WHERE account_id = '{account_id}'"
                )
            except Exception as e:
                print(f'清理测试数据失败: {e}')
            ch_store.close()

    def test_batch_insertion_performance(self):
        """测试批量插入性能"""
        import time

        account_id = 'test_perf_55009728'

        # 生成大量测试数据 (100 条记录 - ClickHouse 单条插入较慢)
        large_records = []
        base_date = datetime(2024, 1, 1)
        for i in range(100):
            date = base_date + timedelta(days=i % 30)
            large_records.append({
                'timestamp': f'{date.strftime("%Y-%m-%d")} 09:30:{i % 60:02d}',
                'code': f'SH{600000 + i % 50:06d}',
                'name': f'测试股票{i % 50}',
                'direction': 'buy_trade' if i % 2 == 0 else 'sell_trade',
                'price': 10.0 + (i % 100) * 0.5,
                'volume': 100 * ((i % 10) + 1)
            })

        ch_store = ClickHouseStore()

        try:
            # 测量插入时间
            start_time = time.time()

            success_count = 0
            for record in large_records:
                success = ch_store.record_trade(
                    account_id=account_id,
                    timestamp=record['timestamp'],
                    stock_code=record['code'],
                    stock_name=record['name'],
                    order_type=record['direction'],
                    remark='performance test',
                    price=record['price'],
                    volume=record['volume'],
                    strategy_name='perf_test'
                )
                if success:
                    success_count += 1

            elapsed_time = time.time() - start_time

            assert success_count == len(large_records), \
                f'插入失败: {success_count}/{len(large_records)}'

            # 验证插入数量
            df = ch_store.query_trades(account_id=account_id)
            actual_count = len(df)
            assert actual_count == len(large_records), \
                f'插入数量不匹配: {actual_count} != {len(large_records)}'

            print(f'\n✓ 批量插入 {len(large_records)} 条记录')
            print(f'✓ 耗时: {elapsed_time:.3f}s')
            print(f'✓ 平均速率: {len(large_records) / elapsed_time:.0f} 条/秒')

            # 性能断言: 100条记录应在6秒内完成 (ClickHouse 单条插入较慢,考虑性能波动)
            assert elapsed_time < 6.0, f'批量插入性能不达标: {elapsed_time:.3f}s > 6.0s'

        finally:
            # 清理测试数据
            try:
                ch_store.client.execute(
                    f"ALTER TABLE {ch_store.database}.trade DELETE WHERE account_id = '{account_id}'"
                )
            except Exception as e:
                print(f'清理测试数据失败: {e}')
            ch_store.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
