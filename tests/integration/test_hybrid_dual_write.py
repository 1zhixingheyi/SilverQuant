#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T020: Integration Test - Hybrid Mode Dual-Write

验证混合模式双写功能:
1. 配置 HybridStore (Redis + File 双写)
2. 执行写入操作
3. 验证数据同时存在于 Redis 和 File
"""

import pytest
import tempfile
import shutil
import os
from storage.hybrid_store import HybridStore
from storage.redis_store import RedisStore
from storage.file_store import FileStore


class TestHybridDualWrite:
    """混合模式双写集成测试"""

    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp(prefix='test_hybrid_')
        yield temp_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_position_data(self):
        """示例持仓数据"""
        return {
            'SH600000': {'days': 5, 'max_price': 12.50, 'min_price': 11.20},
            'SZ000001': {'days': 3, 'max_price': 15.30, 'min_price': 14.50},
            'SH600519': {'days': 10, 'max_price': 1850.00, 'min_price': 1780.00}
        }

    def test_dual_write_to_redis_and_file(self, temp_cache_dir, sample_position_data):
        """测试双写到 Redis 和 File"""
        account_id = 'test_dual_55009728'

        # 1. 创建 HybridStore 实例 (启用双写)
        hybrid_store = HybridStore(
            cache_path=temp_cache_dir,
            enable_redis=True,
            enable_mysql=False,
            enable_clickhouse=False,
            enable_dual_write=True,
            enable_auto_fallback=False
        )

        # 创建独立的 Redis 和 File 实例用于验证
        redis_store = RedisStore()
        file_store = FileStore(cache_path=temp_cache_dir)

        try:
            # 2. 使用 HybridStore 写入数据
            for code, data in sample_position_data.items():
                # 写入持仓天数
                success = hybrid_store.update_held_days(code, account_id, data['days'])
                assert success is True, f'{code} 持仓天数写入失败'

                # 写入最高价
                success = hybrid_store.update_max_price(code, account_id, data['max_price'])
                assert success is True, f'{code} 最高价写入失败'

                # 写入最低价
                success = hybrid_store.update_min_price(code, account_id, data['min_price'])
                assert success is True, f'{code} 最低价写入失败'

            # 3. 验证数据同时存在于 Redis 和 File
            inconsistent_records = []

            for code, expected_data in sample_position_data.items():
                # 从 Redis 读取
                redis_days = redis_store.get_held_days(code, account_id)
                redis_max = redis_store.get_max_price(code, account_id)
                redis_min = redis_store.get_min_price(code, account_id)

                # 从 File 读取
                file_days = file_store.get_held_days(code, account_id)
                file_max = file_store.get_max_price(code, account_id)
                file_min = file_store.get_min_price(code, account_id)

                # 验证一致性
                if redis_days != expected_data['days']:
                    inconsistent_records.append(f'{code} Redis持仓天数不一致')
                if file_days != expected_data['days']:
                    inconsistent_records.append(f'{code} File持仓天数不一致')

                if redis_max != expected_data['max_price']:
                    inconsistent_records.append(f'{code} Redis最高价不一致')
                if file_max != expected_data['max_price']:
                    inconsistent_records.append(f'{code} File最高价不一致')

                if redis_min != expected_data['min_price']:
                    inconsistent_records.append(f'{code} Redis最低价不一致')
                if file_min != expected_data['min_price']:
                    inconsistent_records.append(f'{code} File最低价不一致')

            # 断言所有数据一致
            assert len(inconsistent_records) == 0, \
                f'发现 {len(inconsistent_records)} 条不一致记录:\n' + '\n'.join(inconsistent_records)

            print(f'\n✓ 双写验证通过: {len(sample_position_data)} 只股票的所有数据同时存在于 Redis 和 File')
            print(f'✓ Redis 和 File 数据完全一致')

        finally:
            # 清理 Redis 测试数据
            redis_store.client.delete(f'held_days:{account_id}')
            redis_store.client.delete(f'max_prices:{account_id}')
            redis_store.client.delete(f'min_prices:{account_id}')
            redis_store.close()

    def test_dual_write_transaction_consistency(self, temp_cache_dir):
        """测试双写事务一致性"""
        account_id = 'test_consistency_55009728'

        # 创建 HybridStore 实例
        hybrid_store = HybridStore(
            cache_path=temp_cache_dir,
            enable_redis=True,
            enable_mysql=False,
            enable_clickhouse=False,
            enable_dual_write=True,
            enable_auto_fallback=False
        )

        redis_store = RedisStore()
        file_store = FileStore(cache_path=temp_cache_dir)

        try:
            # 测试场景: 多次更新同一个股票,验证最终一致性
            code = 'SH600000'
            updates = [
                {'days': 1, 'max_price': 10.0, 'min_price': 9.5},
                {'days': 2, 'max_price': 10.5, 'min_price': 9.5},
                {'days': 3, 'max_price': 11.0, 'min_price': 9.5},
                {'days': 4, 'max_price': 11.5, 'min_price': 9.0},
                {'days': 5, 'max_price': 12.0, 'min_price': 9.0}
            ]

            for update in updates:
                hybrid_store.update_held_days(code, account_id, update['days'])
                hybrid_store.update_max_price(code, account_id, update['max_price'])
                hybrid_store.update_min_price(code, account_id, update['min_price'])

            # 验证最终状态一致
            expected = updates[-1]
            redis_days = redis_store.get_held_days(code, account_id)
            file_days = file_store.get_held_days(code, account_id)

            redis_max = redis_store.get_max_price(code, account_id)
            file_max = file_store.get_max_price(code, account_id)

            redis_min = redis_store.get_min_price(code, account_id)
            file_min = file_store.get_min_price(code, account_id)

            # 断言
            assert redis_days == expected['days'] and file_days == expected['days'], \
                f'持仓天数不一致: Redis={redis_days}, File={file_days}, Expected={expected["days"]}'

            assert redis_max == expected['max_price'] and file_max == expected['max_price'], \
                f'最高价不一致: Redis={redis_max}, File={file_max}, Expected={expected["max_price"]}'

            assert redis_min == expected['min_price'] and file_min == expected['min_price'], \
                f'最低价不一致: Redis={redis_min}, File={file_min}, Expected={expected["min_price"]}'

            print(f'\n✓ 事务一致性验证通过')
            print(f'✓ 经过 {len(updates)} 次更新后,Redis 和 File 数据完全一致')
            print(f'✓ 最终状态: 持仓天数={expected["days"]}, 最高价={expected["max_price"]}, 最低价={expected["min_price"]}')

        finally:
            # 清理测试数据
            redis_store.client.delete(f'held_days:{account_id}')
            redis_store.client.delete(f'max_prices:{account_id}')
            redis_store.client.delete(f'min_prices:{account_id}')
            redis_store.close()

    def test_dual_write_batch_operations(self, temp_cache_dir):
        """测试批量操作的双写一致性"""
        account_id = 'test_batch_55009728'

        # 确保测试目录干净
        held_file = os.path.join(temp_cache_dir, 'held_days.json')
        if os.path.exists(held_file):
            os.remove(held_file)

        hybrid_store = HybridStore(
            cache_path=temp_cache_dir,
            enable_redis=True,
            enable_mysql=False,
            enable_clickhouse=False,
            enable_dual_write=True,
            enable_auto_fallback=False
        )

        redis_store = RedisStore()
        file_store = FileStore(cache_path=temp_cache_dir)

        try:
            # 测试1: 批量新增持仓
            codes = ['SH600000', 'SZ000001', 'SH600519', 'SZ000002', 'SH601318']
            success = hybrid_store.batch_new_held(account_id, codes)
            assert success is True, '批量新增失败'

            # 验证所有股票都在 Redis 和 File 中 (初始天数为0)
            for code in codes:
                redis_days = redis_store.get_held_days(code, account_id)
                file_days = file_store.get_held_days(code, account_id)

                assert redis_days == 0, f'{code} Redis初始天数应为0, 实际为 {redis_days}'
                assert file_days == 0, f'{code} File初始天数应为0, 实际为 {file_days}'

            print(f'\n✓ 批量新增验证通过: {len(codes)} 只股票在 Redis 和 File 中都初始化为0')

            # 测试2: 单独更新每只股票的持仓天数 (避免 all_held_inc 的日期标记位问题)
            for i, code in enumerate(codes):
                days = i + 1  # 设置不同的天数
                success = hybrid_store.update_held_days(code, account_id, days)
                assert success is True, f'{code} 更新持仓天数失败'

            # 验证双写一致性
            for i, code in enumerate(codes):
                expected_days = i + 1
                redis_days = redis_store.get_held_days(code, account_id)
                file_days = file_store.get_held_days(code, account_id)

                assert redis_days == expected_days, \
                    f'{code} Redis天数不一致: 期望{expected_days}, 实际{redis_days}'
                assert file_days == expected_days, \
                    f'{code} File天数不一致: 期望{expected_days}, 实际{file_days}'

            print(f'✓ 批量更新验证通过: 所有股票在 Redis 和 File 中数据完全一致')
            print(f'✓ {len(codes)} 只股票的批量新增和更新操作双写成功')

        finally:
            # 清理测试数据
            redis_store.client.delete(f'held_days:{account_id}')
            redis_store.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
