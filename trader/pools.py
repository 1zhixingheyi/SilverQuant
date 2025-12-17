"""
股票池管理模块

提供灵活的股票池构建和管理功能：
- 白名单管理：多种数据源的白名单股票池构建
- 黑名单过滤：基于条件筛选的黑名单机制
- 实时刷新：支持股票池的动态刷新和更新
- 技术择时：基于指数技术指标的股票池时机选择
- 多源整合：问财、通达信、指数成分股等多数据源

股票池架构设计：
- 基础抽象：StockPool基类定义标准接口
- 白名单策略：多种白名单构建策略的实现
- 黑名单策略：多种黑名单过滤策略的实现
- 组合模式：白名单和黑名单的灵活组合
- 缓存机制：股票列表的本地缓存管理

核心功能特性：
- 多层过滤：白名单+黑名单的双重过滤机制
- 动态更新：支持股票池的实时刷新
- 消息通知：股票池更新状态的钉钉推送
- 技术指标：基于MACD、MA等指标的择时策略
- 数据容错：异常股票的自动移除机制

白名单构建策略：
- 问财选股：基于自然语言条件的智能选股
- 自定义列表：从文件读取的股票代码列表
- 通达信自选：读取通达信自选股文件
- 指数成分：各大指数的成分股构建
- 前缀过滤：基于股票代码前缀的筛选

黑名单过滤策略：
- 空黑名单：不启用黑名单过滤
- 问财黑名单：基于问财条件的黑名单
- 技术指标：基于技术指标的黑名单筛选

技术择时策略：
- MA择时：基于指数均线的趋势判断
- MACD择时：基于指数MACD的趋势判断
- 组合择时：多技术指标的综合择时
- 动态周期：可调整的技术指标周期

与其他模块的关系：
- tools/utils_cache.py: 股票代码缓存查询
- tools/utils_remote.py: 远程数据源获取
- tools/utils_ding.py: 股票池状态通知推送
- trader/pools_indicator.py: 技术指标计算
- trader/pools_section.py: 行业概念板块数据
"""

import pandas as pd
from typing import Callable

from tools.constants import MSG_OUTER_SEPARATOR
from tools.utils_basic import symbol_to_code
from tools.utils_cache import get_prefixes_stock_codes, get_index_constituent_codes
from tools.utils_ding import BaseMessager
from tools.utils_remote import get_wencai_codes, get_tdx_zxg_code

from trader.pools_indicator import get_macd_index_indicator, get_ma_index_indicator
from trader.pools_section import get_dfcf_industry_stock_codes, get_dfcf_industry_sections, \
    get_ths_concept_sections, get_ths_concept_stock_codes


class StockPool:
    def __init__(self, account_id: str, strategy_name: str, parameters: any, ding_messager: BaseMessager):
        self.account_id = '**' + str(account_id)[-4:]
        self.strategy_name = strategy_name
        self.messager = ding_messager

        self.pool_parameters = parameters
        self.cache_blacklist: set[str] = set()
        self.cache_whitelist: set[str] = set()
        self.cache_code_list: list[str] = []

    def get_code_list(self) -> list[str]:
        return self.cache_code_list

    def refresh(self):
        # 教学说明：刷新股票池，更新白名单和黑名单
        print(f"🔄 [教学说明] 开始刷新 {self.strategy_name} 股票池...")

        # 教学说明：刷新黑名单，排除高风险股票
        print("🛡️ [教学说明] 刷新黑名单...")
        self.refresh_black()

        # 教学说明：刷新白名单，获取候选股票
        print("✅ [教学说明] 刷新白名单...")
        self.refresh_white()

        # 教学说明：计算最终股票池（白名单 - 黑名单）
        original_whitelist = len(self.cache_whitelist)
        self.cache_code_list = list(self.cache_whitelist.difference(self.cache_blacklist))
        final_count = len(self.cache_code_list)

        # 教学说明：显示股票池统计信息
        print(f"📊 [教学说明] 股票池刷新完成:")
        print(f"  - 白名单股票: {len(self.cache_whitelist)}只")
        print(f"  - 黑名单股票: {len(self.cache_blacklist)}只")
        print(f"  - 过滤掉: {original_whitelist - final_count}只")
        print(f"  - 最终股票池: {final_count}只")

        # 教学说明：发送通知
        if self.messager is not None:
            self.messager.send_text_as_md(
                f'📊 {self.strategy_name}:股票池{final_count}支{MSG_OUTER_SEPARATOR}'
                f'白名单: {len(self.cache_whitelist)} 黑名单: {len(self.cache_blacklist)}')

    def refresh_black(self):
        # 教学说明：清空并重新构建黑名单
        print("🗑️ [教学说明] 清空黑名单缓存...")
        self.cache_blacklist.clear()

    def refresh_white(self):
        # 教学说明：清空并重新构建白名单
        print("📋 [教学说明] 清空白名单缓存...")
        self.cache_whitelist.clear()

    # 删除不符合模式和没有缓存的票池
    def filter_white_list_by_selector(self, filter_func: Callable, cache_history: dict[str, pd.DataFrame]):
        # 教学说明：使用技术指标过滤器进一步筛选白名单股票
        print(f"🔍 [教学说明] 开始使用技术指标过滤白名单股票 (共 {len(self.cache_whitelist)}只)...")

        i = 0
        remove_list = []
        passed_count = 0

        for code in self.cache_whitelist:
            i += 1
            if i % 200 == 0:
                print(f"📊 [教学说明] 已检查 {i}只股票...")

            # 教学说明：检查是否有历史数据
            if code in cache_history and cache_history[code] is not None:
                try:
                    # 教学说明：应用技术指标过滤函数
                    df = filter_func(cache_history[code], code, None)  # 预筛公式默认不需要使用quote所以传None
                    if (len(df) > 0) and (not df['PASS'].values[-1]):
                        remove_list.append(code)
                        print(f"❌ [教学说明] {code} 技术指标检查不通过，移出白名单")
                    else:
                        passed_count += 1
                except Exception as e:
                    print(f"⚠️ [教学说明] {code} 数据处理出错，移出白名单: {e}")
                    remove_list.append(code)
            else:
                # 教学说明：没有历史数据的股票也移除
                print(f"⚠️ [教学说明] {code} 缺少历史数据，移出白名单")
                remove_list.append(code)

        # 教学说明：移除未通过过滤的股票
        for code in remove_list:
            self.cache_whitelist.discard(code)

        print(f"📊 [教学说明] 技术指标过滤完成:")
        print(f"  - 检查数量: {i}只")
        print(f"  - 通过检查: {passed_count}只")
        print(f"  - 移除数量: {len(remove_list)}只")
        print(f"  - 剩余白名单: {len(self.cache_whitelist)}只")

        # 教学说明：发送过滤结果通知
        if self.messager is not None:
            self.messager.send_text_as_md(f'🔍 [{self.account_id}]{self.strategy_name}:技术指标过滤移除{len(remove_list)}支')


# -----------------------
# Black Empty
# -----------------------

class StocksPoolBlackEmpty(StockPool):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)


# -----------------------
# Black Wencai
# -----------------------

class StocksPoolBlackWencai(StockPool):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.black_prompts = parameters.black_prompts

    def refresh_black(self):
        super().refresh_black()

        codes = get_wencai_codes(self.black_prompts)
        self.cache_blacklist.update(codes)


# -----------------------
# White Wencai
# -----------------------

class StocksPoolWhiteWencai(StocksPoolBlackWencai):
    # 教学说明：问财白名单股票池，使用问财智能选股构建白名单
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prompts = parameters.white_prompts
        print(f"💡 [教学说明] 初始化问财白名单股票池，选股条件: {self.white_prompts}")

    def refresh_white(self):
        # 教学说明：使用问财API获取白名单股票
        super().refresh_white()

        print(f"🔍 [教学说明] 使用问财API获取白名单股票: {self.white_prompts}")
        codes = get_wencai_codes(self.white_prompts)
        print(f"📋 [教学说明] 问财返回 {len(codes)}只候选股票")
        self.cache_whitelist.update(codes)


# -----------------------
# White Custom
# -----------------------

# 自定义白名单股票列表
class StocksPoolWhiteCustomSymbol(StocksPoolBlackWencai):
    # 教学说明：自定义白名单股票池，从文件读取预定义的股票代码
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_codes_filepath = parameters.white_codes_filepath
        print(f"📝 [教学说明] 初始化自定义白名单股票池，文件路径: {self.white_codes_filepath}")

    def refresh_white(self):
        # 教学说明：从文件读取自定义股票代码列表
        super().refresh_white()

        print(f"📂 [教学说明] 从文件读取自定义股票代码: {self.white_codes_filepath}")
        try:
            with open(self.white_codes_filepath, 'r') as r:
                lines = r.readlines()
                codes = []
                for line in lines:
                    line = line.replace('\n', '')
                    if len(line) >= 6:
                        line = line[-6:]  # 只获取最后六位
                        code = symbol_to_code(line)
                        codes.append(code)
                print(f"📋 [教学说明] 文件包含 {len(codes)}只股票代码")
                self.cache_whitelist.update(codes)
        except Exception as e:
            print(f"❌ [教学说明] 读取文件失败: {e}")
            print(f"❌ [教学说明] 白名单为空，将使用空列表")


class StocksPoolWhiteCustomTdx(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        # 自选股文件默认路径示例： r'C:\new_tdx\T0002\blocknew\ZXG.blk'
        self.tdx_codes_filepath = parameters.tdx_codes_filepath

    def refresh_white(self):
        super().refresh_white()
        codes = get_tdx_zxg_code(self.tdx_codes_filepath)
        self.cache_whitelist.update(codes)


# -----------------------
# White Indexes
# -----------------------

# 自定义指数成份股
class StocksPoolWhiteIndexes(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_indexes = parameters.white_indexes

    def refresh_white(self):
        super().refresh_white()

        for index in self.white_indexes:
            t_white_codes = get_index_constituent_codes(index)
            self.cache_whitelist.update(t_white_codes)


# 自定义指数成份股 + 指数MA择时
class StocksPoolWhiteIndexesMA(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_indexes = parameters.white_prefixes
        self.white_index_symbol = parameters.white_index_symbol         # 指数名称（默认中证全指000985）
        self.white_ma_above_period = parameters.white_ma_above_period   # 均线周期（默认五日均线）

    def refresh_white(self):
        super().refresh_white()

        allow, info = get_ma_index_indicator(
            symbol=self.white_index_symbol,
            period=self.white_ma_above_period,
        )
        if allow:
            for index in self.white_indexes:
                t_white_codes = get_index_constituent_codes(index)
                self.cache_whitelist.update(t_white_codes)


# 自定义指数成份股 + 指数群MACD择时
class StocksPoolWhiteIndexesMACD(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_indexes = parameters.white_indexes

    def refresh_white(self):
        super().refresh_white()

        for index in self.white_indexes:
            allow, info = get_macd_index_indicator(symbol=index)
            if allow:
                t_white_codes = get_index_constituent_codes(index)
                self.cache_whitelist.update(t_white_codes)


# -----------------------
# White Prefixes
# -----------------------

# 自定义前缀成份股
class StocksPoolWhitePrefixes(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prefixes = parameters.white_prefixes
        if hasattr(parameters, 'white_none_st'):
            self.white_none_st = parameters.white_none_st
        else:
            self.white_none_st = False

    def refresh_white(self):
        super().refresh_white()

        t_white_codes = get_prefixes_stock_codes(self.white_prefixes, self.white_none_st)
        self.cache_whitelist.update(t_white_codes)


# 自定义前缀成份股 + 指数MA择时
class StocksPoolWhitePrefixesMA(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prefixes = parameters.white_prefixes
        self.white_index_symbol = parameters.white_index_symbol         # 指数名称（默认中证全指000985）
        self.white_ma_above_period = parameters.white_ma_above_period   # 均线周期（默认五日均线）

    def refresh_white(self):
        super().refresh_white()

        allow, info = get_ma_index_indicator(
            symbol=self.white_index_symbol,
            period=self.white_ma_above_period,
        )
        if allow:
            t_white_codes = get_prefixes_stock_codes(self.white_prefixes)
            self.cache_whitelist.update(t_white_codes)


# 自定义前缀成份股 + 东方财富行业板块上涨比例预筛（现在容易被封接口）
class StocksPoolWhitePrefixesIndustry(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prefixes = parameters.white_prefixes

    def refresh_white(self):
        super().refresh_white()

        section_names = get_dfcf_industry_sections()
        if self.messager is not None:
            self.messager.send_text_as_md(
                f'[{self.account_id}]{self.strategy_name} 行业板块{MSG_OUTER_SEPARATOR}'
                f'{section_names}')
        t_white_codes = get_dfcf_industry_stock_codes(section_names)

        filter_codes = [code for code in t_white_codes if code[:2] in self.white_prefixes]
        self.cache_whitelist.update(filter_codes)


# 自定义前缀成份股 + 同花顺行业板块上涨个数预筛（现在容易被封接口）
class StocksPoolWhitePrefixesConcept(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager: BaseMessager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prefixes = parameters.white_prefixes

    def refresh_white(self):
        super().refresh_white()

        section_names = get_ths_concept_sections()
        if self.messager is not None:
            self.messager.send_text_as_md(
                f'[{self.account_id}]{self.strategy_name} 概念板块{MSG_OUTER_SEPARATOR}'
                f'{section_names}')
        t_white_codes = get_ths_concept_stock_codes(section_names)
        filter_codes = [code for code in t_white_codes if code[:2] in self.white_prefixes]
        self.cache_whitelist.update(filter_codes)
