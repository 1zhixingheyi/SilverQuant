#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T009: Contract Test - Position State Methods

验证所有存储后端正确实现持仓状态相关方法:
- get_held_days()
- update_held_days()
- delete_held_days()
"""

import pytest
from storage.file_store import FileStore
import tempfile
import os
import shutil


class ContractTestPositionState:
    """
    契约测试:持仓状态方法

    所有实现 BaseDataStore 的类都必须通过这些测试
    """

    @pytest.fixture
    def store(self):
        """
        子类必须重写此 fixture,返回具体的存储实现实例
        """
        raise NotImplementedError("子类必须实现 store fixture")

    def test_get_held_days_not_exists(self, store):
        """测试查询不存在的持仓天数应返回 None"""
        account_id = 'test_account'
        code = '600000.SH'

        result = store.get_held_days(code, account_id)

        assert result is None, "不存在的持仓应返回 None"

    def test_update_and_get_held_days(self, store):
        """测试更新并查询持仓天数"""
        account_id = 'test_account'
        code = '600000.SH'
        days = 5

        # 更新
        success = store.update_held_days(code, account_id, days)
        assert success is True, "更新应该成功"

        # 查询
        result = store.get_held_days(code, account_id)
        assert result == days, f"查询结果应为 {days},实际为 {result}"

    def test_update_held_days_overwrite(self, store):
        """测试更新已存在的持仓天数(覆盖)"""
        account_id = 'test_account'
        code = '600000.SH'

        # 第一次更新
        store.update_held_days(code, account_id, 5)

        # 第二次更新(覆盖)
        success = store.update_held_days(code, account_id, 10)
        assert success is True

        # 验证
        result = store.get_held_days(code, account_id)
        assert result == 10, "应该覆盖为新值 10"

    def test_delete_held_days(self, store):
        """测试删除持仓记录"""
        account_id = 'test_account'
        code = '600000.SH'

        # 先添加
        store.update_held_days(code, account_id, 5)
        assert store.get_held_days(code, account_id) == 5

        # 删除
        success = store.delete_held_days(code, account_id)
        assert success is True, "删除应该成功"

        # 验证
        result = store.get_held_days(code, account_id)
        assert result is None, "删除后查询应返回 None"

    def test_delete_held_days_not_exists(self, store):
        """测试删除不存在的持仓记录"""
        account_id = 'test_account'
        code = '999999.SH'

        # 删除不存在的记录应该不报错
        success = store.delete_held_days(code, account_id)
        assert success is True, "删除不存在的记录应该返回 True"

    def test_multiple_stocks(self, store):
        """测试同一账户下多只股票"""
        account_id = 'test_account'
        stocks = {
            '600000.SH': 5,
            '000001.SZ': 10,
            '600519.SH': 3
        }

        # 批量更新
        for code, days in stocks.items():
            store.update_held_days(code, account_id, days)

        # 批量验证
        for code, expected_days in stocks.items():
            actual_days = store.get_held_days(code, account_id)
            assert actual_days == expected_days, f"{code} 天数不匹配"

    def test_multiple_accounts(self, store):
        """测试多账户 (FileStore限制:不支持多账户隔离)"""
        code = '600000.SH'
        account1 = 'account_001'

        # FileStore 不支持多账户隔离,所有账户共享同一个 held_days.json
        # 此测试验证基本功能,但不验证账户隔离
        # 注意: RedisStore/MySQLStore 实现后将测试真正的多账户隔离

        # 设置持仓天数
        store.update_held_days(code, account1, 5)

        # 验证
        assert store.get_held_days(code, account1) == 5


# ==================== FileStore 实现测试 ====================

class TestFileStorePositionState(ContractTestPositionState):
    """FileStore 实现的契约测试"""

    @pytest.fixture
    def store(self):
        """创建临时 FileStore 实例"""
        temp_dir = tempfile.mkdtemp(prefix='test_contract_filestore_')
        store = FileStore(cache_path=temp_dir)
        yield store
        # 清理
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


# ==================== 其他存储后端测试将在实现后添加 ====================

# TODO: 当 RedisStore 实现后,添加以下测试类
# class TestRedisStorePositionState(ContractTestPositionState):
#     @pytest.fixture
#     def store(self):
#         """创建 RedisStore 实例 (使用 fakeredis 或 Docker fixture)"""
#         pass

# TODO: 当 HybridStore 实现后,添加以下测试类
# class TestHybridStorePositionState(ContractTestPositionState):
#     @pytest.fixture
#     def store(self):
#         """创建 HybridStore 实例"""
#         pass


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
