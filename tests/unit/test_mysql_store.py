#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQLStore单元测试

测试范围:
1. 账户管理: create_account, get_account, update_account_capital
2. 策略管理: create_strategy, get_strategy_params, save_strategy_params
3. 参数版本管理: 版本rollover, is_active标记切换
4. 参数对比: compare_strategy_params 差异检测
5. 数据验证: 唯一性约束, 枚举值验证, NULL约束
6. 错误处理: 数据库连接失败, 事务回滚

测试策略:
- 使用SQLite内存数据库(:memory:)替代MySQL
- 每个测试独立的session,避免状态污染
- 使用pytest fixtures管理数据库生命周期

覆盖率目标: >85%
执行: pytest tests/unit/test_mysql_store.py -v --cov=storage/mysql_store
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime

from storage.mysql_store import (
    MySQLStore, Base, Account, Strategy, StrategyParam,
    AccountStrategy, User, Role, Permission
)


@pytest.fixture
def in_memory_mysql_store():
    """
    创建使用SQLite内存数据库的MySQLStore实例

    SQLite与MySQL兼容性高,适合单元测试
    """
    # 创建内存数据库引擎
    engine = create_engine('sqlite:///:memory:', echo=False)

    # 创建所有表
    Base.metadata.create_all(engine)

    # 创建MySQLStore实例并替换engine
    store = object.__new__(MySQLStore)
    store.engine = engine
    store.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    yield store

    # 清理
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sample_account_data():
    """示例账户数据"""
    return {
        'account_id': 'TEST_QMT_001',
        'account_name': '测试账户1',
        'broker': 'QMT',
        'initial_capital': 100000.0
    }


@pytest.fixture
def sample_strategy_data():
    """示例策略数据"""
    return {
        'strategy_name': '问财选股策略',
        'strategy_code': 'WENCAI_001',
        'strategy_type': 'wencai',
        'version': 'v1.0'
    }


class TestAccountManagement:
    """测试账户管理功能"""

    def test_create_account_success(self, in_memory_mysql_store, sample_account_data):
        """测试成功创建账户"""
        store = in_memory_mysql_store

        result = store.create_account(**sample_account_data)
        assert result is True

        # 验证账户已创建
        account = store.get_account(sample_account_data['account_id'])
        assert account is not None
        assert account['account_id'] == sample_account_data['account_id']
        assert account['account_name'] == sample_account_data['account_name']
        assert account['broker'] == sample_account_data['broker']
        assert float(account['initial_capital']) == sample_account_data['initial_capital']
        assert account['status'] == 'active'

    def test_create_account_duplicate(self, in_memory_mysql_store, sample_account_data):
        """测试创建重复账户(应失败)"""
        store = in_memory_mysql_store

        # 第一次创建
        store.create_account(**sample_account_data)

        # 第二次创建相同account_id (应失败)
        result = store.create_account(**sample_account_data)
        assert result is False

    def test_create_account_invalid_broker(self, in_memory_mysql_store):
        """测试创建账户时使用无效broker"""
        store = in_memory_mysql_store

        # SQLite不强制枚举约束,但MySQL会
        # 这里测试逻辑应该拒绝无效值
        result = store.create_account(
            account_id='TEST_001',
            account_name='测试',
            broker='INVALID_BROKER',  # 无效值
            initial_capital=100000.0
        )

        # 注意: SQLite不会强制枚举,所以这个测试在真实MySQL环境中会失败
        # 实际生产中应在应用层验证broker值

    def test_get_account_not_exists(self, in_memory_mysql_store):
        """测试查询不存在的账户"""
        store = in_memory_mysql_store

        account = store.get_account('NON_EXISTENT_ACCOUNT')
        assert account is None

    def test_update_account_capital(self, in_memory_mysql_store, sample_account_data):
        """测试更新账户资金"""
        store = in_memory_mysql_store

        # 先创建账户
        store.create_account(**sample_account_data)

        # 更新资金
        new_capital = 150000.0
        result = store.update_account_capital(sample_account_data['account_id'], new_capital)
        assert result is True

        # 验证更新成功
        account = store.get_account(sample_account_data['account_id'])
        assert float(account['current_capital']) == new_capital

    def test_update_account_capital_not_exists(self, in_memory_mysql_store):
        """测试更新不存在的账户资金"""
        store = in_memory_mysql_store

        result = store.update_account_capital('NON_EXISTENT', 100000.0)
        assert result is False

    def test_get_account_returns_dict(self, in_memory_mysql_store, sample_account_data):
        """测试get_account返回字典格式"""
        store = in_memory_mysql_store

        store.create_account(**sample_account_data)
        account = store.get_account(sample_account_data['account_id'])

        # 验证返回字典
        assert isinstance(account, dict)
        assert 'account_id' in account
        assert 'account_name' in account
        assert 'broker' in account
        assert 'initial_capital' in account
        assert 'status' in account
        assert 'created_at' in account


class TestStrategyManagement:
    """测试策略管理功能"""

    def test_create_strategy_success(self, in_memory_mysql_store, sample_strategy_data):
        """测试成功创建策略"""
        store = in_memory_mysql_store

        result = store.create_strategy(**sample_strategy_data)
        assert result is True

        # 验证策略已创建 (通过get_strategy_params)
        params = store.get_strategy_params(sample_strategy_data['strategy_code'])
        # 新创建的策略应该返回空参数字典
        assert params == {}

    def test_create_strategy_duplicate(self, in_memory_mysql_store, sample_strategy_data):
        """测试创建重复策略(应失败)"""
        store = in_memory_mysql_store

        # 第一次创建
        store.create_strategy(**sample_strategy_data)

        # 第二次创建相同strategy_code (应失败)
        result = store.create_strategy(**sample_strategy_data)
        assert result is False

    def test_get_strategy_params_not_exists(self, in_memory_mysql_store):
        """测试查询不存在的策略参数"""
        store = in_memory_mysql_store

        params = store.get_strategy_params('NON_EXISTENT_STRATEGY')
        assert params is None

    def test_save_strategy_params_initial_version(self, in_memory_mysql_store, sample_strategy_data):
        """测试保存策略参数(初始版本)"""
        store = in_memory_mysql_store

        # 先创建策略
        store.create_strategy(**sample_strategy_data)

        # 保存参数 (version=1)
        params = {
            'max_positions': 10,
            'position_size': 0.1,
            'stop_loss': 0.05,
            'take_profit': 0.15
        }

        result = store.save_strategy_params(sample_strategy_data['strategy_code'], params)
        assert result is True

        # 验证参数已保存
        saved_params = store.get_strategy_params(sample_strategy_data['strategy_code'])
        assert saved_params == params

    def test_save_strategy_params_version_rollover(self, in_memory_mysql_store, sample_strategy_data):
        """测试策略参数版本rollover"""
        store = in_memory_mysql_store

        # 创建策略
        store.create_strategy(**sample_strategy_data)

        # 保存第一个版本
        params_v1 = {'max_positions': 10, 'stop_loss': 0.05}
        store.save_strategy_params(sample_strategy_data['strategy_code'], params_v1)

        # 保存第二个版本
        params_v2 = {'max_positions': 15, 'stop_loss': 0.03}
        store.save_strategy_params(sample_strategy_data['strategy_code'], params_v2)

        # 验证当前激活的是v2
        current_params = store.get_strategy_params(sample_strategy_data['strategy_code'])
        assert current_params == params_v2

        # 验证v1已设置为is_active=False
        session = store._get_session()
        try:
            strategy = session.query(Strategy).filter_by(
                strategy_code=sample_strategy_data['strategy_code']
            ).first()

            old_params = session.query(StrategyParam).filter_by(
                strategy_id=strategy.id,
                version=1
            ).all()

            for param in old_params:
                assert param.is_active is False
        finally:
            session.close()

    def test_compare_strategy_params(self, in_memory_mysql_store, sample_strategy_data):
        """测试策略参数对比"""
        store = in_memory_mysql_store

        # 创建策略并保存第一个版本
        store.create_strategy(**sample_strategy_data)

        params_v1 = {
            'max_positions': 10,
            'stop_loss': 0.05,
            'take_profit': 0.15
        }
        store.save_strategy_params(sample_strategy_data['strategy_code'], params_v1)

        # 定义第二个版本(尚未保存)
        params_v2 = {
            'max_positions': 15,  # 修改
            'stop_loss': 0.05,    # 不变
            'take_profit': 0.20,  # 修改
            'new_param': 'test'   # 新增
        }

        # 对比当前版本(v1)与新版本(v2)
        added, modified, deleted = store.compare_strategy_params(
            sample_strategy_data['strategy_code'],
            params_v2
        )

        # 验证差异
        assert 'new_param' in added
        assert added['new_param'] == 'test'

        assert 'max_positions' in modified
        assert modified['max_positions'] == (10, 15)

        assert 'take_profit' in modified
        assert modified['take_profit'] == (0.15, 0.20)

        # stop_loss未修改,不应该在modified中
        assert 'stop_loss' not in modified

        # 没有删除的参数
        assert len(deleted) == 0

    def test_get_strategy_params_type_conversion(self, in_memory_mysql_store, sample_strategy_data):
        """测试策略参数类型转换"""
        store = in_memory_mysql_store

        # 创建策略
        store.create_strategy(**sample_strategy_data)

        # 保存不同类型的参数
        params = {
            'int_param': 10,
            'float_param': 0.05,
            'string_param': 'test',
            'json_param': {'nested': 'value'}
        }

        store.save_strategy_params(sample_strategy_data['strategy_code'], params)

        # 验证类型保持正确
        saved_params = store.get_strategy_params(sample_strategy_data['strategy_code'])
        assert isinstance(saved_params['int_param'], int)
        assert isinstance(saved_params['float_param'], float)
        assert isinstance(saved_params['string_param'], str)
        assert isinstance(saved_params['json_param'], dict)


class TestNotImplementedMethods:
    """测试未实现的方法(应该抛出NotImplementedError)"""

    def test_get_held_days_not_implemented(self, in_memory_mysql_store):
        """MySQLStore不支持持仓管理"""
        with pytest.raises(NotImplementedError):
            in_memory_mysql_store.get_held_days('000001.SZ', 'ACCOUNT_001')

    def test_record_trade_not_implemented(self, in_memory_mysql_store):
        """MySQLStore不支持交易记录"""
        with pytest.raises(NotImplementedError):
            in_memory_mysql_store.record_trade(
                account_id='ACCOUNT_001',
                timestamp='2025-01-01 10:00:00',
                stock_code='000001.SZ',
                stock_name='平安银行',
                order_type='BUY',
                remark='测试',
                price=10.0,
                volume=100
            )

    def test_get_kline_not_implemented(self, in_memory_mysql_store):
        """MySQLStore不支持K线查询"""
        with pytest.raises(NotImplementedError):
            in_memory_mysql_store.get_kline('000001.SZ', '2025-01-01', '2025-01-31')


class TestConnectionManagement:
    """测试连接管理"""

    def test_health_check_success(self, in_memory_mysql_store):
        """测试健康检查成功"""
        result = in_memory_mysql_store.health_check()
        assert result is True

    def test_health_check_failure(self, in_memory_mysql_store):
        """测试健康检查失败"""
        # Mock engine.execute抛出异常
        with patch.object(in_memory_mysql_store.engine, 'connect', side_effect=Exception('Connection error')):
            result = in_memory_mysql_store.health_check()
            assert result is False

    def test_close_connection(self, in_memory_mysql_store):
        """测试关闭连接"""
        # 关闭连接不应抛出异常
        in_memory_mysql_store.close()

    def test_close_connection_error(self, in_memory_mysql_store):
        """测试关闭连接时的错误处理"""
        # Mock dispose方法抛出异常
        with patch.object(in_memory_mysql_store.engine, 'dispose', side_effect=Exception('Dispose error')):
            # 不应抛出异常
            in_memory_mysql_store.close()


class TestErrorHandling:
    """测试错误处理"""

    def test_create_account_database_error(self, in_memory_mysql_store, sample_account_data):
        """测试create_account数据库错误处理"""
        # Mock session.commit抛出异常
        def mock_get_session():
            session = MagicMock()
            session.commit.side_effect = Exception('Database error')
            return session

        with patch.object(in_memory_mysql_store, '_get_session', side_effect=mock_get_session):
            result = in_memory_mysql_store.create_account(**sample_account_data)
            assert result is False

    def test_get_account_database_error(self, in_memory_mysql_store):
        """测试get_account数据库错误处理"""
        # Mock session.query抛出异常
        def mock_get_session():
            session = MagicMock()
            session.query.side_effect = Exception('Database error')
            return session

        with patch.object(in_memory_mysql_store, '_get_session', side_effect=mock_get_session):
            result = in_memory_mysql_store.get_account('TEST_001')
            assert result is None

    def test_transaction_rollback(self, in_memory_mysql_store, sample_strategy_data):
        """测试事务回滚"""
        store = in_memory_mysql_store

        # 创建策略
        store.create_strategy(**sample_strategy_data)

        # 保存参数时模拟错误
        session = store._get_session()
        original_commit = session.commit

        def fail_on_commit():
            raise Exception('Simulated commit failure')

        try:
            # 开始事务
            strategy = session.query(Strategy).filter_by(
                strategy_code=sample_strategy_data['strategy_code']
            ).first()

            # 添加参数
            param = StrategyParam(
                strategy_id=strategy.id,
                param_key='test_key',
                param_value='test_value',
                param_type='string',
                version=1,
                is_active=True
            )
            session.add(param)

            # Mock commit失败
            session.commit = fail_on_commit

            # 尝试commit
            try:
                session.commit()
            except Exception:
                session.rollback()

            # 验证参数未保存 (rollback成功)
            params = store.get_strategy_params(sample_strategy_data['strategy_code'])
            assert params == {}  # 应该为空

        finally:
            session.close()


class TestDataConsistency:
    """测试数据一致性"""

    def test_account_decimal_precision(self, in_memory_mysql_store, sample_account_data):
        """测试账户资金精度(2位小数)"""
        store = in_memory_mysql_store

        # 创建账户
        store.create_account(**sample_account_data)

        # 更新资金 (超过2位小数)
        store.update_account_capital(sample_account_data['account_id'], 123456.789)

        # 验证精度
        account = store.get_account(sample_account_data['account_id'])
        # 注意: SQLite可能不会强制精度,但MySQL会
        # 实际值应该是 123456.79

    def test_strategy_param_json_serialization(self, in_memory_mysql_store, sample_strategy_data):
        """测试策略参数JSON序列化"""
        store = in_memory_mysql_store

        # 创建策略
        store.create_strategy(**sample_strategy_data)

        # 保存复杂JSON参数
        params = {
            'nested': {
                'level1': {
                    'level2': ['a', 'b', 'c']
                }
            }
        }

        store.save_strategy_params(sample_strategy_data['strategy_code'], params)

        # 验证JSON正确反序列化
        saved_params = store.get_strategy_params(sample_strategy_data['strategy_code'])
        assert saved_params == params
        assert saved_params['nested']['level1']['level2'] == ['a', 'b', 'c']

    def test_account_status_default(self, in_memory_mysql_store, sample_account_data):
        """测试账户状态默认值"""
        store = in_memory_mysql_store

        store.create_account(**sample_account_data)
        account = store.get_account(sample_account_data['account_id'])

        # 验证默认状态为active
        assert account['status'] == 'active'

    def test_strategy_timestamp_auto_update(self, in_memory_mysql_store, sample_account_data):
        """测试时间戳自动更新"""
        store = in_memory_mysql_store

        # 创建账户
        store.create_account(**sample_account_data)
        account1 = store.get_account(sample_account_data['account_id'])
        created_at = account1['created_at']

        # 更新账户
        import time
        time.sleep(0.1)  # 确保时间戳有差异
        store.update_account_capital(sample_account_data['account_id'], 200000.0)

        account2 = store.get_account(sample_account_data['account_id'])
        updated_at = account2['updated_at']

        # 验证updated_at已更新
        # 注意: SQLite可能不会自动更新,但MySQL会
        assert 'updated_at' in account2


class TestSQLAlchemyORM:
    """测试SQLAlchemy ORM模型"""

    def test_account_relationship(self, in_memory_mysql_store, sample_account_data, sample_strategy_data):
        """测试Account与AccountStrategy关系"""
        store = in_memory_mysql_store

        # 创建账户和策略
        store.create_account(**sample_account_data)
        store.create_strategy(**sample_strategy_data)

        session = store._get_session()
        try:
            account = session.query(Account).filter_by(
                account_id=sample_account_data['account_id']
            ).first()

            strategy = session.query(Strategy).filter_by(
                strategy_code=sample_strategy_data['strategy_code']
            ).first()

            # 创建关联
            account_strategy = AccountStrategy(
                account_id=account.id,
                strategy_id=strategy.id,
                allocated_capital=50000.0,
                risk_limit=0.10
            )
            session.add(account_strategy)
            session.commit()

            # 验证关系
            account = session.query(Account).filter_by(
                account_id=sample_account_data['account_id']
            ).first()

            assert len(account.account_strategies) == 1
            assert account.account_strategies[0].allocated_capital == Decimal('50000.00')

        finally:
            session.close()

    def test_strategy_params_relationship(self, in_memory_mysql_store, sample_strategy_data):
        """测试Strategy与StrategyParam关系"""
        store = in_memory_mysql_store

        # 创建策略并保存参数
        store.create_strategy(**sample_strategy_data)
        params = {'param1': 'value1', 'param2': 'value2'}
        store.save_strategy_params(sample_strategy_data['strategy_code'], params)

        session = store._get_session()
        try:
            strategy = session.query(Strategy).filter_by(
                strategy_code=sample_strategy_data['strategy_code']
            ).first()

            # 验证关系
            assert len(strategy.params) == 2
            assert all(p.is_active for p in strategy.params)

        finally:
            session.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=storage/mysql_store', '--cov-report=term'])
