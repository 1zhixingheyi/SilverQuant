import datetime
import logging
import pandas as pd


# pandas dataframe 显示配置优化
def pd_show_all() -> None:
    pd.set_option('display.width', None)
    pd.set_option('display.min_rows', 1000)
    pd.set_option('display.max_rows', 5000)
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
def logger_init(path=None) -> logging.Logger:
    logger = logging.getLogger('a')
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

        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


# 六位数symbol代码转换成带交易所后缀code格式
def symbol_to_code(symbol: str) -> str:
    if symbol[:2] in ['00', '30', '15', '12']:
        return f'{symbol}.SZ'
    elif symbol[:2] in ['60', '68', '51', '52','53', '56', '58','12']:
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
# 掘金系列代码
# ==========
def symbol_to_gmsymbol(symbol: str) -> str:
    if symbol[:2] in ['00', '30', '15', '12']:
        return f'SZSE.{symbol}'
    elif symbol[:2] in ['60', '68', '51', '52','53', '56', '58','12']:
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


# 判断是不是股票代码
def is_stock(code_or_symbol: str):
    return code_or_symbol[:2] in [
        '00', '30', '60', '68', '82', '83', '87', '88', '43', '92',
    ]
    
# 判断是不是可交易股票代码 包含 股票 ETF 可转债
def is_symbol(code_or_symbol: str):
    return code_or_symbol[:2] in [
        '00', '30', '60', '68', '82', '83', '87', '88', '43', '92',
        # ETF and 可转债
        '15', '51', '52', '53', '56', '58', '11', '12'
    ]
    
# 判断是不是etf代码
def is_fund_etf(code_or_symbol: str):
    return code_or_symbol[:2] in [
        '15', '51', '52', '53', '56', '58'
    ]

# 判断是不是可转债
def is_bond(code_or_symbol: str):
    return code_or_symbol[:2] in [
        '11', '12'
    ]

# 获取symbol的交易所简称
def get_symbol_exchange(symbol: str) -> str:
    if symbol[:2] in ['00', '30', '15', '12']:
        return 'SZ'
    elif symbol[:2] in ['60', '68', '51', '52', '53', '56', '58','11']:
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


# 获取涨停率
def get_limiting_up_rate(code: str) -> float:
    if code[:2] == '30' or code[:2] == '68':
        return 1.2
    elif code[:1] == '8' or code[:1] == '9' or code[:1] == '4':
        return 1.3
    else:
        return 1.1


# 计算一只股票第二天的涨停价
def get_limit_up_price(code: str, pre_close: float) -> float:
    if pre_close == 0:
        return 0

    limit_rate = get_limiting_up_rate(code)
    limit = pre_close * limit_rate
    limit = '%.2f' % limit
    return float(limit)


# 获取跌停率
def get_limiting_down_rate(code: str) -> float:
    if code[:2] == '30' or code[:2] == '68':
        return 0.8
    elif code[:1] == '8' or code[:1] == '9' or code[:1] == '4':
        return 0.7
    else:
        return 0.9


# 计算一只股票第二天的跌停价
def get_limit_down_price(code: str, pre_close: float) -> float:
    if pre_close == 0:
        return 0

    limit_rate = get_limiting_down_rate(code)
    limit = pre_close * limit_rate
    limit = '%.2f' % limit
    return float(limit)


def time_diff_seconds(later_time: datetime.datetime.time, early_time: datetime.datetime.time):
    # 将时间转换为总秒数
    total_seconds_time1 = later_time.hour * 3600 + later_time.minute * 60 + later_time.second
    total_seconds_time2 = early_time.hour * 3600 + early_time.minute * 60 + early_time.second

    # 计算两个时间之间的秒数差
    diff_seconds = total_seconds_time1 - total_seconds_time2

    return diff_seconds


if __name__ == '__main__':
    # logging_init()
    # logging.warning('123456')
    # print(map_num_to_chr(6300))
    # print(get_current_time_percentage('13:01:00'))

    print(get_limit_up_price('301000', 10.00))
    print(get_limit_down_price('301000', 10.00))
