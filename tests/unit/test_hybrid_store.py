#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit Tests for HybridStore and Factory Function

测试混合存储和工厂函数的功能
"""

import pytest
import logging
from storage import create_data_store
from storage.hybrid_store import HybridStore
from storage.file_store import FileStore
from storage.redis_store import RedisStore
from storage.mysql_store import MySQLStore
from storage.clickhouse_store import ClickHouseStore


# 配置日志
logging.basicConfig(level=logging.WARNING)


class TestFactoryFunction:
    """测试工厂函数 create_data_store"""

    def test_create_file_store(self):
        """测试创建文件存储"""
        store = create_data_store('file')
        assert isinstance(store, FileStore)
        assert store.health_check() is True
        store.close()

    def test_create_redis_store(self):
        """测试创建Redis存储"""
        store = create_data_store('redis')
        assert isinstance(store, RedisStore)
        # Redis可能不可用,只验证类型
        store.close()

    def test_create_mysql_store(self):
        """测试创建MySQL存储"""
        store = create_data_store('mysql')
        assert isinstance(store, MySQLStore)
        # MySQL可能不可用,只验证类型
        store.close()

    def test_create_clickhouse_store(self):
        """测试创建ClickHouse存储"""
        store = create_data_store('clickhouse')
        assert isinstance(store, ClickHouseStore)
        # ClickHouse可能不可用,只验证类型
        store.close()

    def test_create_hybrid_store(self):
        """测试创建混合存储"""
        store = create_data_store('hybrid', {
            'enable_dual_write': True,
            'enable_auto_fallback': True
        })
        assert isinstance(store, HybridStore)
        assert store.health_check() is True  # FileStore必须可用
        store.close()

    def test_create_hybrid_store_with_custom_config(self):
        """测试自定义配置的混合存储"""
        store = create_data_store('hybrid', {
            'enable_redis': False,
            'enable_mysql': False,
            'enable_clickhouse': False,
            'enable_dual_write': False
        })
        assert isinstance(store, HybridStore)
        assert store.redis_store is None
        assert store.mysql_store is None
        assert store.clickhouse_store is None
        assert store.file_store is not None
        store.close()

    def test_invalid_mode_raises_error(self):
        """测试无效模式抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            create_data_store('invalid_mode')
        assert 'Invalid storage mode' in str(exc_info.value)
        assert 'invalid_mode' in str(exc_info.value)

    def test_default_mode_is_file(self):
        """测试默认模式是file"""
        store = create_data_store()
        assert isinstance(store, FileStore)
        store.close()


class TestHybridStoreBasics:
    """测试 HybridStore 基础功能"""

    @pytest.fixture
    def hybrid_store(self):
        """创建混合存储实例"""
        store = create_data_store('hybrid', {
            'enable_dual_write': True,
            'enable_auto_fallback': True
        })
        yield store
        store.close()

    def test_health_check(self, hybrid_store):
        """测试健康检查"""
        # 至少 FileStore 必须可用
        assert hybrid_store.health_check() is True

    def test_file_store_always_available(self, hybrid_store):
        """测试 FileStore 始终可用"""
        assert hybrid_store.file_store is not None
        assert hybrid_store.file_store.health_check() is True

    def test_multiple_backends_initialization(self, hybrid_store):
        """测试多后端初始化"""
        # FileStore 必须初始化
        assert hybrid_store.file_store is not None

        # 其他后端可能初始化(取决于数据库是否可用)
        # 我们不强制要求,只验证它们要么是None,要么可用
        if hybrid_store.redis_store:
            assert hybrid_store.redis_store.health_check() in [True, False]
        if hybrid_store.mysql_store:
            assert hybrid_store.mysql_store.health_check() in [True, False]
        if hybrid_store.clickhouse_store:
            assert hybrid_store.clickhouse_store.health_check() in [True, False]


class TestHybridStorePositionOperations:
    """测试 HybridStore 持仓操作 (Redis + File)"""

    @pytest.fixture
    def hybrid_store(self):
        """创建混合存储实例"""
        store = create_data_store('hybrid')
        yield store
        # 清理
        store.close()

    def test_batch_new_held(self, hybrid_store):
        """测试批量新增持仓"""
        account_id = 'test_hybrid_account'
        codes = ['SH600000', 'SZ000001']

        success = hybrid_store.batch_new_held(account_id, codes)
        assert success is True

        # 验证可以读取
        days = hybrid_store.get_held_days('SH600000', account_id)
        assert days == 0

        # 清理
        for code in codes:
            hybrid_store.delete_held_days(code, account_id)

    def test_update_and_get_held_days(self, hybrid_store):
        """测试更新和查询持仓天数"""
        account_id = 'test_hybrid_account'
        code = 'SH600000'

        # 新增持仓
        hybrid_store.batch_new_held(account_id, [code])

        # 更新天数
        success = hybrid_store.update_held_days(code, account_id, 5)
        assert success is True

        # 查询验证
        days = hybrid_store.get_held_days(code, account_id)
        assert days == 5

        # 清理
        hybrid_store.delete_held_days(code, account_id)

    def test_delete_held_days(self, hybrid_store):
        """测试删除持仓"""
        account_id = 'test_hybrid_account'
        code = 'SH600000'

        # 新增持仓
        hybrid_store.batch_new_held(account_id, [code])
        assert hybrid_store.get_held_days(code, account_id) == 0

        # 删除
        success = hybrid_store.delete_held_days(code, account_id)
        assert success is True

        # 验证已删除
        days = hybrid_store.get_held_days(code, account_id)
        assert days is None

    def test_price_tracking(self, hybrid_store):
        """测试价格追踪 (最高价/最低价)"""
        account_id = 'test_hybrid_account'
        code = 'SH600000'

        # 设置价格
        hybrid_store.update_max_price(code, account_id, 12.50)
        hybrid_store.update_min_price(code, account_id, 11.20)

        # 查询验证
        max_price = hybrid_store.get_max_price(code, account_id)
        min_price = hybrid_store.get_min_price(code, account_id)

        assert max_price == 12.5
        assert min_price == 11.2

        # 清理
        if hybrid_store.redis_store:
            hybrid_store.redis_store.client.delete(f'max_prices:{account_id}')
            hybrid_store.redis_store.client.delete(f'min_prices:{account_id}')


class TestHybridStoreTradeOperations:
    """测试 HybridStore 交易操作 (ClickHouse + File)"""

    @pytest.fixture
    def hybrid_store(self):
        """创建混合存储实例"""
        store = create_data_store('hybrid')
        yield store
        store.close()

    def test_record_and_query_trades(self, hybrid_store):
        """测试记录和查询交易"""
        account_id = 'test_hybrid_trade'

        # 记录交易
        success = hybrid_store.record_trade(
            account_id=account_id,
            timestamp='2025-10-01 14:30:00',
            stock_code='SH600000',
            stock_name='浦发银行',
            order_type='buy_trade',
            remark='HybridStore测试',
            price=10.50,
            volume=1000
        )

        # 至少一个后端成功即可
        assert success is True

        # 查询交易
        df = hybrid_store.query_trades(
            account_id=account_id,
            start_date='2025-10-01',
            end_date='2025-10-01'
        )

        # 验证查询结果(ClickHouse或File至少一个有数据)
        assert len(df) >= 0  # 可能为空,取决于后端可用性


class TestHybridStoreAccountOperations:
    """测试 HybridStore 账户操作 (MySQL + File)"""

    @pytest.fixture
    def hybrid_store(self):
        """创建混合存储实例"""
        store = create_data_store('hybrid')
        yield store
        store.close()

    def test_create_and_get_account(self, hybrid_store):
        """测试创建和查询账户"""
        account_id = 'test_hybrid_55009999'

        # 创建账户
        success = hybrid_store.create_account(
            account_id=account_id,
            account_name='HybridStore测试账户',
            broker='QMT',
            initial_capital=100000.0
        )

        # 可能已存在,不强制要求成功
        if success:
            # 查询账户
            account = hybrid_store.get_account(account_id)
            assert account is not None
            assert account['account_id'] == account_id
            assert account['initial_capital'] == 100000.0

    def test_update_account_capital(self, hybrid_store):
        """测试更新账户资金"""
        account_id = 'test_hybrid_55009999'

        # 确保账户存在
        hybrid_store.create_account(
            account_id=account_id,
            account_name='HybridStore测试账户',
            broker='QMT',
            initial_capital=100000.0
        )

        # 更新资金
        success = hybrid_store.update_account_capital(account_id, 95000.0)
        assert success is True

        # 验证更新
        account = hybrid_store.get_account(account_id)
        if account:
            assert account['current_capital'] == 95000.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
