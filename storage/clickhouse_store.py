#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ClickHouseStore: ClickHouse存储实现

COOL层存储,用于交易记录和K线数据的时序数据存储
适用于:
- 交易记录 (record_trade, query_trades, aggregate_trades)
- K线数据 (get_kline, batch_get_kline)
- 海量历史数据查询和聚合统计
"""

from clickhouse_driver import Client
from typing import Optional, Dict, List, Tuple
import pandas as pd
from datetime import datetime
from decimal import Decimal

from storage.base_store import BaseDataStore
from storage.config import CLICKHOUSE_CONFIG


class ClickHouseStore(BaseDataStore):
    """
    ClickHouse存储实现 (COOL层)

    表结构:
    - trade: 交易记录 (按月分区)
    - daily_kline: 日线K线数据 (按月分区)

    性能目标:
    - 交易记录查询 (1年): <100ms
    - K线查询 (60天): <20ms
    - 聚合统计 (3年): <500ms
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        **kwargs
    ):
        """
        初始化ClickHouse存储

        Args:
            host: ClickHouse主机地址,默认从config.py读取
            port: ClickHouse端口,默认从config.py读取
            database: ClickHouse数据库名,默认从config.py读取
            user: ClickHouse用户名,默认从config.py读取
            password: ClickHouse密码,默认从config.py读取
            **kwargs: 其他clickhouse_driver.Client参数
        """
        # 使用配置文件中的默认值
        config = CLICKHOUSE_CONFIG.copy()
        if host:
            config['host'] = host
        if port:
            config['port'] = port
        if database:
            config['database'] = database
        if user:
            config['user'] = user
        if password is not None:
            config['password'] = password

        # 合并自定义参数
        config.update(kwargs)

        # 创建ClickHouse客户端
        self.client = Client(**config)
        self.database = config['database']

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
        """
        记录交易

        Performance: ClickHouse目标 <3ms (单条插入)

        Args:
            timestamp: 交易时间戳 (YYYY-MM-DD HH:MM:SS)
            order_type: 订单类型 (buy_order/sell_order/buy_trade/sell_trade/cancel)
        """
        try:
            # 解析时间戳
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            date = dt.date()

            # 计算成交金额
            amount = round(price * volume, 2)

            # 插入数据
            self.client.execute(
                f'''
                INSERT INTO {self.database}.trade
                (timestamp, date, account_id, stock_code, stock_name,
                 order_type, strategy_name, price, volume, amount, remark)
                VALUES
                ''',
                [(dt, date, account_id, stock_code, stock_name,
                  order_type, strategy_name or '', price, volume, amount, remark)]
            )
            return True

        except Exception as e:
            print(f'[ClickHouseStore] record_trade failed: {e}')
            return False

    def query_trades(
        self,
        account_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        查询交易记录

        Performance: ClickHouse目标 <100ms (1年数据)

        Returns:
            DataFrame with columns: [timestamp, date, stock_code, stock_name,
                                    order_type, price, volume, amount, remark]
        """
        try:
            # 构建WHERE子句
            where_clauses = [f"account_id = '{account_id}'"]
            if start_date:
                where_clauses.append(f"date >= '{start_date}'")
            if end_date:
                where_clauses.append(f"date <= '{end_date}'")
            if stock_code:
                where_clauses.append(f"stock_code = '{stock_code}'")

            where_sql = ' AND '.join(where_clauses)

            # 执行查询
            query = f'''
                SELECT
                    timestamp,
                    date,
                    stock_code,
                    stock_name,
                    order_type,
                    strategy_name,
                    price,
                    volume,
                    amount,
                    remark
                FROM {self.database}.trade
                WHERE {where_sql}
                ORDER BY timestamp DESC
            '''

            result = self.client.execute(query)

            # 转换为DataFrame
            if not result:
                return pd.DataFrame(columns=[
                    'timestamp', 'date', 'stock_code', 'stock_name',
                    'order_type', 'strategy_name', 'price', 'volume', 'amount', 'remark'
                ])

            df = pd.DataFrame(result, columns=[
                'timestamp', 'date', 'stock_code', 'stock_name',
                'order_type', 'strategy_name', 'price', 'volume', 'amount', 'remark'
            ])

            # 转换数据类型
            df['price'] = df['price'].astype(float)
            df['volume'] = df['volume'].astype(int)
            df['amount'] = df['amount'].astype(float)

            return df

        except Exception as e:
            print(f'[ClickHouseStore] query_trades failed: {e}')
            return pd.DataFrame()

    def aggregate_trades(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        group_by: str = 'stock'
    ) -> pd.DataFrame:
        """
        聚合交易统计

        Performance: ClickHouse目标 <500ms (3年数据)

        Args:
            group_by: 'stock' (按股票), 'date' (按日期), 'month' (按月), 'type' (按交易类型)

        Returns:
            DataFrame with aggregated results
        """
        try:
            # 构建GROUP BY子句
            if group_by == 'stock':
                group_cols = 'stock_code, stock_name'
                select_cols = 'stock_code, stock_name, COUNT(*) as trade_count, SUM(volume) as total_volume, SUM(amount) as total_amount'
            elif group_by == 'date':
                group_cols = 'date'
                select_cols = 'date, COUNT(*) as trade_count, SUM(volume) as total_volume, SUM(amount) as total_amount'
            elif group_by == 'month':
                group_cols = 'toYYYYMM(date)'
                select_cols = 'toYYYYMM(date) as month, COUNT(*) as trade_count, SUM(volume) as total_volume, SUM(amount) as total_amount'
            elif group_by == 'type':
                group_cols = 'order_type'
                select_cols = 'order_type, COUNT(*) as trade_count, SUM(volume) as total_volume, SUM(amount) as total_amount'
            else:
                print(f'[ClickHouseStore] Invalid group_by: {group_by}')
                return pd.DataFrame()

            # 执行查询
            query = f'''
                SELECT {select_cols}
                FROM {self.database}.trade
                WHERE account_id = '{account_id}'
                  AND date >= '{start_date}'
                  AND date <= '{end_date}'
                GROUP BY {group_cols}
                ORDER BY total_amount DESC
            '''

            result = self.client.execute(query)

            if not result:
                return pd.DataFrame()

            # 转换为DataFrame
            column_names = select_cols.replace(' as ', ' ').split(', ')
            column_names = [col.split()[-1] for col in column_names]

            df = pd.DataFrame(result, columns=column_names)

            # 转换数据类型
            if 'total_volume' in df.columns:
                df['total_volume'] = df['total_volume'].astype(int)
            if 'total_amount' in df.columns:
                df['total_amount'] = df['total_amount'].astype(float)

            return df

        except Exception as e:
            print(f'[ClickHouseStore] aggregate_trades failed: {e}')
            return pd.DataFrame()

    # ==================== K线数据 (Kline Data) ====================

    def get_kline(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> pd.DataFrame:
        """
        查询K线数据

        Performance: ClickHouse目标 <20ms (60天数据)

        Args:
            frequency: 'daily' (日线, 其他频率暂不支持)

        Returns:
            DataFrame with columns: [date, datetime, open, high, low, close, volume, amount]
        """
        try:
            if frequency != 'daily':
                print(f'[ClickHouseStore] Only daily frequency is supported')
                return pd.DataFrame()

            # 执行查询
            query = f'''
                SELECT
                    date,
                    datetime,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    amount
                FROM {self.database}.daily_kline
                WHERE stock_code = '{stock_code}'
                  AND date >= '{start_date}'
                  AND date <= '{end_date}'
                ORDER BY date ASC
            '''

            result = self.client.execute(query)

            if not result:
                return pd.DataFrame(columns=[
                    'date', 'datetime', 'open', 'high', 'low', 'close', 'volume', 'amount'
                ])

            df = pd.DataFrame(result, columns=[
                'date', 'datetime', 'open', 'high', 'low', 'close', 'volume', 'amount'
            ])

            # 转换数据类型
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(int)
            df['amount'] = df['amount'].astype(float)

            return df

        except Exception as e:
            print(f'[ClickHouseStore] get_kline failed: {e}')
            return pd.DataFrame()

    def batch_get_kline(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> Dict[str, pd.DataFrame]:
        """
        批量查询K线数据

        Performance: ClickHouse目标 <100ms (10只股票 × 60天)

        Returns:
            {stock_code: DataFrame, ...}
        """
        try:
            if frequency != 'daily':
                print(f'[ClickHouseStore] Only daily frequency is supported')
                return {}

            # 构建IN子句
            codes_str = "', '".join(stock_codes)

            # 执行查询
            query = f'''
                SELECT
                    stock_code,
                    date,
                    datetime,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    amount
                FROM {self.database}.daily_kline
                WHERE stock_code IN ('{codes_str}')
                  AND date >= '{start_date}'
                  AND date <= '{end_date}'
                ORDER BY stock_code, date ASC
            '''

            result = self.client.execute(query)

            if not result:
                return {}

            # 转换为DataFrame
            df_all = pd.DataFrame(result, columns=[
                'stock_code', 'date', 'datetime', 'open', 'high', 'low', 'close', 'volume', 'amount'
            ])

            # 按股票代码分组
            result_dict = {}
            for code in stock_codes:
                df_code = df_all[df_all['stock_code'] == code].drop('stock_code', axis=1).copy()

                # 转换数据类型
                if not df_code.empty:
                    df_code['open'] = df_code['open'].astype(float)
                    df_code['high'] = df_code['high'].astype(float)
                    df_code['low'] = df_code['low'].astype(float)
                    df_code['close'] = df_code['close'].astype(float)
                    df_code['volume'] = df_code['volume'].astype(int)
                    df_code['amount'] = df_code['amount'].astype(float)

                result_dict[code] = df_code

            return result_dict

        except Exception as e:
            print(f'[ClickHouseStore] batch_get_kline failed: {e}')
            return {}

    # ==================== 持仓状态 (Position State) - 不支持 ====================

    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        """持仓查询 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def update_held_days(self, code: str, account_id: str, days: int) -> bool:
        """持仓更新 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def delete_held_days(self, code: str, account_id: str) -> bool:
        """持仓删除 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def batch_new_held(self, account_id: str, codes: List[str]) -> bool:
        """批量新增持仓 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def all_held_inc(self, account_id: str) -> bool:
        """持仓天数递增 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def get_max_price(self, code: str, account_id: str) -> Optional[float]:
        """最高价查询 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def update_max_price(self, code: str, account_id: str, price: float) -> bool:
        """最高价更新 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def get_min_price(self, code: str, account_id: str) -> Optional[float]:
        """最低价查询 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    def update_min_price(self, code: str, account_id: str, price: float) -> bool:
        """最低价更新 - ClickHouse不支持,使用RedisStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support position state operations. "
            "Use RedisStore for this operation."
        )

    # ==================== 账户管理 (Account Management) - 不支持 ====================

    def create_account(
        self,
        account_id: str,
        account_name: str,
        broker: str,
        initial_capital: float
    ) -> bool:
        """创建账户 - ClickHouse不支持,使用MySQLStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support account management. "
            "Use MySQLStore for this operation."
        )

    def get_account(self, account_id: str) -> Optional[Dict]:
        """查询账户信息 - ClickHouse不支持,使用MySQLStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support account management. "
            "Use MySQLStore for this operation."
        )

    def update_account_capital(self, account_id: str, current_capital: float) -> bool:
        """更新账户资金 - ClickHouse不支持,使用MySQLStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support account management. "
            "Use MySQLStore for this operation."
        )

    # ==================== 策略管理 (Strategy Management) - 不支持 ====================

    def create_strategy(
        self,
        strategy_name: str,
        strategy_code: str,
        strategy_type: str,
        version: str
    ) -> bool:
        """创建策略 - ClickHouse不支持,使用MySQLStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support strategy management. "
            "Use MySQLStore for this operation."
        )

    def get_strategy_params(self, strategy_code: str) -> Optional[Dict]:
        """查询策略参数 - ClickHouse不支持,使用MySQLStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support strategy management. "
            "Use MySQLStore for this operation."
        )

    def save_strategy_params(self, strategy_code: str, params: Dict) -> bool:
        """保存策略参数 - ClickHouse不支持,使用MySQLStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support strategy management. "
            "Use MySQLStore for this operation."
        )

    def compare_strategy_params(
        self,
        strategy_code: str,
        new_params: Dict
    ) -> Tuple[Dict, Dict, Dict]:
        """比较策略参数差异 - ClickHouse不支持,使用MySQLStore"""
        raise NotImplementedError(
            "ClickHouseStore does not support strategy management. "
            "Use MySQLStore for this operation."
        )

    # ==================== 连接管理 (Connection Management) ====================

    def health_check(self) -> bool:
        """
        健康检查

        ClickHouse检查 SELECT 1 命令响应
        """
        try:
            result = self.client.execute('SELECT 1')
            return result == [(1,)]
        except Exception as e:
            print(f'[ClickHouseStore] health_check failed: {e}')
            return False

    def close(self) -> None:
        """关闭ClickHouse连接"""
        try:
            self.client.disconnect()
        except Exception as e:
            print(f'[ClickHouseStore] close failed: {e}')
