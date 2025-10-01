#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T011: Contract Test - Price Tracking Methods

验证价格追踪相关方法:
- get_max_price()
- update_max_price()
- get_min_price()
- update_min_price()
"""

import pytest
import tempfile
import os
import shutil
from storage.file_store import FileStore


class ContractTestPriceTracking:
    """契约测试:价格追踪方法"""

    @pytest.fixture
    def store(self):
        raise NotImplementedError("子类必须实现 store fixture")

    def test_get_max_price_not_exists(self, store):
        """测试查询不存在的最高价应返回 None"""
        result = store.get_max_price('600000.SH', 'test_account')
        assert result is None

    def test_update_and_get_max_price(self, store):
        """测试更新并查询最高价"""
        code = '600000.SH'
        account_id = 'test_account'
        price = 15.68

        success = store.update_max_price(code, account_id, price)
        assert success is True

        result = store.get_max_price(code, account_id)
        assert result == price

    def test_get_min_price_not_exists(self, store):
        """测试查询不存在的最低价应返回 None"""
        result = store.get_min_price('600000.SH', 'test_account')
        assert result is None

    def test_update_and_get_min_price(self, store):
        """测试更新并查询最低价"""
        code = '600000.SH'
        account_id = 'test_account'
        price = 12.35

        success = store.update_min_price(code, account_id, price)
        assert success is True

        result = store.get_min_price(code, account_id)
        assert result == price

    def test_max_min_price_independence(self, store):
        """测试最高价和最低价独立存储"""
        code = '600000.SH'
        account_id = 'test_account'
        max_price = 18.50
        min_price = 10.20

        store.update_max_price(code, account_id, max_price)
        store.update_min_price(code, account_id, min_price)

        assert store.get_max_price(code, account_id) == max_price
        assert store.get_min_price(code, account_id) == min_price

    def test_price_precision(self, store):
        """测试价格精度(保留3位小数)"""
        code = '600000.SH'
        account_id = 'test_account'
        price = 15.678

        store.update_max_price(code, account_id, price)
        result = store.get_max_price(code, account_id)

        # 允许浮点数误差
        assert abs(result - price) < 0.001, f"价格精度不符,期望 {price},实际 {result}"

    def test_multiple_stocks_prices(self, store):
        """测试多只股票的价格跟踪"""
        account_id = 'test_account'
        stocks = {
            '600000.SH': {'max': 18.5, 'min': 10.2},
            '000001.SZ': {'max': 25.3, 'min': 20.1},
            '600519.SH': {'max': 1680.0, 'min': 1500.5}
        }

        # 批量更新
        for code, prices in stocks.items():
            store.update_max_price(code, account_id, prices['max'])
            store.update_min_price(code, account_id, prices['min'])

        # 批量验证
        for code, prices in stocks.items():
            assert store.get_max_price(code, account_id) == prices['max']
            assert store.get_min_price(code, account_id) == prices['min']


class TestFileStorePriceTracking(ContractTestPriceTracking):
    """FileStore 实现的契约测试"""

    @pytest.fixture
    def store(self):
        temp_dir = tempfile.mkdtemp(prefix='test_contract_filestore_price_')
        store = FileStore(cache_path=temp_dir)
        yield store
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
