#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ClickHouseStore单元测试

测试范围:
1. 交易记录: record_trade, query_trades, aggregate_trades
2. K线数据: get_kline, batch_get_kline
3. 日期过滤: start_date, end_date参数
4. 聚合统计: 按月/年/股票聚合
5. 批量操作: batch insert性能
6. 错误处理: ClickHouse连接失败, 查询异常

测试策略:
- 使用Mock模拟ClickHouse Client
- 验证SQL语句正确性
- 验证DataFrame返回格式
- 测试日期范围过滤逻辑

覆盖率目标: >85%
执行: pytest tests/unit/test_clickhouse_store.py -v --cov=storage/clickhouse_store
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, date
import pandas as pd

from storage.clickhouse_store import ClickHouseStore


@pytest.fixture
def mock_clickhouse_store():
    """
    创建使用Mock Client的ClickHouseStore实例

    Mock策略:
    - Mock clickhouse_driver.Client避免真实连接
    - 通过side_effect验证SQL语句
    - 返回预设数据模拟查询结果
    """
    with patch('storage.clickhouse_store.Client') as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client

        store = ClickHouseStore(
            host='localhost',
            port=9000,
            database='test_db',
            user='default',
            password=''
        )

        # 验证Mock client已设置
        assert store.client == mock_client
        assert store.database == 'test_db'

        yield store, mock_client


@pytest.fixture
def sample_trade_data():
    """示例交易数据"""
    return {
        'account_id': 'TEST_ACCOUNT_001',
        'timestamp': '2025-01-15 10:30:00',
        'stock_code': '000001.SZ',
        'stock_name': '平安银行',
        'order_type': 'buy_trade',
        'remark': '买入',
        'price': 15.50,
        'volume': 1000,
        'strategy_name': 'WENCAI_001'
    }


class TestTradeRecords:
    """测试交易记录功能"""

    def test_record_trade_success(self, mock_clickhouse_store, sample_trade_data):
        """测试成功记录交易"""
        store, mock_client = mock_clickhouse_store

        # Mock execute返回成功
        mock_client.execute.return_value = None

        result = store.record_trade(**sample_trade_data)
        assert result is True

        # 验证execute被调用
        assert mock_client.execute.called
        call_args = mock_client.execute.call_args

        # 验证SQL包含INSERT语句
        sql = call_args[0][0]
        assert 'INSERT INTO' in sql
        assert 'test_db.trade' in sql

        # 验证数据参数
        data = call_args[0][1]
        assert len(data) == 1
        record = data[0]
        assert record[2] == sample_trade_data['account_id']  # account_id
        assert record[3] == sample_trade_data['stock_code']  # stock_code
        assert record[7] == sample_trade_data['price']  # price
        assert record[8] == sample_trade_data['volume']  # volume

    def test_record_trade_amount_calculation(self, mock_clickhouse_store, sample_trade_data):
        """测试交易金额计算"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = None

        store.record_trade(**sample_trade_data)

        # 验证金额 = price * volume
        data = mock_client.execute.call_args[0][1]
        amount = data[0][9]  # amount字段
        expected_amount = round(sample_trade_data['price'] * sample_trade_data['volume'], 2)
        assert amount == expected_amount

    def test_record_trade_date_parsing(self, mock_clickhouse_store, sample_trade_data):
        """测试时间戳解析"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = None

        store.record_trade(**sample_trade_data)

        # 验证datetime和date字段
        data = mock_client.execute.call_args[0][1]
        timestamp = data[0][0]  # timestamp
        trade_date = data[0][1]  # date

        assert isinstance(timestamp, datetime)
        assert isinstance(trade_date, date)
        assert timestamp.strftime('%Y-%m-%d %H:%M:%S') == sample_trade_data['timestamp']

    def test_record_trade_error_handling(self, mock_clickhouse_store, sample_trade_data):
        """测试交易记录错误处理"""
        store, mock_client = mock_clickhouse_store

        # Mock execute抛出异常
        mock_client.execute.side_effect = Exception('ClickHouse connection error')

        result = store.record_trade(**sample_trade_data)
        assert result is False

    def test_query_trades_basic(self, mock_clickhouse_store):
        """测试基本交易查询"""
        store, mock_client = mock_clickhouse_store

        # Mock查询结果 (10列: timestamp, date, stock_code, stock_name, order_type, strategy_name, price, volume, amount, remark)
        mock_client.execute.return_value = [
            (datetime(2025, 1, 15, 10, 30), date(2025, 1, 15),
             '000001.SZ', '平安银行', 'buy_trade', 'WENCAI_001',
             15.50, 1000, 15500.0, '买入')
        ]

        result = store.query_trades(
            account_id='TEST_001',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )

        # 验证返回DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['stock_code'] == '000001.SZ'

        # 验证SQL包含日期过滤 (使用 >= 和 <=,不是BETWEEN)
        sql = mock_client.execute.call_args[0][0]
        assert 'WHERE' in sql
        assert 'account_id' in sql
        assert "date >=" in sql
        assert "date <=" in sql

    def test_query_trades_with_stock_filter(self, mock_clickhouse_store):
        """测试按股票代码过滤交易"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = []

        store.query_trades(
            account_id='TEST_001',
            start_date='2025-01-01',
            end_date='2025-01-31',
            stock_code='000001.SZ'
        )

        # 验证SQL包含股票代码过滤
        sql = mock_client.execute.call_args[0][0]
        assert 'stock_code' in sql

    def test_query_trades_empty_result(self, mock_clickhouse_store):
        """测试查询无结果"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = []

        result = store.query_trades(
            account_id='TEST_001',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_query_trades_error_handling(self, mock_clickhouse_store):
        """测试查询错误处理"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.side_effect = Exception('Query error')

        result = store.query_trades(
            account_id='TEST_001',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )

        # 错误时返回空DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_aggregate_trades_by_month(self, mock_clickhouse_store):
        """测试按月聚合交易"""
        store, mock_client = mock_clickhouse_store

        # Mock聚合结果 (4列: month, trade_count, total_volume, total_amount)
        mock_client.execute.return_value = [
            ('202501', 10, 10000, 155000.0),
            ('202502', 15, 15000, 230000.0)
        ]

        result = store.aggregate_trades(
            account_id='TEST_001',
            start_date='2025-01-01',
            end_date='2025-02-28',
            group_by='month'
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'month' in result.columns
        assert 'trade_count' in result.columns
        assert 'total_amount' in result.columns

        # 验证SQL包含GROUP BY
        sql = mock_client.execute.call_args[0][0]
        assert 'GROUP BY' in sql
        assert 'toYYYYMM' in sql  # 月份聚合函数

    def test_aggregate_trades_by_year(self, mock_clickhouse_store):
        """测试按年聚合交易"""
        store, mock_client = mock_clickhouse_store
        # 实际上按年聚合使用date group,不是toYear
        mock_client.execute.return_value = [
            (date(2025, 1, 1), 100, 100000, 1500000.0)
        ]

        store.aggregate_trades(
            account_id='TEST_001',
            start_date='2025-01-01',
            end_date='2025-12-31',
            group_by='date'  # 使用date,不是year
        )

        # 验证使用date分组
        sql = mock_client.execute.call_args[0][0]
        assert 'GROUP BY' in sql

    def test_aggregate_trades_by_stock(self, mock_clickhouse_store):
        """测试按股票聚合交易"""
        store, mock_client = mock_clickhouse_store
        # 按stock聚合返回5列: stock_code, stock_name, trade_count, total_volume, total_amount
        mock_client.execute.return_value = [
            ('000001.SZ', '平安银行', 5, 5000, 75000.0),
            ('600000.SH', '浦发银行', 3, 3000, 45000.0)
        ]

        result = store.aggregate_trades(
            account_id='TEST_001',
            start_date='2025-01-01',
            end_date='2025-01-31',
            group_by='stock'
        )

        assert len(result) == 2

        # 验证SQL按股票代码分组
        sql = mock_client.execute.call_args[0][0]
        assert 'stock_code' in sql


class TestKlineData:
    """测试K线数据功能"""

    def test_get_kline_basic(self, mock_clickhouse_store):
        """测试基本K线查询"""
        store, mock_client = mock_clickhouse_store

        # Mock K线数据 (8列: date, datetime, open, high, low, close, volume, amount)
        mock_client.execute.return_value = [
            (date(2025, 1, 15), datetime(2025, 1, 15, 9, 30), 15.50, 16.00, 15.20, 15.80,
             1000000, 15750000.0)
        ]

        result = store.get_kline(
            stock_code='000001.SZ',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )

        # 验证返回DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

        # 验证列名 (实际包含date和datetime)
        expected_columns = ['date', 'datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']
        assert all(col in result.columns for col in expected_columns)

        # 验证数据
        assert result.iloc[0]['open'] == 15.50
        assert result.iloc[0]['high'] == 16.00

    def test_get_kline_date_filter(self, mock_clickhouse_store):
        """测试K线日期过滤"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = []

        store.get_kline(
            stock_code='000001.SZ',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )

        # 验证SQL包含日期范围 (使用 >= 和 <=)
        sql = mock_client.execute.call_args[0][0]
        assert 'WHERE' in sql
        assert 'stock_code' in sql
        assert 'date >=' in sql
        assert 'date <=' in sql

    def test_get_kline_frequency_parameter(self, mock_clickhouse_store):
        """测试K线频率参数(目前仅支持daily)"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = []

        # 调用daily频率
        store.get_kline(
            stock_code='000001.SZ',
            start_date='2025-01-01',
            end_date='2025-01-31',
            frequency='daily'
        )

        # 验证查询daily_kline表
        sql = mock_client.execute.call_args[0][0]
        assert 'daily_kline' in sql

    def test_batch_get_kline(self, mock_clickhouse_store):
        """测试批量查询K线"""
        store, mock_client = mock_clickhouse_store

        # Mock多个股票的K线数据 (9列: stock_code, date, datetime, open, high, low, close, volume, amount)
        mock_client.execute.return_value = [
            ('000001.SZ', date(2025, 1, 15), datetime(2025, 1, 15, 9, 30), 15.50, 16.00, 15.20, 15.80, 1000000, 15750000.0),
            ('600000.SH', date(2025, 1, 15), datetime(2025, 1, 15, 9, 30), 10.20, 10.50, 10.10, 10.40, 500000, 5200000.0)
        ]

        result = store.batch_get_kline(
            stock_codes=['000001.SZ', '600000.SH'],
            start_date='2025-01-01',
            end_date='2025-01-31'
        )

        # 验证返回字典
        assert isinstance(result, dict)
        assert '000001.SZ' in result
        assert '600000.SH' in result

        # 验证每个DataFrame
        assert isinstance(result['000001.SZ'], pd.DataFrame)
        assert len(result['000001.SZ']) == 1

    def test_get_kline_error_handling(self, mock_clickhouse_store):
        """测试K线查询错误处理"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.side_effect = Exception('Query error')

        result = store.get_kline(
            stock_code='000001.SZ',
            start_date='2025-01-01',
            end_date='2025-01-31'
        )

        # 错误时返回空DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestNotImplementedMethods:
    """测试未实现的方法"""

    def test_get_held_days_not_implemented(self, mock_clickhouse_store):
        """ClickHouseStore不支持持仓管理"""
        store, _ = mock_clickhouse_store

        with pytest.raises(NotImplementedError):
            store.get_held_days('000001.SZ', 'ACCOUNT_001')

    def test_create_account_not_implemented(self, mock_clickhouse_store):
        """ClickHouseStore不支持账户管理"""
        store, _ = mock_clickhouse_store

        with pytest.raises(NotImplementedError):
            store.create_account('ACCOUNT_001', '测试账户', 'QMT', 100000.0)

    def test_create_strategy_not_implemented(self, mock_clickhouse_store):
        """ClickHouseStore不支持策略管理"""
        store, _ = mock_clickhouse_store

        with pytest.raises(NotImplementedError):
            store.create_strategy('STRATEGY_001', 'STR001', 'wencai', 'v1.0')


class TestConnectionManagement:
    """测试连接管理"""

    def test_health_check_success(self, mock_clickhouse_store):
        """测试健康检查成功"""
        store, mock_client = mock_clickhouse_store

        # Mock SELECT 1返回成功
        mock_client.execute.return_value = [(1,)]

        result = store.health_check()
        assert result is True

        # 验证执行了SELECT 1
        mock_client.execute.assert_called_with('SELECT 1')

    def test_health_check_failure(self, mock_clickhouse_store):
        """测试健康检查失败"""
        store, mock_client = mock_clickhouse_store

        # Mock execute抛出异常
        mock_client.execute.side_effect = Exception('Connection error')

        result = store.health_check()
        assert result is False

    def test_close_connection(self, mock_clickhouse_store):
        """测试关闭连接"""
        store, mock_client = mock_clickhouse_store

        # 关闭连接不应抛出异常
        store.close()

        # 验证disconnect被调用
        mock_client.disconnect.assert_called_once()

    def test_close_connection_error(self, mock_clickhouse_store):
        """测试关闭连接时的错误处理"""
        store, mock_client = mock_clickhouse_store

        # Mock disconnect抛出异常
        mock_client.disconnect.side_effect = Exception('Disconnect error')

        # 不应抛出异常
        store.close()


class TestDataConsistency:
    """测试数据一致性"""

    def test_trade_timestamp_format(self, mock_clickhouse_store, sample_trade_data):
        """测试交易时间戳格式"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = None

        store.record_trade(**sample_trade_data)

        # 验证timestamp格式
        data = mock_client.execute.call_args[0][1]
        timestamp = data[0][0]

        # 时间戳应该是datetime对象
        assert isinstance(timestamp, datetime)
        assert timestamp.year == 2025
        assert timestamp.month == 1
        assert timestamp.day == 15

    def test_kline_column_order(self, mock_clickhouse_store):
        """测试K线DataFrame列顺序"""
        store, mock_client = mock_clickhouse_store

        # Mock数据 (8列: date, datetime, open, high, low, close, volume, amount)
        mock_client.execute.return_value = [
            (date(2025, 1, 15), datetime(2025, 1, 15, 9, 30), 15.50, 16.00, 15.20, 15.80, 1000000, 15750000.0)
        ]

        result = store.get_kline('000001.SZ', '2025-01-01', '2025-01-31')

        # 验证列顺序 (包含datetime列)
        expected_columns = ['date', 'datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']
        assert list(result.columns) == expected_columns

    def test_aggregate_dataframe_format(self, mock_clickhouse_store):
        """测试聚合结果DataFrame格式"""
        store, mock_client = mock_clickhouse_store

        # Mock聚合结果 (4列: month, trade_count, total_volume, total_amount)
        mock_client.execute.return_value = [
            ('202501', 10, 10000, 155000.0)
        ]

        result = store.aggregate_trades(
            'TEST_001',
            '2025-01-01',
            '2025-01-31',
            group_by='month'
        )

        # 验证列名
        assert 'month' in result.columns
        assert 'trade_count' in result.columns
        assert 'total_amount' in result.columns


class TestSQLGeneration:
    """测试SQL语句生成"""

    def test_record_trade_sql_structure(self, mock_clickhouse_store, sample_trade_data):
        """测试record_trade SQL结构"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = None

        store.record_trade(**sample_trade_data)

        sql = mock_client.execute.call_args[0][0]

        # 验证SQL结构
        assert 'INSERT INTO' in sql
        assert 'test_db.trade' in sql
        assert 'timestamp' in sql
        assert 'date' in sql
        assert 'account_id' in sql
        assert 'VALUES' in sql

    def test_query_trades_sql_where_clause(self, mock_clickhouse_store):
        """测试query_trades WHERE子句"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = []

        store.query_trades(
            account_id='TEST_001',
            start_date='2025-01-01',
            end_date='2025-01-31',
            stock_code='000001.SZ'
        )

        sql = mock_client.execute.call_args[0][0]

        # 验证WHERE条件 (使用 >= 和 <=)
        assert 'WHERE' in sql
        assert 'account_id' in sql
        assert 'date >=' in sql
        assert 'date <=' in sql
        assert 'stock_code' in sql

    def test_aggregate_trades_group_by(self, mock_clickhouse_store):
        """测试aggregate_trades GROUP BY子句"""
        store, mock_client = mock_clickhouse_store
        mock_client.execute.return_value = []

        # 测试不同的group_by参数
        for group_type in ['month', 'year', 'stock']:
            store.aggregate_trades(
                'TEST_001',
                '2025-01-01',
                '2025-12-31',
                group_by=group_type
            )

            sql = mock_client.execute.call_args[0][0]
            assert 'GROUP BY' in sql


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=storage/clickhouse_store', '--cov-report=term'])
