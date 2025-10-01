#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库健康检查脚本
检查 Redis, MySQL, ClickHouse 服务状态
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import redis
import pymysql
from clickhouse_driver import Client
from storage.config import REDIS_CONFIG, MYSQL_CONFIG, CLICKHOUSE_CONFIG


def check_redis():
    """检查 Redis 连接"""
    try:
        r = redis.Redis(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            db=REDIS_CONFIG['db'],
            socket_connect_timeout=3
        )
        response = r.ping()
        if response:
            return True, "✓ Redis 连接正常"
        else:
            return False, "✗ Redis PING 失败"
    except redis.ConnectionError as e:
        return False, f"✗ Redis 连接失败: {e}"
    except Exception as e:
        return False, f"✗ Redis 检查异常: {e}"


def check_mysql():
    """检查 MySQL 连接"""
    try:
        connection = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            connect_timeout=3
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result and result[0] == 1:
                connection.close()
                return True, "✓ MySQL 连接正常"
            else:
                connection.close()
                return False, "✗ MySQL 查询失败"
    except pymysql.err.OperationalError as e:
        return False, f"✗ MySQL 连接失败: {e}"
    except Exception as e:
        return False, f"✗ MySQL 检查异常: {e}"


def check_clickhouse():
    """检查 ClickHouse 连接"""
    try:
        client = Client(
            host=CLICKHOUSE_CONFIG['host'],
            port=CLICKHOUSE_CONFIG['port'],
            database=CLICKHOUSE_CONFIG['database'],
            user=CLICKHOUSE_CONFIG.get('user', 'default'),
            password=CLICKHOUSE_CONFIG.get('password', ''),
            connect_timeout=3,
            send_receive_timeout=3
        )
        result = client.execute("SELECT 1")
        if result and result[0][0] == 1:
            return True, "✓ ClickHouse 连接正常"
        else:
            return False, "✗ ClickHouse 查询失败"
    except Exception as e:
        return False, f"✗ ClickHouse 连接失败: {e}"


def main():
    """主函数"""
    print("=" * 60)
    print("数据库健康检查")
    print("=" * 60)

    services = [
        ("Redis", check_redis),
        ("MySQL", check_mysql),
        ("ClickHouse", check_clickhouse),
    ]

    results = []
    all_ok = True
    some_degraded = False

    for service_name, check_func in services:
        print(f"\n检查 {service_name}...")
        ok, message = check_func()
        results.append((service_name, ok, message))
        print(f"  {message}")

        if not ok:
            all_ok = False
            some_degraded = True

    # 输出汇总
    print("\n" + "=" * 60)
    print("健康检查结果汇总:")
    print("=" * 60)

    for service_name, ok, message in results:
        status_symbol = "✓" if ok else "✗"
        status_text = "正常" if ok else "异常"
        print(f"  {status_symbol} {service_name:12s}: {status_text}")

    print("=" * 60)

    # 返回退出码
    if all_ok:
        print("\n✓ 所有服务正常 (exit code: 0)")
        return 0
    elif some_degraded:
        print("\n⚠ 部分服务异常 (exit code: 1)")
        return 1
    else:
        print("\n✗ 所有服务异常 (exit code: 2)")
        return 2


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
