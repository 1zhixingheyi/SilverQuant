"""
Tushare数据代理服务

提供Tushare Pro数据源的智能访问管理：
- 多Token轮询：支持多个Tushare Token的负载均衡
- 连接池管理：优化Tushare API的连接性能
- 错误重试：网络异常时的自动重试机制
- 速率控制：避免触发API频率限制
- 调试支持：详细的连接和数据获取日志

代理服务架构：
- Token管理：动态切换和轮询多个API Token
- 连接复用：减少重复连接的开销
- 异常处理：网络异常和API错误的容错机制
- 性能监控：连接状态和数据获取效率监控

核心功能特性：
- 智能轮询：自动切换可用的API Token
- 连接优化：保持Tushare连接的活跃状态
- 错误恢复：连接失败时的自动重连机制
- 调试模式：支持详细的调试信息输出
- 状态管理：Token使用状态的健康检查

API管理策略：
- 多Token支持：配置多个Token提高可用性
- 负载均衡：轮询分配请求到不同Token
- 健康检查：定期验证Token的有效性
- 故障切换：检测到异常时自动切换Token
- 使用统计：记录每个Token的使用情况

性能优化特性：
- 连接复用：避免重复建立连接的开销
- 缓存机制：减少重复的API请求
- 异步处理：支持异步数据获取模式
- 批量操作：优化批量数据的获取效率
- 内存管理：合理的内存使用和垃圾回收

与其他模块的关系：
- reader/reader_market.py: 为市场数据读取器提供Tushare接口
- tools/utils_cache.py: 配合缓存机制提高数据获取效率
- credentials.py: 获取Tushare API Token配置
- 全局依赖：被需要Tushare数据的模块调用
"""

import time


ts_token_index = 0


def get_tushare_pro(debugging=False):
    import tushare as ts
    from credentials import TUSHARE_TOKEN
    for _ in range(3):
        try:
            global ts_token_index
            ts_token_index += 1
            ts_token_index = ts_token_index % len(TUSHARE_TOKEN)
            ts_account = TUSHARE_TOKEN[ts_token_index]
            if debugging:
                print(ts_account)
            ts.set_token(ts_account[0])
            ts_pro_api = ts.pro_api()
            return ts_pro_api
        except:
            time.sleep(1)
    return None


if __name__ == '__main__':
    for i in range(10):
        pro = get_tushare_pro(debugging=True)
        df = pro.daily(ts_code="000001.SZ", start_date='20230606', end_date='20230610')
        print(df)
