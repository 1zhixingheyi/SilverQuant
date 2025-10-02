# 配置管理方案设计

**日期**: 2025-10-01
**状态**: 已实施

## 设计原则

### 关注点分离 (Separation of Concerns)

**credentials.py** 和 **storage/config.py** 各司其职:

| 文件 | 职责 | 内容 | 版本控制 |
|------|------|------|----------|
| `credentials.py` | 存储凭证 | 仅包含敏感值(host, port, password等) | .gitignore (不提交) |
| `credentials_sample.py` | 凭证模板 | 示例值,供新用户复制使用 | 提交到仓库 |
| `storage/config.py` | 配置逻辑 | 环境变量覆盖、配置验证、默认值 | 提交到仓库 |

## 文件结构

### credentials.py (凭证文件,简洁)

```python
# 将本文件复制重命名为 credentials.py 生效

# ... 原有配置 ...

# ============================================================
# 数据存储凭证 (Data Storage Credentials)
# ============================================================
# Redis 连接凭证
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = ''  # 如果 Redis 设置了密码,在此填写

# MySQL 连接凭证
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'silverquant2024'
MYSQL_DATABASE = 'silverquant'

# ClickHouse 连接凭证
CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_PORT = 9000
CLICKHOUSE_USER = 'default'
CLICKHOUSE_PASSWORD = 'silverquant2024'
CLICKHOUSE_DATABASE = 'silverquant'

# 数据存储模式: "file", "redis", "mysql", "clickhouse", "hybrid"
DATA_STORE_MODE = 'file'
```

**特点**:
- ✅ 仅 25 行,简洁易懂
- ✅ 只包含值,无复杂逻辑
- ✅ 与原有配置风格一致
- ✅ 易于用户修改

### storage/config.py (配置管理,功能丰富)

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据存储配置管理模块
从 credentials.py 读取凭证,构建完整的配置对象
"""

import os
from credentials import (
    CACHE_PROD_PATH,
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD,
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD, CLICKHOUSE_DATABASE,
    DATA_STORE_MODE
)

# Redis 配置 (环境变量覆盖)
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', REDIS_HOST),
    'port': int(os.getenv('REDIS_PORT', REDIS_PORT)),
    'password': os.getenv('REDIS_PASSWORD', REDIS_PASSWORD) or None,
    'db': int(os.getenv('REDIS_DB', 0)),
    'decode_responses': True,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'max_connections': 50,
}

# ... MySQL, ClickHouse 配置 ...

# 配置验证
def validate_config():
    """验证配置的有效性"""
    errors = []
    # ... 验证逻辑 ...
    if errors:
        raise ValueError("Configuration validation failed")
    return True
```

**特点**:
- ✅ 支持环境变量覆盖(便于 Docker/K8s 部署)
- ✅ 包含连接池、超时等高级配置
- ✅ 提供配置验证功能
- ✅ 可安全提交到仓库(无敏感信息)

## 使用方式

### 开发人员视角

1. **初始化配置**:
   ```bash
   cp credentials_sample.py credentials.py
   vim credentials.py  # 修改数据库密码等敏感信息
   ```

2. **在代码中使用**:
   ```python
   # 导入配置(而非凭证)
   from storage.config import REDIS_CONFIG, STORAGE_MODE

   # 创建 Redis 连接
   import redis
   r = redis.Redis(**REDIS_CONFIG)
   ```

3. **环境变量覆盖** (可选):
   ```bash
   export DATA_STORE_MODE=hybrid
   export REDIS_HOST=192.168.1.100
   export MYSQL_PASSWORD=my_secure_password
   python run_wencai_v1.py
   ```

### 运维人员视角

1. **Docker 部署**:
   ```yaml
   # docker-compose.yml
   services:
     silverquant:
       image: silverquant:latest
       environment:
         - DATA_STORE_MODE=hybrid
         - REDIS_HOST=redis-cluster
         - MYSQL_HOST=mysql-primary
         - MYSQL_PASSWORD=${MYSQL_PASSWORD}  # 从 .env 读取
   ```

2. **验证配置**:
   ```bash
   python -m storage.config
   # 输出: Current Storage Configuration: {...}
   # 输出: ✓ Configuration is valid
   ```

## 设计优势

### 1. 安全性

- **凭证不提交**: `credentials.py` 在 `.gitignore` 中,不会泄露密码
- **逻辑可审计**: `storage/config.py` 提交到仓库,代码审查时可验证配置逻辑

### 2. 灵活性

- **本地开发**: 修改 `credentials.py` 即可,无需设置环境变量
- **容器部署**: 通过环境变量覆盖,无需修改代码
- **多环境**: 开发/测试/生产环境使用不同的环境变量

### 3. 可维护性

- **职责清晰**: credentials.py (是什么) vs config.py (怎么用)
- **易于测试**: config.py 可以 mock credentials 进行单元测试
- **文档友好**: 新人看 credentials_sample.py 就知道需要配置什么

### 4. 向后兼容

- **保持风格**: credentials.py 结构与原有配置一致
- **渐进式采用**: 现有代码继续使用文件模式,新功能使用数据库模式
- **平滑迁移**: 用户仅需在 credentials.py 中添加几行配置

## 与其他项目对比

### Django 风格 (settings.py)
```python
# settings.py (所有配置都在一个文件)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PASSWORD': 'hardcoded_password',  # ❌ 不安全
    }
}
```
**问题**: settings.py 提交到仓库,密码泄露风险

### 环境变量风格 (12-Factor App)
```python
# config.py (所有配置从环境变量读取)
REDIS_HOST = os.environ['REDIS_HOST']  # ❌ 必须设置环境变量
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
```
**问题**: 本地开发需要设置大量环境变量,不便于快速上手

### SilverQuant 风格 (credentials.py + config.py)
```python
# credentials.py (凭证,不提交)
REDIS_PASSWORD = 'my_secret'

# storage/config.py (逻辑,提交)
REDIS_CONFIG = {
    'password': os.getenv('REDIS_PASSWORD', REDIS_PASSWORD),
}
```
**优点**: 兼顾安全性和易用性,支持两种使用方式

## 替代方案及弃用原因

### 方案1: 所有配置都在 credentials.py ❌

**弃用原因**:
- credentials.py 变得臃肿(原 24 行 → 80+ 行)
- 违反"凭证模板应简洁"的设计原则
- 配置逻辑无法进行代码审查

### 方案2: 使用 .env 文件 ⚠️

**弃用原因**:
- 需要引入 `python-dotenv` 依赖
- 与项目现有风格(credentials.py)不一致
- 增加学习成本

### 方案3: 使用 YAML/JSON 配置文件 ⚠️

**弃用原因**:
- 无法使用 Python 表达式(如 `os.path.join()`)
- 类型不明确,需要额外的 schema 验证
- 环境变量覆盖需要额外的库支持

## 测试策略

### 单元测试 (tests/unit/test_config.py)

```python
def test_config_from_credentials():
    """测试从 credentials.py 读取配置"""
    from storage.config import REDIS_CONFIG
    assert REDIS_CONFIG['host'] == 'localhost'

def test_config_env_override(monkeypatch):
    """测试环境变量覆盖"""
    monkeypatch.setenv('REDIS_HOST', '192.168.1.100')
    import importlib
    import storage.config
    importlib.reload(storage.config)
    assert storage.config.REDIS_CONFIG['host'] == '192.168.1.100'

def test_config_validation():
    """测试配置验证"""
    from storage.config import validate_config
    assert validate_config() == True
```

## 总结

当前配置方案遵循以下原则:

1. **安全第一**: 凭证不提交到仓库
2. **易用性**: 本地开发无需设置环境变量
3. **灵活性**: 支持环境变量覆盖(适合容器部署)
4. **一致性**: 与项目现有风格保持一致
5. **可维护性**: 关注点分离,职责清晰

该方案在 Phase 3.1 Setup 阶段已实施完成,后续阶段将基于此配置架构开发存储模块。
