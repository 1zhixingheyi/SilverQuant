#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T018: Integration Test - Migrate Positions (File → Redis)

验证持仓数据迁移流程:
1. 从 held_days.json 读取持仓数据
2. 迁移到 Redis
3. 验证数据一致性 (数量、值都匹配)
"""

import pytest
import tempfile
import shutil
import os
import json
from storage.file_store import FileStore
from storage.redis_store import RedisStore


class TestMigratePositions:
    """持仓数据迁移集成测试"""

    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp(prefix='test_migrate_')
        yield temp_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_held_data(self):
        """示例持仓数据"""
        return {
            'SH600000': 5,
            'SZ000001': 3,
            'SH600519': 10,
            'SZ000002': 1,
            'SH601318': 7
        }

    @pytest.fixture
    def sample_price_data(self):
        """示例价格数据"""
        return {
            'max_prices': {
                'SH600000': 12.50,
                'SZ000001': 15.30,
                'SH600519': 1850.00
            },
            'min_prices': {
                'SH600000': 11.20,
                'SZ000001': 14.50,
                'SH600519': 1780.00
            }
        }

    def test_migrate_held_days_to_redis(self, temp_cache_dir, sample_held_data, sample_price_data):
        """测试迁移持仓天数到 Redis"""
        account_id = 'test_migrate_55009728'

        # 1. 准备文件存储的测试数据
        file_store = FileStore(cache_path=temp_cache_dir)

        # 写入持仓天数
        held_path = os.path.join(temp_cache_dir, 'held_days.json')
        with open(held_path, 'w') as f:
            json.dump(sample_held_data, f)

        # 写入价格数据
        max_price_path = os.path.join(temp_cache_dir, 'max_prices.json')
        min_price_path = os.path.join(temp_cache_dir, 'min_prices.json')
        with open(max_price_path, 'w') as f:
            json.dump(sample_price_data['max_prices'], f)
        with open(min_price_path, 'w') as f:
            json.dump(sample_price_data['min_prices'], f)

        # 2. 从文件读取并迁移到 Redis
        redis_store = RedisStore()

        try:
            # 读取文件数据
            held_data = json.load(open(held_path))
            max_prices = json.load(open(max_price_path))
            min_prices = json.load(open(min_price_path))

            # 迁移持仓天数
            for code, days in held_data.items():
                success = redis_store.update_held_days(code, account_id, days)
                assert success is True, f'迁移 {code} 失败'

            # 迁移价格数据
            for code, price in max_prices.items():
                redis_store.update_max_price(code, account_id, price)
            for code, price in min_prices.items():
                redis_store.update_min_price(code, account_id, price)

            # 3. 验证数据一致性
            for code, expected_days in sample_held_data.items():
                actual_days = redis_store.get_held_days(code, account_id)
                assert actual_days == expected_days, \
                    f'{code} 持仓天数不一致: 期望 {expected_days}, 实际 {actual_days}'

            for code, expected_price in sample_price_data['max_prices'].items():
                actual_price = redis_store.get_max_price(code, account_id)
                assert actual_price == expected_price, \
                    f'{code} 最高价不一致: 期望 {expected_price}, 实际 {actual_price}'

            for code, expected_price in sample_price_data['min_prices'].items():
                actual_price = redis_store.get_min_price(code, account_id)
                assert actual_price == expected_price, \
                    f'{code} 最低价不一致: 期望 {expected_price}, 实际 {actual_price}'

            print(f'\n✓ 成功迁移 {len(held_data)} 条持仓记录')
            print(f'✓ 成功迁移 {len(max_prices)} 条最高价记录')
            print(f'✓ 成功迁移 {len(min_prices)} 条最低价记录')

        finally:
            # 清理 Redis 测试数据
            redis_store.client.delete(f'held_days:{account_id}')
            redis_store.client.delete(f'max_prices:{account_id}')
            redis_store.client.delete(f'min_prices:{account_id}')
            redis_store.close()

    def test_verify_position_consistency(self, temp_cache_dir, sample_held_data):
        """测试迁移后数据一致性验证"""
        account_id = 'test_consistency_55009728'

        # 1. 准备双份数据 (File + Redis)
        file_store = FileStore(cache_path=temp_cache_dir)
        redis_store = RedisStore()

        try:
            # 写入测试数据到 File
            held_path = os.path.join(temp_cache_dir, 'held_days.json')
            with open(held_path, 'w') as f:
                json.dump(sample_held_data, f)

            # 写入测试数据到 Redis
            for code, days in sample_held_data.items():
                redis_store.update_held_days(code, account_id, days)

            # 2. 验证一致性
            inconsistent_records = []
            for code in sample_held_data.keys():
                file_days = file_store.get_held_days(code, account_id)
                redis_days = redis_store.get_held_days(code, account_id)

                if file_days != redis_days:
                    inconsistent_records.append({
                        'code': code,
                        'file': file_days,
                        'redis': redis_days
                    })

            # 3. 断言一致性
            assert len(inconsistent_records) == 0, \
                f'发现 {len(inconsistent_records)} 条不一致记录: {inconsistent_records}'

            print(f'\n✓ 验证通过: {len(sample_held_data)} 条记录完全一致')

        finally:
            # 清理
            redis_store.client.delete(f'held_days:{account_id}')
            redis_store.close()

    def test_batch_migration_performance(self, temp_cache_dir):
        """测试批量迁移性能"""
        import time

        account_id = 'test_perf_55009728'

        # 生成大量测试数据 (100 条记录)
        large_held_data = {
            f'SH{600000 + i:06d}': i % 30 for i in range(100)
        }

        # 准备文件数据
        held_path = os.path.join(temp_cache_dir, 'held_days.json')
        with open(held_path, 'w') as f:
            json.dump(large_held_data, f)

        redis_store = RedisStore()

        try:
            # 测量迁移时间
            start_time = time.time()

            # 使用 Pipeline 批量写入
            pipeline = redis_store.client.pipeline()
            for code, days in large_held_data.items():
                pipeline.hset(f'held_days:{account_id}', code, days)
            pipeline.execute()

            elapsed_time = time.time() - start_time

            # 验证迁移完成
            migrated_count = redis_store.client.hlen(f'held_days:{account_id}')
            assert migrated_count == len(large_held_data), \
                f'迁移数量不匹配: 期望 {len(large_held_data)}, 实际 {migrated_count}'

            print(f'\n✓ 批量迁移 {len(large_held_data)} 条记录')
            print(f'✓ 耗时: {elapsed_time:.3f}s')
            print(f'✓ 平均速率: {len(large_held_data) / elapsed_time:.0f} 条/秒')

            # 性能断言: 100条记录应在1秒内完成
            assert elapsed_time < 1.0, f'批量迁移性能不达标: {elapsed_time:.3f}s > 1.0s'

        finally:
            # 清理
            redis_store.client.delete(f'held_days:{account_id}')
            redis_store.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
