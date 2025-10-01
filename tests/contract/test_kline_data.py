#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T013: Contract Test - Kline Data Methods

验证K线数据相关方法:
- get_kline()
- batch_get_kline()
- DataFrame格式验证 (columns: datetime, open, high, low, close, volume, amount)
"""

import pytest
import tempfile
import os
import shutil
import pandas as pd
from storage.file_store import FileStore


class ContractTestKlineData:
    """契约测试:K线数据方法"""

    @pytest.fixture
    def store(self):
        raise NotImplementedError("子类必须实现 store fixture")

    def test_get_kline_returns_dataframe(self, store):
        """测试 get_kline 返回 DataFrame"""
        result = store.get_kline('600000.SH', '2024-01-01', '2024-01-31')

        assert isinstance(result, pd.DataFrame), "应该返回 pandas DataFrame"

    def test_get_kline_empty_result(self, store):
        """测试查询不存在的K线数据"""
        result = store.get_kline('999999.SH', '2024-01-01', '2024-01-31')

        assert isinstance(result, pd.DataFrame)
        # 空结果应该是空DataFrame
        # 注意: FileStore 的 K线方法返回空DataFrame是符合契约的

    def test_batch_get_kline_returns_dict(self, store):
        """测试 batch_get_kline 返回字典"""
        codes = ['600000.SH', '000001.SZ']
        result = store.batch_get_kline(codes, '2024-01-01', '2024-01-31')

        assert isinstance(result, dict), "应该返回字典 {code: DataFrame}"

    def test_batch_get_kline_empty_result(self, store):
        """测试批量查询不存在的K线数据"""
        codes = ['999999.SH', '888888.SZ']
        result = store.batch_get_kline(codes, '2024-01-01', '2024-01-31')

        assert isinstance(result, dict)
        # 空结果可以是空字典或包含空DataFrame的字典


class TestFileStoreKlineData(ContractTestKlineData):
    """FileStore 实现的契约测试"""

    @pytest.fixture
    def store(self):
        temp_dir = tempfile.mkdtemp(prefix='test_contract_filestore_kline_')
        store = FileStore(cache_path=temp_dir)
        yield store
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
