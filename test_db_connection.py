#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试数据库连接脚本"""

import sys

# 测试 MySQL 连接
def test_mysql():
    try:
        import pymysql
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='860721',
            database='silverquant_storage'
        )
        print('✅ MySQL连接成功')
        print(f'当前数据库: {conn.db.decode()}')

        cursor = conn.cursor()
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        print(f'现有表数量: {len(tables)}')
        for t in tables[:10]:
            print(f'  - {t[0]}')

        conn.close()
        return True
    except Exception as e:
        print(f'❌ MySQL连接失败: {e}')
        return False

# 测试 Redis 连接
def test_redis():
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print('✅ Redis连接成功')

        # 测试基本操作
        r.set('test_key', 'test_value')
        val = r.get('test_key')
        print(f'测试读写: {val}')
        r.delete('test_key')
        return True
    except Exception as e:
        print(f'❌ Redis连接失败: {e}')
        return False

# 测试 ClickHouse 连接
def test_clickhouse():
    try:
        from clickhouse_driver import Client
        client = Client(
            host='127.0.0.1',
            port=9000,
            user='default',
            password='860721',
            database='default'
        )
        result = client.execute('SELECT version()')
        print(f'✅ ClickHouse连接成功 (版本: {result[0][0]})')

        # 检查是否有 lianghua_clickhouse 数据库
        dbs = client.execute('SHOW DATABASES')
        db_names = [db[0] for db in dbs]
        if 'lianghua_clickhouse' in db_names:
            print('  - lianghua_clickhouse 数据库存在')
        else:
            print('  - lianghua_clickhouse 数据库不存在，需要创建')

        return True
    except Exception as e:
        print(f'❌ ClickHouse连接失败: {e}')
        return False

if __name__ == '__main__':
    print('='*60)
    print('数据库连接测试')
    print('='*60)

    results = {}

    print('\n[1/3] 测试 MySQL...')
    results['mysql'] = test_mysql()

    print('\n[2/3] 测试 Redis...')
    results['redis'] = test_redis()

    print('\n[3/3] 测试 ClickHouse...')
    results['clickhouse'] = test_clickhouse()

    print('\n' + '='*60)
    print('测试结果汇总:')
    print('='*60)
    for name, status in results.items():
        symbol = '✅' if status else '❌'
        print(f'{symbol} {name.upper()}: {"成功" if status else "失败"}')

    # 返回状态码
    sys.exit(0 if all(results.values()) else 1)
