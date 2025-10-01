#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T015: Contract Test - Strategy Management Methods

验证策略管理相关方法:
- create_strategy()
- get_strategy_params()
- save_strategy_params()
- compare_strategy_params()
"""

import pytest
import tempfile
import os
import shutil
from storage.file_store import FileStore


class ContractTestStrategyManagement:
    """契约测试:策略管理方法"""

    @pytest.fixture
    def store(self):
        raise NotImplementedError("子类必须实现 store fixture")

    def test_create_strategy(self, store):
        """测试创建策略"""
        success = store.create_strategy(
            strategy_name='测试策略',
            strategy_code='test_strategy',
            strategy_type='wencai',
            version='1.0.0'
        )

        assert success is True, "创建策略应该成功"

    def test_get_strategy_params_not_exists(self, store):
        """测试查询不存在的策略参数"""
        result = store.get_strategy_params('not_exists')

        assert result is None, "不存在的策略应返回 None"

    def test_create_and_get_strategy_params(self, store):
        """测试创建策略并查询参数"""
        strategy_code = 'test_strategy_001'

        # 创建策略
        store.create_strategy('测试策略001', strategy_code, 'wencai', '1.0.0')

        # 查询参数(初始为空)
        params = store.get_strategy_params(strategy_code)

        assert params is not None
        assert isinstance(params, dict), "参数应该是字典"
        # 初始参数可能是空字典
        assert isinstance(params, dict)

    def test_save_strategy_params(self, store):
        """测试保存策略参数"""
        strategy_code = 'test_strategy_002'

        # 先创建策略
        store.create_strategy('测试策略002', strategy_code, 'remote', '1.0.0')

        # 保存参数
        new_params = {'threshold': 0.05, 'period': 20}
        success = store.save_strategy_params(strategy_code, new_params)
        assert success is True

        # 验证
        params = store.get_strategy_params(strategy_code)
        assert params == new_params

    def test_save_strategy_params_overwrite(self, store):
        """测试覆盖策略参数"""
        strategy_code = 'test_strategy_003'

        # 创建并保存初始参数
        store.create_strategy('测试策略003', strategy_code, 'technical', '1.0.0')
        store.save_strategy_params(strategy_code, {'threshold': 0.05})

        # 覆盖参数
        new_params = {'threshold': 0.08, 'period': 30}
        success = store.save_strategy_params(strategy_code, new_params)
        assert success is True

        # 验证
        params = store.get_strategy_params(strategy_code)
        assert params == new_params

    def test_compare_strategy_params(self, store):
        """测试对比策略参数差异"""
        strategy_code = 'test_strategy_004'

        # 创建并保存初始参数
        store.create_strategy('测试策略004', strategy_code, 'wencai', '1.0.0')
        old_params = {'threshold': 0.05, 'period': 20, 'ma_type': 'EMA'}
        store.save_strategy_params(strategy_code, old_params)

        # 新参数
        new_params = {'threshold': 0.08, 'period': 20, 'stop_loss': 0.03}

        # 对比差异
        added, modified, deleted = store.compare_strategy_params(strategy_code, new_params)

        assert isinstance(added, dict)
        assert isinstance(modified, dict)
        assert isinstance(deleted, dict)

        # 验证差异
        assert 'stop_loss' in added, "新增参数应该包含 stop_loss"
        assert 'threshold' in modified, "修改参数应该包含 threshold"
        assert 'ma_type' in deleted, "删除参数应该包含 ma_type"

    def test_create_duplicate_strategy(self, store):
        """测试创建重复策略应失败"""
        strategy_code = 'duplicate_strategy'

        # 第一次创建
        success1 = store.create_strategy('策略1', strategy_code, 'wencai', '1.0.0')
        assert success1 is True

        # 第二次创建(重复)
        success2 = store.create_strategy('策略2', strategy_code, 'remote', '2.0.0')
        assert success2 is False, "创建重复策略应该失败"


class TestFileStoreStrategyManagement(ContractTestStrategyManagement):
    """FileStore 实现的契约测试"""

    @pytest.fixture
    def store(self):
        temp_dir = tempfile.mkdtemp(prefix='test_contract_filestore_strategy_')
        store = FileStore(cache_path=temp_dir)
        yield store
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
