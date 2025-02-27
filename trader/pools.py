import pandas as pd
from typing import Set, Callable

from tools.utils_basic import symbol_to_code
from tools.utils_cache import get_prefixes_stock_codes, get_index_constituent_codes
from tools.utils_remote import get_wencai_codes

from trader.pools_indicator import get_macd_trend_indicator, get_ma_trend_indicator
from trader.pools_section import get_dfcf_industry_stock_codes, get_dfcf_industry_sections, \
    get_ths_concept_sections, get_ths_concept_stock_codes


class StockPool:
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        self.account_id = '**' + str(account_id)[-4:]
        self.strategy_name = strategy_name
        self.ding_messager = ding_messager

        self.cache_blacklist: Set[str] = set()
        self.cache_whitelist: Set[str] = set()

    def get_code_list(self) -> list[str]:
        return list(self.cache_whitelist.difference(self.cache_blacklist))

    def refresh(self):
        self.refresh_black()
        self.refresh_white()

        print(f'White list refreshed {len(self.cache_whitelist)} codes.')
        print(f'Black list refreshed {len(self.cache_blacklist)} codes.')
        print(f'Total list refreshed {len(self.get_code_list())} codes.')

        if self.ding_messager is not None:
            self.ding_messager.send_text(
                f'[{self.account_id}]{self.strategy_name}:更新{len(self.get_code_list())}支\n'
                f'白名单: {len(self.cache_whitelist)} '
                f'黑名单: {len(self.cache_blacklist)}')

    def refresh_black(self):
        self.cache_blacklist.clear()

    def refresh_white(self):
        self.cache_whitelist.clear()

    # 删除不符合模式和没有缓存的票池
    def filter_white_list_by_selector(self, selector: Callable, cache_history: dict[str, pd.DataFrame]):
        remove_list = []

        for code in self.cache_whitelist:
            if code in cache_history:
                df = selector(cache_history[code], code, None)  # 预筛公式默认不需要使用quote所以传None
                if not df['PASS'].values[-1]:
                    remove_list.append(code)
            else:
                remove_list.append(code)

        for code in remove_list:
            self.cache_whitelist.discard(code)

        if self.ding_messager is not None:
            self.ding_messager.send_text(f'[{self.account_id}]{self.strategy_name}:筛除{len(remove_list)}支\n')


# -----------------------
# Black Empty
# -----------------------

class StocksPoolBlackEmpty(StockPool):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)

# -----------------------
# Black Wencai
# -----------------------

class StocksPoolBlackWencai(StockPool):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
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
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prompts = parameters.white_prompts

    def refresh_white(self):
        super().refresh_white()

        codes = get_wencai_codes(self.white_prompts)
        self.cache_whitelist.update(codes)

# -----------------------
# White Custom
# -----------------------

class StocksPoolWhiteCustomSymbol(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_codes_filepath = parameters.white_codes_filepath

    def refresh_white(self):
        super().refresh_white()

        with open(self.white_codes_filepath, 'r') as r:
            lines = r.readlines()
            codes = []
            for line in lines:
                line = line.replace('\n', '')
                if len(line) >= 6:
                    line = line[-6:]  # 只获取最后六位
                    code = symbol_to_code(line)
                    codes.append(code)
            self.cache_whitelist.update(codes)

# -----------------------
# White Indexes
# -----------------------

class StocksPoolWhiteIndexes(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_indexes = parameters.white_indexes

    def refresh_white(self):
        super().refresh_white()

        for index in self.white_indexes:
            t_white_codes = get_index_constituent_codes(index)
            self.cache_whitelist.update(t_white_codes)


class StocksPoolWhiteIndexesMACD(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_indexes = parameters.white_indexes

    def refresh_white(self):
        super().refresh_white()

        for index in self.white_indexes:
            allow, info = get_macd_trend_indicator(symbol=index)
            if allow:
                t_white_codes = get_index_constituent_codes(index)
                self.cache_whitelist.update(t_white_codes)

# -----------------------
# White Prefixes
# -----------------------

class StocksPoolWhitePrefixes(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prefixes = parameters.white_prefixes

    def refresh_white(self):
        super().refresh_white()

        t_white_codes = get_prefixes_stock_codes(self.white_prefixes)
        self.cache_whitelist.update(t_white_codes)


class StocksPoolWhitePrefixesMA(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prefixes = parameters.white_prefixes
        self.white_index = parameters.white_index

    def refresh_white(self):
        super().refresh_white()

        allow, info = get_ma_trend_indicator(symbol=self.white_index)
        if allow:
            t_white_codes = get_prefixes_stock_codes(self.white_prefixes)
            self.cache_whitelist.update(t_white_codes)


class StocksPoolWhitePrefixesIndustry(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prefixes = parameters.white_prefixes

    def refresh_white(self):
        super().refresh_white()

        section_names = get_dfcf_industry_sections()
        if self.ding_messager is not None:
            self.ding_messager.send_text(
                f'[{self.account_id}]{self.strategy_name} 行业板块\n'
                f'{section_names}')
        t_white_codes = get_dfcf_industry_stock_codes(section_names)

        filter_codes = [code for code in t_white_codes if code[:2] in self.white_prefixes]
        self.cache_whitelist.update(filter_codes)


class StocksPoolWhitePrefixesConcept(StocksPoolBlackWencai):
    def __init__(self, account_id: str, strategy_name: str, parameters, ding_messager):
        super().__init__(account_id, strategy_name, parameters, ding_messager)
        self.white_prefixes = parameters.white_prefixes

    def refresh_white(self):
        super().refresh_white()

        section_names = get_ths_concept_sections()
        if self.ding_messager is not None:
            self.ding_messager.send_text(
                f'[{self.account_id}]{self.strategy_name} 概念板块\n'
                f'{section_names}')
        t_white_codes = get_ths_concept_stock_codes(section_names)
        filter_codes = [code for code in t_white_codes if code[:2] in self.white_prefixes]
        self.cache_whitelist.update(filter_codes)
