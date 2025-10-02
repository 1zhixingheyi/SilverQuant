#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FileStore: 文件存储实现
包装现有的 utils_cache 函数,提供统一的 BaseDataStore 接口
"""

import os
import csv
import threading
import datetime
from typing import Optional, Dict, List, Tuple
import pandas as pd

from storage.base_store import BaseDataStore
from storage.config import CACHE_PROD_PATH
from tools import utils_cache


class FileStore(BaseDataStore):
    """
    文件存储实现,包装现有的 utils_cache 函数
    适用于:
    - 单机部署场景
    - 小规模数据(< 10000 条持仓记录)
    - 向后兼容现有文件存储逻辑
    """

    def __init__(self, cache_path: str = CACHE_PROD_PATH):
        """
        初始化文件存储

        Args:
            cache_path: 缓存目录路径,默认从 config.py 读取
        """
        self.cache_path = cache_path
        os.makedirs(self.cache_path, exist_ok=True)

        # 文件路径定义
        self.path_held = os.path.join(cache_path, 'held_days.json')
        self.path_max_prices = os.path.join(cache_path, 'max_prices.json')
        self.path_min_prices = os.path.join(cache_path, 'min_prices.json')
        self.path_trades = os.path.join(cache_path, 'trades.csv')
        self.path_accounts = os.path.join(cache_path, 'accounts.json')
        self.path_strategies = os.path.join(cache_path, 'strategies.json')

        # 线程锁
        self._held_lock = threading.Lock()
        self._price_lock = threading.Lock()
        self._trade_lock = threading.Lock()
        self._account_lock = threading.Lock()
        self._strategy_lock = threading.Lock()

        # 初始化必要的文件
        self._init_files()

    def _init_files(self):
        """初始化必要的 JSON 文件"""
        for path in [self.path_held, self.path_max_prices, self.path_min_prices,
                     self.path_accounts, self.path_strategies]:
            if not os.path.exists(path):
                utils_cache.save_json(path, {})

    # ==================== 持仓状态 (Position State) ====================

    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        """
        查询持仓天数

        Performance: 文件存储目标 <2ms (规范要求 <1ms,文件 IO 放宽到 2ms)
        """
        held_days_data = utils_cache.load_json(self.path_held)
        # 文件存储暂不支持多账户,使用全局持仓数据
        return held_days_data.get(code)

    def update_held_days(self, code: str, account_id: str, days: int) -> bool:
        """更新持仓天数"""
        try:
            with self._held_lock:
                held_days_data = utils_cache.load_json(self.path_held)
                held_days_data[code] = days
                utils_cache.save_json(self.path_held, held_days_data)
            return True
        except Exception as e:
            print(f'[FileStore] update_held_days failed: {e}')
            return False

    def delete_held_days(self, code: str, account_id: str) -> bool:
        """删除持仓记录"""
        try:
            utils_cache.del_key(self._held_lock, self.path_held, code)
            return True
        except Exception as e:
            print(f'[FileStore] delete_held_days failed: {e}')
            return False

    def batch_new_held(self, account_id: str, codes: List[str]) -> bool:
        """批量新增持仓,初始天数为 0"""
        try:
            utils_cache.new_held(self._held_lock, self.path_held, codes)
            return True
        except Exception as e:
            print(f'[FileStore] batch_new_held failed: {e}')
            return False

    def all_held_inc(self, account_id: str) -> bool:
        """
        所有持仓天数 +1 (原子操作)

        使用 _inc_date 标记位确保同一天只执行一次
        Performance: 文件存储目标 <20ms (规范要求 <10ms,文件 IO 放宽到 20ms)

        Returns:
            True: 执行了递增操作
            False: 今日已执行过,跳过
        """
        return utils_cache.all_held_inc(self._held_lock, self.path_held)

    def get_max_price(self, code: str, account_id: str) -> Optional[float]:
        """查询持仓期间最高价"""
        max_prices = utils_cache.load_json(self.path_max_prices)
        return max_prices.get(code)

    def update_max_price(self, code: str, account_id: str, price: float) -> bool:
        """更新最高价"""
        try:
            with self._price_lock:
                max_prices = utils_cache.load_json(self.path_max_prices)
                max_prices[code] = round(price, 3)
                utils_cache.save_json(self.path_max_prices, max_prices)
            return True
        except Exception as e:
            print(f'[FileStore] update_max_price failed: {e}')
            return False

    def get_min_price(self, code: str, account_id: str) -> Optional[float]:
        """查询持仓期间最低价"""
        min_prices = utils_cache.load_json(self.path_min_prices)
        return min_prices.get(code)

    def update_min_price(self, code: str, account_id: str, price: float) -> bool:
        """更新最低价"""
        try:
            with self._price_lock:
                min_prices = utils_cache.load_json(self.path_min_prices)
                min_prices[code] = round(price, 3)
                utils_cache.save_json(self.path_min_prices, min_prices)
            return True
        except Exception as e:
            print(f'[FileStore] update_min_price failed: {e}')
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
        """
        记录交易

        Performance: 文件存储目标 <5ms (追加写入,规范要求 <3ms,文件 IO 放宽到 5ms)
        """
        try:
            utils_cache.record_deal(
                self._trade_lock,
                self.path_trades,
                timestamp,
                stock_code,
                stock_name,
                order_type,
                remark,
                price,
                volume
            )
            return True
        except Exception as e:
            print(f'[FileStore] record_trade failed: {e}')
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

        Returns:
            DataFrame with columns: [日期, 时间, 代码, 名称, 类型, 注释, 成交价, 成交量]
        """
        try:
            if not os.path.exists(self.path_trades):
                return pd.DataFrame(columns=['日期', '时间', '代码', '名称', '类型', '注释', '成交价', '成交量'])

            # 尝试多种编码读取 CSV (utils_cache.record_deal 使用系统默认编码)
            df = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
                try:
                    df = pd.read_csv(self.path_trades, encoding=encoding)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if df is None:
                print(f'[FileStore] Failed to decode CSV with any encoding')
                return pd.DataFrame()

            # 过滤条件
            if start_date:
                df = df[df['日期'] >= start_date]
            if end_date:
                df = df[df['日期'] <= end_date]
            if stock_code:
                df = df[df['代码'] == stock_code]

            return df
        except Exception as e:
            print(f'[FileStore] query_trades failed: {e}')
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

        Args:
            group_by: 'stock' (按股票), 'date' (按日期), 'type' (按交易类型)

        Returns:
            DataFrame with aggregated results
        """
        try:
            df = self.query_trades(account_id, start_date, end_date)

            if df.empty:
                return pd.DataFrame()

            # 计算成交金额
            df['成交金额'] = df['成交价'] * df['成交量']

            # 聚合逻辑
            if group_by == 'stock':
                result = df.groupby('代码').agg({
                    '名称': 'first',
                    '成交量': 'sum',
                    '成交金额': 'sum',
                    '成交价': 'mean'
                }).reset_index()
            elif group_by == 'date':
                result = df.groupby('日期').agg({
                    '成交量': 'sum',
                    '成交金额': 'sum'
                }).reset_index()
            elif group_by == 'type':
                result = df.groupby('类型').agg({
                    '成交量': 'sum',
                    '成交金额': 'sum'
                }).reset_index()
            else:
                result = df

            return result
        except Exception as e:
            print(f'[FileStore] aggregate_trades failed: {e}')
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
        查询 K线数据

        注意: 文件存储不支持 K线持久化,返回空 DataFrame
        需要调用方从实时数据源获取 (如 akshare, mootdx)
        """
        print(f'[FileStore] K线数据不支持文件存储,请使用实时数据源')
        return pd.DataFrame()

    def batch_get_kline(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> Dict[str, pd.DataFrame]:
        """
        批量查询 K线数据

        注意: 文件存储不支持 K线持久化,返回空字典
        """
        print(f'[FileStore] K线数据不支持文件存储,请使用实时数据源')
        return {}

    # ==================== 账户管理 (Account Management) ====================

    def create_account(
        self,
        account_id: str,
        account_name: str,
        broker: str,
        initial_capital: float
    ) -> bool:
        """创建账户"""
        try:
            with self._account_lock:
                accounts = utils_cache.load_json(self.path_accounts)

                if account_id in accounts:
                    print(f'[FileStore] Account {account_id} already exists')
                    return False

                accounts[account_id] = {
                    'account_name': account_name,
                    'broker': broker,
                    'initial_capital': initial_capital,
                    'current_capital': initial_capital,
                    'status': 'active',
                    'created_at': datetime.datetime.now().isoformat()
                }

                utils_cache.save_json(self.path_accounts, accounts)
            return True
        except Exception as e:
            print(f'[FileStore] create_account failed: {e}')
            return False

    def get_account(self, account_id: str) -> Optional[Dict]:
        """查询账户信息"""
        accounts = utils_cache.load_json(self.path_accounts)
        return accounts.get(account_id)

    def update_account_capital(self, account_id: str, current_capital: float) -> bool:
        """更新账户资金"""
        try:
            with self._account_lock:
                accounts = utils_cache.load_json(self.path_accounts)

                if account_id not in accounts:
                    print(f'[FileStore] Account {account_id} not found')
                    return False

                accounts[account_id]['current_capital'] = current_capital
                accounts[account_id]['updated_at'] = datetime.datetime.now().isoformat()

                utils_cache.save_json(self.path_accounts, accounts)
            return True
        except Exception as e:
            print(f'[FileStore] update_account_capital failed: {e}')
            return False

    # ==================== 策略管理 (Strategy Management) ====================

    def create_strategy(
        self,
        strategy_name: str,
        strategy_code: str,
        strategy_type: str,
        version: str
    ) -> bool:
        """创建策略"""
        try:
            with self._strategy_lock:
                strategies = utils_cache.load_json(self.path_strategies)

                if strategy_code in strategies:
                    print(f'[FileStore] Strategy {strategy_code} already exists')
                    return False

                strategies[strategy_code] = {
                    'strategy_name': strategy_name,
                    'strategy_type': strategy_type,
                    'version': version,
                    'status': 'active',
                    'params': {},
                    'created_at': datetime.datetime.now().isoformat()
                }

                utils_cache.save_json(self.path_strategies, strategies)
            return True
        except Exception as e:
            print(f'[FileStore] create_strategy failed: {e}')
            return False

    def get_strategy_params(self, strategy_code: str) -> Optional[Dict]:
        """查询策略参数"""
        strategies = utils_cache.load_json(self.path_strategies)
        if strategy_code in strategies:
            return strategies[strategy_code].get('params', {})
        return None

    def save_strategy_params(self, strategy_code: str, params: Dict) -> bool:
        """保存策略参数"""
        try:
            with self._strategy_lock:
                strategies = utils_cache.load_json(self.path_strategies)

                if strategy_code not in strategies:
                    print(f'[FileStore] Strategy {strategy_code} not found')
                    return False

                strategies[strategy_code]['params'] = params
                strategies[strategy_code]['updated_at'] = datetime.datetime.now().isoformat()

                utils_cache.save_json(self.path_strategies, strategies)
            return True
        except Exception as e:
            print(f'[FileStore] save_strategy_params failed: {e}')
            return False

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

    # ==================== 连接管理 (Connection Management) ====================

    def health_check(self) -> bool:
        """
        健康检查

        文件存储检查缓存目录是否可写
        """
        try:
            test_file = os.path.join(self.cache_path, '.health_check')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
            return True
        except Exception as e:
            print(f'[FileStore] health_check failed: {e}')
            return False

    def close(self) -> None:
        """
        关闭连接

        文件存储无需显式关闭,此方法为接口兼容
        """
        pass
