#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FileStore 单元测试
"""

import os
import shutil
import tempfile
import datetime
import pytest
import pandas as pd

from storage.file_store import FileStore


class TestFileStore:
    """FileStore 测试套件"""

    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp(prefix='test_filestore_')
        yield temp_dir
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def store(self, temp_cache_dir):
        """创建 FileStore 实例"""
        return FileStore(cache_path=temp_cache_dir)

    # ==================== 持仓状态测试 ====================

    def test_held_days_crud(self, store):
        """测试持仓天数的增删改查"""
        account_id = 'test_account'
        code = '600000.SH'

        # 初始查询应返回 None
        assert store.get_held_days(code, account_id) is None

        # 更新持仓天数
        assert store.update_held_days(code, account_id, 5) is True
        assert store.get_held_days(code, account_id) == 5

        # 更新为新值
        assert store.update_held_days(code, account_id, 10) is True
        assert store.get_held_days(code, account_id) == 10

        # 删除持仓
        assert store.delete_held_days(code, account_id) is True
        assert store.get_held_days(code, account_id) is None

    def test_batch_new_held(self, store):
        """测试批量新增持仓"""
        account_id = 'test_account'
        codes = ['600000.SH', '000001.SZ', '600519.SH']

        assert store.batch_new_held(account_id, codes) is True

        # 验证所有持仓天数为 0
        for code in codes:
            assert store.get_held_days(code, account_id) == 0

    def test_all_held_inc(self, store):
        """测试持仓天数全局递增"""
        account_id = 'test_account'
        codes = ['600000.SH', '000001.SZ']

        # 初始化持仓
        store.batch_new_held(account_id, codes)

        # 第一次递增应成功
        assert store.all_held_inc(account_id) is True
        assert store.get_held_days('600000.SH', account_id) == 1
        assert store.get_held_days('000001.SZ', account_id) == 1

        # 同一天再次递增应跳过
        assert store.all_held_inc(account_id) is False
        assert store.get_held_days('600000.SH', account_id) == 1  # 未变化

    def test_max_min_price(self, store):
        """测试最高价/最低价管理"""
        account_id = 'test_account'
        code = '600000.SH'

        # 初始查询返回 None
        assert store.get_max_price(code, account_id) is None
        assert store.get_min_price(code, account_id) is None

        # 更新最高价
        assert store.update_max_price(code, account_id, 15.68) is True
        assert store.get_max_price(code, account_id) == 15.68

        # 更新最低价
        assert store.update_min_price(code, account_id, 12.35) is True
        assert store.get_min_price(code, account_id) == 12.35

    # ==================== 交易记录测试 ====================

    def test_record_trade(self, store):
        """测试交易记录"""
        account_id = 'test_account'
        timestamp = str(int(datetime.datetime.now().timestamp()))

        assert store.record_trade(
            account_id=account_id,
            timestamp=timestamp,
            stock_code='600000.SH',
            stock_name='浦发银行',
            order_type='buy',
            remark='开仓',
            price=10.50,
            volume=1000,
            strategy_name='test_strategy'
        ) is True

        # 验证文件已创建
        assert os.path.exists(store.path_trades)

    def test_query_trades(self, store):
        """测试交易查询"""
        account_id = 'test_account'
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        timestamp = str(int(datetime.datetime.now().timestamp()))

        # 记录多笔交易
        store.record_trade(account_id, timestamp, '600000.SH', '浦发银行', 'buy', '开仓', 10.50, 1000)
        store.record_trade(account_id, timestamp, '000001.SZ', '平安银行', 'buy', '开仓', 12.30, 500)

        # 查询所有交易
        df = store.query_trades(account_id)
        assert len(df) == 2
        assert '600000.SH' in df['代码'].values
        assert '000001.SZ' in df['代码'].values

        # 按股票代码过滤
        df_filtered = store.query_trades(account_id, stock_code='600000.SH')
        assert len(df_filtered) == 1
        assert df_filtered.iloc[0]['代码'] == '600000.SH'

    def test_aggregate_trades(self, store):
        """测试交易聚合统计"""
        account_id = 'test_account'
        timestamp = str(int(datetime.datetime.now().timestamp()))
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        # 记录多笔交易
        store.record_trade(account_id, timestamp, '600000.SH', '浦发银行', 'buy', '开仓', 10.0, 1000)
        store.record_trade(account_id, timestamp, '600000.SH', '浦发银行', 'buy', '加仓', 11.0, 500)
        store.record_trade(account_id, timestamp, '000001.SZ', '平安银行', 'buy', '开仓', 12.0, 300)

        # 按股票聚合
        df_by_stock = store.aggregate_trades(account_id, today, today, group_by='stock')
        assert len(df_by_stock) == 2

        row_600000 = df_by_stock[df_by_stock['代码'] == '600000.SH'].iloc[0]
        assert row_600000['成交量'] == 1500  # 1000 + 500
        assert row_600000['成交金额'] == 15500  # 10*1000 + 11*500

    # ==================== K线数据测试 ====================

    def test_kline_operations(self, store):
        """测试 K线操作 (文件存储不支持,应返回空)"""
        df = store.get_kline('600000.SH', '2024-01-01', '2024-01-31')
        assert df.empty

        result = store.batch_get_kline(['600000.SH', '000001.SZ'], '2024-01-01', '2024-01-31')
        assert result == {}

    # ==================== 账户管理测试 ====================

    def test_account_management(self, store):
        """测试账户管理"""
        account_id = 'test_account_001'

        # 创建账户
        assert store.create_account(
            account_id=account_id,
            account_name='测试账户',
            broker='QMT',
            initial_capital=100000.0
        ) is True

        # 查询账户
        account = store.get_account(account_id)
        assert account is not None
        assert account['account_name'] == '测试账户'
        assert account['broker'] == 'QMT'
        assert account['initial_capital'] == 100000.0
        assert account['current_capital'] == 100000.0

        # 更新资金
        assert store.update_account_capital(account_id, 105000.0) is True
        account = store.get_account(account_id)
        assert account['current_capital'] == 105000.0

        # 重复创建应失败
        assert store.create_account(account_id, '重复账户', 'GM', 50000.0) is False

    # ==================== 策略管理测试 ====================

    def test_strategy_management(self, store):
        """测试策略管理"""
        strategy_code = 'test_strategy_001'

        # 创建策略
        assert store.create_strategy(
            strategy_name='测试策略',
            strategy_code=strategy_code,
            strategy_type='wencai',
            version='1.0.0'
        ) is True

        # 查询参数 (初始为空)
        params = store.get_strategy_params(strategy_code)
        assert params == {}

        # 保存参数
        new_params = {'threshold': 0.05, 'period': 20}
        assert store.save_strategy_params(strategy_code, new_params) is True

        # 验证参数
        params = store.get_strategy_params(strategy_code)
        assert params == new_params

        # 重复创建应失败
        assert store.create_strategy('重复策略', strategy_code, 'remote', '2.0.0') is False

    def test_compare_strategy_params(self, store):
        """测试策略参数比较"""
        strategy_code = 'test_strategy_002'

        # 创建策略并设置初始参数
        store.create_strategy('对比测试策略', strategy_code, 'technical', '1.0.0')
        old_params = {'threshold': 0.05, 'period': 20, 'ma_type': 'EMA'}
        store.save_strategy_params(strategy_code, old_params)

        # 新参数
        new_params = {'threshold': 0.08, 'period': 20, 'stop_loss': 0.03}

        # 比较差异
        added, modified, deleted = store.compare_strategy_params(strategy_code, new_params)

        assert added == {'stop_loss': 0.03}
        assert modified == {'threshold': (0.05, 0.08)}
        assert deleted == {'ma_type': 'EMA'}

    # ==================== 连接管理测试 ====================

    def test_health_check(self, store):
        """测试健康检查"""
        assert store.health_check() is True

    def test_close(self, store):
        """测试关闭连接 (无操作)"""
        store.close()  # 不应抛出异常


# ==================== 集成测试场景 ====================

class TestFileStoreIntegration:
    """FileStore 集成测试"""

    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp(prefix='test_filestore_integration_')
        yield temp_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def store(self, temp_cache_dir):
        """创建 FileStore 实例"""
        return FileStore(cache_path=temp_cache_dir)

    def test_complete_trading_flow(self, store):
        """测试完整交易流程"""
        account_id = 'integration_account'
        code = '600000.SH'
        timestamp = str(int(datetime.datetime.now().timestamp()))

        # 1. 创建账户
        store.create_account(account_id, '集成测试账户', 'QMT', 100000.0)

        # 2. 创建策略
        store.create_strategy('集成测试策略', 'integration_strategy', 'wencai', '1.0.0')
        store.save_strategy_params('integration_strategy', {'threshold': 0.05})

        # 3. 记录买入交易
        store.record_trade(account_id, timestamp, code, '浦发银行', 'buy', '开仓', 10.0, 1000, 'integration_strategy')

        # 4. 新增持仓
        store.batch_new_held(account_id, [code])

        # 5. 持仓天数递增
        assert store.all_held_inc(account_id) is True
        assert store.get_held_days(code, account_id) == 1

        # 6. 更新最高价
        store.update_max_price(code, account_id, 12.5)

        # 7. 查询交易记录
        df = store.query_trades(account_id, stock_code=code)
        assert len(df) == 1

        # 8. 更新账户资金
        store.update_account_capital(account_id, 98000.0)  # 买入后资金减少

        # 9. 验证最终状态
        assert store.get_held_days(code, account_id) == 1
        assert store.get_max_price(code, account_id) == 12.5
        account = store.get_account(account_id)
        assert account['current_capital'] == 98000.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
