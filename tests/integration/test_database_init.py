#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T017: Integration Test - Database Initialization

验证数据库初始化流程:
1. 部署数据库容器 (Redis, MySQL, ClickHouse)
2. 执行初始化脚本 (init.sql, init_clickhouse.py)
3. 验证所有表已创建
4. 验证预定义数据已插入 (roles, permissions)
"""

import pytest
import redis
import pymysql
from clickhouse_driver import Client
from storage.config import REDIS_CONFIG, MYSQL_CONFIG, CLICKHOUSE_CONFIG


class TestDatabaseInitialization:
    """数据库初始化集成测试"""

    @pytest.fixture(scope="class")
    def redis_client(self):
        """Redis连接fixture"""
        try:
            client = redis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                password=REDIS_CONFIG.get('password') or None,
                decode_responses=True
            )
            # 测试连接
            client.ping()
            yield client
        except Exception as e:
            pytest.skip(f"Redis 不可用,跳过测试: {e}")

    @pytest.fixture(scope="class")
    def mysql_conn(self):
        """MySQL连接fixture"""
        try:
            conn = pymysql.connect(
                host=MYSQL_CONFIG['host'],
                port=MYSQL_CONFIG['port'],
                user=MYSQL_CONFIG['user'],
                password=MYSQL_CONFIG['password'],
                database=MYSQL_CONFIG['database']
            )
            yield conn
            conn.close()
        except Exception as e:
            pytest.skip(f"MySQL 不可用,跳过测试: {e}")

    @pytest.fixture(scope="class")
    def clickhouse_client(self):
        """ClickHouse连接fixture"""
        try:
            client = Client(
                host=CLICKHOUSE_CONFIG['host'],
                port=CLICKHOUSE_CONFIG['port'],
                user=CLICKHOUSE_CONFIG.get('user', 'default'),
                password=CLICKHOUSE_CONFIG.get('password', ''),
                database=CLICKHOUSE_CONFIG['database']
            )
            # 测试连接
            client.execute('SELECT 1')
            yield client
        except Exception as e:
            pytest.skip(f"ClickHouse 不可用,跳过测试: {e}")

    def test_redis_connection(self, redis_client):
        """测试Redis连接"""
        result = redis_client.ping()
        assert result is True, "Redis PING 应该返回 True"

    def test_mysql_connection(self, mysql_conn):
        """测试MySQL连接"""
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1, "MySQL查询应该返回1"

    def test_clickhouse_connection(self, clickhouse_client):
        """测试ClickHouse连接"""
        result = clickhouse_client.execute("SELECT 1")
        assert result == [(1,)], "ClickHouse查询应该返回[(1,)]"

    def test_mysql_tables_exist(self, mysql_conn):
        """测试MySQL表是否已创建"""
        expected_tables = [
            'account', 'strategy', 'strategy_param', 'account_strategy',
            'user', 'role', 'permission', 'user_role', 'role_permission'
        ]

        with mysql_conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]

        for table in expected_tables:
            assert table in tables, f"表 {table} 应该存在"

    def test_mysql_predefined_roles(self, mysql_conn):
        """测试MySQL预定义角色是否已插入"""
        expected_roles = ['admin', 'developer', 'trader', 'viewer']

        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT role_code FROM role")
            roles = [row[0] for row in cursor.fetchall()]

        for role_code in expected_roles:
            assert role_code in roles, f"角色 {role_code} 应该已插入"

    def test_mysql_predefined_permissions(self, mysql_conn):
        """测试MySQL预定义权限是否已插入"""
        with mysql_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM permission")
            count = cursor.fetchone()[0]

        # init.sql 中定义了8个权限
        assert count >= 8, f"权限数量应该 >= 8,实际为 {count}"

    def test_clickhouse_tables_exist(self, clickhouse_client):
        """测试ClickHouse表是否已创建"""
        expected_tables = ['trade', 'daily_kline']

        # 查询数据库中的表
        result = clickhouse_client.execute(
            f"SHOW TABLES FROM {CLICKHOUSE_CONFIG['database']}"
        )
        tables = [row[0] for row in result]

        for table in expected_tables:
            assert table in tables, f"表 {table} 应该存在"

    def test_clickhouse_trade_table_structure(self, clickhouse_client):
        """测试ClickHouse trade表结构"""
        result = clickhouse_client.execute(
            f"DESCRIBE TABLE {CLICKHOUSE_CONFIG['database']}.trade"
        )

        # 提取列名
        columns = [row[0] for row in result]

        expected_columns = [
            'id', 'timestamp', 'date', 'account_id', 'stock_code',
            'stock_name', 'order_type', 'remark', 'price', 'volume',
            'amount', 'strategy_name'
        ]

        for col in expected_columns:
            assert col in columns, f"列 {col} 应该存在于 trade 表"

    def test_clickhouse_kline_table_structure(self, clickhouse_client):
        """测试ClickHouse daily_kline表结构"""
        result = clickhouse_client.execute(
            f"DESCRIBE TABLE {CLICKHOUSE_CONFIG['database']}.daily_kline"
        )

        columns = [row[0] for row in result]

        expected_columns = [
            'id', 'stock_code', 'date', 'datetime',
            'open', 'high', 'low', 'close', 'volume', 'amount'
        ]

        for col in expected_columns:
            assert col in columns, f"列 {col} 应该存在于 daily_kline 表"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
