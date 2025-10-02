#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T014: Contract Test - Account Management Methods

验证账户管理相关方法:
- create_account()
- get_account()
- update_account_capital()
"""

import pytest
import tempfile
import os
import shutil
from storage.file_store import FileStore


class ContractTestAccountManagement:
    """契约测试:账户管理方法"""

    @pytest.fixture
    def store(self):
        raise NotImplementedError("子类必须实现 store fixture")

    def test_create_account(self, store):
        """测试创建账户"""
        success = store.create_account(
            account_id='test_001',
            account_name='测试账户',
            broker='QMT',
            initial_capital=100000.0
        )

        assert success is True, "创建账户应该成功"

    def test_get_account_not_exists(self, store):
        """测试查询不存在的账户"""
        result = store.get_account('not_exists')

        assert result is None, "不存在的账户应返回 None"

    def test_create_and_get_account(self, store):
        """测试创建并查询账户"""
        account_id = 'test_002'
        account_name = '测试账户2'
        broker = 'QMT'
        initial_capital = 100000.0

        # 创建
        store.create_account(account_id, account_name, broker, initial_capital)

        # 查询
        account = store.get_account(account_id)

        assert account is not None
        assert isinstance(account, dict), "账户信息应该是字典"
        assert account['account_name'] == account_name
        assert account['broker'] == broker
        assert account['initial_capital'] == initial_capital

    def test_create_duplicate_account(self, store):
        """测试创建重复账户应失败"""
        account_id = 'test_003'

        # 第一次创建
        success1 = store.create_account(account_id, '账户1', 'QMT', 100000.0)
        assert success1 is True

        # 第二次创建(重复)
        success2 = store.create_account(account_id, '账户2', 'GM', 50000.0)
        assert success2 is False, "创建重复账户应该失败"

    def test_update_account_capital(self, store):
        """测试更新账户资金"""
        account_id = 'test_004'

        # 先创建账户
        store.create_account(account_id, '测试账户4', 'QMT', 100000.0)

        # 更新资金
        success = store.update_account_capital(account_id, 105000.0)
        assert success is True

        # 验证
        account = store.get_account(account_id)
        assert account['current_capital'] == 105000.0

    def test_update_account_capital_not_exists(self, store):
        """测试更新不存在的账户资金"""
        success = store.update_account_capital('not_exists', 100000.0)

        assert success is False, "更新不存在的账户应该失败"

    def test_multiple_accounts(self, store):
        """测试创建多个账户"""
        accounts = [
            ('account_001', '账户1', 'QMT', 100000.0),
            ('account_002', '账户2', 'GM', 200000.0),
            ('account_003', '账户3', 'TDX', 50000.0)
        ]

        # 批量创建
        for account_id, name, broker, capital in accounts:
            success = store.create_account(account_id, name, broker, capital)
            assert success is True

        # 批量验证
        for account_id, name, broker, capital in accounts:
            account = store.get_account(account_id)
            assert account is not None
            assert account['account_name'] == name
            assert account['broker'] == broker


class TestFileStoreAccountManagement(ContractTestAccountManagement):
    """FileStore 实现的契约测试"""

    @pytest.fixture
    def store(self):
        temp_dir = tempfile.mkdtemp(prefix='test_contract_filestore_account_')
        store = FileStore(cache_path=temp_dir)
        yield store
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
