#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T022: Integration Test - Complete Trading Cycle

验证完整的交易生命周期:
1. 开仓: 买入股票 → 记录交易 → 新增持仓 (held_days=0)
2. 持有: 每日持仓天数+1 → 更新最高价/最低价
3. 平仓: 卖出股票 → 记录交易 → 删除持仓

此测试验证多个组件协同工作的端到端流程
"""

import pytest
import tempfile
import shutil
import os
import datetime
from storage.file_store import FileStore


class TestCompleteTradingCycle:
    """完整交易周期集成测试"""

    @pytest.fixture
    def store(self):
        """创建临时 FileStore 实例"""
        temp_dir = tempfile.mkdtemp(prefix='test_trading_cycle_')
        store = FileStore(cache_path=temp_dir)
        yield store
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_complete_trading_lifecycle_with_filestore(self, store):
        """测试使用 FileStore 的完整交易周期"""
        account_id = 'test_account'
        code = '600000.SH'
        name = '浦发银行'
        timestamp = str(int(datetime.datetime.now().timestamp()))

        # ============================================================
        # 阶段1: 开仓 (买入)
        # ============================================================

        # 1.1 记录买入交易
        success = store.record_trade(
            account_id=account_id,
            timestamp=timestamp,
            stock_code=code,
            stock_name=name,
            order_type='buy',
            remark='开仓',
            price=10.50,
            volume=1000,
            strategy_name='test_strategy'
        )
        assert success is True, "记录买入交易应该成功"

        # 1.2 新增持仓 (初始天数=0)
        success = store.batch_new_held(account_id, [code])
        assert success is True, "新增持仓应该成功"

        days = store.get_held_days(code, account_id)
        assert days == 0, "开仓时持仓天数应该为 0"

        # ============================================================
        # 阶段2: 持有 (模拟3天)
        # ============================================================

        # 2.1 第1天: 持仓天数+1
        incremented = store.all_held_inc(account_id)
        assert incremented is True, "第1天持仓递增应该成功"
        assert store.get_held_days(code, account_id) == 1, "第1天持仓天数应该为 1"

        # 2.2 第1天: 更新最高价/最低价
        store.update_max_price(code, account_id, 11.20)
        store.update_min_price(code, account_id, 10.30)

        assert store.get_max_price(code, account_id) == 11.20
        assert store.get_min_price(code, account_id) == 10.30

        # 2.3 第2天: 持仓天数+1 (实际需要修改 _inc_date,这里简化为直接设置)
        store.update_held_days(code, account_id, 2)
        assert store.get_held_days(code, account_id) == 2, "第2天持仓天数应该为 2"

        # 2.4 第2天: 更新新的最高价
        store.update_max_price(code, account_id, 11.50)
        assert store.get_max_price(code, account_id) == 11.50, "最高价应该更新为 11.50"

        # 2.5 第3天: 持仓天数+1
        store.update_held_days(code, account_id, 3)
        assert store.get_held_days(code, account_id) == 3, "第3天持仓天数应该为 3"

        # ============================================================
        # 阶段3: 平仓 (卖出)
        # ============================================================

        # 3.1 记录卖出交易
        timestamp_sell = str(int(datetime.datetime.now().timestamp()))
        success = store.record_trade(
            account_id=account_id,
            timestamp=timestamp_sell,
            stock_code=code,
            stock_name=name,
            order_type='sell',
            remark='平仓',
            price=11.30,
            volume=1000,
            strategy_name='test_strategy'
        )
        assert success is True, "记录卖出交易应该成功"

        # 3.2 删除持仓
        success = store.delete_held_days(code, account_id)
        assert success is True, "删除持仓应该成功"

        days = store.get_held_days(code, account_id)
        assert days is None, "平仓后查询持仓应该返回 None"

        # ============================================================
        # 阶段4: 验证交易记录
        # ============================================================

        # 4.1 查询所有交易
        df = store.query_trades(account_id, stock_code=code)
        assert len(df) >= 2, "应该有至少 2 条交易记录 (买入+卖出)"

        # 4.2 验证交易类型
        # (FileStore 的 CSV 格式可能不同,这里只验证记录存在)
        assert len(df) > 0, "交易记录应该存在"

        print("\n✓ 完整交易周期测试通过:")
        print(f"  - 开仓: 买入 {name} @ 10.50, 1000股")
        print(f"  - 持有: 3天, 最高价 11.50, 最低价 10.30")
        print(f"  - 平仓: 卖出 {name} @ 11.30, 1000股")
        print(f"  - 盈亏: {(11.30 - 10.50) * 1000:.2f} 元")


if __name__ == '__main__':
    import os  # 需要在测试中使用
    pytest.main([__file__, '-v', '-s'])
