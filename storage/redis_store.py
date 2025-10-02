#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RedisStore: Redis存储实现

HOT层存储,用于高频读写的持仓状态数据
适用于:
- 持仓天数查询/更新 (<1ms响应)
- 持仓期间最高价/最低价追踪
- 多账户持仓隔离
"""

import redis
from typing import Optional, Dict, List, Tuple
import pandas as pd
from datetime import datetime

from storage.base_store import BaseDataStore
from storage.config import REDIS_CONFIG


class RedisStore(BaseDataStore):
    """
    Redis存储实现 (HOT层)

    数据结构设计:
    - held_days:{account_id} → Hash {stock_code: days}
    - max_prices:{account_id} → Hash {stock_code: price}
    - min_prices:{account_id} → Hash {stock_code: price}
    - _inc_date:{account_id} → String (YYYY-MM-DD) 用于 all_held_inc 幂等性

    性能目标:
    - get_held_days: <1ms (单次HGET)
    - update_held_days: <1ms (单次HSET)
    - all_held_inc: <10ms (Lua脚本原子操作)
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        password: str = None,
        db: int = None,
        **kwargs
    ):
        """
        初始化Redis存储

        Args:
            host: Redis主机地址,默认从config.py读取
            port: Redis端口,默认从config.py读取
            password: Redis密码,默认从config.py读取
            db: Redis数据库编号,默认从config.py读取
            **kwargs: 其他redis.Redis参数
        """
        # 使用配置文件中的默认值
        config = REDIS_CONFIG.copy()
        if host:
            config['host'] = host
        if port:
            config['port'] = port
        if password is not None:
            config['password'] = password
        if db is not None:
            config['db'] = db

        # 合并自定义参数
        config.update(kwargs)

        # 创建Redis连接池
        pool = redis.ConnectionPool(**config)
        self.client = redis.Redis(connection_pool=pool)

        # 注册Lua脚本(用于all_held_inc原子操作)
        self._register_lua_scripts()

    def _register_lua_scripts(self):
        """注册Lua脚本到Redis"""
        # all_held_inc Lua脚本: 原子性地检查日期并递增所有持仓天数
        self.lua_all_held_inc = self.client.register_script("""
            local held_key = KEYS[1]       -- held_days:{account_id}
            local date_key = KEYS[2]       -- _inc_date:{account_id}
            local today = ARGV[1]          -- YYYY-MM-DD

            -- 检查今日是否已执行过
            local last_date = redis.call('GET', date_key)
            if last_date == today then
                return 0  -- 今日已执行,返回0
            end

            -- 获取所有持仓代码和天数
            local held_data = redis.call('HGETALL', held_key)
            if #held_data == 0 then
                return 0  -- 无持仓数据,返回0
            end

            -- 递增所有持仓天数
            local count = 0
            for i = 1, #held_data, 2 do
                local code = held_data[i]
                local days = tonumber(held_data[i + 1])
                redis.call('HSET', held_key, code, days + 1)
                count = count + 1
            end

            -- 更新日期标记
            redis.call('SET', date_key, today)

            return count  -- 返回递增的持仓数量
        """)

    # ==================== 持仓状态 (Position State) ====================

    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        """
        查询持仓天数

        Performance: Redis目标 <1ms (单次HGET)
        """
        try:
            key = f'held_days:{account_id}'
            result = self.client.hget(key, code)
            return int(result) if result else None
        except Exception as e:
            print(f'[RedisStore] get_held_days failed: {e}')
            return None

    def update_held_days(self, code: str, account_id: str, days: int) -> bool:
        """更新持仓天数"""
        try:
            key = f'held_days:{account_id}'
            self.client.hset(key, code, days)
            return True
        except Exception as e:
            print(f'[RedisStore] update_held_days failed: {e}')
            return False

    def delete_held_days(self, code: str, account_id: str) -> bool:
        """删除持仓记录"""
        try:
            key = f'held_days:{account_id}'
            self.client.hdel(key, code)
            return True
        except Exception as e:
            print(f'[RedisStore] delete_held_days failed: {e}')
            return False

    def batch_new_held(self, account_id: str, codes: List[str]) -> bool:
        """批量新增持仓,初始天数为 0"""
        try:
            if not codes:
                return True

            key = f'held_days:{account_id}'
            # 使用pipeline批量写入
            pipeline = self.client.pipeline()
            for code in codes:
                pipeline.hset(key, code, 0)
            pipeline.execute()
            return True
        except Exception as e:
            print(f'[RedisStore] batch_new_held failed: {e}')
            return False

    def all_held_inc(self, account_id: str) -> bool:
        """
        所有持仓天数 +1 (原子操作)

        使用Lua脚本确保原子性和幂等性:
        - 检查今日是否已执行过 (_inc_date标记位)
        - 原子性地递增所有持仓天数

        Performance: Redis目标 <10ms

        Returns:
            True: 执行了递增操作
            False: 今日已执行过,跳过
        """
        try:
            held_key = f'held_days:{account_id}'
            date_key = f'_inc_date:{account_id}'
            today = datetime.now().strftime('%Y-%m-%d')

            # 执行Lua脚本
            result = self.lua_all_held_inc(
                keys=[held_key, date_key],
                args=[today]
            )

            return result > 0  # 返回True表示执行了递增
        except Exception as e:
            print(f'[RedisStore] all_held_inc failed: {e}')
            return False

    def get_max_price(self, code: str, account_id: str) -> Optional[float]:
        """查询持仓期间最高价"""
        try:
            key = f'max_prices:{account_id}'
            result = self.client.hget(key, code)
            return float(result) if result else None
        except Exception as e:
            print(f'[RedisStore] get_max_price failed: {e}')
            return None

    def update_max_price(self, code: str, account_id: str, price: float) -> bool:
        """更新最高价"""
        try:
            key = f'max_prices:{account_id}'
            self.client.hset(key, code, round(price, 3))
            return True
        except Exception as e:
            print(f'[RedisStore] update_max_price failed: {e}')
            return False

    def get_min_price(self, code: str, account_id: str) -> Optional[float]:
        """查询持仓期间最低价"""
        try:
            key = f'min_prices:{account_id}'
            result = self.client.hget(key, code)
            return float(result) if result else None
        except Exception as e:
            print(f'[RedisStore] get_min_price failed: {e}')
            return None

    def update_min_price(self, code: str, account_id: str, price: float) -> bool:
        """更新最低价"""
        try:
            key = f'min_prices:{account_id}'
            self.client.hset(key, code, round(price, 3))
            return True
        except Exception as e:
            print(f'[RedisStore] update_min_price failed: {e}')
            return False

    # ==================== 交易记录 (Trade Records) ====================

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
        """记录交易 - Redis不支持,使用ClickHouse"""
        raise NotImplementedError(
            "RedisStore does not support trade records. "
            "Use ClickHouseStore for this operation."
        )

    def query_trades(
        self,
        account_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> pd.DataFrame:
        """查询交易记录 - Redis不支持,使用ClickHouse"""
        raise NotImplementedError(
            "RedisStore does not support trade queries. "
            "Use ClickHouseStore for this operation."
        )

    def aggregate_trades(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        group_by: str = 'stock'
    ) -> pd.DataFrame:
        """聚合交易统计 - Redis不支持,使用ClickHouse"""
        raise NotImplementedError(
            "RedisStore does not support trade aggregation. "
            "Use ClickHouseStore for this operation."
        )

    # ==================== K线数据 (Kline Data) ====================

    def get_kline(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> pd.DataFrame:
        """查询K线数据 - Redis不支持,使用ClickHouse"""
        raise NotImplementedError(
            "RedisStore does not support kline data. "
            "Use ClickHouseStore for this operation."
        )

    def batch_get_kline(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> Dict[str, pd.DataFrame]:
        """批量查询K线数据 - Redis不支持,使用ClickHouse"""
        raise NotImplementedError(
            "RedisStore does not support kline data. "
            "Use ClickHouseStore for this operation."
        )

    # ==================== 账户管理 (Account Management) ====================

    def create_account(
        self,
        account_id: str,
        account_name: str,
        broker: str,
        initial_capital: float
    ) -> bool:
        """创建账户 - Redis不支持,使用MySQLStore"""
        raise NotImplementedError(
            "RedisStore does not support account management. "
            "Use MySQLStore for this operation."
        )

    def get_account(self, account_id: str) -> Optional[Dict]:
        """查询账户信息 - Redis不支持,使用MySQLStore"""
        raise NotImplementedError(
            "RedisStore does not support account management. "
            "Use MySQLStore for this operation."
        )

    def update_account_capital(self, account_id: str, current_capital: float) -> bool:
        """更新账户资金 - Redis不支持,使用MySQLStore"""
        raise NotImplementedError(
            "RedisStore does not support account management. "
            "Use MySQLStore for this operation."
        )

    # ==================== 策略管理 (Strategy Management) ====================

    def create_strategy(
        self,
        strategy_name: str,
        strategy_code: str,
        strategy_type: str,
        version: str
    ) -> bool:
        """创建策略 - Redis不支持,使用MySQLStore"""
        raise NotImplementedError(
            "RedisStore does not support strategy management. "
            "Use MySQLStore for this operation."
        )

    def get_strategy_params(self, strategy_code: str) -> Optional[Dict]:
        """查询策略参数 - Redis不支持,使用MySQLStore"""
        raise NotImplementedError(
            "RedisStore does not support strategy management. "
            "Use MySQLStore for this operation."
        )

    def save_strategy_params(self, strategy_code: str, params: Dict) -> bool:
        """保存策略参数 - Redis不支持,使用MySQLStore"""
        raise NotImplementedError(
            "RedisStore does not support strategy management. "
            "Use MySQLStore for this operation."
        )

    def compare_strategy_params(
        self,
        strategy_code: str,
        new_params: Dict
    ) -> Tuple[Dict, Dict, Dict]:
        """比较策略参数差异 - Redis不支持,使用MySQLStore"""
        raise NotImplementedError(
            "RedisStore does not support strategy management. "
            "Use MySQLStore for this operation."
        )

    # ==================== 连接管理 (Connection Management) ====================

    def health_check(self) -> bool:
        """
        健康检查

        Redis检查PING命令响应
        """
        try:
            return self.client.ping()
        except Exception as e:
            print(f'[RedisStore] health_check failed: {e}')
            return False

    def close(self) -> None:
        """关闭Redis连接"""
        try:
            self.client.close()
        except Exception as e:
            print(f'[RedisStore] close failed: {e}')
