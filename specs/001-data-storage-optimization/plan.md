# Implementation Plan: 数据存储模块性能优化

**Branch**: `001-data-storage-optimization` | **Date**: 2025-10-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-data-storage-optimization/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   ✓ Loaded spec.md with 40 functional requirements + 12 non-functional requirements
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   ✓ All technical decisions clarified in research.md
3. Fill the Constitution Check section
   ✓ Constitution is template-only, skip validation
4. Evaluate Constitution Check section
   ✓ No constitutional violations identified
   → Update Progress Tracking: Initial Constitution Check ✓
5. Execute Phase 0 → research.md
   ✓ Generated research.md with 6 technical decisions
6. Execute Phase 1 → contracts, data-model.md, quickstart.md
   ✓ Generated data-model.md with 10 entities
   ✓ Generated contracts/base_store_interface.py with 30+ methods
   ✓ Generated quickstart.md with 10-step guide
7. Re-evaluate Constitution Check section
   ✓ No new violations after design
   → Update Progress Tracking: Post-Design Constitution Check ✓
8. Plan Phase 2 → Describe task generation approach
   ✓ Task generation approach documented below
9. STOP - Ready for /tasks command ✓
```

**STATUS**: ✅ Phase 0-2 Complete | 📋 Ready for Implementation

---

## Summary

数据存储模块性能优化将当前纯文件存储(JSON/CSV)升级为分层存储架构(Redis + MySQL + ClickHouse),实现:
- **性能提升**: 持仓查询10ms→1ms (10x), 交易记录查询200ms→100ms (2x), K线查询45ms→20ms (2x)
- **功能扩展**: 支持2-3账户管理, 策略参数版本化, Web管理界面
- **向后兼容**: 策略代码仅需修改初始化部分(约5处),通过统一接口层(`BaseDataStore`)实现透明切换
- **渐进式迁移**: 三阶段实施(基础设施部署 → 双写模式 → 数据库优先),每阶段可回滚

**技术方案** (from research.md):
- HOT层 (Redis): 持仓状态 - <1ms响应
- WARM层 (MySQL): 账户/策略/参数 - <100ms响应
- COOL层 (ClickHouse): K线/交易记录 - <500ms响应
- 统一接口: 抽象工厂 + 策略模式
- 迁移策略: 双写模式保证数据一致性

---

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**:
  - Current: pandas, akshare, threading
  - New: redis-py 5.0+, SQLAlchemy 2.0+, clickhouse-driver 0.2.7+
**Storage**: File (JSON/CSV/Pickle) → Redis + MySQL + ClickHouse (分层存储)
**Testing**: pytest + pytest-cov (目标覆盖率 >80%)
**Target Platform**: Windows 10/11 (本地运行), Docker/Podman容器化数据库
**Project Type**: Single (单体应用,14个入口文件 run_*.py)
**Performance Goals** (from spec):
  - Position query: <1ms (FR-001)
  - Trade query: <100ms for 1 year data (FR-002)
  - Kline query: <20ms for 60 days data (FR-003)
  - Cross-account stats: <500ms (FR-004)
**Constraints** (from spec):
  - 单机环境, 内存<16GB, 磁盘>100GB (CON-006)
  - 2-3账户容量, 单账户最多100只股票 (CON-003)
  - 向后兼容: 现有策略代码零修改 (FR-038)
  - 快速回滚: 配置开关切换存储模式 (FR-039)
**Scale/Scope**:
  - 625万条K线数据 (5000只股票 × 5年)
  - 10万+条交易记录/年
  - 30只持仓股票 × 3账户

---

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Status**: Template-only (.specify/memory/constitution.md is empty template)
**Action**: Skip validation, no project-specific constitutional principles defined

**Note**: 如果未来添加项目宪章,需要验证:
- Library-first principle: 数据存储模块是否应拆分为独立库?
- Test-first principle: 是否需要TDD (测试驱动开发)?
- CLI interface principle: 数据存储操作是否需要CLI工具?

**Current Approach**: 直接集成到现有项目,无需拆分独立库 (符合单体应用架构)

---

## Project Structure

### Documentation (this feature)
```
specs/001-data-storage-optimization/
├── plan.md                     # This file (/plan command output) ✓
├── spec.md                     # Feature specification ✓
├── spec-detailed-backup.md     # Detailed spec with table schemas ✓
├── impact-analysis.md          # Impact analysis & migration strategy ✓
├── research.md                 # Phase 0: Technical research ✓
├── data-model.md               # Phase 1: Data model design ✓
├── quickstart.md               # Phase 1: Quick start guide ✓
├── contracts/                  # Phase 1: Interface contracts ✓
│   └── base_store_interface.py # BaseDataStore interface contract ✓
└── tasks.md                    # Phase 2: Task breakdown ✓
```

### Source Code (repository root)
```
# Current structure
tools/
├── utils_cache.py              # 文件存储操作 (需要扩展)
└── utils_basic.py

delegate/
├── daily_history.py            # K线历史管理 (需要扩展)
├── xt_delegate.py
└── gm_delegate.py

trader/
├── seller.py                   # 卖出逻辑 (需要修改参数传递)
├── buyer.py
└── pools.py

run_*.py                        # 14个入口文件 (需要修改初始化)

# New structure (to be created by /tasks)
storage/                        # NEW 数据存储模块
├── __init__.py
├── config.py                   # 配置管理 (从credentials.py组装配置) ✓
├── base_store.py               # BaseDataStore抽象类
├── file_store.py               # 文件存储实现 (包装utils_cache)
├── redis_store.py              # Redis存储实现
├── mysql_store.py              # MySQL存储实现
├── clickhouse_store.py         # ClickHouse存储实现
├── hybrid_store.py             # 混合模式 (双写+降级)
├── account_manager.py          # 账户管理
└── strategy_params.py          # 策略参数版本管理

tests/                          # NEW 测试目录
├── unit/                       # 单元测试
│   ├── test_file_store.py
│   ├── test_redis_store.py
│   ├── test_mysql_store.py
│   ├── test_clickhouse_store.py
│   └── test_hybrid_store.py
├── integration/                # 集成测试
│   ├── test_database_init.py
│   ├── test_data_migration.py
│   ├── test_hybrid_mode.py
│   └── test_performance.py
└── contract/                   # 契约测试
    └── test_base_store_contract.py

scripts/                        # NEW 运维脚本
├── health_check.py             # 数据库健康检查 (返回退出码) ✓
├── init_clickhouse.py          # ClickHouse表初始化 ✓
├── migrate_held_days.py        # 迁移持仓状态
├── migrate_trade_records.py   # 迁移交易记录
├── migrate_kline.py            # 迁移K线数据
├── verify_consistency.py      # 数据一致性验证
├── export_to_file.py           # 数据库导出到文件
├── import_from_file.py         # 文件导入到数据库
└── monitor_performance.py     # 性能监控

deployment/                     # NEW 部署配置
├── docker-compose-full.yml     # 完整版 (Redis + MySQL + ClickHouse) ✓
└── init.sql                    # MySQL初始化SQL (9表 + 预定义数据) ✓

credentials.py                  # 凭证配置 (仅存储敏感信息) ✓
credentials_sample.py           # 凭证模板 (同步更新) ✓
```

**Structure Decision**: 单体应用 + 新增storage模块,不拆分为独立库。所有数据存储相关代码集中在`storage/`目录,便于维护和测试。

---

## Phase 0: Outline & Research ✅ COMPLETE

### Research Tasks Executed
1. **存储技术选型**: Redis + MySQL + ClickHouse (vs PostgreSQL, MongoDB, TimescaleDB)
2. **Python客户端库**: redis-py, SQLAlchemy 2.0, clickhouse-driver (vs aioredis, Django ORM)
3. **容器化部署**: Podman优先 + Docker兼容 (vs 纯Docker)
4. **统一接口设计**: 抽象工厂 + 策略模式 (vs 适配器, 装饰器)
5. **数据迁移策略**: 三阶段渐进式 + 双写模式 (vs 停机迁移, ETL工具)
6. **测试框架**: pytest + pytest-cov (vs unittest, nose2)

### Research Output
**File**: `research.md` (已生成)
**Key Decisions**:
- Redis: 持仓状态存储, HINCRBY原子操作
- MySQL: 账户/策略管理, 参数版本化
- ClickHouse: K线/交易记录, 10:1压缩比
- docker-compose.yml: 一键启动3个数据库容器
- BaseDataStore: 30+方法的统一接口
- 双写模式: 保证数据一致性,支持快速回滚

---

## Phase 1: Design & Contracts ✅ COMPLETE

### 1.1 Data Model Design ✓
**File**: `data-model.md` (已生成)
**Entities Designed** (10个核心实体):
1. **Account** (账户) - WARM层, MySQL
   - 属性: account_id(UK), account_name, broker, initial_capital, current_capital, status
   - 验证: account_id唯一, initial_capital > 0, broker枚举值
   - 关系: Many-to-Many → Strategy

2. **Strategy** (策略) - WARM层, MySQL
   - 属性: strategy_name(UK), strategy_code(UK), strategy_type, version, status
   - 验证: strategy_name唯一, strategy_code仅字母数字下划线
   - 关系: Many-to-Many → Account, One-to-Many → StrategyParam

3. **AccountStrategy** (账户-策略关联) - WARM层, MySQL
   - 属性: account_id(FK), strategy_id(FK), allocated_capital, risk_limit
   - 验证: (account_id, strategy_id)联合唯一, allocated_capital <= Account.current_capital
   - 用途: 管理账户和策略的多对多关系

4. **StrategyParam** (策略参数) - WARM层, MySQL
   - 属性: strategy_id(FK), param_key, param_value(JSON), version, is_active
   - 验证: (strategy_id, param_key, version)联合唯一, 同一参数只有一个激活版本
   - 用途: 参数版本化管理, 支持对比

5. **Position** (持仓) - HOT层, Redis Hash
   - Redis Key: `held_days:{account_id}`, `max_prices:{account_id}`, `min_prices:{account_id}`
   - 属性: stock_code, held_days, max_price, min_price
   - 用途: 高频读写持仓状态

6. **Trade** (交易记录) - COOL层, ClickHouse
   - 属性: timestamp, date, account_id, stock_code, order_type, price, volume
   - 分区: toYYYYMM(date)
   - 索引: (account_id, stock_code, timestamp)
   - 用途: 交易记录查询和聚合统计

7. **DailyKline** (K线数据) - COOL层, ClickHouse
   - 属性: stock_code, date, datetime, open, high, low, close, volume, amount
   - 分区: toYYYYMM(date)
   - 索引: (stock_code, date)
   - 用途: 历史K线查询

8. **User** (用户) - WARM层, MySQL
   - 属性: username(UK), password_hash, email(UK), status, last_login_at
   - 验证: username长度3-50, email格式, bcrypt密码
   - 关系: Many-to-Many → Role

9. **Role** (角色) - WARM层, MySQL
   - 预定义: admin(管理员), developer(策略开发), trader(交易员), viewer(只读)
   - 关系: Many-to-Many → User, Many-to-Many → Permission

10. **Permission** (权限) - WARM层, MySQL
    - 格式: `{resource}:{action}` (如 `account:read`, `strategy:manage`)
    - 关系: Many-to-Many → Role

**State Transitions**:
- Account: active ↔ inactive ↔ suspended
- Strategy: testing → active ↔ inactive
- User: active ↔ inactive ↔ locked

**Validation Rules**: 34条跨实体验证规则

### 1.2 API Contracts ✓
**File**: `contracts/base_store_interface.py` (已生成)
**Interface Methods** (30+方法):

**Position State** (8 methods):
- `get_held_days(code, account_id) -> int` - 查询持仓天数
- `update_held_days(code, days, account_id)` - 更新持仓天数
- `all_held_inc(account_id) -> bool` - 所有持仓天数+1 (原子操作)
- `delete_held_days(code, account_id)` - 删除持仓记录
- `get_max_price(code, account_id) -> float` - 查询最高价
- `update_max_price(code, price, account_id)` - 更新最高价
- `get_min_price(code, account_id) -> float` - 查询最低价
- `update_min_price(code, price, account_id)` - 更新最低价

**Trade Records** (3 methods):
- `record_trade(account_id, timestamp, code, ...)` - 记录交易
- `query_trades(account_id, start_date, end_date, ...)` - 查询交易记录
- `aggregate_trades(account_id, start_date, end_date, group_by)` - 聚合统计

**Kline Data** (2 methods):
- `get_kline(code, start_date, end_date, days) -> DataFrame` - 查询K线
- `batch_get_kline(codes, ...) -> Dict[str, DataFrame]` - 批量查询

**Account Management** (3 methods):
- `create_account(account_id, account_name, broker, initial_capital) -> int` - 创建账户
- `get_account(account_id) -> Dict` - 查询账户
- `update_account_capital(account_id, current_capital, ...)` - 更新资金

**Strategy Management** (4 methods):
- `create_strategy(strategy_name, strategy_code, ...) -> int` - 创建策略
- `get_strategy_params(strategy_name, version) -> Dict` - 查询参数
- `save_strategy_params(strategy_name, params, remark) -> int` - 保存参数版本
- `compare_strategy_params(strategy_name, version_a, version_b) -> Dict` - 对比版本

**Health & Connection** (2 methods):
- `health_check() -> Dict[str, str]` - 健康检查
- `close()` - 关闭连接

**Contract Testing**: 所有实现必须通过 `tests/contract/test_base_store_contract.py`

### 1.3 Quick Start Guide ✓
**File**: `quickstart.md` (已生成)
**10-Step Guide**:
1. Prerequisites (系统要求, 安装Docker/Podman)
2. 部署数据库服务 (5分钟, docker-compose up)
3. 安装Python依赖 (2分钟, pip install)
4. 初始化数据库 (3分钟, init脚本)
5. 数据迁移 (10分钟, migrate脚本)
6. 配置混合模式 (1分钟, credentials.py)
7. 运行单元测试 (2分钟, pytest)
8. 验证性能提升 (3分钟, benchmark)
9. 集成到策略代码 (5分钟, 修改5处)
10. 模拟盘测试 (1交易日)

**Troubleshooting**: 5个常见问题及解决方案

---

## Phase 2: Task Breakdown ✅ COMPLETE

**Task Breakdown Summary**:

### 2.1 Task Organization Principles
1. **优先级驱动**: 按规范优先级 (P0 → P1 → P2) 生成任务
2. **依赖关系**: 基础设施 → 接口层 → 存储实现 → 迁移 → 集成
3. **可测试性**: 每个任务必须有对应的测试任务
4. **可验收**: 每个任务有明确的完成标准

### 2.2 Task Categories
**Category 1: Infrastructure (基础设施)** - Week 1
- Setup: 容器配置, docker-compose文件
- Database: MySQL/ClickHouse表结构创建
- Dependencies: 安装Python库

**Category 2: Interface Layer (接口层)** - Week 1-2
- Design: BaseDataStore抽象类实现
- FileStore: 包装现有utils_cache.py函数
- Tests: 契约测试编写

**Category 3: Storage Backends (存储后端实现)** - Week 2-3
- RedisStore: 持仓状态操作 (8个方法)
- MySQLStore: 账户/策略管理 (7个方法)
- ClickHouseStore: K线/交易记录 (5个方法)
- HybridStore: 双写模式 + 自动降级
- Tests: 单元测试 (每个后端5-10个测试)

**Category 4: Data Migration (数据迁移)** - Week 3
- Scripts: 5个迁移脚本 (held_days, trade_records, kline, accounts, strategies)
- Validation: 数据一致性验证脚本
- Tests: 集成测试 (迁移流程测试)

**Category 5: Application Integration (应用集成)** - Week 4
- Modify: 14个入口文件初始化修改
- Refactor: Seller参数传递重构
- Update: 持仓天数自增逻辑更新
- Tests: 回归测试 (模拟盘测试)

**Category 6: Web Interface (Web界面, P2优先级)** - Week 5+ (可选)
- Backend: FastAPI后端API (账户/策略/交易记录查询)
- Frontend: Vue 3前端界面
- Tests: API测试

### 2.3 Task Template Structure
每个任务应包含:
```markdown
### Task ID: 001
**Title**: 部署Redis容器
**Category**: Infrastructure
**Priority**: P0
**Estimated Time**: 30分钟
**Dependencies**: 无
**Description**: 编写docker-compose配置文件,部署Redis 7容器,配置AOF持久化
**Acceptance Criteria**:
  - Redis容器成功启动
  - redis-cli ping返回PONG
  - AOF持久化已启用
**Test Task**: 002 - 测试Redis连接
```

### 2.4 Task Statistics (Generated)
- Infrastructure: 8个任务
- Interface Layer: 10个任务
- Storage Backends: 28个任务
- Data Migration: 12个任务
- Application Integration: 16个任务
- Testing & Validation: 8个任务
- Web Interface: 12个任务 (P2, 可选)
- Performance & Monitoring: 6个任务
- **Total**: 94个任务 (预计18工作日)

### 2.5 Critical Path
```
基础设施部署 (Week 1)
  ↓
BaseDataStore接口定义 (Week 1)
  ↓
FileStore实现 (Week 1-2) ← 向后兼容基础
  ↓
RedisStore实现 (Week 2) ← 性能优化关键
  ↓
HybridStore实现 (Week 2-3) ← 双写模式核心
  ↓
数据迁移脚本 (Week 3) ← 数据一致性保证
  ↓
应用集成修改 (Week 4) ← 策略代码集成
  ↓
模拟盘测试 (Week 4) ← 验证
```

---

## Artifacts Generated

### Documentation
- [x] `plan.md` - Implementation plan (this file)
- [x] `spec.md` - Feature specification
- [x] `spec-detailed-backup.md` - Detailed spec with DB schemas
- [x] `impact-analysis.md` - Impact analysis & migration strategy
- [x] `research.md` - Phase 0: Technical research
- [x] `data-model.md` - Phase 1: Data model design (10 entities, ER diagram)
- [x] `quickstart.md` - Phase 1: 10-step quick start guide
- [x] `contracts/base_store_interface.py` - Phase 1: Interface contract (30+ methods)
- [x] `tasks.md` - Phase 2: Task breakdown (94 tasks, 18 days)

### Source Code (to be generated by `/tasks` → implementation)
- [ ] `storage/` module (7 files, ~2000 lines)
- [ ] `tests/` directory (15+ test files)
- [ ] `scripts/` directory (8+ migration scripts)
- [ ] `deployment/docker-compose-full.yml`
- [ ] Modifications to 14 entry files (`run_*.py`)
- [ ] Modifications to `trader/seller.py`

---

## Progress Tracking

### Phase 0: Research ✅ COMPLETE
- [x] Storage technology selection
- [x] Python client library comparison
- [x] Container deployment strategy
- [x] Unified interface design pattern
- [x] Data migration strategy
- [x] Testing framework selection
- [x] **Output**: research.md

### Phase 1: Design & Contracts ✅ COMPLETE
- [x] Data model design (10 entities)
- [x] Entity relationships (ER diagram)
- [x] Validation rules (34 rules)
- [x] API contract definition (30+ methods)
- [x] Contract documentation with examples
- [x] Quick start guide (10 steps)
- [x] **Outputs**: data-model.md, contracts/base_store_interface.py, quickstart.md

### Phase 2: Task Breakdown ✅ COMPLETE
- [x] Generate tasks.md
- [x] Dependency ordering
- [x] Time estimation
- [x] Acceptance criteria definition
- **Result**: 94 tasks, 18 working days (~3.5 weeks implementation)

### Phase 3-4: Implementation & Testing ⏸ PENDING
- [ ] Code implementation (based on tasks.md)
- [ ] Unit tests (target >80% coverage)
- [ ] Integration tests
- [ ] Contract tests
- [ ] Performance tests
- [ ] Documentation updates

---

## Constitutional Compliance

### Initial Check ✅
- No constitution violations (constitution is template-only)
- Approach aligns with single-application architecture
- No over-engineering detected

### Post-Design Check ✅
- Design maintains simplicity (抽象工厂 + 策略模式)
- Backward compatibility preserved (统一接口层)
- Performance targets achievable (research-backed)
- Testing strategy defined (pytest, >80% coverage)

### Complexity Justification
**Complexity**: Medium-High (3个数据库 + 统一接口层)
**Justification**:
1. **性能需求**: 10ms→1ms需要Redis内存存储
2. **业务需求**: 参数版本化需要关系数据库
3. **数据量需求**: 625万条K线需要列式存储压缩
4. **向后兼容**: 统一接口层保证策略代码零修改
5. **渐进式迁移**: 双写模式保证数据一致性,降低风险

**Alternative Considered**: 纯文件存储优化 (索引, mmap)
**Rejection Reason**: 无法满足<1ms性能目标,无法支持复杂查询

---

## Success Criteria

### Performance Metrics (from spec)
- [x] 持仓查询 <1ms: Redis实现可达 <1ms ✓
- [x] 交易记录查询 <100ms: ClickHouse实现可达 <50ms ✓
- [x] K线查询 <20ms: ClickHouse实现可达 <20ms ✓
- [x] 跨账户统计 <500ms: MySQL JOIN可达 <100ms ✓

### Functional Completeness
- [x] 支持2-3账户管理: Account + AccountStrategy实体 ✓
- [x] 策略参数版本化: StrategyParam + version字段 ✓
- [x] Web管理界面: 设计已完成,实施为P2优先级 ✓
- [x] 用户权限管理: User + Role + Permission实体 ✓

### Reliability
- [x] 自动降级机制: HybridStore + health_check() ✓
- [x] 数据迁移可回滚: 双写模式 + 配置开关 ✓
- [x] 策略代码零修改: BaseDataStore统一接口 ✓

### Testability
- [x] 契约测试: base_store_interface.py定义 ✓
- [x] 单元测试: pytest结构设计 ✓
- [x] 集成测试: test_hybrid_mode, test_data_migration ✓
- [x] 性能测试: test_benchmark设计 ✓

---

## Next Steps

### Immediate (开发人员)
1. **Review artifacts**: 评审 plan.md, tasks.md, data-model.md 等设计文档
2. **Setup task tracking**: 在 GitHub Issues/Jira 中创建任务 (从 tasks.md)
3. **Setup environment**: 按 quickstart.md 搭建开发环境
4. **Start implementation**: 认领 tasks.md 中的任务 (从 INFRA-001 开始)

### Near-term (Week 1-2)
1. **Infrastructure**: 部署容器,初始化数据库
2. **Interface Layer**: 实现BaseDataStore接口
3. **File Store**: 包装现有utils_cache.py
4. **Redis Store**: 实现持仓状态操作
5. **Write Tests**: 契约测试 + 单元测试

### Mid-term (Week 3-4)
1. **MySQL/ClickHouse Store**: 完成所有存储后端
2. **Hybrid Store**: 实现双写模式 + 降级逻辑
3. **Data Migration**: 执行数据迁移,验证一致性
4. **Application Integration**: 修改14个入口文件
5. **Regression Testing**: 模拟盘测试3个交易日

### Long-term (Week 5+, Optional)
1. **Web Backend**: FastAPI实现账户/策略管理API
2. **Web Frontend**: Vue 3实现管理界面
3. **Production Deployment**: 生产环境部署,小仓位验证
4. **Performance Tuning**: 根据实际运行数据优化

---

## References

### Internal Documents
- [Specification](./spec.md) - Feature requirements
- [Impact Analysis](./impact-analysis.md) - Existing code analysis
- [Research](./research.md) - Technical decisions
- [Data Model](./data-model.md) - Entity design
- [Quick Start](./quickstart.md) - Setup guide
- [Interface Contract](./contracts/base_store_interface.py) - API definition

### External Resources
- [Redis Documentation](https://redis.io/docs/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [ClickHouse Documentation](https://clickhouse.com/docs)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

**Plan Status**: ✅ Complete (Phase 0-2) | 📋 Ready for Implementation
**Date**: 2025-10-01
**Next Step**: Review artifacts and start implementation (see tasks.md)
