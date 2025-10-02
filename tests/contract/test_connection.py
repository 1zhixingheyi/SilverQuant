#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T016: Contract Test - Connection Management Methods

验证连接管理相关方法:
- health_check()
- close()
"""

import pytest
import tempfile
import os
import shutil
from storage.file_store import FileStore


class ContractTestConnection:
    """契约测试:连接管理方法"""

    @pytest.fixture
    def store(self):
        raise NotImplementedError("子类必须实现 store fixture")

    def test_health_check(self, store):
        """测试健康检查"""
        result = store.health_check()

        assert isinstance(result, bool), "health_check 应该返回布尔值"
        # 新创建的存储实例应该健康
        assert result is True, "健康的存储应该返回 True"

    def test_close(self, store):
        """测试关闭连接"""
        # close 方法不应该抛出异常
        try:
            store.close()
            success = True
        except Exception as e:
            success = False
            print(f"close() 抛出异常: {e}")

        assert success is True, "close() 不应该抛出异常"

    def test_health_check_after_close(self, store):
        """测试关闭后的健康检查"""
        # 先关闭
        store.close()

        # 关闭后调用 health_check 应该能正常执行(不一定要返回False)
        try:
            result = store.health_check()
            # 对于FileStore,关闭后health_check仍可能返回True (因为只是检查目录可写)
            assert isinstance(result, bool)
        except Exception:
            # 某些存储可能在关闭后抛出异常,这也是可以接受的
            pass

    def test_multiple_close_calls(self, store):
        """测试多次调用 close()"""
        # 多次调用 close() 不应该报错
        store.close()
        store.close()
        store.close()

        # 成功执行即通过测试

    def test_operations_after_health_check(self, store):
        """测试 health_check 后存储仍可正常使用"""
        # 先健康检查
        health = store.health_check()
        assert health is True

        # 然后执行正常操作
        success = store.update_held_days('600000.SH', 'test_account', 5)
        assert success is True, "health_check后应该仍能正常操作"

        # 验证数据
        days = store.get_held_days('600000.SH', 'test_account')
        assert days == 5


class TestFileStoreConnection(ContractTestConnection):
    """FileStore 实现的契约测试"""

    @pytest.fixture
    def store(self):
        temp_dir = tempfile.mkdtemp(prefix='test_contract_filestore_connection_')
        store = FileStore(cache_path=temp_dir)
        yield store
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
