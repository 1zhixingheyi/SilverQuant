#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据存储模块日志配置

功能:
- 日志轮转: 单文件最大10MB, 保留5个备份
- 日志级别: INFO用于慢查询, WARNING用于降级事件, ERROR用于数据不一致
- 性能监控: 记录查询耗时
"""

import logging
import time
from logging.handlers import RotatingFileHandler
from functools import wraps
from typing import Callable, Any
import os


# 日志配置常量
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 5
SLOW_QUERY_THRESHOLD_MS = 100  # 慢查询阈值: 100ms


def setup_storage_logger(
    name: str = 'storage',
    log_dir: str = './_cache',
    level: int = logging.INFO
) -> logging.Logger:
    """
    配置存储模块日志记录器

    Args:
        name: Logger名称
        log_dir: 日志文件目录
        level: 日志级别

    Returns:
        配置好的Logger实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 文件Handler - 使用轮转
    log_file = os.path.join(log_dir, f'{name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_FILE_MAX_BYTES,
        backupCount=LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(level)

    # 控制台Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # 控制台只显示WARNING及以上

    # 日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_performance(operation_name: str, logger: logging.Logger = None):
    """
    性能监控装饰器

    记录操作耗时,超过阈值时记录慢查询日志

    Args:
        operation_name: 操作名称 (如 "get_held_days", "query_trades")
        logger: Logger实例,默认使用storage logger

    Usage:
        @log_performance("get_held_days")
        def get_held_days(self, code, account_id):
            ...
    """
    if logger is None:
        logger = logging.getLogger('storage')

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000

                # 慢查询日志
                if elapsed_ms > SLOW_QUERY_THRESHOLD_MS:
                    logger.info(
                        f'[SLOW_QUERY] {operation_name} took {elapsed_ms:.2f}ms '
                        f'(threshold: {SLOW_QUERY_THRESHOLD_MS}ms)'
                    )

                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(
                    f'[ERROR] {operation_name} failed after {elapsed_ms:.2f}ms: {e}'
                )
                raise
        return wrapper
    return decorator


def log_degradation(backend: str, operation: str, logger: logging.Logger = None):
    """
    降级事件日志装饰器

    记录数据库降级到文件存储的事件

    Args:
        backend: 后端名称 ("Redis", "MySQL", "ClickHouse")
        operation: 操作名称
        logger: Logger实例

    Usage:
        @log_degradation("Redis", "get_held_days")
        def _redis_get_held_days(self, code, account_id):
            ...
    """
    if logger is None:
        logger = logging.getLogger('storage')

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f'[DEGRADATION] {backend} {operation} failed: {e}. '
                    f'Falling back to File storage.'
                )
                raise
        return wrapper
    return decorator


def log_data_inconsistency(
    operation: str,
    expected: Any,
    actual: Any,
    logger: logging.Logger = None
):
    """
    记录数据一致性错误

    Args:
        operation: 操作名称
        expected: 期望值
        actual: 实际值
        logger: Logger实例
    """
    if logger is None:
        logger = logging.getLogger('storage')

    logger.error(
        f'[DATA_INCONSISTENCY] {operation}: '
        f'expected={expected}, actual={actual}'
    )


# 创建默认logger
storage_logger = setup_storage_logger()
