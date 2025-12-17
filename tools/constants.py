
"""
SilverQuant系统常量定义

提供量化交易系统的核心常量配置：
- 消息格式分隔符：统一消息推送格式标准
- 数据源配置：多数据源标识和选择
- 复权方式：前复权、后复权、不复权选项
- 逆回购代码：沪深两市逆回购产品代码
- 指数代码：全市场主要指数标识符
- 仓位管理：持仓信息项和时间标识

常量架构设计：
- 枚举类设计：使用类封装相关常量组
- 分类管理：按功能模块分组定义常量
- 标准化命名：统一的命名规范和语义
- 扩展性：预留扩展空间，支持新增常量

消息格式常量：
- 内部分隔符：单空行分隔消息段落
- 外部分隔符：双空行分隔主要消息块
- 格式统一：与钉钉、飞书推送格式兼容

数据源标识：
- AKShare：开源免费数据源
- Tushare：专业付费数据源
- MOOTDX：通达信数据加速
- TDXZIP：通达离线数据包
- MiniQMT：QMT实时数据接口

指数体系覆盖：
- 主要指数：上证、深证、沪深300
- 中证系列：中证100/500/800/1000/2000/全指
- 特色指数：创业板、科创50、北证50
- 国际指数：中证A50、中证A500

与其他模块的关系：
- 全局引用：被系统中所有模块引用
- tools/utils_*.py: 工具模块的配置参数
- reader/*: 数据源选择和配置
- trader/*: 指数成分股选择
- selector/*: 股票池范围定义
"""

MSG_INNER_SEPARATOR = '\n \n'
MSG_OUTER_SEPARATOR = '\n\n '


DEFAULT_DAILY_COLUMNS = ['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']


# 数据源常量
class DataSource:
    AKSHARE = 'akshare'
    TUSHARE = 'tushare'
    MOOTDX = 'mootdx'
    TDXZIP = 'tdxzip'
    MINIQMT = 'miniqmt'
    BAOSTOCK = 'baostock'


# 复权常量
class ExitRight:
    BFQ = ''     # 不复权
    QFQ = 'qfq'  # 前复权
    HFQ = 'hfq'  # 后复权


# 逆回购常量
REPURCHASE_CODES = ['131810.SZ', '131811.SZ', '131800.SZ', '131809.SZ', '131801.SZ', '131802.SZ',
                    '131803.SZ', '131805.SZ', '131806.SZ', '204001.SH', '204002.SH', '204003.SH',
                    '204004.SH', '204007.SH', '204014.SH', '204028.SH', '204091.SH', '204182.SH']


# 指数常量
class IndexSymbol:
    INDEX_SH_ZS = '000001'      # 上证指数
    INDEX_SZ_CZ = '399001'      # 深证指数
    INDEX_SZ_50 = '399850'      # 深证50
    INDEX_SZ_100 = '399330'     # 深证100
    INDEX_HS_300 = '000300'     # 沪深300
    INDEX_ZZ_100 = '000903'     # 中证100
    INDEX_ZZ_500 = '000905'     # 中证500
    INDEX_ZZ_800 = '000906'     # 中证800
    INDEX_ZZ_1000 = '000852'    # 中证1000
    INDEX_ZZ_2000 = '932000'    # 中证2000
    INDEX_ZZ_ALL = '000985'     # 中证全指
    INDEX_CY_ZS = '399006'      # 创业指数
    INDEX_KC_50 = '000688'      # 科创50
    INDEX_BZ_50 = '899050'      # 北证50
    INDEX_ZX_100 = '399005'     # 中小100
    INDEX_ZZ_A50 = '000050'     # 中证A50
    INDEX_ZZ_A500 = '000510'    # 中证A500


# 仓位项常量
class InfoItem:
    IncDate = '_inc_date'   # 执行所有持仓日+1操作的日期flag:'%Y-%m-%d'
    DayCount = 'day_count'  # 持仓时间（单位：天）
