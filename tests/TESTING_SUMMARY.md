# 数据存储模块测试总结

**日期**: 2025-10-01
**测试覆盖目标**: >80%

## 测试架构 (三层)

### 1. 契约测试 (Contract Tests) - tests/contract/ ✅
**目的**: 验证所有存储实现符合 BaseDataStore 接口契约

已实施的契约测试:
- test_position_state.py: 持仓状态方法 (get_held_days, update_held_days, delete_held_days)
- test_position_increment.py: 持仓递增原子性 (all_held_inc)
- test_price_tracking.py: 价格追踪方法 (get_max_price, update_max_price, etc.)
- test_trade_records.py: 交易记录方法 (record_trade, query_trades, aggregate_trades)
- test_kline_data.py: K线数据方法 (get_kline, batch_get_kline)
- test_account_mgmt.py: 账户管理方法 (create_account, get_account, etc.)
- test_strategy_mgmt.py: 策略管理方法 (create_strategy, get_strategy_params, etc.)
- test_connection.py: 连接管理 (health_check, close)

**执行方式**: `pytest tests/contract/ -v`
**覆盖范围**: 所有 BaseDataStore 接口方法

### 2. 单元测试 (Unit Tests) - tests/unit/
**目的**: 测试各存储实现的具体逻辑

#### T077: FileStore 单元测试 ✅
**文件**: tests/unit/test_file_store.py
**测试内容**:
- 持仓状态: 文件读写正确性, JSON格式验证
- 交易记录: CSV追加写入, pandas读取过滤
- K线数据: 缓存机制, DataFrame格式
- 并发安全: 文件锁测试
- 错误处理: 文件不存在, 权限错误

**覆盖率目标**: >90%
**执行**: `pytest tests/unit/test_file_store.py -v --cov=storage/file_store`

#### T078: RedisStore 单元测试 ✅
**文件**: tests/unit/test_redis_store.py
**测试内容**:
- 持仓状态: HGET/HSET正确性 ✅
- all_held_inc: Lua脚本原子性和幂等性 (10线程并发测试) ✅
- 价格追踪: HGET/HSET max/min prices, 精度保留3位小数 ✅
- 多账户隔离: 验证不同账户数据独立性 ✅
- 连接管理: health_check, close ✅
- 错误处理: Redis连接失败, 超时等异常 ✅
- NotImplementedError: 验证不支持的方法正确抛出异常 ✅
- 数据一致性: 类型转换, Redis键格式验证 ✅

**技术选型**: fakeredis v2.31.3 (Python模拟all_held_inc Lua逻辑)
**覆盖率**: 67% (未覆盖部分为NotImplementedError方法和Lua脚本注册)
**测试数量**: 37个测试用例,全部通过
**执行**: `pytest tests/unit/test_redis_store.py -v --cov=storage`

#### T079: MySQLStore 单元测试 ✅
**文件**: tests/unit/test_mysql_store.py
**测试内容**:
- 账户管理: create_account (唯一性约束), get_account (字典格式), update_account_capital ✅
- 策略管理: create_strategy (重复检测), get_strategy_params (版本过滤), save_strategy_params (版本rollover) ✅
- 参数版本化: is_active标志切换 (旧版本设为False), 版本号自增 ✅
- 参数对比: compare_strategy_params (added/modified/deleted差异检测) ✅
- SQLAlchemy ORM: Account-Strategy关系, Strategy-Param关系 ✅
- 事务处理: 提交失败回滚验证 ✅
- 错误处理: 数据库连接失败, 查询异常 ✅
- 数据一致性: Decimal精度, JSON序列化, 时间戳自动更新, 默认值 ✅
- NotImplementedError: 验证不支持的方法正确抛出异常 ✅

**技术选型**: SQLite in-memory database (完全兼容SQLAlchemy ORM)
**覆盖率**: 82% (未覆盖部分主要为NotImplementedError方法)
**测试数量**: 30个测试用例,全部通过
**执行**: `pytest tests/unit/test_mysql_store.py -v --cov=storage`

#### T080: ClickHouseStore 单元测试 ⏸
**文件**: tests/unit/test_clickhouse_store.py (待创建)
**测试内容**:
- 交易记录: INSERT批量写入, 分区查询
- K线数据: 时间范围过滤, 聚合统计
- 聚合查询: aggregate_trades (按月/年统计)
- 性能测试: 大数据量查询 (<100ms)
- 错误处理: ClickHouse连接失败

**依赖**: Docker ClickHouse容器
**覆盖率目标**: >85%
**执行**: `pytest tests/unit/test_clickhouse_store.py -v --cov=storage/clickhouse_store`

#### T081: HybridStore 单元测试 ✅
**文件**: tests/unit/test_hybrid_store.py
**测试内容**:
- 双写模式: 验证Redis和File同时写入
- 自动降级: Mock数据库异常, 验证降级到File
- 健康检查: 聚合所有后端状态
- 降级日志: 验证WARNING日志记录
- 一致性: 双写后数据一致性校验

**覆盖率目标**: >85%
**执行**: `pytest tests/unit/test_hybrid_store.py -v --cov=storage/hybrid_store`

### 3. 集成测试 (Integration Tests) - tests/integration/ ✅
**目的**: 测试实际使用场景

已实施的集成测试:
- test_database_init.py: 数据库初始化流程
- test_migrate_positions.py: 持仓数据迁移
- test_migrate_trades.py: 交易记录迁移
- test_hybrid_dual_write.py: 双写模式验证
- test_auto_fallback.py: 自动降级验证
- test_trading_cycle.py: 完整交易周期

**执行方式**: `pytest tests/integration/ -v`
**前提**: Docker数据库容器运行中

## T082: 性能基准测试 ⏸
**文件**: tests/integration/test_performance.py (待创建)
**测试内容**:
- get_held_days: <1ms (Redis)
- query_trades: <100ms (ClickHouse, 1年数据)
- get_kline: <20ms (ClickHouse, 60天)
- aggregate_trades: <500ms (ClickHouse, 3年)
- 性能报告: before/after对比图表

**执行**: `pytest tests/integration/test_performance.py -v --benchmark-only`

##执行全部测试

```bash
# 契约测试
pytest tests/contract/ -v

# 单元测试 (已有)
pytest tests/unit/test_file_store.py -v --cov=storage/file_store
pytest tests/unit/test_hybrid_store.py -v --cov=storage/hybrid_store

# 单元测试 (待补充)
pytest tests/unit/test_redis_store.py -v --cov=storage/redis_store
pytest tests/unit/test_mysql_store.py -v --cov=storage/mysql_store
pytest tests/unit/test_clickhouse_store.py -v --cov=storage/clickhouse_store

# 集成测试
pytest tests/integration/ -v

# 性能测试
pytest tests/integration/test_performance.py -v --benchmark-only

# 全部测试 + 覆盖率报告
pytest tests/ -v --cov=storage --cov-report=html --cov-report=term
```

## 测试状态总结

| 测试类型 | 状态 | 覆盖范围 |
|---------|------|---------|
| 契约测试 (T009-T016) | ✅ 完成 | 100% 接口方法 |
| 集成测试 (T017-T022) | ✅ 完成 | 6个关键场景 |
| FileStore单元测试 (T077) | ✅ 完成 | >90% 代码 |
| HybridStore单元测试 (T081) | ✅ 完成 | >85% 代码 |
| RedisStore单元测试 (T078) | ✅ 完成 | 67% 覆盖 (37测试) |
| MySQLStore单元测试 (T079) | ✅ 完成 | 82% 覆盖 (30测试) |
| ClickHouseStore单元测试 (T080) | ⏸ 待实施 | 目标>85% |
| 性能基准测试 (T082) | ⏸ 待实施 | 4个关键指标 |

## 测试优先级建议

**高优先级** (必须实施):
1. 契约测试: 确保接口一致性 ✅
2. FileStore测试: 向后兼容性基础 ✅
3. HybridStore测试: 双写和降级逻辑 ✅
4. 集成测试: 端到端验证 ✅

**中优先级** (推荐实施):
1. RedisStore测试: 高频操作正确性
2. 性能测试: 验证优化效果

**低优先级** (可选):
1. MySQLStore测试: WARM层低频操作
2. ClickHouseStore测试: COOL层查询验证

## 测试数据准备

### Mock数据生成器
```python
# tests/conftest.py
import pytest
from datetime import datetime, timedelta

@pytest.fixture
def mock_held_days():
    """生成测试持仓数据"""
    return {
        '000001.SZ': 5,
        '600000.SH': 3,
        '300750.SZ': 1
    }

@pytest.fixture
def mock_trade_records():
    """生成测试交易记录"""
    trades = []
    base_date = datetime.now() - timedelta(days=30)
    for i in range(100):
        trades.append({
            'timestamp': (base_date + timedelta(days=i)).isoformat(),
            'account_id': 'TEST001',
            'stock_code': f'{i%10:06d}.SZ',
            'order_type': 'BUY' if i % 2 == 0 else 'SELL',
            'price': 10.0 + i * 0.1,
            'volume': 100 * (i + 1)
        })
    return trades
```

## 覆盖率报告

查看详细覆盖率报告:
```bash
# 生成HTML报告
pytest tests/ --cov=storage --cov-report=html

# 打开报告
start htmlcov/index.html  # Windows
```

**当前覆盖率估算** (基于已完成测试):
- storage/base_store.py: 100% (抽象类)
- storage/file_store.py: ~90% (已测试)
- storage/hybrid_store.py: ~85% (已测试)
- storage/redis_store.py: ~60% (仅契约测试)
- storage/mysql_store.py: ~60% (仅契约测试)
- storage/clickhouse_store.py: ~60% (仅契约测试)
- storage/logging_config.py: ~70% (装饰器已使用)
- **整体覆盖率**: ~75% (目标: >80%)

## 下一步行动

1. **完成 T078-T080**: 创建 Redis/MySQL/ClickHouse 单元测试
2. **完成 T082**: 创建性能基准测试
3. **提高覆盖率**: 补充边界条件和异常处理测试
4. **CI/CD集成**: 在GitHub Actions中自动运行测试

---

**测试哲学**: "Contract First, Integration Second, Unit Last"
- 契约测试确保接口一致性
- 集成测试验证实际使用场景
- 单元测试覆盖边界条件和错误处理
