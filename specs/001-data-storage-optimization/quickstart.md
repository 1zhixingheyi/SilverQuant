# Quick Start Guide: 数据存储模块性能优化

**Feature**: 001-data-storage-optimization
**Date**: 2025-10-01
**Audience**: 开发人员、测试人员

本指南帮助您快速搭建开发环境并验证数据存储优化功能。

---

## Prerequisites

### 系统要求
- **操作系统**: Windows 10/11 with WSL2 或 Linux
- **内存**: 至少8GB可用内存(推荐16GB)
- **磁盘**: 至少20GB可用空间
- **Python**: 3.10+
- **容器环境**: Docker 或 Podman (二选一)

### 安装容器环境

#### 选项1: Docker Desktop (推荐Windows用户)
```bash
# 访问 https://www.docker.com/products/docker-desktop
# 下载并安装 Docker Desktop
# 启动 Docker Desktop并等待图标变绿
docker --version  # 验证安装
```

#### 选项2: Podman (推荐Linux用户)
```bash
# Windows (通过WSL2)
wsl --install  # 如果尚未安装WSL
# 在WSL中安装Podman
sudo apt update
sudo apt install podman

# Linux
sudo dnf install podman  # Fedora
sudo apt install podman  # Ubuntu 20.10+

podman --version  # 验证安装
```

---

## Step 1: 部署数据库服务 (5分钟)

### 1.1 启动容器服务

```bash
# 进入项目目录
cd E:\AI\code_2\lianghua\SilverQuant

# 启动所有数据库服务
docker-compose -f deployment/docker-compose-full.yml up -d

# 或使用Podman
podman-compose -f deployment/docker-compose-full.yml up -d

# 检查服务状态
docker ps  # 应该看到3个容器: redis, mysql, clickhouse
```

### 1.2 验证服务就绪

```bash
# 测试Redis连接
docker exec silverquant-redis redis-cli ping
# 预期输出: PONG

# 测试MySQL连接
docker exec silverquant-mysql mysql -uroot -psilverquant2024 -e "SELECT 1"
# 预期输出: 1

# 测试ClickHouse连接
curl http://localhost:8123/
# 预期输出: Ok.
```

**常见问题**:
- **端口被占用**: 修改`docker-compose-full.yml`中的端口映射
- **Docker启动失败**: 确保Docker Desktop正在运行
- **Podman权限错误**: 使用`podman-compose up -d --userns=keep-id`

---

## Step 2: 安装Python依赖 (2分钟)

### 2.1 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2.2 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装数据库客户端库
pip install redis>=5.0.0
pip install sqlalchemy>=2.0.0
pip install pymysql>=1.1.0
pip install clickhouse-driver>=0.2.7

# 安装测试框架
pip install pytest pytest-cov pytest-mock

# 验证安装
python -c "import redis; print('Redis client OK')"
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "from clickhouse_driver import Client; print('ClickHouse client OK')"
```

---

## Step 3: 初始化数据库 (3分钟)

### 3.1 创建MySQL表结构

```bash
# 运行数据库初始化脚本
python scripts/init_database.py

# 预期输出:
# ✓ MySQL 连接成功
# ✓ 创建表 accounts
# ✓ 创建表 strategies
# ✓ 创建表 account_strategy
# ✓ 创建表 strategy_params
# ✓ 创建表 users
# ✓ 创建表 roles
# ✓ 创建表 permissions
# ✓ 数据库初始化完成
```

### 3.2 创建ClickHouse表结构

```bash
# 运行ClickHouse初始化脚本
python scripts/init_clickhouse.py

# 预期输出:
# ✓ ClickHouse 连接成功
# ✓ 创建表 trade_records
# ✓ 创建表 daily_kline
# ✓ ClickHouse初始化完成
```

---

## Step 4: 数据迁移 (10分钟)

### 4.1 备份现有数据

```bash
# 备份JSON文件
cp _cache/prod_pwc/held_days.json _cache/backup/held_days.json.bak
cp _cache/prod_pwc/max_price.json _cache/backup/max_price.json.bak
cp _cache/prod_pwc/min_price.json _cache/backup/min_price.json.bak

# 备份CSV文件
cp _cache/prod_pwc/deal_hist.csv _cache/backup/deal_hist.csv.bak
```

### 4.2 迁移持仓状态 (JSON → Redis)

```bash
# 运行迁移脚本
python scripts/migrate_held_days.py --account 55009728

# 预期输出:
# 读取文件: _cache/prod_pwc/held_days.json
# 发现 15 条持仓记录
# 迁移到 Redis: held_days:55009728
# ✓ 迁移完成: 15/15 成功

# 验证数据一致性
python scripts/verify_consistency.py --type held_days --account 55009728

# 预期输出:
# ✓ 数据一致性验证通过: 15/15 记录匹配
```

### 4.3 迁移交易记录 (CSV → ClickHouse)

```bash
# 运行迁移脚本
python scripts/migrate_trade_records.py --account 55009728

# 预期输出:
# 读取文件: _cache/prod_pwc/deal_hist.csv
# 发现 1250 条交易记录
# 批量写入 ClickHouse: trade_records
# ✓ 迁移完成: 1250/1250 成功

# 验证数据一致性
python scripts/verify_consistency.py --type trades --account 55009728

# 预期输出:
# ✓ 数据一致性验证通过: 1250/1250 记录匹配
```

### 4.4 迁移K线数据 (CSV → ClickHouse)

```bash
# 迁移所有股票K线数据(约5000只股票 × 550天)
python scripts/migrate_kline.py --all

# 预期输出:
# 扫描目录: _cache/_daily_MOOTDX
# 发现 5000 个CSV文件
# 进度: [========================================] 5000/5000 (100%)
# ✓ 迁移完成: 2,750,000 条K线数据
# 压缩效果: 2.1GB → 210MB (压缩比 10:1)
# 耗时: 8分钟

# 验证数据完整性
python scripts/verify_consistency.py --type kline --sample 100

# 预期输出:
# 随机采样 100 只股票验证
# ✓ 数据一致性验证通过: 100/100 股票匹配
```

---

## Step 5: 配置混合模式 (1分钟)

### 5.1 修改配置文件

编辑 `credentials.py`:

```python
# 数据存储模式配置
DATA_STORE_MODE = 'hybrid'  # 'file', 'redis', 'mysql', 'clickhouse', 'hybrid'

# Redis配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = None  # 如果设置了密码,在这里填写

# MySQL配置
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_DATABASE = 'silverquant'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'silverquant2024'

# ClickHouse配置
CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_HTTP_PORT = 8123
CLICKHOUSE_NATIVE_PORT = 9000
```

### 5.2 测试混合模式

```bash
# 运行混合模式测试
python tests/integration/test_hybrid_mode.py

# 预期输出:
# ✓ 文件存储初始化成功
# ✓ Redis存储初始化成功
# ✓ 混合存储初始化成功
# ✓ 双写测试通过
# ✓ 自动降级测试通过 (Redis故障时降级到文件)
# ✓ 所有测试通过 (5/5)
```

---

## Step 6: 运行单元测试 (2分钟)

### 6.1 运行所有测试

```bash
# 运行单元测试
pytest tests/unit/ -v

# 预期输出:
# tests/unit/test_file_store.py::test_get_held_days PASSED
# tests/unit/test_file_store.py::test_all_held_inc PASSED
# tests/unit/test_redis_store.py::test_get_held_days PASSED
# tests/unit/test_redis_store.py::test_atomic_inc PASSED
# tests/unit/test_hybrid_store.py::test_auto_fallback PASSED
# ...
# ========================= 45 passed in 1.2s =========================
```

### 6.2 查看测试覆盖率

```bash
# 生成覆盖率报告
pytest tests/ --cov=storage --cov-report=html

# 打开报告
# Windows:
start htmlcov/index.html
# Linux/Mac:
xdg-open htmlcov/index.html

# 预期覆盖率: >80%
```

---

## Step 7: 验证性能提升 (3分钟)

### 7.1 运行性能基准测试

```bash
# 运行性能测试
python tests/performance/test_benchmark.py

# 预期输出:
# ===== Position State Query Benchmark =====
# File Storage: 10.5ms (avg of 1000 queries)
# Redis Storage: 0.8ms (avg of 1000 queries)
# ✓ Speedup: 13.1x
#
# ===== Trade Record Query Benchmark =====
# CSV Full Scan: 215ms (1 year data)
# ClickHouse Indexed: 45ms (1 year data)
# ✓ Speedup: 4.8x
#
# ===== Kline Query Benchmark =====
# CSV Memory Cache: 12ms (60 days data)
# ClickHouse: 18ms (60 days data)
# Note: CSV faster due to pre-loaded memory cache
#
# ===== All Performance Targets Met =====
# ✓ Position query: 0.8ms < 1ms target
# ✓ Trade query: 45ms < 100ms target
# ✓ Kline query: 18ms < 20ms target
```

---

## Step 8: 集成到策略代码 (5分钟)

### 8.1 修改入口文件

编辑 `run_wencai_qmt.py`:

```python
# === 原代码 (修改前) ===
PATH_BASE = CACHE_PROD_PATH if IS_PROD else CACHE_TEST_PATH
PATH_HELD = PATH_BASE + '/held_days.json'
PATH_MAXP = PATH_BASE + '/max_price.json'
PATH_MINP = PATH_BASE + '/min_price.json'

# === 新代码 (修改后) ===
from storage.hybrid_store import create_data_store

# 创建数据存储实例
data_store = create_data_store(
    mode=DATA_STORE_MODE,  # 从credentials.py读取
    config={
        'base_path': CACHE_PROD_PATH if IS_PROD else CACHE_TEST_PATH,
        'redis': {'host': REDIS_HOST, 'port': REDIS_PORT},
        'mysql': {'host': MYSQL_HOST, 'port': MYSQL_PORT, 'database': MYSQL_DATABASE},
        'clickhouse': {'host': CLICKHOUSE_HOST, 'port': CLICKHOUSE_NATIVE_PORT},
    }
)

# 账户ID
ACCOUNT_ID = QMT_ACCOUNT_ID
```

### 8.2 修改Seller参数传递

编辑 `trader/seller.py`:

```python
# === 原代码 (修改前) ===
def execute_sell(
    self, quotes, curr_date, curr_time, positions,
    held_days: Dict[str, int],           # 字典参数
    max_prices: Dict[str, float],
    cache_history: Dict[str, pd.DataFrame],
):
    for position in positions:
        code = position.stock_code
        if (code in held_days) and (code in max_prices):
            held_day = held_days[code]
            max_price = max_prices[code]

# === 新代码 (修改后) ===
def execute_sell(
    self, quotes, curr_date, curr_time, positions,
    data_store: BaseDataStore,  # 数据存储接口
    account_id: str,
):
    for position in positions:
        code = position.stock_code
        held_day = data_store.get_held_days(code, account_id)  # 接口调用
        max_price = data_store.get_max_price(code, account_id)
        if held_day is not None and max_price is not None:
            # ... 卖出逻辑保持不变
```

### 8.3 修改持仓天数自增

编辑 `run_wencai_qmt.py`:

```python
# === 原代码 (修改前) ===
def held_increase() -> None:
    update_position_held(disk_lock, my_delegate, PATH_HELD)
    if all_held_inc(disk_lock, PATH_HELD):
        logging.warning('===== 所有持仓计数 +1 =====')

# === 新代码 (修改后) ===
def held_increase() -> None:
    update_position_held(data_store, my_delegate, ACCOUNT_ID)  # 传递data_store
    if data_store.all_held_inc(ACCOUNT_ID):  # 接口调用
        logging.warning('===== 所有持仓计数 +1 =====')
```

---

## Step 9: 模拟盘测试 (1交易日)

### 9.1 启动模拟盘

```bash
# 使用掘金模拟盘测试
python run_wencai_qmt.py --sim

# 观察日志输出:
# [09:15] ✓ 数据存储初始化成功 (混合模式: Redis + 文件降级)
# [09:15] ✓ 健康检查通过: {'redis': 'ok', 'file': 'ok'}
# [09:25] ✓ 持仓天数+1 完成 (15只股票)
# [14:50] ✓ 买入 SH600000 1000股 @ 10.50元
# [14:50] ✓ 持仓状态更新: held_days=0, max_price=10.50
# [14:50] ✓ 交易记录保存: ClickHouse写入耗时 5ms
# [15:00] ✓ 收盘数据保存完成
```

### 9.2 验证数据一致性

```bash
# 交易日结束后,验证文件和数据库数据一致
python scripts/verify_consistency.py --type all --account 55009728

# 预期输出:
# ===== 持仓状态 =====
# ✓ 数据一致性验证通过: 16/16 记录匹配
#
# ===== 交易记录 =====
# ✓ 数据一致性验证通过: 1253/1253 记录匹配 (新增3笔)
#
# ===== 所有验证通过 =====
```

---

## Step 10: 切换到数据库优先模式 (可选)

经过1周双写模式运行稳定后,可以切换到数据库优先模式:

### 10.1 修改配置

编辑 `credentials.py`:

```python
# 从混合模式切换到Redis优先
DATA_STORE_MODE = 'redis'  # 不再写文件,仅读数据库
```

### 10.2 重启策略程序

```bash
python run_wencai_qmt.py

# 观察日志:
# [09:15] ✓ 数据存储初始化成功 (Redis模式)
# [09:15] ⚠ 文件存储已禁用 (仅用于应急降级)
```

### 10.3 监控性能提升

```bash
# 查看实时性能指标
python scripts/monitor_performance.py

# 预期输出:
# ===== Real-time Performance Metrics =====
# Position Query (last 1000 calls):
#   - Avg: 0.9ms
#   - P50: 0.8ms
#   - P95: 1.2ms
#   - P99: 1.5ms
# ✓ 达成目标: <1ms
#
# Trade Query (last 100 calls):
#   - Avg: 52ms
#   - P50: 48ms
#   - P95: 65ms
#   - P99: 75ms
# ✓ 达成目标: <100ms
```

---

## Troubleshooting (故障排查)

### 问题1: Redis连接失败

**症状**: `redis.exceptions.ConnectionError: Error connecting to localhost:6379`

**解决方案**:
```bash
# 检查Redis容器是否运行
docker ps | grep redis

# 检查Redis日志
docker logs silverquant-redis

# 重启Redis容器
docker restart silverquant-redis

# 验证连接
docker exec silverquant-redis redis-cli ping
```

### 问题2: MySQL连接被拒绝

**症状**: `pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`

**解决方案**:
```bash
# 检查MySQL容器状态
docker ps | grep mysql

# 检查MySQL日志
docker logs silverquant-mysql

# 等待MySQL完全启动 (首次启动需要1-2分钟)
docker exec silverquant-mysql mysqladmin ping

# 预期输出: mysqld is alive
```

### 问题3: ClickHouse查询超时

**症状**: `clickhouse_driver.errors.SocketTimeoutError: Timeout`

**解决方案**:
```bash
# 检查ClickHouse内存占用
docker stats silverquant-clickhouse

# 如果内存不足 (<500MB),增加内存限制
# 编辑 docker-compose-full.yml:
# clickhouse:
#   deploy:
#     resources:
#       limits:
#         memory: 2G

# 重启ClickHouse
docker-compose -f deployment/docker-compose-full.yml restart clickhouse
```

### 问题4: 数据不一致

**症状**: `verify_consistency.py` 报告不一致

**解决方案**:
```bash
# 查看具体不一致记录
python scripts/verify_consistency.py --type held_days --account 55009728 --verbose

# 输出示例:
# ✗ SH600000: 文件=5, Redis=6 (差异=1)
#
# 原因分析: Redis已执行持仓天数+1,但文件尚未更新

# 强制同步 (从数据库导出到文件)
python scripts/export_to_file.py --type held_days --account 55009728

# 或从文件导入到数据库
python scripts/import_from_file.py --type held_days --account 55009728
```

### 问题5: 性能未达预期

**症状**: 基准测试显示性能未达标

**解决方案**:
```bash
# 检查容器资源限制
docker stats

# 检查Redis是否启用持久化 (会影响性能)
docker exec silverquant-redis redis-cli CONFIG GET save
# 如果输出不为空,禁用RDB:
docker exec silverquant-redis redis-cli CONFIG SET save ""

# 检查ClickHouse表是否有正确的分区和索引
docker exec -it silverquant-clickhouse clickhouse-client
# 执行查询:
# SHOW CREATE TABLE daily_kline;
# 确认 PARTITION BY 和 ORDER BY 正确

# 清理ClickHouse旧分区 (释放资源)
python scripts/cleanup_old_partitions.py --before 2020-01-01
```

---

## Next Steps

完成快速上手指南后,您可以:

1. **阅读详细设计**:
   - `data-model.md` - 数据模型设计
   - `contracts/base_store_interface.py` - 统一接口定义
   - `research.md` - 技术选型依据

2. **查看实施计划**:
   - `plan.md` - 完整实施计划
   - `tasks.md` - 任务分解 (运行 `/tasks` 命令生成)

3. **参与开发**:
   - 查看 `tasks.md` 中的待办任务
   - 认领任务并创建特性分支
   - 提交Pull Request

4. **报告问题**:
   - GitHub Issues: [项目地址]/issues
   - 附上完整的错误日志和环境信息

---

**Guide Version**: 1.0
**Last Updated**: 2025-10-01
**Maintainer**: SilverQuant Team
