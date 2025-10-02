#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T010: Contract Test - Position Increment Atomicity

验证 all_held_inc() 方法的原子性:
- 同一天第一次调用应返回 True (执行了递增)
- 同一天第二次调用应返回 False (跳过递增)
- 所有持仓天数应该正确递增 +1
"""

import pytest
import tempfile
import os
import shutil
from storage.file_store import FileStore


class ContractTestPositionIncrement:
    """
    契约测试:持仓天数递增原子性

    所有实现 BaseDataStore 的类都必须通过这些测试
    """

    @pytest.fixture
    def store(self):
        """子类必须重写此 fixture"""
        raise NotImplementedError("子类必须实现 store fixture")

    def test_all_held_inc_first_call(self, store):
        """测试同一天第一次调用 all_held_inc 应该成功"""
        account_id = 'test_account'
        codes = ['600000.SH', '000001.SZ', '600519.SH']

        # 初始化持仓
        for code in codes:
            store.update_held_days(code, account_id, 0)

        # 第一次调用应该返回 True
        result = store.all_held_inc(account_id)
        assert result is True, "第一次调用应该返回 True (执行了递增)"

        # 验证所有持仓天数都增加了 1
        for code in codes:
            days = store.get_held_days(code, account_id)
            assert days == 1, f"{code} 的持仓天数应该为 1,实际为 {days}"

    def test_all_held_inc_second_call_same_day(self, store):
        """测试同一天第二次调用 all_held_inc 应该跳过"""
        account_id = 'test_account'
        codes = ['600000.SH', '000001.SZ']

        # 初始化持仓
        for code in codes:
            store.update_held_days(code, account_id, 0)

        # 第一次调用
        result1 = store.all_held_inc(account_id)
        assert result1 is True, "第一次调用应该返回 True"

        # 第二次调用(同一天)
        result2 = store.all_held_inc(account_id)
        assert result2 is False, "同一天第二次调用应该返回 False (跳过递增)"

        # 验证持仓天数没有再次增加
        for code in codes:
            days = store.get_held_days(code, account_id)
            assert days == 1, f"{code} 的持仓天数应该仍为 1,实际为 {days}"

    def test_all_held_inc_empty_positions(self, store):
        """测试空持仓时调用 all_held_inc"""
        account_id = 'test_account_empty'

        # 没有任何持仓
        result = store.all_held_inc(account_id)

        # 应该能正常执行,不报错
        # 返回值可以是 True (执行了标记) 或 False (无持仓,跳过)
        assert isinstance(result, bool), "应该返回布尔值"

    def test_all_held_inc_increments_all_positions(self, store):
        """测试 all_held_inc 递增所有持仓,不遗漏"""
        account_id = 'test_account'
        initial_days = {
            '600000.SH': 0,
            '000001.SZ': 3,
            '600519.SH': 10,
            '688001.SH': 1
        }

        # 初始化不同天数的持仓
        for code, days in initial_days.items():
            store.update_held_days(code, account_id, days)

        # 执行递增
        result = store.all_held_inc(account_id)
        assert result is True

        # 验证所有持仓都增加了 1
        for code, original_days in initial_days.items():
            new_days = store.get_held_days(code, account_id)
            expected_days = original_days + 1
            assert new_days == expected_days, f"{code} 应该增加到 {expected_days},实际为 {new_days}"

    def test_all_held_inc_multiple_accounts(self, store):
        """测试多账户 all_held_inc (FileStore限制:不支持多账户隔离)"""
        account1 = 'account_001'
        code = '600000.SH'

        # FileStore 不支持多账户隔离,所有账户共享同一个 held_days.json
        # 此测试验证基本功能,但不验证账户隔离
        # 注意: RedisStore/MySQLStore 实现后将测试真正的多账户隔离

        # 初始化持仓
        store.update_held_days(code, account1, 5)

        # 执行递增
        result1 = store.all_held_inc(account1)
        assert result1 is True

        # 验证递增成功(不区分账户)
        days = store.get_held_days(code, account1)
        assert days == 6, f"持仓天数应该增加到 6,实际为 {days}"

    def test_all_held_inc_idempotent_same_day(self, store):
        """测试 all_held_inc 的幂等性 (同一天多次调用)"""
        account_id = 'test_account'
        codes = ['600000.SH', '000001.SZ']

        # 初始化持仓
        for code in codes:
            store.update_held_days(code, account_id, 0)

        # 第一次调用
        result1 = store.all_held_inc(account_id)
        assert result1 is True

        # 连续多次调用(模拟异常重试)
        result2 = store.all_held_inc(account_id)
        result3 = store.all_held_inc(account_id)
        result4 = store.all_held_inc(account_id)

        assert result2 is False
        assert result3 is False
        assert result4 is False

        # 验证持仓天数仍然只增加了 1 次
        for code in codes:
            days = store.get_held_days(code, account_id)
            assert days == 1, f"{code} 应该只增加 1 次,实际为 {days}"


# ==================== FileStore 实现测试 ====================

class TestFileStorePositionIncrement(ContractTestPositionIncrement):
    """FileStore 实现的契约测试"""

    @pytest.fixture
    def store(self):
        """创建临时 FileStore 实例"""
        temp_dir = tempfile.mkdtemp(prefix='test_contract_filestore_inc_')
        store = FileStore(cache_path=temp_dir)
        yield store
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


# ==================== 其他存储后端测试将在实现后添加 ====================

# TODO: RedisStore 契约测试
# class TestRedisStorePositionIncrement(ContractTestPositionIncrement):
#     @pytest.fixture
#     def store(self):
#         pass

# TODO: HybridStore 契约测试
# class TestHybridStorePositionIncrement(ContractTestPositionIncrement):
#     @pytest.fixture
#     def store(self):
#         pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
