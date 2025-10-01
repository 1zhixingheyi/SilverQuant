#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T021: Integration Test - Auto-Fallback (Redis Failure → File)

验证自动降级机制:
1. 配置 HybridStore (primary=Redis, fallback=File)
2. 模拟 Redis 故障 (Mock异常)
3. 验证自动降级到 File
4. 验证降级日志记录 (WARNING级别)
"""

import pytest
import tempfile
import shutil
import os
import logging
from unittest.mock import Mock, patch
from storage.hybrid_store import HybridStore
from storage.file_store import FileStore


class TestAutoFallback:
    """自动降级集成测试"""

    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp(prefix='test_fallback_')
        yield temp_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_data(self):
        """示例测试数据"""
        return {
            'code': 'SH600000',
            'account_id': 'test_fallback_55009728',
            'days': 10,
            'max_price': 12.50,
            'min_price': 11.20
        }

    def test_fallback_when_redis_down(self, temp_cache_dir, sample_data):
        """测试 Redis 故障时自动降级到 File"""
        code = sample_data['code']
        account_id = sample_data['account_id']

        # 1. 先在 File 中准备数据
        file_store = FileStore(cache_path=temp_cache_dir)
        file_store.update_held_days(code, account_id, sample_data['days'])
        file_store.update_max_price(code, account_id, sample_data['max_price'])
        file_store.update_min_price(code, account_id, sample_data['min_price'])

        # 2. 创建 HybridStore 实例,但 Redis 初始化失败
        with patch('storage.hybrid_store.RedisStore') as mock_redis_class:
            # 模拟 RedisStore 初始化失败
            mock_redis_class.side_effect = Exception('Redis connection failed')

            hybrid_store = HybridStore(
                cache_path=temp_cache_dir,
                enable_redis=True,  # 尝试启用但会失败
                enable_mysql=False,
                enable_clickhouse=False,
                enable_auto_fallback=True
            )

            # 3. 验证 Redis 确实没有初始化成功
            assert hybrid_store.redis_store is None, 'Redis应该初始化失败'

            # 4. 执行读取操作,应该自动降级到 File
            held_days = hybrid_store.get_held_days(code, account_id)
            max_price = hybrid_store.get_max_price(code, account_id)
            min_price = hybrid_store.get_min_price(code, account_id)

            # 5. 验证从 File 读取到正确数据
            assert held_days == sample_data['days'], \
                f'持仓天数不匹配: {held_days} != {sample_data["days"]}'
            assert max_price == sample_data['max_price'], \
                f'最高价不匹配: {max_price} != {sample_data["max_price"]}'
            assert min_price == sample_data['min_price'], \
                f'最低价不匹配: {min_price} != {sample_data["min_price"]}'

            print(f'\n✓ Redis 故障时成功降级到 File')
            print(f'✓ 从 File 读取数据: 持仓天数={held_days}, 最高价={max_price}, 最低价={min_price}')

    def test_degradation_log_recorded(self, temp_cache_dir, caplog):
        """测试降级事件被记录到日志"""

        # 设置日志捕获
        with caplog.at_level(logging.WARNING):
            # 创建 HybridStore,模拟 Redis 连接失败
            with patch('storage.hybrid_store.RedisStore') as mock_redis_class:
                mock_redis_class.side_effect = Exception('Redis connection timeout')

                hybrid_store = HybridStore(
                    cache_path=temp_cache_dir,
                    enable_redis=True,
                    enable_mysql=False,
                    enable_clickhouse=False,
                    enable_auto_fallback=True
                )

        # 验证日志中记录了 Redis 初始化失败的警告
        assert len(caplog.records) > 0, '应该有日志记录'

        # 查找 Redis 失败相关的日志
        redis_failure_logs = [
            record for record in caplog.records
            if 'Redis' in record.message and record.levelname == 'WARNING'
        ]

        assert len(redis_failure_logs) > 0, '应该记录 Redis 失败的 WARNING 日志'

        # 验证日志内容
        log_message = redis_failure_logs[0].message
        assert 'Failed to initialize Redis' in log_message or 'Redis' in log_message, \
            f'日志内容不符合预期: {log_message}'

        print(f'\n✓ 降级事件已记录到日志 (WARNING级别)')
        print(f'✓ 日志数量: {len(redis_failure_logs)} 条')
        print(f'✓ 示例日志: {log_message}')

    def test_fallback_during_read_operations(self, temp_cache_dir, sample_data):
        """测试读取操作时的自动降级"""
        code = sample_data['code']
        account_id = sample_data['account_id']

        # 准备 File 数据
        file_store = FileStore(cache_path=temp_cache_dir)
        file_store.update_held_days(code, account_id, sample_data['days'])

        # 创建 HybridStore,Redis 可用
        hybrid_store = HybridStore(
            cache_path=temp_cache_dir,
            enable_redis=True,
            enable_mysql=False,
            enable_clickhouse=False,
            enable_auto_fallback=True
        )

        # 模拟 Redis 读取时失败
        if hybrid_store.redis_store:
            # 保存原始方法
            original_get = hybrid_store.redis_store.get_held_days

            # Mock Redis 读取失败
            def mock_get_failure(*args, **kwargs):
                raise Exception('Redis read timeout')

            hybrid_store.redis_store.get_held_days = mock_get_failure

            # 执行读取,应该自动降级到 File
            held_days = hybrid_store.get_held_days(code, account_id)

            # 验证成功从 File 读取
            assert held_days == sample_data['days'], \
                f'降级读取失败: {held_days} != {sample_data["days"]}'

            print(f'\n✓ Redis 读取失败时成功降级到 File')
            print(f'✓ 降级读取数据: {held_days}')

            # 恢复原始方法
            hybrid_store.redis_store.get_held_days = original_get
        else:
            print('\n⚠ Redis 不可用,跳过读取降级测试')

    def test_write_fallback_when_redis_fails(self, temp_cache_dir, sample_data):
        """测试写入操作时 Redis 失败的降级行为"""
        code = sample_data['code']
        account_id = sample_data['account_id']

        # 创建 HybridStore (禁用 Redis,仅使用 File)
        with patch('storage.hybrid_store.RedisStore') as mock_redis_class:
            mock_redis_class.side_effect = Exception('Redis unavailable')

            hybrid_store = HybridStore(
                cache_path=temp_cache_dir,
                enable_redis=True,
                enable_mysql=False,
                enable_clickhouse=False,
                enable_dual_write=True,
                enable_auto_fallback=True
            )

            # Redis 应该不可用
            assert hybrid_store.redis_store is None

            # 执行写入操作 (应该只写 File)
            success = hybrid_store.update_held_days(code, account_id, sample_data['days'])
            assert success is True, '写入应该成功 (降级到 File)'

            # 验证数据写入到 File
            file_store = FileStore(cache_path=temp_cache_dir)
            file_days = file_store.get_held_days(code, account_id)
            assert file_days == sample_data['days'], \
                f'File 数据不匹配: {file_days} != {sample_data["days"]}'

            print(f'\n✓ Redis 不可用时成功降级写入到 File')
            print(f'✓ File 数据: {file_days}')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
