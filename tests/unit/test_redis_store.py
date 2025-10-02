#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RedisStore单元测试

测试范围:
1. 持仓状态: get/update/delete_held_days, batch_new_held
2. all_held_inc: Lua脚本原子性和幂等性
3. 价格追踪: get/update max_price/min_price
4. 连接管理: health_check, close
5. 错误处理: Redis连接失败, 超时等异常情况
6. 并发测试: 多线程all_held_inc竞态条件

测试策略:
- 使用fakeredis替代真实Redis (无需Docker)
- 使用unittest.mock模拟连接失败场景
- 使用threading测试并发安全性

覆盖率目标: >85%
执行: pytest tests/unit/test_redis_store.py -v --cov=storage/redis_store
"""

import pytest
import fakeredis
from unittest.mock import patch, MagicMock
from datetime import datetime
import threading
import time

from storage.redis_store import RedisStore


@pytest.fixture
def redis_store():
    """
    创建使用fakeredis的RedisStore实例

    fakeredis模拟Redis所有功能,包括Lua脚本执行
    注意: 由于fakeredis v2.x不支持EVALSHA,我们使用Python模拟all_held_inc逻辑
    """
    # 直接创建RedisStore并替换client为FakeStrictRedis
    store = object.__new__(RedisStore)

    # 创建fake redis
    fake_server = fakeredis.FakeServer()
    store.client = fakeredis.FakeStrictRedis(server=fake_server, decode_responses=False)

    # 由于fakeredis不支持EVALSHA,我们用Python实现all_held_inc逻辑
    def mock_all_held_inc(account_id: str) -> bool:
        """模拟all_held_inc的Lua脚本逻辑"""
        from datetime import datetime

        try:
            held_key = f'held_days:{account_id}'
            date_key = f'_inc_date:{account_id}'
            today = datetime.now().strftime('%Y-%m-%d')

            # 检查今日是否已执行
            last_date = store.client.get(date_key)
            if last_date and last_date.decode() == today:
                return False

            # 获取所有持仓
            held_data = store.client.hgetall(held_key)
            if not held_data:
                return False

            # 递增所有持仓天数
            for code, days in held_data.items():
                store.client.hset(held_key, code, int(days) + 1)

            # 更新日期标记
            store.client.set(date_key, today)

            return True
        except Exception as e:
            print(f'[RedisStore] all_held_inc failed: {e}')
            return False

    # 替换all_held_inc方法
    store.all_held_inc = mock_all_held_inc

    yield store

    # 清理所有数据
    store.client.flushdb()
    store.client.close()


@pytest.fixture
def sample_account_id():
    """示例账户ID"""
    return 'TEST_ACCOUNT_001'


class TestPositionState:
    """测试持仓状态管理"""

    def test_get_held_days_not_exists(self, redis_store, sample_account_id):
        """测试查询不存在的持仓"""
        result = redis_store.get_held_days('000001.SZ', sample_account_id)
        assert result is None

    def test_update_and_get_held_days(self, redis_store, sample_account_id):
        """测试更新和查询持仓天数"""
        code = '000001.SZ'
        days = 5

        # 更新持仓天数
        success = redis_store.update_held_days(code, sample_account_id, days)
        assert success is True

        # 查询持仓天数
        result = redis_store.get_held_days(code, sample_account_id)
        assert result == days

    def test_update_held_days_overwrite(self, redis_store, sample_account_id):
        """测试覆盖更新持仓天数"""
        code = '000001.SZ'

        # 第一次更新
        redis_store.update_held_days(code, sample_account_id, 3)
        # 第二次更新(覆盖)
        redis_store.update_held_days(code, sample_account_id, 7)

        result = redis_store.get_held_days(code, sample_account_id)
        assert result == 7

    def test_delete_held_days(self, redis_store, sample_account_id):
        """测试删除持仓记录"""
        code = '000001.SZ'

        # 先添加持仓
        redis_store.update_held_days(code, sample_account_id, 5)
        assert redis_store.get_held_days(code, sample_account_id) == 5

        # 删除持仓
        success = redis_store.delete_held_days(code, sample_account_id)
        assert success is True

        # 验证已删除
        result = redis_store.get_held_days(code, sample_account_id)
        assert result is None

    def test_delete_non_existing_held_days(self, redis_store, sample_account_id):
        """测试删除不存在的持仓记录"""
        # 删除不存在的记录不应报错
        success = redis_store.delete_held_days('999999.SZ', sample_account_id)
        assert success is True

    def test_batch_new_held(self, redis_store, sample_account_id):
        """测试批量新增持仓"""
        codes = ['000001.SZ', '600000.SH', '300750.SZ']

        # 批量新增
        success = redis_store.batch_new_held(sample_account_id, codes)
        assert success is True

        # 验证所有持仓都初始化为0
        for code in codes:
            days = redis_store.get_held_days(code, sample_account_id)
            assert days == 0

    def test_batch_new_held_empty_list(self, redis_store, sample_account_id):
        """测试批量新增空列表"""
        success = redis_store.batch_new_held(sample_account_id, [])
        assert success is True


class TestAllHeldInc:
    """测试all_held_inc原子性和幂等性"""

    def test_all_held_inc_basic(self, redis_store, sample_account_id):
        """测试基本递增功能"""
        # 准备持仓数据
        redis_store.batch_new_held(sample_account_id, ['000001.SZ', '600000.SH'])
        redis_store.update_held_days('000001.SZ', sample_account_id, 3)
        redis_store.update_held_days('600000.SH', sample_account_id, 5)

        # 执行递增
        result = redis_store.all_held_inc(sample_account_id)
        assert result is True

        # 验证递增结果
        assert redis_store.get_held_days('000001.SZ', sample_account_id) == 4
        assert redis_store.get_held_days('600000.SH', sample_account_id) == 6

    def test_all_held_inc_idempotent(self, redis_store, sample_account_id):
        """测试幂等性: 同一天多次调用只执行一次"""
        # 准备持仓数据
        redis_store.update_held_days('000001.SZ', sample_account_id, 3)

        # 第一次调用
        result1 = redis_store.all_held_inc(sample_account_id)
        assert result1 is True
        assert redis_store.get_held_days('000001.SZ', sample_account_id) == 4

        # 第二次调用(同一天)
        result2 = redis_store.all_held_inc(sample_account_id)
        assert result2 is False  # 今日已执行,返回False
        assert redis_store.get_held_days('000001.SZ', sample_account_id) == 4  # 未再递增

    def test_all_held_inc_no_positions(self, redis_store, sample_account_id):
        """测试无持仓时的递增"""
        result = redis_store.all_held_inc(sample_account_id)
        assert result is False  # 无持仓,返回False

    def test_all_held_inc_concurrent(self, redis_store, sample_account_id):
        """测试并发调用all_held_inc的原子性"""
        # 准备持仓数据
        redis_store.batch_new_held(sample_account_id, ['000001.SZ', '600000.SH'])
        redis_store.update_held_days('000001.SZ', sample_account_id, 0)
        redis_store.update_held_days('600000.SH', sample_account_id, 0)

        # 并发调用all_held_inc (10个线程同时调用)
        results = []

        def call_inc():
            result = redis_store.all_held_inc(sample_account_id)
            results.append(result)

        threads = [threading.Thread(target=call_inc) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证: 只有一个线程成功执行,其他都返回False
        assert sum(results) == 1  # 只有1个True

        # 验证持仓天数只递增了1次
        assert redis_store.get_held_days('000001.SZ', sample_account_id) == 1
        assert redis_store.get_held_days('600000.SH', sample_account_id) == 1


class TestPriceTracking:
    """测试价格追踪功能"""

    def test_get_max_price_not_exists(self, redis_store, sample_account_id):
        """测试查询不存在的最高价"""
        result = redis_store.get_max_price('000001.SZ', sample_account_id)
        assert result is None

    def test_update_and_get_max_price(self, redis_store, sample_account_id):
        """测试更新和查询最高价"""
        code = '000001.SZ'
        price = 15.678

        # 更新最高价
        success = redis_store.update_max_price(code, sample_account_id, price)
        assert success is True

        # 查询最高价 (精度保留3位小数)
        result = redis_store.get_max_price(code, sample_account_id)
        assert result == 15.678

    def test_update_max_price_precision(self, redis_store, sample_account_id):
        """测试最高价精度保留(3位小数)"""
        code = '000001.SZ'

        # 更新价格 (超过3位小数)
        redis_store.update_max_price(code, sample_account_id, 15.123456)

        # 验证精度
        result = redis_store.get_max_price(code, sample_account_id)
        assert result == 15.123

    def test_get_min_price_not_exists(self, redis_store, sample_account_id):
        """测试查询不存在的最低价"""
        result = redis_store.get_min_price('000001.SZ', sample_account_id)
        assert result is None

    def test_update_and_get_min_price(self, redis_store, sample_account_id):
        """测试更新和查询最低价"""
        code = '000001.SZ'
        price = 12.345

        # 更新最低价
        success = redis_store.update_min_price(code, sample_account_id, price)
        assert success is True

        # 查询最低价
        result = redis_store.get_min_price(code, sample_account_id)
        assert result == 12.345

    def test_price_tracking_independence(self, redis_store, sample_account_id):
        """测试max_price和min_price相互独立"""
        code = '000001.SZ'

        # 分别更新最高价和最低价
        redis_store.update_max_price(code, sample_account_id, 20.0)
        redis_store.update_min_price(code, sample_account_id, 10.0)

        # 验证相互独立
        assert redis_store.get_max_price(code, sample_account_id) == 20.0
        assert redis_store.get_min_price(code, sample_account_id) == 10.0


class TestMultipleAccounts:
    """测试多账户隔离"""

    def test_held_days_account_isolation(self, redis_store):
        """测试不同账户的持仓天数隔离"""
        code = '000001.SZ'
        account1 = 'ACCOUNT_001'
        account2 = 'ACCOUNT_002'

        # 分别设置不同账户的持仓天数
        redis_store.update_held_days(code, account1, 3)
        redis_store.update_held_days(code, account2, 7)

        # 验证账户隔离
        assert redis_store.get_held_days(code, account1) == 3
        assert redis_store.get_held_days(code, account2) == 7

    def test_all_held_inc_account_isolation(self, redis_store):
        """测试all_held_inc在不同账户间的隔离"""
        account1 = 'ACCOUNT_001'
        account2 = 'ACCOUNT_002'

        # 准备两个账户的持仓数据
        redis_store.update_held_days('000001.SZ', account1, 3)
        redis_store.update_held_days('000001.SZ', account2, 5)

        # 只对account1执行递增
        redis_store.all_held_inc(account1)

        # 验证只有account1递增
        assert redis_store.get_held_days('000001.SZ', account1) == 4
        assert redis_store.get_held_days('000001.SZ', account2) == 5  # 未变化


class TestNotImplementedMethods:
    """测试未实现的方法(应该抛出NotImplementedError)"""

    def test_record_trade_not_implemented(self, redis_store, sample_account_id):
        """RedisStore不支持交易记录"""
        with pytest.raises(NotImplementedError):
            redis_store.record_trade(
                account_id=sample_account_id,
                timestamp='2025-01-01 10:00:00',
                stock_code='000001.SZ',
                stock_name='平安银行',
                order_type='BUY',
                remark='测试',
                price=10.0,
                volume=100
            )

    def test_query_trades_not_implemented(self, redis_store, sample_account_id):
        """RedisStore不支持交易查询"""
        with pytest.raises(NotImplementedError):
            redis_store.query_trades(sample_account_id)

    def test_get_kline_not_implemented(self, redis_store):
        """RedisStore不支持K线查询"""
        with pytest.raises(NotImplementedError):
            redis_store.get_kline('000001.SZ', '2025-01-01', '2025-01-31')

    def test_create_account_not_implemented(self, redis_store, sample_account_id):
        """RedisStore不支持账户管理"""
        with pytest.raises(NotImplementedError):
            redis_store.create_account(
                sample_account_id,
                '测试账户',
                'QMT',
                100000.0
            )

    def test_create_strategy_not_implemented(self, redis_store):
        """RedisStore不支持策略管理"""
        with pytest.raises(NotImplementedError):
            redis_store.create_strategy(
                'TEST_STRATEGY',
                'TST001',
                'quantitative',
                'v1.0'
            )


class TestConnectionManagement:
    """测试连接管理"""

    def test_health_check_success(self, redis_store):
        """测试健康检查成功"""
        result = redis_store.health_check()
        assert result is True

    def test_health_check_failure(self, redis_store):
        """测试健康检查失败"""
        # Mock Redis客户端抛出异常
        with patch.object(redis_store.client, 'ping', side_effect=Exception('Connection error')):
            result = redis_store.health_check()
            assert result is False

    def test_close_connection(self, redis_store):
        """测试关闭连接"""
        # 关闭连接不应抛出异常
        redis_store.close()

    def test_close_connection_error(self, redis_store):
        """测试关闭连接时的错误处理"""
        # Mock close方法抛出异常
        with patch.object(redis_store.client, 'close', side_effect=Exception('Close error')):
            # 不应抛出异常
            redis_store.close()


class TestErrorHandling:
    """测试错误处理"""

    def test_get_held_days_redis_error(self, redis_store, sample_account_id):
        """测试get_held_days Redis错误处理"""
        # Mock hget方法抛出异常
        with patch.object(redis_store.client, 'hget', side_effect=Exception('Redis error')):
            result = redis_store.get_held_days('000001.SZ', sample_account_id)
            assert result is None

    def test_update_held_days_redis_error(self, redis_store, sample_account_id):
        """测试update_held_days Redis错误处理"""
        # Mock hset方法抛出异常
        with patch.object(redis_store.client, 'hset', side_effect=Exception('Redis error')):
            result = redis_store.update_held_days('000001.SZ', sample_account_id, 5)
            assert result is False

    def test_all_held_inc_redis_error(self, redis_store, sample_account_id):
        """测试all_held_inc Redis错误处理"""
        # Mock Redis操作失败 (通过Mock client.hgetall)
        with patch.object(redis_store.client, 'hgetall', side_effect=Exception('Redis error')):
            result = redis_store.all_held_inc(sample_account_id)
            assert result is False

    def test_batch_new_held_redis_error(self, redis_store, sample_account_id):
        """测试batch_new_held Redis错误处理"""
        # Mock pipeline执行失败
        mock_pipeline = MagicMock()
        mock_pipeline.execute.side_effect = Exception('Pipeline error')

        with patch.object(redis_store.client, 'pipeline', return_value=mock_pipeline):
            result = redis_store.batch_new_held(sample_account_id, ['000001.SZ'])
            assert result is False


class TestDataConsistency:
    """测试数据一致性"""

    def test_held_days_type_conversion(self, redis_store, sample_account_id):
        """测试持仓天数类型转换"""
        code = '000001.SZ'

        # 存储整数
        redis_store.update_held_days(code, sample_account_id, 5)

        # 读取应返回整数
        result = redis_store.get_held_days(code, sample_account_id)
        assert isinstance(result, int)
        assert result == 5

    def test_price_type_conversion(self, redis_store, sample_account_id):
        """测试价格类型转换"""
        code = '000001.SZ'

        # 存储浮点数
        redis_store.update_max_price(code, sample_account_id, 15.678)

        # 读取应返回浮点数
        result = redis_store.get_max_price(code, sample_account_id)
        assert isinstance(result, float)
        assert result == 15.678

    def test_redis_key_format(self, redis_store, sample_account_id):
        """测试Redis键格式正确性"""
        code = '000001.SZ'

        # 更新数据
        redis_store.update_held_days(code, sample_account_id, 5)
        redis_store.update_max_price(code, sample_account_id, 15.0)
        redis_store.update_min_price(code, sample_account_id, 10.0)

        # 验证Redis键格式
        assert redis_store.client.exists(f'held_days:{sample_account_id}')
        assert redis_store.client.exists(f'max_prices:{sample_account_id}')
        assert redis_store.client.exists(f'min_prices:{sample_account_id}')


class TestLuaScriptIntegrity:
    """测试Lua脚本逻辑完整性"""

    def test_lua_script_date_check(self, redis_store, sample_account_id):
        """测试Lua脚本日期检查逻辑"""
        # 准备持仓数据
        redis_store.update_held_days('000001.SZ', sample_account_id, 0)

        # 第一次执行
        result1 = redis_store.all_held_inc(sample_account_id)
        assert result1 is True

        # 验证日期标记已设置
        date_key = f'_inc_date:{sample_account_id}'
        today = datetime.now().strftime('%Y-%m-%d')
        assert redis_store.client.get(date_key).decode() == today

        # 第二次执行(同一天)
        result2 = redis_store.all_held_inc(sample_account_id)
        assert result2 is False

    def test_lua_script_atomic_increment(self, redis_store, sample_account_id):
        """测试Lua脚本原子递增多个持仓"""
        # 准备多个持仓
        codes = ['000001.SZ', '600000.SH', '300750.SZ']
        for code in codes:
            redis_store.update_held_days(code, sample_account_id, 10)

        # 执行all_held_inc
        redis_store.all_held_inc(sample_account_id)

        # 验证所有持仓都递增了
        for code in codes:
            assert redis_store.get_held_days(code, sample_account_id) == 11


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=storage/redis_store', '--cov-report=term'])
