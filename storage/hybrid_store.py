#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HybridStore: 混合存储实现

多后端混合存储,支持双写模式和自动降级
特性:
- 持仓状态: Redis (主) + File (备)
- 账户/策略: MySQL (主) + File (备)
- 交易/K线: ClickHouse (主) + File (备)
- 自动降级: 数据库异常时自动切换到文件存储
- 双写模式: 同时写入数据库和文件,确保数据一致性
"""

import logging
from typing import Optional, Dict, List, Tuple
import pandas as pd

from storage.base_store import BaseDataStore
from storage.file_store import FileStore
from storage.redis_store import RedisStore
from storage.mysql_store import MySQLStore
from storage.clickhouse_store import ClickHouseStore


# 配置日志
logger = logging.getLogger(__name__)


class HybridStore(BaseDataStore):
    """
    混合存储实现

    架构设计:
    - HOT层 (Redis + File): 持仓状态
    - WARM层 (MySQL + File): 账户/策略
    - COOL层 (ClickHouse + File): 交易/K线

    降级策略:
    - 读操作: 优先数据库,失败则降级到文件
    - 写操作: 双写数据库和文件,数据库失败不影响文件写入
    - 日志记录: 降级事件记录在 WARNING 级别
    """

    def __init__(
        self,
        cache_path: str = None,
        enable_redis: bool = True,
        enable_mysql: bool = True,
        enable_clickhouse: bool = True,
        enable_dual_write: bool = True,
        enable_auto_fallback: bool = True
    ):
        """
        初始化混合存储

        Args:
            cache_path: 文件存储路径
            enable_redis: 是否启用Redis
            enable_mysql: 是否启用MySQL
            enable_clickhouse: 是否启用ClickHouse
            enable_dual_write: 是否启用双写模式
            enable_auto_fallback: 是否启用自动降级
        """
        self.enable_dual_write = enable_dual_write
        self.enable_auto_fallback = enable_auto_fallback

        # 初始化 FileStore (必需,作为备份)
        self.file_store = FileStore(cache_path) if cache_path else FileStore()

        # 初始化数据库存储 (可选)
        self.redis_store = None
        self.mysql_store = None
        self.clickhouse_store = None

        if enable_redis:
            try:
                self.redis_store = RedisStore()
                if not self.redis_store.health_check():
                    logger.warning('[HybridStore] Redis health check failed, will use File only')
                    self.redis_store = None
            except Exception as e:
                logger.warning(f'[HybridStore] Failed to initialize Redis: {e}')
                self.redis_store = None

        if enable_mysql:
            try:
                self.mysql_store = MySQLStore()
                if not self.mysql_store.health_check():
                    logger.warning('[HybridStore] MySQL health check failed, will use File only')
                    self.mysql_store = None
            except Exception as e:
                logger.warning(f'[HybridStore] Failed to initialize MySQL: {e}')
                self.mysql_store = None

        if enable_clickhouse:
            try:
                self.clickhouse_store = ClickHouseStore()
                if not self.clickhouse_store.health_check():
                    logger.warning('[HybridStore] ClickHouse health check failed, will use File only')
                    self.clickhouse_store = None
            except Exception as e:
                logger.warning(f'[HybridStore] Failed to initialize ClickHouse: {e}')
                self.clickhouse_store = None

    # ==================== 持仓状态 (Position State) - Redis + File ====================

    def get_held_days(self, code: str, account_id: str) -> Optional[int]:
        """
        查询持仓天数

        策略: 优先 Redis,失败则降级到 File
        """
        # 尝试 Redis
        if self.redis_store:
            try:
                result = self.redis_store.get_held_days(code, account_id)
                return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] Redis get_held_days failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.get_held_days(code, account_id)

    def update_held_days(self, code: str, account_id: str, days: int) -> bool:
        """
        更新持仓天数

        策略: 双写 Redis + File
        """
        success_redis = False
        success_file = False

        # 写入 Redis
        if self.redis_store:
            try:
                success_redis = self.redis_store.update_held_days(code, account_id, days)
            except Exception as e:
                logger.error(f'[HybridStore] Redis update_held_days failed: {e}')

        # 写入 File (双写模式或Redis失败)
        if self.enable_dual_write or not success_redis:
            try:
                success_file = self.file_store.update_held_days(code, account_id, days)
            except Exception as e:
                logger.error(f'[HybridStore] File update_held_days failed: {e}')

        # 至少一个成功即可
        return success_redis or success_file

    def delete_held_days(self, code: str, account_id: str) -> bool:
        """
        删除持仓记录

        策略: 双写 Redis + File
        """
        success_redis = False
        success_file = False

        # 删除 Redis
        if self.redis_store:
            try:
                success_redis = self.redis_store.delete_held_days(code, account_id)
            except Exception as e:
                logger.error(f'[HybridStore] Redis delete_held_days failed: {e}')

        # 删除 File
        if self.enable_dual_write or not success_redis:
            try:
                success_file = self.file_store.delete_held_days(code, account_id)
            except Exception as e:
                logger.error(f'[HybridStore] File delete_held_days failed: {e}')

        return success_redis or success_file

    def batch_new_held(self, account_id: str, codes: List[str]) -> bool:
        """
        批量新增持仓

        策略: 双写 Redis + File
        """
        success_redis = False
        success_file = False

        # 写入 Redis
        if self.redis_store:
            try:
                success_redis = self.redis_store.batch_new_held(account_id, codes)
            except Exception as e:
                logger.error(f'[HybridStore] Redis batch_new_held failed: {e}')

        # 写入 File
        if self.enable_dual_write or not success_redis:
            try:
                success_file = self.file_store.batch_new_held(account_id, codes)
            except Exception as e:
                logger.error(f'[HybridStore] File batch_new_held failed: {e}')

        return success_redis or success_file

    def all_held_inc(self, account_id: str) -> bool:
        """
        所有持仓天数 +1

        策略: 优先 Redis Lua脚本,失败则降级到 File
        """
        # 尝试 Redis
        if self.redis_store:
            try:
                result = self.redis_store.all_held_inc(account_id)
                # 如果启用双写,同时更新File
                if self.enable_dual_write and result:
                    try:
                        self.file_store.all_held_inc(account_id)
                    except Exception as e:
                        logger.error(f'[HybridStore] File all_held_inc failed in dual-write: {e}')
                return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] Redis all_held_inc failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.all_held_inc(account_id)

    def get_max_price(self, code: str, account_id: str) -> Optional[float]:
        """
        查询持仓期间最高价

        策略: 优先 Redis,失败则降级到 File
        """
        # 尝试 Redis
        if self.redis_store:
            try:
                result = self.redis_store.get_max_price(code, account_id)
                return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] Redis get_max_price failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.get_max_price(code, account_id)

    def update_max_price(self, code: str, account_id: str, price: float) -> bool:
        """
        更新最高价

        策略: 双写 Redis + File
        """
        success_redis = False
        success_file = False

        # 写入 Redis
        if self.redis_store:
            try:
                success_redis = self.redis_store.update_max_price(code, account_id, price)
            except Exception as e:
                logger.error(f'[HybridStore] Redis update_max_price failed: {e}')

        # 写入 File
        if self.enable_dual_write or not success_redis:
            try:
                success_file = self.file_store.update_max_price(code, account_id, price)
            except Exception as e:
                logger.error(f'[HybridStore] File update_max_price failed: {e}')

        return success_redis or success_file

    def get_min_price(self, code: str, account_id: str) -> Optional[float]:
        """
        查询持仓期间最低价

        策略: 优先 Redis,失败则降级到 File
        """
        # 尝试 Redis
        if self.redis_store:
            try:
                result = self.redis_store.get_min_price(code, account_id)
                return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] Redis get_min_price failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.get_min_price(code, account_id)

    def update_min_price(self, code: str, account_id: str, price: float) -> bool:
        """
        更新最低价

        策略: 双写 Redis + File
        """
        success_redis = False
        success_file = False

        # 写入 Redis
        if self.redis_store:
            try:
                success_redis = self.redis_store.update_min_price(code, account_id, price)
            except Exception as e:
                logger.error(f'[HybridStore] Redis update_min_price failed: {e}')

        # 写入 File
        if self.enable_dual_write or not success_redis:
            try:
                success_file = self.file_store.update_min_price(code, account_id, price)
            except Exception as e:
                logger.error(f'[HybridStore] File update_min_price failed: {e}')

        return success_redis or success_file

    # ==================== 交易记录 (Trade Records) - ClickHouse + File ====================

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

        策略: 双写 ClickHouse + File
        """
        success_clickhouse = False
        success_file = False

        # 写入 ClickHouse
        if self.clickhouse_store:
            try:
                success_clickhouse = self.clickhouse_store.record_trade(
                    account_id, timestamp, stock_code, stock_name,
                    order_type, remark, price, volume, strategy_name
                )
            except Exception as e:
                logger.error(f'[HybridStore] ClickHouse record_trade failed: {e}')

        # 写入 File
        if self.enable_dual_write or not success_clickhouse:
            try:
                success_file = self.file_store.record_trade(
                    account_id, timestamp, stock_code, stock_name,
                    order_type, remark, price, volume, strategy_name
                )
            except Exception as e:
                logger.error(f'[HybridStore] File record_trade failed: {e}')

        return success_clickhouse or success_file

    def query_trades(
        self,
        account_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        查询交易记录

        策略: 优先 ClickHouse,失败则降级到 File
        """
        # 尝试 ClickHouse
        if self.clickhouse_store:
            try:
                result = self.clickhouse_store.query_trades(
                    account_id, start_date, end_date, stock_code
                )
                if not result.empty:
                    return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] ClickHouse query_trades failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.query_trades(account_id, start_date, end_date, stock_code)

    def aggregate_trades(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        group_by: str = 'stock'
    ) -> pd.DataFrame:
        """
        聚合交易统计

        策略: 优先 ClickHouse,失败则降级到 File
        """
        # 尝试 ClickHouse
        if self.clickhouse_store:
            try:
                result = self.clickhouse_store.aggregate_trades(
                    account_id, start_date, end_date, group_by
                )
                if not result.empty:
                    return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] ClickHouse aggregate_trades failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.aggregate_trades(account_id, start_date, end_date, group_by)

    # ==================== K线数据 (Kline Data) - ClickHouse + File ====================

    def get_kline(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> pd.DataFrame:
        """
        查询K线数据

        策略: 优先 ClickHouse,失败则降级到 File
        """
        # 尝试 ClickHouse
        if self.clickhouse_store:
            try:
                result = self.clickhouse_store.get_kline(
                    stock_code, start_date, end_date, frequency
                )
                if not result.empty:
                    return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] ClickHouse get_kline failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.get_kline(stock_code, start_date, end_date, frequency)

    def batch_get_kline(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        frequency: str = 'daily'
    ) -> Dict[str, pd.DataFrame]:
        """
        批量查询K线数据

        策略: 优先 ClickHouse,失败则降级到 File
        """
        # 尝试 ClickHouse
        if self.clickhouse_store:
            try:
                result = self.clickhouse_store.batch_get_kline(
                    stock_codes, start_date, end_date, frequency
                )
                if result:
                    return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] ClickHouse batch_get_kline failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.batch_get_kline(stock_codes, start_date, end_date, frequency)

    # ==================== 账户管理 (Account Management) - MySQL + File ====================

    def create_account(
        self,
        account_id: str,
        account_name: str,
        broker: str,
        initial_capital: float
    ) -> bool:
        """
        创建账户

        策略: 优先 MySQL,失败则降级到 File
        """
        # 尝试 MySQL
        if self.mysql_store:
            try:
                success = self.mysql_store.create_account(
                    account_id, account_name, broker, initial_capital
                )
                if success:
                    # 双写到 File
                    if self.enable_dual_write:
                        try:
                            self.file_store.create_account(
                                account_id, account_name, broker, initial_capital
                            )
                        except Exception as e:
                            logger.error(f'[HybridStore] File create_account failed in dual-write: {e}')
                    return True
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] MySQL create_account failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.create_account(account_id, account_name, broker, initial_capital)

    def get_account(self, account_id: str) -> Optional[Dict]:
        """
        查询账户信息

        策略: 优先 MySQL,失败则降级到 File
        """
        # 尝试 MySQL
        if self.mysql_store:
            try:
                result = self.mysql_store.get_account(account_id)
                if result:
                    return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] MySQL get_account failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.get_account(account_id)

    def update_account_capital(self, account_id: str, current_capital: float) -> bool:
        """
        更新账户资金

        策略: 双写 MySQL + File
        """
        success_mysql = False
        success_file = False

        # 写入 MySQL
        if self.mysql_store:
            try:
                success_mysql = self.mysql_store.update_account_capital(account_id, current_capital)
            except Exception as e:
                logger.error(f'[HybridStore] MySQL update_account_capital failed: {e}')

        # 写入 File
        if self.enable_dual_write or not success_mysql:
            try:
                success_file = self.file_store.update_account_capital(account_id, current_capital)
            except Exception as e:
                logger.error(f'[HybridStore] File update_account_capital failed: {e}')

        return success_mysql or success_file

    # ==================== 策略管理 (Strategy Management) - MySQL + File ====================

    def create_strategy(
        self,
        strategy_name: str,
        strategy_code: str,
        strategy_type: str,
        version: str
    ) -> bool:
        """
        创建策略

        策略: 优先 MySQL,失败则降级到 File
        """
        # 尝试 MySQL
        if self.mysql_store:
            try:
                success = self.mysql_store.create_strategy(
                    strategy_name, strategy_code, strategy_type, version
                )
                if success:
                    # 双写到 File
                    if self.enable_dual_write:
                        try:
                            self.file_store.create_strategy(
                                strategy_name, strategy_code, strategy_type, version
                            )
                        except Exception as e:
                            logger.error(f'[HybridStore] File create_strategy failed in dual-write: {e}')
                    return True
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] MySQL create_strategy failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.create_strategy(strategy_name, strategy_code, strategy_type, version)

    def get_strategy_params(self, strategy_code: str) -> Optional[Dict]:
        """
        查询策略参数

        策略: 优先 MySQL,失败则降级到 File
        """
        # 尝试 MySQL
        if self.mysql_store:
            try:
                result = self.mysql_store.get_strategy_params(strategy_code)
                if result:
                    return result
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] MySQL get_strategy_params failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.get_strategy_params(strategy_code)

    def save_strategy_params(self, strategy_code: str, params: Dict) -> bool:
        """
        保存策略参数

        策略: 双写 MySQL + File
        """
        success_mysql = False
        success_file = False

        # 写入 MySQL
        if self.mysql_store:
            try:
                success_mysql = self.mysql_store.save_strategy_params(strategy_code, params)
            except Exception as e:
                logger.error(f'[HybridStore] MySQL save_strategy_params failed: {e}')

        # 写入 File
        if self.enable_dual_write or not success_mysql:
            try:
                success_file = self.file_store.save_strategy_params(strategy_code, params)
            except Exception as e:
                logger.error(f'[HybridStore] File save_strategy_params failed: {e}')

        return success_mysql or success_file

    def compare_strategy_params(
        self,
        strategy_code: str,
        new_params: Dict
    ) -> Tuple[Dict, Dict, Dict]:
        """
        比较策略参数差异

        策略: 优先 MySQL,失败则降级到 File
        """
        # 尝试 MySQL
        if self.mysql_store:
            try:
                return self.mysql_store.compare_strategy_params(strategy_code, new_params)
            except Exception as e:
                if self.enable_auto_fallback:
                    logger.warning(f'[HybridStore] MySQL compare_strategy_params failed, fallback to File: {e}')
                else:
                    raise

        # 降级到 File
        return self.file_store.compare_strategy_params(strategy_code, new_params)

    # ==================== 连接管理 (Connection Management) ====================

    def health_check(self) -> bool:
        """
        健康检查

        聚合所有后端的健康状态
        """
        health_status = {
            'file': False,
            'redis': False,
            'mysql': False,
            'clickhouse': False
        }

        # 检查 File
        try:
            health_status['file'] = self.file_store.health_check()
        except Exception as e:
            logger.error(f'[HybridStore] File health check failed: {e}')

        # 检查 Redis
        if self.redis_store:
            try:
                health_status['redis'] = self.redis_store.health_check()
            except Exception as e:
                logger.error(f'[HybridStore] Redis health check failed: {e}')

        # 检查 MySQL
        if self.mysql_store:
            try:
                health_status['mysql'] = self.mysql_store.health_check()
            except Exception as e:
                logger.error(f'[HybridStore] MySQL health check failed: {e}')

        # 检查 ClickHouse
        if self.clickhouse_store:
            try:
                health_status['clickhouse'] = self.clickhouse_store.health_check()
            except Exception as e:
                logger.error(f'[HybridStore] ClickHouse health check failed: {e}')

        # 只要 File 可用即可 (最基本的降级保证)
        return health_status['file']

    def close(self) -> None:
        """关闭所有后端连接"""
        try:
            self.file_store.close()
        except Exception as e:
            logger.error(f'[HybridStore] File close failed: {e}')

        if self.redis_store:
            try:
                self.redis_store.close()
            except Exception as e:
                logger.error(f'[HybridStore] Redis close failed: {e}')

        if self.mysql_store:
            try:
                self.mysql_store.close()
            except Exception as e:
                logger.error(f'[HybridStore] MySQL close failed: {e}')

        if self.clickhouse_store:
            try:
                self.clickhouse_store.close()
            except Exception as e:
                logger.error(f'[HybridStore] ClickHouse close failed: {e}')
