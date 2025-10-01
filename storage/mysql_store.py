#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQLStore: MySQL存储实现

WARM层存储,用于账户、策略、用户权限等关系数据
适用于:
- 账户管理 (create_account, get_account, update_account_capital)
- 策略管理 (create_strategy, get_strategy_params, save_strategy_params)
- 用户权限管理 (User, Role, Permission)
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric, DateTime, Boolean,
    Text, Enum, ForeignKey, UniqueConstraint, Index, func, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import Optional, Dict, List, Tuple
import pandas as pd
from datetime import datetime
import json

from storage.base_store import BaseDataStore
from storage.config import MYSQL_CONFIG


# SQLAlchemy ORM Base
Base = declarative_base()


# ==================== ORM Models ====================

class Account(Base):
    """账户表 (from data-model.md)"""
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    account_name = Column(String(100), nullable=False)
    broker = Column(Enum('QMT', 'GM', 'TDX'), nullable=False)
    initial_capital = Column(Numeric(20, 2), nullable=False)
    current_capital = Column(Numeric(20, 2), nullable=True)
    total_assets = Column(Numeric(20, 2), nullable=True)
    position_value = Column(Numeric(20, 2), nullable=True)
    status = Column(Enum('active', 'inactive', 'suspended'), nullable=False, default='active')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    account_strategies = relationship('AccountStrategy', back_populates='account')


class Strategy(Base):
    """策略表 (from data-model.md)"""
    __tablename__ = 'strategy'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), unique=True, nullable=False, index=True)
    strategy_code = Column(String(50), unique=True, nullable=False, index=True)
    strategy_type = Column(Enum('wencai', 'remote', 'technical'), nullable=False)
    version = Column(String(20), nullable=False)
    status = Column(Enum('active', 'testing', 'inactive'), nullable=False, default='active')
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    account_strategies = relationship('AccountStrategy', back_populates='strategy')
    params = relationship('StrategyParam', back_populates='strategy')


class AccountStrategy(Base):
    """账户-策略关联表 (from data-model.md)"""
    __tablename__ = 'account_strategy'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    strategy_id = Column(Integer, ForeignKey('strategy.id'), nullable=False)
    allocated_capital = Column(Numeric(20, 2), nullable=False)
    risk_limit = Column(Numeric(5, 2), nullable=False)
    status = Column(Enum('active', 'paused'), nullable=False, default='active')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    account = relationship('Account', back_populates='account_strategies')
    strategy = relationship('Strategy', back_populates='account_strategies')

    # 约束
    __table_args__ = (
        UniqueConstraint('account_id', 'strategy_id', name='uq_account_strategy'),
    )


class StrategyParam(Base):
    """策略参数表 (from data-model.md)"""
    __tablename__ = 'strategy_param'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey('strategy.id'), nullable=False)
    param_key = Column(String(100), nullable=False)
    param_value = Column(Text, nullable=False)
    param_type = Column(Enum('int', 'float', 'string', 'json'), nullable=False)
    version = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关系
    strategy = relationship('Strategy', back_populates='params')

    # 约束和索引
    __table_args__ = (
        UniqueConstraint('strategy_id', 'param_key', 'version', name='uq_strategy_param_version'),
        Index('idx_strategy_active', 'strategy_id', 'param_key', 'is_active'),
    )


class User(Base):
    """用户表 (from data-model.md)"""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    status = Column(Enum('active', 'inactive', 'locked'), nullable=False, default='active')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    user_roles = relationship('UserRole', back_populates='user')


class Role(Base):
    """角色表 (from data-model.md)"""
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关系
    user_roles = relationship('UserRole', back_populates='role')
    role_permissions = relationship('RolePermission', back_populates='role')


class Permission(Base):
    """权限表 (from data-model.md)"""
    __tablename__ = 'permission'

    id = Column(Integer, primary_key=True, autoincrement=True)
    permission_name = Column(String(50), unique=True, nullable=False, index=True)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关系
    role_permissions = relationship('RolePermission', back_populates='permission')


class UserRole(Base):
    """用户-角色关联表 (from data-model.md)"""
    __tablename__ = 'user_role'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关系
    user = relationship('User', back_populates='user_roles')
    role = relationship('Role', back_populates='user_roles')

    # 约束
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )


class RolePermission(Base):
    """角色-权限关联表 (from data-model.md)"""
    __tablename__ = 'role_permission'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permission.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关系
    role = relationship('Role', back_populates='role_permissions')
    permission = relationship('Permission', back_populates='role_permissions')

    # 约束
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )


# ==================== MySQLStore Implementation ====================

class MySQLStore(BaseDataStore):
    """
    MySQL存储实现 (WARM层)

    适用场景:
    - 账户管理 (2-3个账户)
    - 策略管理 (参数版本化)
    - 用户权限管理

    性能目标:
    - 账户查询: <100ms
    - 策略参数查询: <100ms
    - 参数版本对比: <500ms
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        database: str = None,
        **kwargs
    ):
        """
        初始化MySQL存储

        Args:
            host: MySQL主机地址,默认从config.py读取
            port: MySQL端口,默认从config.py读取
            user: MySQL用户名,默认从config.py读取
            password: MySQL密码,默认从config.py读取
            database: MySQL数据库名,默认从config.py读取
            **kwargs: 其他SQLAlchemy参数
        """
        # 使用配置文件中的默认值
        config = MYSQL_CONFIG.copy()
        if host:
            config['host'] = host
        if port:
            config['port'] = port
        if user:
            config['user'] = user
        if password:
            config['password'] = password
        if database:
            config['database'] = database

        # 构建连接字符串
        connection_string = (
            f"mysql+pymysql://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['database']}"
            f"?charset={config['charset']}"
        )

        # 创建引擎和会话
        self.engine = create_engine(
            connection_string,
            pool_size=config.get('pool_size', 10),
            pool_recycle=config.get('pool_recycle', 3600),
            echo=False,
            **kwargs
        )

        # 创建会话工厂
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def _get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    # ==================== 账户管理 (Account Management) ====================

    def create_account(
        self,
        account_id: str,
        account_name: str,
        broker: str,
        initial_capital: float
    ) -> bool:
        """
        创建账户

        验证规则:
        - account_id 全局唯一
        - initial_capital > 0
        - broker 必须为 QMT/GM/TDX
        """
        session = self._get_session()
        try:
            # 检查唯一性
            existing = session.query(Account).filter_by(account_id=account_id).first()
            if existing:
                print(f'[MySQLStore] Account {account_id} already exists')
                return False

            # 验证
            if initial_capital <= 0:
                print(f'[MySQLStore] initial_capital must be > 0')
                return False

            if broker not in ['QMT', 'GM', 'TDX']:
                print(f'[MySQLStore] broker must be QMT/GM/TDX')
                return False

            # 创建账户
            account = Account(
                account_id=account_id,
                account_name=account_name,
                broker=broker,
                initial_capital=initial_capital,
                current_capital=initial_capital,
                status='active'
            )
            session.add(account)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f'[MySQLStore] create_account failed: {e}')
            return False
        finally:
            session.close()

    def get_account(self, account_id: str) -> Optional[Dict]:
        """查询账户信息"""
        session = self._get_session()
        try:
            account = session.query(Account).filter_by(account_id=account_id).first()
            if not account:
                return None

            return {
                'id': account.id,
                'account_id': account.account_id,
                'account_name': account.account_name,
                'broker': account.broker,
                'initial_capital': float(account.initial_capital),
                'current_capital': float(account.current_capital) if account.current_capital else None,
                'total_assets': float(account.total_assets) if account.total_assets else None,
                'position_value': float(account.position_value) if account.position_value else None,
                'status': account.status,
                'created_at': account.created_at.isoformat(),
                'updated_at': account.updated_at.isoformat()
            }

        except Exception as e:
            print(f'[MySQLStore] get_account failed: {e}')
            return None
        finally:
            session.close()

    def update_account_capital(self, account_id: str, current_capital: float) -> bool:
        """更新账户资金"""
        session = self._get_session()
        try:
            account = session.query(Account).filter_by(account_id=account_id).first()
            if not account:
                print(f'[MySQLStore] Account {account_id} not found')
                return False

            if current_capital < 0:
                print(f'[MySQLStore] current_capital must be >= 0')
                return False

            account.current_capital = current_capital
            account.updated_at = datetime.now()
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f'[MySQLStore] update_account_capital failed: {e}')
            return False
        finally:
            session.close()

    # ==================== 策略管理 (Strategy Management) ====================

    def create_strategy(
        self,
        strategy_name: str,
        strategy_code: str,
        strategy_type: str,
        version: str
    ) -> bool:
        """创建策略"""
        session = self._get_session()
        try:
            # 检查唯一性
            existing = session.query(Strategy).filter_by(strategy_code=strategy_code).first()
            if existing:
                print(f'[MySQLStore] Strategy {strategy_code} already exists')
                return False

            # 验证
            if strategy_type not in ['wencai', 'remote', 'technical']:
                print(f'[MySQLStore] strategy_type must be wencai/remote/technical')
                return False

            # 创建策略
            strategy = Strategy(
                strategy_name=strategy_name,
                strategy_code=strategy_code,
                strategy_type=strategy_type,
                version=version,
                status='active'
            )
            session.add(strategy)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f'[MySQLStore] create_strategy failed: {e}')
            return False
        finally:
            session.close()

    def get_strategy_params(self, strategy_code: str) -> Optional[Dict]:
        """
        查询策略参数 (当前激活版本)

        返回格式: {param_key: param_value, ...}
        """
        session = self._get_session()
        try:
            # 查询策略
            strategy = session.query(Strategy).filter_by(strategy_code=strategy_code).first()
            if not strategy:
                return None

            # 查询激活参数
            params = session.query(StrategyParam).filter_by(
                strategy_id=strategy.id,
                is_active=True
            ).all()

            # 转换为字典
            result = {}
            for param in params:
                # 根据类型解析值
                if param.param_type == 'int':
                    result[param.param_key] = int(param.param_value)
                elif param.param_type == 'float':
                    result[param.param_key] = float(param.param_value)
                elif param.param_type == 'json':
                    result[param.param_key] = json.loads(param.param_value)
                else:
                    result[param.param_key] = param.param_value

            return result

        except Exception as e:
            print(f'[MySQLStore] get_strategy_params failed: {e}')
            return None
        finally:
            session.close()

    def save_strategy_params(self, strategy_code: str, params: Dict) -> bool:
        """
        保存策略参数 (新版本)

        操作:
        1. 查询当前最大版本号
        2. 将旧激活版本的 is_active 设为 False
        3. 插入新版本参数,is_active=True
        """
        session = self._get_session()
        try:
            # 查询策略
            strategy = session.query(Strategy).filter_by(strategy_code=strategy_code).first()
            if not strategy:
                print(f'[MySQLStore] Strategy {strategy_code} not found')
                return False

            # 开启事务
            # 1. 查询当前最大版本号
            max_version = session.query(func.max(StrategyParam.version)).filter_by(
                strategy_id=strategy.id
            ).scalar() or 0
            new_version = max_version + 1

            # 2. 将旧激活版本设为非激活
            session.query(StrategyParam).filter_by(
                strategy_id=strategy.id,
                is_active=True
            ).update({'is_active': False})

            # 3. 插入新版本参数
            for key, value in params.items():
                # 推断参数类型
                if isinstance(value, bool):
                    param_type = 'json'
                    param_value = json.dumps(value)
                elif isinstance(value, int):
                    param_type = 'int'
                    param_value = str(value)
                elif isinstance(value, float):
                    param_type = 'float'
                    param_value = str(value)
                elif isinstance(value, (dict, list)):
                    param_type = 'json'
                    param_value = json.dumps(value, ensure_ascii=False)
                else:
                    param_type = 'string'
                    param_value = str(value)

                param = StrategyParam(
                    strategy_id=strategy.id,
                    param_key=key,
                    param_value=param_value,
                    param_type=param_type,
                    version=new_version,
                    is_active=True
                )
                session.add(param)

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f'[MySQLStore] save_strategy_params failed: {e}')
            return False
        finally:
            session.close()

    def compare_strategy_params(
        self,
        strategy_code: str,
        new_params: Dict
    ) -> Tuple[Dict, Dict, Dict]:
        """
        比较策略参数差异

        Returns:
            (added, modified, deleted)
            added: 新增的参数 {key: new_value}
            modified: 修改的参数 {key: (old_value, new_value)}
            deleted: 删除的参数 {key: old_value}
        """
        old_params = self.get_strategy_params(strategy_code) or {}

        added = {k: v for k, v in new_params.items() if k not in old_params}
        deleted = {k: v for k, v in old_params.items() if k not in new_params}
        modified = {
            k: (old_params[k], new_params[k])
            for k in old_params.keys() & new_params.keys()
            if old_params[k] != new_params[k]
        }

        return added, modified, deleted

    # ==================== 持仓状态 (Position State) - 不支持 ====================

    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        """持仓查询 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def update_held_days(self, code: str, account_id: str, days: int) -> bool:
        """持仓更新 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def delete_held_days(self, code: str, account_id: str) -> bool:
        """持仓删除 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def batch_new_held(self, account_id: str, codes: List[str]) -> bool:
        """批量新增持仓 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def all_held_inc(self, account_id: str) -> bool:
        """持仓天数递增 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def get_max_price(self, code: str, account_id: str) -> Optional[float]:
        """最高价查询 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def update_max_price(self, code: str, account_id: str, price: float) -> bool:
        """最高价更新 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def get_min_price(self, code: str, account_id: str) -> Optional[float]:
        """最低价查询 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def update_min_price(self, code: str, account_id: str, price: float) -> bool:
        """最低价更新 - MySQL不支持,使用RedisStore"""
        raise NotImplementedError(
            "MySQLStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    # ==================== 交易记录 (Trade Records) - 不支持 ====================

    def record_trade(
        self,
        account_id: str,
        timestamp: str,
        stock_code: str,
        stock_name: str,
        order_type: str,
        remark: str,
        price: float,
        volume: int,
        strategy_name: Optional[str] = None
    ) -> bool:
        """记录交易 - MySQL不支持,使用ClickHouseStore"""
        raise NotImplementedError(
            "MySQLStore does not support trade records. "
            "Use ClickHouseStore for this operation."
        )

    def query_trades(
        self,
        account_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> pd.DataFrame:
        """查询交易记录 - MySQL不支持,使用ClickHouseStore"""
        raise NotImplementedError(
            "MySQLStore does not support trade queries. "
            "Use ClickHouseStore for this operation."
        )

    def aggregate_trades(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        group_by: str = 'stock'
    ) -> pd.DataFrame:
        """聚合交易统计 - MySQL不支持,使用ClickHouseStore"""
        raise NotImplementedError(
            "MySQLStore does not support trade aggregation. "
            "Use ClickHouseStore for this operation."
        )

    # ==================== K线数据 (Kline Data) - 不支持 ====================

    def get_kline(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> pd.DataFrame:
        """查询K线数据 - MySQL不支持,使用ClickHouseStore"""
        raise NotImplementedError(
            "MySQLStore does not support kline data. "
            "Use ClickHouseStore for this operation."
        )

    def batch_get_kline(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> Dict[str, pd.DataFrame]:
        """批量查询K线数据 - MySQL不支持,使用ClickHouseStore"""
        raise NotImplementedError(
            "MySQLStore does not support kline data. "
            "Use ClickHouseStore for this operation."
        )

    # ==================== 连接管理 (Connection Management) ====================

    def health_check(self) -> bool:
        """
        健康检查

        MySQL检查 SELECT 1 命令响应
        """
        session = self._get_session()
        try:
            session.execute(text('SELECT 1'))
            return True
        except Exception as e:
            print(f'[MySQLStore] health_check failed: {e}')
            return False
        finally:
            session.close()

    def close(self) -> None:
        """关闭MySQL连接"""
        try:
            self.engine.dispose()
        except Exception as e:
            print(f'[MySQLStore] close failed: {e}')
