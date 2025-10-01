#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T012: Contract Test - Trade Records Methods

验证交易记录相关方法:
- record_trade()
- query_trades()
- aggregate_trades()
"""

import pytest
import tempfile
import os
import shutil
import datetime
import pandas as pd
from storage.file_store import FileStore


class ContractTestTradeRecords:
    """契约测试:交易记录方法"""

    @pytest.fixture
    def store(self):
        raise NotImplementedError("子类必须实现 store fixture")

    def test_record_trade(self, store):
        """测试记录交易"""
        account_id = 'test_account'
        timestamp = str(int(datetime.datetime.now().timestamp()))

        success = store.record_trade(
            account_id=account_id,
            timestamp=timestamp,
            stock_code='600000.SH',
            stock_name='浦发银行',
            order_type='buy',
            remark='开仓',
            price=10.50,
            volume=1000,
            strategy_name='test_strategy'
        )

        assert success is True, "记录交易应该成功"

    def test_query_trades_empty(self, store):
        """测试查询空交易记录"""
        account_id = 'empty_account'

        df = store.query_trades(account_id)

        assert isinstance(df, pd.DataFrame), "应该返回 DataFrame"
        # 允许空DataFrame或有列名的空DataFrame
        assert len(df) == 0, "空账户应该返回空 DataFrame"

    def test_query_trades_with_results(self, store):
        """测试查询有交易记录"""
        account_id = 'test_account'
        timestamp = str(int(datetime.datetime.now().timestamp()))

        # 记录多笔交易
        store.record_trade(account_id, timestamp, '600000.SH', '浦发银行', 'buy', '开仓', 10.50, 1000)
        store.record_trade(account_id, timestamp, '000001.SZ', '平安银行', 'buy', '开仓', 12.30, 500)

        # 查询
        df = store.query_trades(account_id)

        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 2, "应该至少有 2 条记录"

    def test_query_trades_filter_by_code(self, store):
        """测试按股票代码过滤"""
        account_id = 'test_account'
        timestamp = str(int(datetime.datetime.now().timestamp()))

        store.record_trade(account_id, timestamp, '600000.SH', '浦发银行', 'buy', '开仓', 10.50, 1000)
        store.record_trade(account_id, timestamp, '000001.SZ', '平安银行', 'buy', '开仓', 12.30, 500)

        # 只查询 600000.SH
        df = store.query_trades(account_id, stock_code='600000.SH')

        assert len(df) >= 1
        # 验证返回的都是 600000.SH (如果DataFrame有'代码'列)
        if '代码' in df.columns and len(df) > 0:
            assert all(df['代码'] == '600000.SH'), "过滤后应该只有 600000.SH"

    def test_aggregate_trades(self, store):
        """测试交易聚合统计"""
        account_id = 'test_account'
        timestamp = str(int(datetime.datetime.now().timestamp()))
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        # 记录同一股票的多笔交易
        store.record_trade(account_id, timestamp, '600000.SH', '浦发银行', 'buy', '开仓', 10.0, 1000)
        store.record_trade(account_id, timestamp, '600000.SH', '浦发银行', 'buy', '加仓', 11.0, 500)

        # 按股票聚合
        df = store.aggregate_trades(account_id, today, today, group_by='stock')

        assert isinstance(df, pd.DataFrame)
        # 如果有数据,验证聚合结果
        if len(df) > 0:
            assert '代码' in df.columns or '成交量' in df.columns, "聚合结果应该包含必要的列"


class TestFileStoreTradeRecords(ContractTestTradeRecords):
    """FileStore 实现的契约测试"""

    @pytest.fixture
    def store(self):
        temp_dir = tempfile.mkdtemp(prefix='test_contract_filestore_trade_')
        store = FileStore(cache_path=temp_dir)
        yield store
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
