# Technical Research: 数据存储模块性能优化

**Feature**: 001-data-storage-optimization
**Date**: 2025-10-01
**Status**: Complete

## Research Scope

基于功能规范和影响分析,以下技术决策需要研究支撑:
1. **存储技术选型**: 内存数据库、关系数据库、时序数据库的选择
2. **Python数据库客户端库**: 性能、成熟度、社区支持对比
3. **容器化部署**: Docker vs Podman在Windows环境的支持
4. **统一接口设计模式**: 抽象工厂、适配器、策略模式的适用性
5. **数据迁移策略**: 双写模式、事件溯源、ETL工具对比
6. **测试框架选型**: pytest vs unittest vs nose2

---

## 1. 存储技术选型

### 决策: Redis + MySQL + ClickHouse

**选择理由**:

#### Redis (内存数据库 - HOT层)
- **用途**: 持仓状态(持仓天数、最高价、最低价)
- **性能**: 单次查询<1ms,支持原子操作(HINCRBY)
- **数据结构**: Hash - `held_days:{account_id}` → `{code: days}`
- **持久化**: AOF每秒同步,最多丢失1秒数据
- **内存占用**: 约100MB (3账户×100股票×3字段×100字节)

**替代方案考虑**:
- **Memcached**: 不支持持久化,不支持复杂数据结构 ❌
- **KeyDB**: Redis fork,多线程支持,但本项目单机环境无需多核优势 ⚠️
- **文件内存映射(mmap)**: Python内置,但无原子操作,多进程不安全 ❌

#### MySQL (关系数据库 - WARM层)
- **用途**: 账户管理、策略配置、策略参数版本、用户权限
- **事务支持**: ACID保证账户资金一致性
- **查询能力**: 支持复杂JOIN(账户-策略多对多关系)
- **版本化**: 通过version字段实现参数历史追溯
- **社区支持**: 文档完善,Python生态成熟(SQLAlchemy ORM)

**替代方案考虑**:
- **PostgreSQL**: 功能更强大(JSON字段、全文索引),但Windows环境部署复杂 ⚠️
- **SQLite**: 轻量级,但不支持并发写入,多账户场景下会阻塞 ❌
- **MongoDB**: NoSQL灵活,但缺少事务支持(5.0+才支持),关系查询复杂 ❌

#### ClickHouse (列式数据库 - COOL层)
- **用途**: K线历史数据(625万条)、交易记录(10万+条/年)
- **压缩比**: 10:1 (2GB CSV → 200MB ClickHouse)
- **查询性能**: 按日期范围查询<50ms,聚合统计(月度盈亏)<100ms
- **分区策略**: 按月分区(toYYYYMM),自动裁剪旧数据
- **批量写入**: INSERT ... SELECT适合CSV导入

**替代方案考虑**:
- **TimescaleDB**: PostgreSQL扩展,时序优化,但部署复杂 ⚠️
- **InfluxDB**: 专用时序数据库,但不支持UPDATE(K线数据修正场景不适用) ❌
- **保留CSV + DuckDB查询**: DuckDB支持直接查询CSV,但压缩效果差 ⚠️

**综合评估**:
| 技术 | 性能 | 学习曲线 | 部署复杂度 | 社区支持 | 推荐度 |
|------|------|---------|-----------|---------|-------|
| Redis | 优秀 | 低 | 低 | 优秀 | ✅ 强烈推荐 |
| MySQL | 良好 | 低 | 低 | 优秀 | ✅ 强烈推荐 |
| ClickHouse | 优秀 | 中 | 中 | 良好 | ✅ 推荐 |
| PostgreSQL | 优秀 | 中 | 中 | 优秀 | ⚠️ 可选替代 |

---

## 2. Python数据库客户端库

### 决策: redis-py + SQLAlchemy + clickhouse-driver

#### redis-py (官方Redis客户端)
- **版本**: 5.0+ (支持Python 3.10+)
- **性能**: 单进程约10万QPS
- **连接池**: 内置连接池,自动重连
- **安装**: `pip install redis`
- **示例**:
  ```python
  import redis
  r = redis.Redis(host='localhost', port=6379, decode_responses=True)
  r.hset('held_days:55009728', 'SH600000', 5)
  days = r.hget('held_days:55009728', 'SH600000')  # '5'
  ```

**替代方案**:
- **aioredis**: 异步支持,但本项目同步模式足够 ⚠️
- **hiredis**: C扩展加速,但redis-py 5.0已内置hiredis解析器 ✅

#### SQLAlchemy 2.0 (ORM框架)
- **版本**: 2.0+ (全新API,类型提示支持)
- **优势**:
  - 声明式模型定义(Declarative Base)
  - 自动生成表结构(metadata.create_all)
  - 查询构建器(select/insert/update)
  - 支持多种数据库(MySQL/PostgreSQL/SQLite)
- **安装**: `pip install sqlalchemy pymysql`
- **示例**:
  ```python
  from sqlalchemy import create_engine, Column, Integer, String
  from sqlalchemy.orm import declarative_base, Session

  Base = declarative_base()

  class Account(Base):
      __tablename__ = 'accounts'
      id = Column(Integer, primary_key=True)
      account_id = Column(String(50), unique=True)
      account_name = Column(String(100))

  engine = create_engine('mysql+pymysql://user:pass@localhost/silverquant')
  Base.metadata.create_all(engine)  # 自动建表
  ```

**替代方案**:
- **Django ORM**: 功能强大,但依赖Django框架,过重 ❌
- **Peewee**: 轻量级,但社区支持不如SQLAlchemy ⚠️
- **原生SQL**: 性能最优,但需手写CRUD,维护成本高 ❌

#### clickhouse-driver (官方ClickHouse客户端)
- **版本**: 0.2.7+
- **性能**: 支持原生TCP协议(比HTTP快30%)
- **批量插入**: INSERT ... VALUES支持生成器,内存高效
- **安装**: `pip install clickhouse-driver`
- **示例**:
  ```python
  from clickhouse_driver import Client

  client = Client('localhost')
  client.execute('CREATE TABLE IF NOT EXISTS daily_kline (...)')

  # 批量插入
  data = [('SH600000', '2024-01-01', 10.5, 10.8, ...)]
  client.execute('INSERT INTO daily_kline VALUES', data)

  # 查询
  result = client.execute("SELECT * FROM daily_kline WHERE code='SH600000' AND date >= '2024-01-01'")
  ```

**替代方案**:
- **clickhouse-sqlalchemy**: SQLAlchemy方言支持,但查询性能略低 ⚠️
- **HTTP接口**: 通用性好,但性能比原生TCP慢 ❌

**依赖清单** (`requirements-db.txt`):
```
redis>=5.0.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
clickhouse-driver>=0.2.7
cryptography>=41.0.0  # SQLAlchemy加密支持
```

---

## 3. 容器化部署: Podman vs Docker

### 决策: 优先Podman,兼容Docker

**Podman优势**:
- **无守护进程**: 不需要后台服务,资源占用低
- **Rootless模式**: 普通用户运行,安全性更高
- **兼容Docker**: 命令行兼容(podman = docker)
- **Windows支持**: Podman Desktop + WSL2后端

**Docker优势**:
- **生态成熟**: Docker Compose广泛使用
- **Windows原生**: Docker Desktop集成度高

**推荐策略**:
1. 提供`docker-compose.yml`配置文件(兼容Podman Compose)
2. 启动脚本自动检测:
   ```bash
   if command -v podman &> /dev/null; then
       CONTAINER_CMD="podman-compose"
   elif command -v docker &> /dev/null; then
       CONTAINER_CMD="docker-compose"
   else
       echo "Error: 请安装 Docker 或 Podman"
       exit 1
   fi
   ```

**docker-compose.yml结构**:
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    container_name: silverquant-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    container_name: silverquant-mysql
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: silverquant2024
      MYSQL_DATABASE: silverquant
    volumes:
      - mysql-data:/var/lib/mysql
    restart: unless-stopped

  clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: silverquant-clickhouse
    ports:
      - "8123:8123"  # HTTP
      - "9000:9000"  # Native
    volumes:
      - clickhouse-data:/var/lib/clickhouse
    restart: unless-stopped

volumes:
  redis-data:
  mysql-data:
  clickhouse-data:
```

---

## 4. 统一接口设计模式

### 决策: 抽象工厂模式 + 策略模式

**设计目标**:
1. **向后兼容**: 策略代码无需知道数据来自文件还是数据库
2. **灵活切换**: 通过配置开关切换存储后端
3. **渐进式迁移**: 支持双写模式(同时写文件和数据库)

**模式选择**:

#### 抽象工厂模式 (创建统一接口)
```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, List

class BaseDataStore(ABC):
    """统一数据存储接口"""

    @abstractmethod
    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        """查询持仓天数"""
        pass

    @abstractmethod
    def update_held_days(self, code: str, days: int, account_id: str):
        """更新持仓天数"""
        pass

    @abstractmethod
    def all_held_inc(self, account_id: str) -> bool:
        """所有持仓天数+1"""
        pass

    @abstractmethod
    def get_max_prices(self, codes: List[str], account_id: str) -> Dict[str, float]:
        """批量查询最高价"""
        pass

    @abstractmethod
    def record_trade(self, account_id: str, timestamp: str, code: str,
                    name: str, order_type: str, remark: str,
                    price: float, volume: int):
        """记录交易"""
        pass

    @abstractmethod
    def get_kline(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """查询K线数据"""
        pass
```

#### 策略模式 (实现多种存储后端)
```python
class FileDataStore(BaseDataStore):
    """文件存储实现(包装现有utils_cache.py)"""
    def __init__(self, base_path: str):
        self.base_path = base_path

    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        path = f'{self.base_path}/held_days.json'
        held_days = load_json(path)  # 复用现有函数
        return held_days.get(code)

class RedisDataStore(BaseDataStore):
    """Redis存储实现"""
    def __init__(self, redis_client):
        self.redis = redis_client

    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        key = f'held_days:{account_id}'
        value = self.redis.hget(key, code)
        return int(value) if value else None

class HybridDataStore(BaseDataStore):
    """混合模式(双写+自动降级)"""
    def __init__(self, primary: BaseDataStore, fallback: BaseDataStore):
        self.primary = primary
        self.fallback = fallback

    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        try:
            return self.primary.get_held_days(code, account_id)
        except Exception as e:
            logging.warning(f'主存储故障,降级到备用存储: {e}')
            return self.fallback.get_held_days(code, account_id)
```

#### 工厂函数 (根据配置创建)
```python
def create_data_store(mode: str, config: dict) -> BaseDataStore:
    """工厂函数:根据模式创建数据存储"""
    if mode == 'file':
        return FileDataStore(config['base_path'])
    elif mode == 'redis':
        redis_client = redis.Redis(**config['redis'])
        return RedisDataStore(redis_client)
    elif mode == 'hybrid':
        primary = create_data_store('redis', config)
        fallback = create_data_store('file', config)
        return HybridDataStore(primary, fallback)
    else:
        raise ValueError(f'Unknown mode: {mode}')
```

**替代方案考虑**:
- **适配器模式**: 逐个适配现有函数,但代码重复多 ❌
- **装饰器模式**: 动态添加缓存层,但降级逻辑复杂 ⚠️
- **仓储模式**: 领域驱动设计,但本项目过于重量级 ❌

---

## 5. 数据迁移策略

### 决策: 三阶段渐进式迁移 + 双写模式

**Phase 1: 基础设施部署 (Week 1)**
- 部署容器服务(Redis + MySQL + ClickHouse)
- 开发统一接口层(`storage/base_store.py`)
- 开发文件存储包装器(`storage/file_store.py`)
- 单元测试验证接口正确性

**Phase 2: 双写模式运行 (Week 2-3)**
- 开发数据库存储实现(`storage/redis_store.py`, `storage/mysql_store.py`, `storage/clickhouse_store.py`)
- 配置`HybridDataStore`:
  - **写操作**: 同时写文件和数据库
  - **读操作**: 优先从文件读取(保持现有逻辑)
- 运行3-5个交易日,收集性能指标
- 执行数据一致性验证(`scripts/verify_consistency.py`)

**Phase 3: 切换数据库优先 (Week 4)**
- 修改`HybridDataStore`:
  - **读操作**: 优先从数据库读取,失败时降级到文件
  - **写操作**: 继续双写(保险)
- 修改14个入口文件,初始化`data_store`
- 全面回归测试(模拟盘3个交易日)
- 生产环境小仓位验证

**迁移工具设计**:

```python
# scripts/migrate_held_days.py
def migrate_held_days():
    """迁移持仓天数 JSON → Redis"""
    file_data = load_json(PATH_HELD)
    redis_client = redis.Redis(host='localhost', port=6379)

    for code, days in file_data.items():
        if code != '_inc_date':
            redis_client.hset('held_days:55009728', code, days)

    print(f'迁移完成: {len(file_data)-1} 条持仓记录')

# scripts/verify_consistency.py
def verify_held_days():
    """验证文件和Redis数据一致性"""
    file_data = load_json(PATH_HELD)
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_data = redis_client.hgetall('held_days:55009728')

    inconsistent = []
    for code in file_data.keys():
        if code != '_inc_date':
            file_val = file_data[code]
            redis_val = int(redis_data.get(code, 0))
            if file_val != redis_val:
                inconsistent.append((code, file_val, redis_val))

    if inconsistent:
        print(f'发现 {len(inconsistent)} 条不一致记录:')
        for code, f_val, r_val in inconsistent:
            print(f'  {code}: 文件={f_val}, Redis={r_val}')
    else:
        print('✅ 数据一致性验证通过')
```

**回滚策略**:
```python
# credentials.py
DATA_STORE_MODE = 'file'  # 'file', 'redis', 'hybrid'

# 一旦出现问题,修改配置并重启即可回滚
```

**替代方案考虑**:
- **事件溯源**: 记录所有变更事件,可重放,但实现复杂 ❌
- **ETL工具(Airflow/Dagster)**: 专业数据管道,但本项目数据量小,过度设计 ❌
- **直接切换**: 停机迁移,风险高,不可回滚 ❌

---

## 6. 测试框架选型

### 决策: pytest + pytest-cov

**选择理由**:
- **简洁语法**: 无需继承unittest.TestCase,直接写函数
- **Fixture机制**: 依赖注入,测试数据隔离
- **插件生态**: pytest-cov(覆盖率)、pytest-mock(Mock)、pytest-asyncio(异步)
- **参数化测试**: `@pytest.mark.parametrize`减少重复代码
- **并行执行**: pytest-xdist支持多核加速

**安装**:
```bash
pip install pytest pytest-cov pytest-mock
```

**测试结构**:
```
tests/
├── unit/                    # 单元测试
│   ├── test_file_store.py
│   ├── test_redis_store.py
│   └── test_hybrid_store.py
├── integration/             # 集成测试
│   ├── test_database_init.py
│   ├── test_data_migration.py
│   └── test_performance.py
└── contract/                # 契约测试
    ├── test_base_store_contract.py
    └── test_api_endpoints.py
```

**示例测试**:
```python
# tests/unit/test_redis_store.py
import pytest
from storage.redis_store import RedisDataStore

@pytest.fixture
def redis_store(redis_client):
    """Fixture: 创建Redis存储实例"""
    return RedisDataStore(redis_client)

def test_get_held_days(redis_store):
    """测试查询持仓天数"""
    # Arrange
    redis_store.update_held_days('SH600000', 5, '55009728')

    # Act
    days = redis_store.get_held_days('SH600000', '55009728')

    # Assert
    assert days == 5

def test_all_held_inc(redis_store):
    """测试持仓天数+1"""
    # Arrange
    redis_store.update_held_days('SH600000', 5, '55009728')
    redis_store.update_held_days('SZ000001', 3, '55009728')

    # Act
    redis_store.all_held_inc('55009728')

    # Assert
    assert redis_store.get_held_days('SH600000', '55009728') == 6
    assert redis_store.get_held_days('SZ000001', '55009728') == 4
```

**覆盖率目标**: >80%

**替代方案考虑**:
- **unittest**: Python内置,但语法冗长,Fixture机制弱 ⚠️
- **nose2**: unittest扩展,但社区活跃度不如pytest ⚠️
- **doctest**: 嵌入文档,但不适合复杂测试 ❌

---

## Research Validation

### 关键决策确认
- [x] 存储技术选型: Redis + MySQL + ClickHouse
- [x] Python客户端库: redis-py + SQLAlchemy + clickhouse-driver
- [x] 容器化部署: 优先Podman,兼容Docker
- [x] 统一接口设计: 抽象工厂 + 策略模式
- [x] 数据迁移策略: 三阶段渐进式迁移
- [x] 测试框架: pytest + pytest-cov

### 无需进一步研究的领域
- Web框架选型(规范P2优先级,可延后)
- 前端技术栈(规范P2优先级,可延后)
- 监控告警方案(规范Out of Scope)

### 准备进入Phase 1设计阶段
所有技术决策已明确,可以开始:
1. 数据模型设计(`data-model.md`)
2. API契约定义(`contracts/`)
3. 快速上手指南(`quickstart.md`)

---

**Research Completed**: 2025-10-01
**Next Phase**: Phase 1 - Design & Contracts
