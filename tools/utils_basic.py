"""
基础工具函数模块

提供量化交易系统的基础工具函数集：
- 调试工具：条件性调试输出和信息打印
- 日志系统：灵活的多文件日志配置和管理
- 代码转换：多平台股票代码格式的相互转换
- 类型判断：股票、ETF、债券等金融产品的类型识别
- 价格计算：涨跌停价格和幅度的精确计算
- 时间处理：交易时间计算和格式转换

工具函数架构：
- 代码标准化：统一的股票代码格式转换接口
- 平台适配：支持新浪、通达信、掘金等平台代码格式
- 精确计算：基于Decimal的金融精度计算
- 时间管理：交易时间的标准化处理和计算

核心功能特性：
- 多格式支持：股票代码在多种格式间的无缝转换
- 类型识别：基于代码前缀的金融产品类型判断
- 涨跌停计算：考虑不同板块涨跌幅限制的精确计算
- 日志管理：支持文件和控制台的多重日志输出
- 时间工具：交易时间百分比和秒数转换工具

代码转换功能：
- 标准格式：6位数字代码与交易所后缀的转换
- 新浪格式：sz/sh前缀的新浪财经代码格式
- 通达信格式：0/1/2前缀的通达信代码格式
- 掘金格式：SZSE/SHSE/BJSE前缀的掘金代码格式

金融产品识别：
- 股票判断：沪深、创业板、科创板、北交所股票识别
- 涨跌幅判断：10cm、20cm、30cm涨跌幅限制识别
- ETF识别：交易所交易基金的代码识别
- 债券识别：可转债的代码识别和分类

价格计算工具：
- 涨跌停幅度：基于板块的涨跌幅限制计算
- 涨跌停价格：基于昨收价的精确涨跌停价计算
- 精度控制：使用Decimal确保金融计算精度
- 四舍五入：标准的金融四舍五入处理

时间处理功能：
- 交易时间：连续竞价交易时间的百分比计算
- 时间转换：多种时间格式间的转换工具
- 秒数计算：交易时间内的秒数累计计算
- K线转换：日线到周线、月线的K线数据转换

与其他模块的关系：
- 全局依赖：被系统中所有模块广泛使用
- 数据转换：为数据读取和交易执行提供代码转换
- 计算支持：为策略执行提供价格和时间计算
- 调试支持：为系统调试提供条件性输出工具
"""

import datetime
import logging
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP


IS_DEBUG = False


def debug(*args, **kwargs):
    if IS_DEBUG:
        print(*args, **kwargs)


# pandas dataframe 显示配置优化
def pd_show_all() -> None:
    pd.set_option('display.width', None)
    pd.set_option('display.min_rows', 9999)
    pd.set_option('display.max_rows', 9999)
    pd.set_option('display.max_columns', 200)
    pd.set_option('display.unicode.ambiguous_as_wide', True)
    pd.set_option('display.unicode.east_asian_width', True)
    pd.set_option('display.float_format', lambda x: f'{x:.3f}')


# logging 模块的初始化配置
def logging_init(path=None, level=logging.DEBUG, file_line=False):
    file_line_fmt = ""
    if file_line:
        file_line_fmt = "%(filename)s[line:%(lineno)d] - %(levelname)s: "
    logging.basicConfig(
        level=level,
        format=file_line_fmt + "%(asctime)s|%(message)s",
        filename=path
    )


# 多文件 logger的配置
def logger_init(path=None, name='default') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 移除已存在的处理器
    for handler in logger.handlers:
        logger.removeHandler(handler)

    if path is None:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
    else:
        handler = logging.FileHandler(path)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s|%(message)s')
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


# 六位数symbol代码转换成带交易所后缀code格式
def symbol_to_code(symbol: str | int) -> str:
    symbol = str(symbol) if type(symbol) == int else symbol

    if symbol[:2] in ['00', '30', '15', '12']:
        return f'{symbol}.SZ'
    elif symbol[:2] in ['60', '68', '51', '52', '53', '56', '58', '11']:
        return f'{symbol}.SH'
    elif symbol[:2] in ['83', '87', '43', '82', '88', '92']:
        return f'{symbol}.BJ'
    else:
        return f'{symbol}.--'


# 带交易所后缀code格式转换成六位数symbol代码
def code_to_symbol(code: str) -> str:
    arr = code.split('.')
    assert len(arr) == 2, 'code不符合格式'
    return arr[0]


# ==========
# 新浪系列代码
# ==========


def code_to_sina_symbol(code: str) -> str:
    [symbol, exchange] = code.split('.')
    if exchange == 'SZ':
        return 'sz' + symbol
    elif exchange == 'SH':
        return 'sh' + symbol
    elif exchange == 'BJ':
        return 'bj' + symbol
    return code         # 这里先不变，不报错


def sina_symbol_to_code(sina_symbol: str) -> str:
    if len(sina_symbol) != 8:
        return sina_symbol    # 这里先不变，不报错
    elif sina_symbol[0:2].lower() == 'sz':
        return sina_symbol[2:8] + '.SZ'
    elif sina_symbol[0:2].lower() == 'sh':
        return sina_symbol[2:8] + '.SH'
    elif sina_symbol[0:2].lower() == 'bj':
        return sina_symbol[2:8] + '.BJ'
    else:
        return sina_symbol    # 这里先不变，不报错


# ==========
# 通达信系列代码
# ==========


def code_to_tdxsymbol(code: str) -> str:
    [symbol, exchange] = code.split('.')
    if exchange == 'SZ':
        return '0' + symbol
    elif exchange == 'SH':
        return '1' + symbol
    elif exchange == 'BJ':
        return '2' + symbol
    return code         # 这里先不变，不报错


def tdxsymbol_to_code(tdxsymbol: str) -> str:
    if len(tdxsymbol) != 7:
        return tdxsymbol    # 这里先不变，不报错
    elif tdxsymbol[0] == '0':
        return tdxsymbol[1:7] + '.SZ'
    elif tdxsymbol[0] == '1':
        return tdxsymbol[1:7] + '.SH'
    elif tdxsymbol[0] == '2':
        return tdxsymbol[1:7] + '.BJ'
    else:
        return tdxsymbol    # 这里先不变，不报错


def symbol_to_tdxsymbol(code: str) -> str:
    """ 转换代码函数 """
    # 深证为0，沪市为1，北交所为2
    code = ''.join(c for c in code if c.isdigit())  # 只取股票代码中数字代码部分
    # A股，股票代码转换，如：1601068，2300250
    if len(code) == 6:
        if code[0] == "6" or code[0] == "9":  # 上证股票
            return "1" + code
        if code[0] == "0" or code[0] == "3" or code[0] == "2":  # 深证股票
            return "0" + code
        if code[0] == "4" or code[0] == "8":  # 北证股票
            return "2" + code
    return code


# ==========
# 掘金系列代码
# ==========


def symbol_to_gmsymbol(symbol: str | int) -> str:
    symbol = str(symbol) if type(symbol) == int else symbol

    if symbol[:2] in ['00', '30', '15', '12']:
        return f'SZSE.{symbol}'
    elif symbol[:2] in ['60', '68', '51', '52', '53', '56', '58', '11']:
        return f'SHSE.{symbol}'
    elif symbol[:2] in ['83', '87', '43', '82', '88', '92']:
        return f'BJSE.{symbol}'
    else:
        return f'--SE.{symbol}'


def gmsymbol_to_symbol(gmsymbol: str) -> str:
    arr = gmsymbol.split('.')
    assert len(arr) == 2, 'code不符合格式'
    return arr[-1]


def code_to_gmsymbol(code: str) -> str:
    return symbol_to_gmsymbol(code_to_symbol(code))


def gmsymbol_to_code(gmsymbol: str) -> str:
    return symbol_to_code(gmsymbol_to_symbol(gmsymbol))


# 判断是不是可交易股票代码 包含 股票 ETF 可转债
def is_symbol(code_or_symbol: str):
    return code_or_symbol[:2] in [
        '00', '30',  # 深交所
        '60', '68',  # 上交所
        '82', '83', '87', '88', '43', '92',  # 北交所
        '15', '51', '52', '53', '56', '58',  # ETF
        '11', '12',  # 可转债
    ]


def is_stock(code_or_symbol: str | int):
    """ 判断是不是股票代码 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] in ['00', '30', '60', '68', '82', '83', '87', '88', '43', '92']


def is_stock_10cm(code_or_symbol: str | int):
    """ 判断是不是10cm票 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] in ['00', '60']


def is_stock_20cm(code_or_symbol: str | int):
    """ 判断是不是20cm票 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] in ['30', '68']


def is_stock_30cm(code_or_symbol: str | int):
    """ 判断是不是20cm票 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] in ['82', '83', '87', '88', '43', '92']


def is_stock_cy(code_or_symbol: str | int):
    """ 判断是不是创业板 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] == '30'


def is_stock_kc(code_or_symbol: str | int):
    """ 判断是不是科创板 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] == '68'


def is_stock_bj(code_or_symbol: str | int):
    """ 判断是不是北交所 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] in ['82', '83', '87', '88', '43', '92']


def is_fund_etf(code_or_symbol: str | int):
    """ 判断是不是etf代码 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] in ['15', '51', '52', '53', '56', '58']


def is_bond(code_or_symbol: str | int):
    """ 判断是不是可转债 """
    code_or_symbol = str(code_or_symbol) if type(code_or_symbol) == int else code_or_symbol
    return code_or_symbol[:2] in ['11', '12']


# 获取symbol的交易所简称
def get_symbol_exchange(symbol: str) -> str:
    if symbol[:2] in ['00', '30', '15', '12']:
        return 'SZ'
    elif symbol[:2] in ['60', '68', '51', '52', '53', '56', '58', '11']:
        return 'SH'
    elif symbol[:2] in ['83', '87', '43', '82', '88', '92']:
        return 'BJ'
    else:
        return ''


# 获取code的交易所简称
def get_code_exchange(code: str) -> str:
    arr = code.split('.')
    assert len(arr) == 2, 'code不符合格式'
    return arr[1][:2]


# 大数字转换成字母码
def map_num_to_chr(num):
    quotient = num // 100
    if quotient < 10:
        return chr(quotient + 48)  # 将数字转换为对应的 ASCII 字符
    elif quotient < 36:
        return chr(quotient - 10 + 97)  # 将数字转换为小写字母
    elif quotient < 62:
        return chr(quotient - 36 + 65)  # 将数字转换为大写字母
    else:
        return '.'


# 获取当前时间在一天连续竞价交易时间的百分位
def get_current_time_percentage(time: str) -> float:
    [hr, mn, sc] = time.split(':')
    if hr == '09' and '30' <= mn <= '59':
        tsc = ((int(hr) - 9) * 60 + int(mn) - 30) * 60 + int(sc)
    elif hr == '10':
        tsc = ((int(hr) - 9) * 60 + int(mn) - 30) * 60 + int(sc)
    elif hr == '11' and '0' <= mn <= '30':
        tsc = ((int(hr) - 9) * 60 + int(mn) - 30) * 60 + int(sc)
    elif '13' <= hr <= '15':
        tsc = ((int(hr) - 13 + 2) * 60 + int(mn)) * 60 + int(sc)
    else:
        return -1

    return float(tsc) / 3600 / 4


# 获取涨停幅
def get_limiting_up_rate(code_or_symbol: str) -> float:
    if code_or_symbol[:2] == '30' or code_or_symbol[:2] == '68':
        return 1.2
    elif code_or_symbol[:1] == '8' or code_or_symbol[:1] == '9' or code_or_symbol[:1] == '4':
        return 1.3
    else:
        return 1.1


# 获取涨停价
def get_limit_up_price(code_or_symbol: str, pre_close: float) -> float:
    if pre_close is None or pre_close <= 0:
        return 0.0

    limit_rate = get_limiting_up_rate(code_or_symbol)

    pre_close_dec = Decimal(str(pre_close)).quantize(Decimal('0.00'))
    limit_price_dec = pre_close_dec * Decimal(str(limit_rate))
    limit_price_dec = limit_price_dec.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

    return float(limit_price_dec)


# 获取跌停幅
def get_limiting_down_rate(code_or_symbol: str) -> float:
    if code_or_symbol[:2] == '30' or code_or_symbol[:2] == '68':
        return 0.8
    elif code_or_symbol[:1] == '8' or code_or_symbol[:1] == '9' or code_or_symbol[:1] == '4':
        return 0.7
    else:
        return 0.9


# 获取跌停价
def get_limit_down_price(code_or_symbol: str, pre_close: float) -> float:
    if pre_close is None or pre_close <= 0:
        return 0.0

    limit_rate = get_limiting_down_rate(code_or_symbol)

    pre_close_dec = Decimal(str(pre_close)).quantize(Decimal('0.00'))
    limit_price_dec = pre_close_dec * Decimal(str(limit_rate))
    limit_price_dec = limit_price_dec.quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

    return float(limit_price_dec)


# TODO
def get_st_limit_up_rate():
    return


# TODO
def get_st_limit_up_price():
    return


# TODO
def get_st_limit_down_rate():
    return


# TODO
def get_st_limit_down_price():
    return


def time_diff_seconds(later_time: datetime.datetime.time, early_time: datetime.datetime.time):
    """ 将时间转换为总秒数 """
    total_seconds_time1 = later_time.hour * 3600 + later_time.minute * 60 + later_time.second
    total_seconds_time2 = early_time.hour * 3600 + early_time.minute * 60 + early_time.second

    # 计算两个时间之间的秒数差
    diff_seconds = abs(total_seconds_time1 - total_seconds_time2)

    return diff_seconds


# 迅投相关数据
# past_seconds 当日交易日已经过去多少秒，计算量比这类指标需要
def hms_to_past_seconds(hour: int, minute: int, second: int) -> int:
    time_int = hour * 100 + minute
    if time_int < 930:
        return 0
    elif 930 <= time_int < 1130:
        return hour * 3600 + minute * 60 + second - (3600 * 9 + 60 * 30)
    elif 1130 <= time_int < 1300:
        return 3600 * 2
    elif 1300 <= time_int < 1500:
        return hour * 3600 + minute * 60 + second - (3600 * 13) + 3600 * 2
    else:
        return 3600 * 4


def xt_time_tag_to_hms(time_tag: str) -> tuple[int, int, int]:
    dt = datetime.datetime.strptime(time_tag, '%Y%m%d %H:%M:%S')
    return dt.hour, dt.minute, dt.second


def xt_time_tag_to_past_seconds(time_tag: int | str) -> int:
    hour, minute, second = xt_time_tag_to_hms(str(time_tag))
    return hms_to_past_seconds(hour, minute, second)


# sub_whole 的 quotes 时间格式
def xt_time_to_hms(timestamp: int) -> tuple[int, int, int]:
    if len(str(timestamp)) > 10:
        timestamp = timestamp // 1000
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.hour, dt.minute, dt.second
    return 0, 0, 0


def xt_time_to_past_seconds(timestamp: int) -> int:
    hour, minute, second = xt_time_to_hms(timestamp)
    return hms_to_past_seconds(hour, minute, second)


# =======================
#  Convert daily history
# =======================


def convert_daily_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    将日线K线数据转换为周线数据（datetime为该周内最后一个交易日的日期）
    参数: df: 包含日线数据的DataFrame，需包含datetime, open, high, low, close, volume, amount列
    返回: 周线数据的DataFrame，按周一到周日合并，datetime为周内最后一个交易日的日期
    """
    data = df.copy()

    # 1. 保留原始整数日期，同时新增datetime类型列用于分组（确定属于哪一周）
    data['dt'] = pd.to_datetime(data['datetime'], format='%Y%m%d')
    data = data.set_index('dt')  # 用datetime类型索引进行周分组

    # 2. 按周一到周日分组（周区间：[周一, 下周一)）
    weekly_groups = data.resample('W-MON', closed='left', label='left')  # 分组逻辑不变，仅用于划分周范围

    # 3. 聚合规则：核心是对原始datetime取组内最后一个值
    weekly_data = weekly_groups.agg({
        'datetime': 'last',       # 周内最后一个交易日的原始整数日期
        'open': 'first',          # 周内第一个开盘价
        'high': 'max',            # 周内最高价
        'low': 'min',             # 周内最低价
        'close': 'last',          # 周内最后一个收盘价
        'volume': 'sum',          # 周内成交量总和
        'amount': 'sum'           # 周内成交额总和
    }).dropna()  # 移除无数据的周

    # 4. 恢复列顺序和原始数据类型
    weekly_data = weekly_data.reset_index(drop=True)[['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']]
    for col in weekly_data.columns:
        weekly_data[col] = weekly_data[col].astype(df[col].dtype)

    return weekly_data


def convert_daily_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    将日线K线数据转换为月线数据（datetime为当月最后一个交易日的日期）
    参数: df: 包含日线数据的DataFrame，需包含datetime, open, high, low, close, volume, amount列
    返回: 月线数据的DataFrame，按自然月划分（1月-12月），datetime为当月最后一个交易日的日期
    """
    data = df.copy()

    # 1. 保留原始整数日期，新增datetime类型列用于按月分组
    data['dt'] = pd.to_datetime(data['datetime'], format='%Y%m%d')
    data = data.set_index('dt')  # 用datetime索引进行月份分组

    # 2. 按自然月分组（1月1日-1月最后一天，2月1日-2月最后一天...）
    # 频率'M'表示按月分组，默认按自然月划分
    monthly_groups = data.resample('M')

    # 3. 聚合规则：与周线逻辑一致，仅周期改为月
    monthly_data = monthly_groups.agg({
        'datetime': 'last',       # 当月最后一个交易日的原始整数日期
        'open': 'first',          # 当月第一个交易日的开盘价
        'high': 'max',            # 当月最高价
        'low': 'min',             # 当月最低价
        'close': 'last',          # 当月最后一个交易日的收盘价
        'volume': 'sum',          # 当月成交量总和
        'amount': 'sum'           # 当月成交额总和
    }).dropna()  # 移除无数据的月份

    # 4. 恢复列顺序和原始数据类型
    monthly_data = monthly_data.reset_index(drop=True)[['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']]
    for col in monthly_data.columns:
        monthly_data[col] = monthly_data[col].astype(df[col].dtype)

    return monthly_data