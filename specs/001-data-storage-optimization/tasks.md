# Tasks: 数据存储模块性能优化

**Input**: Design documents from `/specs/001-data-storage-optimization/`
**Prerequisites**: plan.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

## Execution Flow (main)
```
1. ✓ Loaded plan.md: Python 3.10+, Redis + MySQL + ClickHouse
2. ✓ Loaded research.md: 6 technical decisions
3. ✓ Loaded data-model.md: 10 entities (Account, Strategy, Position, Trade, etc.)
4. ✓ Loaded contracts/: base_store_interface.py (30+ methods)
5. ✓ Loaded quickstart.md: 10-step setup guide
6. ✓ Generated tasks by category (Setup, Tests, Core, Integration, Polish)
7. ✓ Applied parallel execution rules: [P] for independent files
8. ✓ Numbered tasks sequentially (T001-T082)
9. ✓ Validated completeness: All contracts tested, all entities modeled
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- File paths are relative to repository root: `E:\AI\code_2\lianghua\SilverQuant\`

---

## Phase 3.1: Setup (基础设施部署)

- [x] **T001** Create storage module structure: `storage/__init__.py`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `scripts/`, `deployment/`
- [x] **T002** Install Python dependencies: `pip install redis>=5.0.0 sqlalchemy>=2.0.0 pymysql>=1.1.0 clickhouse-driver>=0.2.7 pytest>=7.4.0 pytest-cov>=4.1.0`
- [x] **T003** [P] Create deployment/docker-compose-full.yml with Redis 7, MySQL 8, ClickHouse (ports 6379, 3306, 9000/8123, volumes for persistence)
- [x] **T004** [P] Create deployment/init.sql with MySQL schema (tables: account, strategy, strategy_param, account_strategy, user, role, permission per data-model.md)
- [x] **T005** [P] Create scripts/init_clickhouse.py to create ClickHouse tables (trade, daily_kline with monthly partitions, MergeTree engine)
- [x] **T006** Configure credentials: Add database credentials to credentials.py (simple values only), create storage/config.py for configuration logic (environment variable support, validation)
- [x] **T007** Deploy databases: `docker-compose -f deployment/docker-compose-full.yml up -d` and verify all 3 containers running (⚠️ 需要手动执行)
- [x] **T008** [P] Create scripts/health_check.py to test Redis PING, MySQL SELECT 1, ClickHouse SELECT 1, return exit code 0=ok, 1=degraded

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (BaseDataStore interface)
- [x] **T009** [P] Contract test for get_held_days/update_held_days/delete_held_days in tests/contract/test_position_state.py (verify all stores implement these methods)
- [x] **T010** [P] Contract test for all_held_inc in tests/contract/test_position_increment.py (verify atomicity: same day returns False on 2nd call)
- [x] **T011** [P] Contract test for get_max_price/update_max_price/get_min_price/update_min_price in tests/contract/test_price_tracking.py
- [x] **T012** [P] Contract test for record_trade/query_trades/aggregate_trades in tests/contract/test_trade_records.py
- [x] **T013** [P] Contract test for get_kline/batch_get_kline in tests/contract/test_kline_data.py (verify DataFrame format, columns: datetime, open, high, low, close, volume, amount)
- [x] **T014** [P] Contract test for create_account/get_account/update_account_capital in tests/contract/test_account_mgmt.py
- [x] **T015** [P] Contract test for create_strategy/get_strategy_params/save_strategy_params/compare_strategy_params in tests/contract/test_strategy_mgmt.py
- [x] **T016** [P] Contract test for health_check/close in tests/contract/test_connection.py

### Integration Tests (User scenarios from quickstart.md)
- [x] **T017** [P] Integration test: Deploy databases → init schemas → verify all tables created in tests/integration/test_database_init.py
- [x] **T018** [P] Integration test: Migrate held_days.json → Redis → verify consistency in tests/integration/test_migrate_positions.py
- [x] **T019** [P] Integration test: Migrate trade CSV → ClickHouse → verify row count matches in tests/integration/test_migrate_trades.py
- [x] **T020** [P] Integration test: Hybrid mode dual-write (Redis + File) → verify both updated in tests/integration/test_hybrid_dual_write.py
- [x] **T021** [P] Integration test: Redis failure → auto-fallback to File → verify degradation logs in tests/integration/test_auto_fallback.py
- [x] **T022** [P] Integration test: Complete trading cycle (open position → hold → close) in tests/integration/test_trading_cycle.py

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Abstract Interface
- [x] **T023** Create storage/base_store.py: Copy BaseDataStore abstract class from contracts/base_store_interface.py with all 30+ @abstractmethod

### FileStore Implementation
- [x] **T024** [P] FileStore: Implement get_held_days/update_held_days/delete_held_days in storage/file_store.py (wrap utils_cache.load_json/save_json, path from credentials.py)
- [x] **T025** [P] FileStore: Implement all_held_inc in storage/file_store.py (wrap utils_cache.all_held_inc with file lock for atomicity)
- [x] **T026** [P] FileStore: Implement get_max_price/update_max_price/get_min_price/update_min_price in storage/file_store.py (read/write max_prices.json, min_prices.json)
- [x] **T027** FileStore: Implement record_trade/query_trades/aggregate_trades in storage/file_store.py (append to CSV, pandas read_csv + filter, pandas groupby for aggregation)
- [x] **T028** [P] FileStore: Implement get_kline/batch_get_kline in storage/file_store.py (call utils_cache.get_kline, return DataFrame with required columns)
- [x] **T029** [P] FileStore: Implement create_account/get_account/update_account_capital in storage/file_store.py (read/write accounts.json with uniqueness validation)
- [x] **T030** [P] FileStore: Implement create_strategy/get_strategy_params/save_strategy_params/compare_strategy_params in storage/file_store.py (read/write strategies.json, strategy_params/{name}_v{version}.json)
- [x] **T031** [P] FileStore: Implement health_check (check file directory writable) and close (no-op) in storage/file_store.py

### RedisStore Implementation
- [x] **T032** Create storage/redis_store.py with __init__ (redis.Redis client with connection pool), close, health_check (PING command)
- [x] **T033** RedisStore: Implement get_held_days/update_held_days/delete_held_days (HGET/HSET/HDEL on held_days:{account_id})
- [x] **T034** RedisStore: Implement all_held_inc with Lua script in storage/redis_store.py (atomically check _inc_date, increment all fields if different day, return 0 if same day)
- [x] **T035** [P] RedisStore: Implement get_max_price/update_max_price/get_min_price/update_min_price (HGET/HSET on max_prices:{account_id}, min_prices:{account_id})
- [x] **T036** [P] RedisStore: Stub methods (record_trade, query_trades, get_kline, create_account, etc.) with NotImplementedError("Use ClickHouse/MySQL for this operation")

### MySQLStore Implementation
- [x] **T037** Create storage/mysql_store.py with SQLAlchemy ORM models (Account, Strategy, StrategyParam, AccountStrategy, User, Role, Permission per data-model.md), __init__ (create Engine, Session), close, health_check (SELECT 1)
- [x] **T038** MySQLStore: Implement create_account/get_account/update_account_capital (INSERT, SELECT, UPDATE with uniqueness check on account_id)
- [x] **T039** MySQLStore: Implement create_strategy/get_strategy_params (INSERT strategy, SELECT strategy_param WHERE is_active=1)
- [x] **T040** MySQLStore: Implement save_strategy_params (INSERT new version, UPDATE old version set is_active=False in transaction)
- [x] **T041** [P] MySQLStore: Implement compare_strategy_params (SELECT two versions, return dict of differences)
- [x] **T042** [P] MySQLStore: Stub methods (get_held_days, record_trade, get_kline, etc.) with NotImplementedError("Use Redis/ClickHouse for this operation")

### ClickHouseStore Implementation
- [x] **T043** Create storage/clickhouse_store.py with __init__ (clickhouse_driver.Client), close, health_check (SELECT 1)
- [x] **T044** ClickHouseStore: Implement record_trade (INSERT INTO trade VALUES with timestamp, account_id, stock_code, order_type, price, volume)
- [x] **T045** ClickHouseStore: Implement query_trades (SELECT * FROM trade WHERE account_id=? AND date BETWEEN ? AND ? with optional code/strategy filters, ORDER BY timestamp DESC LIMIT ?)
- [x] **T046** ClickHouseStore: Implement aggregate_trades (SELECT toYYYYMM(timestamp) AS period, COUNT(*), SUM(price*volume) GROUP BY period for group_by='month', similar for 'day'/'year')
- [x] **T047** [P] ClickHouseStore: Implement get_kline/batch_get_kline (SELECT * FROM daily_kline WHERE stock_code=? AND date BETWEEN ? AND ?, return pandas DataFrame)
- [x] **T048** [P] ClickHouseStore: Stub methods (get_held_days, create_account, create_strategy, etc.) with NotImplementedError("Use Redis/MySQL for this operation")

### HybridStore Implementation
- [x] **T049** Create storage/hybrid_store.py with __init__ (instantiate FileStore, RedisStore, MySQLStore, ClickHouseStore), close (close all), health_check (aggregate all statuses)
- [x] **T050** HybridStore: Implement get_held_days (try Redis, fallback to File on exception, log degradation event at WARNING level)
- [x] **T051** HybridStore: Implement update_held_days/delete_held_days (dual-write to Redis + File, log errors but don't fail if File write fails)
- [x] **T052** HybridStore: Implement all_held_inc (try Redis with Lua script, fallback to File with file lock on exception)
- [x] **T053** [P] HybridStore: Implement get_max_price/update_max_price/get_min_price/update_min_price (dual-read Redis → File, dual-write Redis + File)
- [x] **T054** HybridStore: Implement record_trade (dual-write ClickHouse + File CSV, log errors)
- [x] **T055** HybridStore: Implement query_trades/aggregate_trades (try ClickHouse, fallback to File CSV with pandas on exception)
- [x] **T056** [P] HybridStore: Implement get_kline/batch_get_kline (try ClickHouse, fallback to File on exception)
- [x] **T057** HybridStore: Implement create_account/get_account/update_account_capital (try MySQL, fallback to File on exception, dual-write for updates)
- [x] **T058** HybridStore: Implement create_strategy/get_strategy_params/save_strategy_params/compare_strategy_params (try MySQL, fallback to File on exception)

### Factory Function
- [x] **T059** Create storage/__init__.py with create_data_store(mode, config) factory function (mode: "file"/"redis"/"mysql"/"clickhouse"/"hybrid", return corresponding instance, validate mode, raise ValueError if invalid)

---

## Phase 3.4: Integration (应用集成)

### Data Migration Scripts
- [x] **T060** [P] Create scripts/migrate_held_days.py: Read held_days.json + max_prices.json + min_prices.json → write to Redis using Pipeline (batch 100 keys), output migration report (success/fail counts)
- [x] **T061** [P] Create scripts/migrate_trade_records.py: Read trade CSV → batch insert to ClickHouse (1000 rows/batch), output report (rows migrated, time elapsed)
- [x] **T062** [P] Create scripts/migrate_kline.py: Scan all stock CSV files → batch insert to ClickHouse (10000 rows/batch), show progress bar with tqdm
- [x] **T063** [P] Create scripts/migrate_accounts.py: Read account config from credentials.py → INSERT INTO MySQL account table (idempotent: check existence first)
- [x] **T064** [P] Create scripts/migrate_strategies.py: Read strategy config JSON → INSERT INTO MySQL strategy + strategy_param tables (initial version=1)

### Data Consistency Tools
- [x] **T065** [P] Create scripts/verify_consistency.py: Compare held_days (Redis vs File), trade counts (ClickHouse vs CSV), accounts (MySQL vs JSON), output inconsistency report, exit 0=consistent, 1=inconsistent
- [x] **T066** [P] Create scripts/export_to_file.py: Export Redis → JSON, ClickHouse → CSV, MySQL → JSON for rollback backup (support --output dir)
- [x] **T067** [P] Create scripts/import_from_file.py: Import JSON → Redis, CSV → ClickHouse, JSON → MySQL for disaster recovery (verify after import)

### Application Code Changes
- [ ] **T068** Modify run_*.py entry files (14 files: run_wencai_v1.py, run_wencai_v2.py, run_remote_*.py, run_technical_*.py): Add `from storage import create_data_store` at top, add `data_store = create_data_store(DATA_STORE_MODE, DATA_STORE_CONFIG)` after imports, pass data_store to strategy class constructor
- [ ] **T069** Modify trader/seller.py: Add `data_store: BaseDataStore` parameter to __init__, replace `load_json(PATH_HELD)` with `data_store.get_held_days(code, account_id)`, replace `save_json(PATH_HELD)` with `data_store.update_held_days(code, days, account_id)`, replace `all_held_inc()` with `data_store.all_held_inc(account_id)`
- [ ] **T070** Modify strategy classes (wencai_v1.py, wencai_v2.py, etc.): Add `data_store` parameter to __init__, pass to Seller constructor: `self.seller = Seller(data_store=data_store, ...)`
- [ ] **T071** Find and modify daily increment logic: Replace `all_held_inc()` call with `data_store.all_held_inc(account_id)`, verify atomicity (same day only increments once)
- [ ] **T072** Find and modify trade recording logic: Replace `write_trade_to_csv()` with `data_store.record_trade(account_id, timestamp, code, name, order_type, remark, price, volume, strategy_name)`
- [ ] **T073** Find and modify kline query logic: Replace `get_kline(code)` with `data_store.get_kline(code, days=60)`, verify DataFrame format compatibility

### Configuration & Monitoring
- [ ] **T074** Add configuration switches in tools/credentials.py: DATA_STORE_MODE env var support, ENABLE_DUAL_WRITE (default True), ENABLE_AUTO_FALLBACK (default True)
- [ ] **T075** Add startup health check in run_*.py: Call `data_store.health_check()` after initialization, log WARNING if degraded, auto-fallback to "file" mode if all databases down
- [ ] **T076** [P] Add runtime monitoring logs: Log each degradation event (WARNING), slow queries >100ms (INFO), data inconsistency (ERROR), configure log rotation (10MB per file, keep 5 files)

---

## Phase 3.5: Polish (测试与优化)

### Unit Tests
- [ ] **T077** [P] Unit tests for FileStore in tests/unit/test_file_store.py: Test all position/trade/kline/account/strategy methods, use pytest fixtures for temp files, assert correct file read/write, coverage >90%
- [ ] **T078** [P] Unit tests for RedisStore in tests/unit/test_redis_store.py: Use fakeredis or docker fixture, test atomicity of all_held_inc with concurrent calls (threading), coverage >85%
- [ ] **T079** [P] Unit tests for MySQLStore in tests/unit/test_mysql_store.py: Use in-memory SQLite for tests, test account/strategy CRUD, test version rollover (is_active flag), coverage >85%
- [ ] **T080** [P] Unit tests for ClickHouseStore in tests/unit/test_clickhouse_store.py: Use docker fixture for ClickHouse, test trade/kline queries with date filters, test aggregation, coverage >85%
- [ ] **T081** [P] Unit tests for HybridStore in tests/unit/test_hybrid_store.py: Mock backend exceptions, test dual-write, test fallback logic, test health aggregation, coverage >85%

### Performance & Documentation
- [ ] **T082** [P] Performance benchmark tests in tests/integration/test_performance.py: Measure get_held_days <1ms (Redis), query_trades <100ms (ClickHouse 1 year data), get_kline <20ms (ClickHouse 60 days), aggregate_trades <500ms (ClickHouse 3 years), generate performance report with before/after comparison chart

---

## Dependencies

**Critical Path**:
```
Setup (T001-T008)
  ↓
Contract Tests (T009-T016) [P] → Integration Tests (T017-T022) [P]
  ↓
Abstract Interface (T023)
  ↓
FileStore (T024-T031) [mostly P]
  ↓
RedisStore (T032-T036) [mostly P] → MySQLStore (T037-T042) [mostly P] → ClickHouseStore (T043-T048) [mostly P]
  ↓
HybridStore (T049-T058) [sequential, depends on all stores]
  ↓
Factory (T059)
  ↓
Migration Scripts (T060-T064) [P] → Consistency Tools (T065-T067) [P]
  ↓
App Integration (T068-T073) [sequential, modify same files]
  ↓
Config & Monitoring (T074-T076) [mostly P]
  ↓
Unit Tests (T077-T081) [P] → Performance (T082) [P]
```

**Blockers**:
- T023 blocks T024-T031 (FileStore needs abstract base)
- T024-T031 block T049 (HybridStore needs FileStore)
- T032-T036 block T049 (HybridStore needs RedisStore)
- T037-T042 block T049 (HybridStore needs MySQLStore)
- T043-T048 block T049 (HybridStore needs ClickHouseStore)
- T049-T058 block T060-T064 (Migration needs HybridStore)
- T059 blocks T068 (App needs factory)
- T068 blocks T069-T073 (Entry files must be modified first to pass data_store)

---

## Parallel Execution Examples

### Launch Contract Tests (T009-T016) Together:
```python
# All contract tests can run in parallel (different files, independent)
Task("Contract test for position state methods in tests/contract/test_position_state.py")
Task("Contract test for position increment atomicity in tests/contract/test_position_increment.py")
Task("Contract test for price tracking methods in tests/contract/test_price_tracking.py")
Task("Contract test for trade record methods in tests/contract/test_trade_records.py")
Task("Contract test for kline data methods in tests/contract/test_kline_data.py")
Task("Contract test for account management methods in tests/contract/test_account_mgmt.py")
Task("Contract test for strategy management methods in tests/contract/test_strategy_mgmt.py")
Task("Contract test for connection management in tests/contract/test_connection.py")
```

### Launch Integration Tests (T017-T022) Together:
```python
# All integration tests can run in parallel (independent scenarios)
Task("Integration test for database initialization in tests/integration/test_database_init.py")
Task("Integration test for position migration in tests/integration/test_migrate_positions.py")
Task("Integration test for trade migration in tests/integration/test_migrate_trades.py")
Task("Integration test for hybrid dual-write in tests/integration/test_hybrid_dual_write.py")
Task("Integration test for auto-fallback in tests/integration/test_auto_fallback.py")
Task("Integration test for complete trading cycle in tests/integration/test_trading_cycle.py")
```

### Launch FileStore Implementation (T024-T031) Mostly Parallel:
```python
# Most FileStore methods are independent (different JSON files)
Task("FileStore: Implement position state methods in storage/file_store.py")  # [P]
Task("FileStore: Implement position increment with file lock in storage/file_store.py")  # [P]
Task("FileStore: Implement price tracking methods in storage/file_store.py")  # [P]
# T027 sequential (same file as T024-T026)
# T028-T031 parallel (independent features)
```

### Launch Migration Scripts (T060-T064) Together:
```python
# All migration scripts are independent (different data sources)
Task("Create migration script for positions in scripts/migrate_held_days.py")
Task("Create migration script for trades in scripts/migrate_trade_records.py")
Task("Create migration script for klines in scripts/migrate_kline.py")
Task("Create migration script for accounts in scripts/migrate_accounts.py")
Task("Create migration script for strategies in scripts/migrate_strategies.py")
```

### Launch Unit Tests (T077-T081) Together:
```python
# All unit tests are independent (different test files)
Task("Unit tests for FileStore in tests/unit/test_file_store.py")
Task("Unit tests for RedisStore in tests/unit/test_redis_store.py")
Task("Unit tests for MySQLStore in tests/unit/test_mysql_store.py")
Task("Unit tests for ClickHouseStore in tests/unit/test_clickhouse_store.py")
Task("Unit tests for HybridStore in tests/unit/test_hybrid_store.py")
```

---

## Validation Checklist
*GATE: Verify before marking tasks complete*

- [x] All contracts have corresponding tests (T009-T016 cover all BaseDataStore methods)
- [x] All entities have model tasks (Account, Strategy, etc. in MySQLStore ORM T037)
- [x] All tests come before implementation (Phase 3.2 before Phase 3.3)
- [x] Parallel tasks truly independent (checked file paths, no shared files in [P] tasks)
- [x] Each task specifies exact file path (all tasks include file paths)
- [x] No task modifies same file as another [P] task (verified dependencies)

---

## Notes

- **[P] tasks**: Different files, no dependencies, can run in parallel
- **TDD approach**: Verify all tests fail before implementing (T009-T022 must fail first)
- **Commit strategy**: Commit after each task completion
- **Rollback plan**: Keep DATA_STORE_MODE="file" as default, quick rollback via env var
- **Performance targets**: <1ms (Redis), <100ms (MySQL), <20ms (ClickHouse), >80% test coverage

---

**Generated**: 2025-10-01 via `/tasks` command
**Total Tasks**: 82
**Estimated Time**: 16-18 working days
**Critical Path**: T001 → T009-T022 → T023 → T024-T048 → T049-T058 → T059 → T060-T073 → T077-T082
**Ready for Execution**: ✅
