"""
问财智能选股工具

提供基于同花顺问财平台的智能选股功能：
- 自然语言查询：支持中文自然语言选股条件描述
- 多条件组合：技术指标、基本面、市场情绪等多维度筛选
- 实时数据：获取最新的股价和选股结果
- 价格提取：智能识别和提取股票当前价格
- 调试支持：详细的选股过程调试信息

选股架构设计：
- 查询接口：基于pywencai库的问财API封装
- 提示词管理：支持预定义和自定义选股提示词
- 价格映射：多列名智能匹配价格数据
- 结果处理：DataFrame到字典的数据转换

核心功能特性：
- 智能解析：自动识别不同格式的价格列名
- 实时更新：基于当前日期的动态价格列匹配
- 错误处理：网络异常和数据异常的容错机制
- 调试输出：可选的详细选股过程信息
- 灵活配置：支持内部提示词和外部提示词

选股条件支持：
- 技术指标：MACD金叉、均线排列、成交量等
- 基本面：PE、PB、ROE等财务指标
- 市场范围：指数成分股、行业分类等
- 交易条件：价格区间、涨跌幅限制等
- 时间条件：特定时间周期的技术指标

价格列识别策略：
- 动态日期：根据当前日期生成价格列名
- 多重匹配：支持多种价格列名格式
- 数据类型：确保价格数据为float类型
- 容错机制：列名不匹配时的优雅处理

与其他模块的关系：
- selector/select_prompts.py: 选股提示词配置来源
- trader/buyer.py: 为买入策略提供选股结果
- trader/pools.py: 股票池过滤的数据来源
- run_wencai_qmt.py: 问财策略的入口文件
"""

import datetime
import pywencai
from selector.select_prompts import prompts


default_prompt = "中证500成分股，非ST，非科创，MACD金叉，按价格从小到大"  # 这里自定义问财选股的问句prompt


def get_prompt(prompt_number: any = 0) -> str:
    ans = default_prompt

    if type(prompts) == list and prompt_number < len(prompts):
        ans = prompts[prompt_number]

    if type(prompts) == dict and prompt_number in prompts:
        ans = prompts[prompt_number]

    print('选股问句：', ans, '\n')
    return ans


def get_wencai_codes_prices(query, debugging=False) -> dict[str, str]:
    df = pywencai.get(query=query)

    if df is not None and type(df) is not dict and df.shape[0] > 0:
        possible_price_columns = [
            '现价(元)',
            '最新价',
            f'收盘价:不复权[{datetime.datetime.now().strftime("%Y%m%d")}]',
            f'收盘价:不复权(元)[{datetime.datetime.now().strftime("%Y%m%d")}]',
        ]

        target_col = None

        for temp_col in possible_price_columns:
            if temp_col in df.columns:
                target_col = temp_col
                break

        if target_col is None:
            return {}

        df['curr_price'] = df[target_col].astype(float)
        if debugging:
            now = datetime.datetime.now()
            # now_day = now.strftime("%Y-%m-%d")
            # now_min = now.strftime("%H:%M")
            print(f'Wencai: {now.strftime("%H:%M:%S")}\n', df[['股票代码', '股票简称', 'curr_price']])
        return df.set_index('股票代码')['curr_price'].to_dict()
    return {}


if __name__ == '__main__':
    a = get_wencai_codes_prices([get_prompt()], debugging=True)
    print(a)
    i = 0
    for k in a:
        i += 1
        print(i, '\t', k, '\t', a[k])
