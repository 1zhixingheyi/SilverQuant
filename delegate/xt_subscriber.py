import time
import datetime
import json
import pickle
import random
import threading
import traceback
from typing import Dict, Callable, Optional

import pandas as pd
from xtquant import xtdata

from delegate.xt_delegate import XtDelegate
from delegate.daily_history import DailyHistoryCache
from delegate.daily_reporter import DailyReporter

from tools.utils_cache import StockNames, InfoItem, check_is_open_day, get_trading_date_list
from tools.utils_cache import load_pickle, save_pickle, load_json, save_json
from tools.utils_ding import BaseMessager
from tools.utils_mootdx import get_tdxzip_history
from tools.utils_remote import DataSource, ExitRight, get_daily_history, qmt_quote_to_tick


class BaseSubscriber:
    pass


class XtSubscriber(BaseSubscriber):
    def __init__(
        self,
        account_id: str,
        strategy_name: str,
        delegate: Optional[XtDelegate],
        path_deal: str,
        path_assets: str,
        execute_strategy: Callable,         # 策略回调函数
        execute_interval: int = 1,          # 策略执行间隔，单位（秒）
        before_trade_day: Callable = None,  # 盘前函数
        near_trade_begin: Callable = None,  # 盘后函数
        finish_trade_day: Callable = None,  # 盘后函数
        use_outside_data: bool = False,     # 默认使用原版 QMT data （定期 call 数据但不传入quotes）
        use_ap_scheduler: bool = False,     # 默认使用旧版 schedule （尽可能向前兼容旧策略吧）
        ding_messager: BaseMessager = None,
        open_tick_memory_cache: bool = False,
        tick_memory_data_frame: bool = False,
        open_today_deal_report: bool = False,   # 每日交易记录报告
        open_today_hold_report: bool = False,   # 每日持仓记录报告
        today_report_show_bank: bool = False,   # 是否显示银行流水（国金QMT会卡死所以默认关闭）
    ):
        self.account_id = '**' + str(account_id)[-4:]
        self.strategy_name = strategy_name
        self.delegate = delegate
        if self.delegate is not None:
            self.delegate.subscriber = self

        self.path_deal = path_deal
        self.path_assets = path_assets

        self.execute_strategy = execute_strategy
        self.execute_interval = execute_interval
        self.before_trade_day = before_trade_day    # 提前准备某些耗时长的任务
        self.near_trade_begin = near_trade_begin    # 有些数据临近开盘才更新，这里保证内存里的数据正确
        self.finish_trade_day = finish_trade_day    # 盘后及时做一些总结汇报入库类的整理工作
        self.messager = ding_messager

        self.lock_quotes_update = threading.Lock()  # 聚合实时打点缓存的锁

        self.cache_quotes: Dict[str, Dict] = {}     # 记录实时的价格信息
        self.cache_limits: Dict[str, str] = {       # 限制执行次数的缓存集合
            'prev_seconds': '',                     # 限制每秒一次跑策略扫描的缓存
            'prev_minutes': '',                     # 限制每分钟屏幕心跳换行的缓存
        }
        self.cache_history: Dict[str, pd.DataFrame] = {}    # 记录历史日线行情的信息 { code: DataFrame }

        self.open_tick = open_tick_memory_cache
        self.is_ticks_df = tick_memory_data_frame
        self.quick_ticks: bool = False                          # 是否开启quick tick模式
        self.today_ticks: Dict[str, list | pd.DataFrame] = {}   # 记录tick的历史信息

        self.open_today_deal_report = open_today_deal_report
        self.open_today_hold_report = open_today_hold_report
        self.today_report_show_bank = today_report_show_bank

        self.code_list = ['000001.SH']  # 默认只有上证指数
        self.stock_names = StockNames()
        self.last_callback_time = datetime.datetime.now()       # 上次返回quotes 时间

        # 这个成员变量区别于cache_history，保存全部股票的日线数据550天，cache_history只包含code_list中指定天数数据
        self.history_day_klines : Dict[str, pd.DataFrame] = {}

        self.__extend_codes = ['399001.SZ', '510230.SH', '512680.SH', '159915.SZ', '510500.SH',
                               '588000.SH', '159101.SZ', '399006.SZ', '159315.SZ']

        self.use_outside_data = use_outside_data
        self.use_ap_scheduler = use_ap_scheduler
        if self.use_outside_data:
            self.use_ap_scheduler = True  # 如果use_outside_data 被设置为True，则需强制使用apscheduler

        self.daily_reporter = DailyReporter(
            self.account_id,
            self.strategy_name,
            self.delegate,
            self.path_deal,
            self.path_assets,
            self.messager,
            self.use_outside_data,
            self.today_report_show_bank,
        )

        if self.use_ap_scheduler:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.executors.pool import ThreadPoolExecutor
            executors = {
                'default': ThreadPoolExecutor(32),
            }
            job_defaults = {
                'coalesce': True,
                'misfire_grace_time': 180,
                'max_instances': 3
            }
            self.scheduler = BlockingScheduler(timezone='Asia/Shanghai', executors=executors, job_defaults=job_defaults)

        if self.is_ticks_df:
            self.tick_df_cols = ['time', 'price', 'high', 'low', 'volume', 'amount'] \
                + [f'askPrice{i}' for i in range(1, 6)] \
                + [f'askVol{i}' for i in range(1, 6)] \
                + [f'bidPrice{i}' for i in range(1, 6)] \
                + [f'bidVol{i}' for i in range(1, 6)]

        self.curr_trade_date = '1990-12-19' #记录当前股票交易日期

    # -----------------------
    # 策略触发主函数
    # -----------------------
    def callback_sub_whole(self, quotes: Dict) -> None:
        # 教学说明：QMT行情数据回调主函数，每次收到行情数据时被调用
        # 这是量化策略的核心驱动函数，负责实时行情数据的处理和策略执行调度
        now = datetime.datetime.now()
        self.last_callback_time = now

        curr_date = now.strftime('%Y-%m-%d')
        curr_time = now.strftime('%H:%M')

        # 教学说明：每分钟输出一次时间标记，方便控制台观察运行状态
        if self.cache_limits['prev_minutes'] != curr_time:
            self.cache_limits['prev_minutes'] = curr_time
            print(f'\n[{curr_time}]', end='')

        curr_seconds = now.strftime('%S')
        with self.lock_quotes_update:
            self.cache_quotes.update(quotes)  # 合并最新数据

        # 教学说明：策略执行控制，每秒最多执行一次策略，避免过度频繁调用
        if self.cache_limits['prev_seconds'] != curr_seconds:
            self.cache_limits['prev_seconds'] = curr_seconds

            print_mark = '.' if len(self.cache_quotes) > 0 else 'x'

            if int(curr_seconds) % self.execute_interval == 0:
                # 教学说明：Tick数据记录模式（完整模式：先记录再执行策略）
                if self.open_tick and (not self.quick_ticks):
                    print(f"📝 [教学说明] 记录完整Tick数据到内存缓存...")
                    self.record_tick_to_memory(self.cache_quotes)

                # 教学说明：执行策略核心函数，传入当前时间和行情数据
                print(f"⚡ [教学说明] 执行策略逻辑 (间隔{self.execute_interval}秒)")
                # str(%Y-%m-%d) str(%H:%M) str(%S) dict(code: quotes)
                is_clear = self.execute_strategy(curr_date, curr_time, curr_seconds, self.cache_quotes)

                # 教学说明：Tick数据记录模式（快速模式：先执行策略再记录）
                if self.open_tick and self.quick_ticks:
                    print(f"⚡ [教学说明] 记录快速Tick数据到内存缓存...")
                    self.record_tick_to_memory(self.cache_quotes)

                if is_clear:
                    print(f"🧹 [教学说明] 清空行情缓存，准备接收新数据")
                    with self.lock_quotes_update:
                        self.cache_quotes.clear()  # execute_strategy() return True means need clear

                print(print_mark, end='')  # 每秒钟开始的时候输出一个点

    def callback_run_no_quotes(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        now = datetime.datetime.now()
        self.last_callback_time = now

        curr_date = now.strftime('%Y-%m-%d')
        curr_time = now.strftime('%H:%M')

        # 每分钟输出一行开头
        if self.cache_limits['prev_minutes'] != curr_time:
            self.cache_limits['prev_minutes'] = curr_time
            print(f'\n[{curr_time}]', end='')

        curr_seconds = now.strftime('%S')
        if self.cache_limits['prev_seconds'] != curr_seconds:
            self.cache_limits['prev_seconds'] = curr_seconds

            if int(curr_seconds) % self.execute_interval == 0:
                print('.', end='')  # cache_quotes 肯定没数据，这里就是输出观察线程健康
                # str(%Y-%m-%d), str(%H:%M), str(%S)
                self.execute_strategy(curr_date, curr_time, curr_seconds, {})

    def callback_open_no_quotes(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        if self.messager is not None:
            self.messager.send_text_as_md(f'[{self.account_id}]{self.strategy_name}:开启')
        print('[启动策略]', end='')

    def callback_close_no_quotes(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        print('\n[关闭策略]')
        if self.messager is not None:
            self.messager.send_text_as_md(f'[{self.account_id}]{self.strategy_name}:结束')

    # -----------------------
    # 监测主策略执行
    # -----------------------
    def callback_monitor(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        now = datetime.datetime.now()
        callback_timedelta = (now - self.last_callback_time).total_seconds()
        if callback_timedelta > 60:
            if self.messager is not None:
                self.messager.send_text_as_md(
                    f'[{self.account_id}]{self.strategy_name}:中断\n请检查QMT数据源 ',
                    alert=True,
                )
            if len(self.code_list) > 1 and xtdata.get_client():
                print('尝试重新订阅行情数据')
                time.sleep(1)
                self.resubscribe_tick(notice=True)

    # -----------------------
    # 订阅tick相关
    # -----------------------
    def subscribe_tick(self, resume: bool = False):
        # 教学说明：开启实时行情数据订阅，这是策略获取市场数据的入口
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        print(f"📡 [教学说明] 开始订阅实时行情数据，股票数量: {len(self.code_list)}只")
        if self.messager is not None:
            self.messager.send_text_as_md(f'[{self.account_id}]{self.strategy_name}:'
                                          f'{"恢复" if resume else "开启"} {len(self.code_list)}支')
        print('[开启行情订阅]', end='')
        xtdata.enable_hello = False  # 关闭QMT的hello消息，减少控制台噪音
        print(f"🔗 [教学说明] 注册行情回调函数，开始接收实时Tick数据...")
        self.cache_limits['sub_seq'] = xtdata.subscribe_whole_quote(self.code_list, callback=self.callback_sub_whole)

    def unsubscribe_tick(self, pause: bool = False):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        if 'sub_seq' in self.cache_limits:
            xtdata.unsubscribe_quote(self.cache_limits['sub_seq'])
            print('\n[结束行情订阅]')
            if self.messager is not None:
                self.messager.send_text_as_md(f'[{self.account_id}]{self.strategy_name}:'
                                              f'{"暂停" if pause else "关闭"}')

    def resubscribe_tick(self, notice: bool = False):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        if 'sub_seq' in self.cache_limits:
            xtdata.unsubscribe_quote(self.cache_limits['sub_seq'])
        self.cache_limits['sub_seq'] = xtdata.subscribe_whole_quote(self.code_list, callback=self.callback_sub_whole)
        xtdata.enable_hello = False

        if self.messager is not None and notice:
            self.messager.send_text_as_md(f'[{self.account_id}]{self.strategy_name}:'
                                          f'重启 {len(self.code_list)}支')
        print('\n[重启行情订阅]', end='')

    def update_code_list(self, code_list: list[str]):
        # 加上证指数防止没数据不打点
        self.code_list = ['000001.SH'] + code_list
        extend = 10 - len(self.code_list)
        if extend > 0:
            self.code_list.extend(self.__extend_codes[:extend])  # 防止数据太少长时间不返回数据导致断流

    # -----------------------
    # 盘中实时的tick历史
    # -----------------------
    def record_tick_to_memory(self, quotes):
        # 记录 tick 历史
        if self.is_ticks_df:
            for code in quotes:
                quote = quotes[code]
                tick = qmt_quote_to_tick(quote)
                new_tick_df = pd.DataFrame([tick], columns=self.tick_df_cols)
                if code not in self.today_ticks:
                    self.today_ticks[code] = new_tick_df
                else:
                    self.today_ticks[code] = pd.concat([self.today_ticks[code], new_tick_df], ignore_index=True)
        else:
            for code in quotes:
                if code not in self.today_ticks:
                    self.today_ticks[code] = []

                quote = quotes[code]
                tick_time = datetime.datetime.fromtimestamp(quote['time'] / 1000).strftime('%H:%M:%S')
                self.today_ticks[code].append([
                    tick_time,                          # 成交时间，格式：%H:%M:%S
                    round(quote['lastPrice'], 3),       # 成交价格
                    round(quote['high'], 3),            # 成交最高价
                    round(quote['low'], 3),             # 成交最最低价
                    int(quote['volume']),               # 累计成交量（手）
                    round(quote['amount'], 3),          # 累计成交额（元）
                    [round(p, 3) if isinstance(p, (int, float)) else p for p in quote['askPrice']],  # 卖价
                    [int(v) if isinstance(v, (int, float)) else v for v in quote['askVol']],         # 卖量
                    [round(p, 3) if isinstance(p, (int, float)) else p for p in quote['bidPrice']],  # 买价
                    [int(v) if isinstance(v, (int, float)) else v for v in quote['bidVol']],         # 买量
                ])

    def clean_ticks_history(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        self.today_ticks.clear()
        self.today_ticks = {}
        print(f"已清除tick缓存")

    def save_tick_history(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        if self.is_ticks_df:
            pickle_file = f'./_cache/debug/tick_history_{self.strategy_name}.pkl'
            with open(pickle_file, 'wb') as f:
                pickle.dump(self.today_ticks, f)
            print(f"当日tick数据已存储为 {pickle_file} 文件")
        else:
            json_file = f'./_cache/debug/tick_history_{self.strategy_name}.json'
            with open(json_file, 'w') as file:
                json.dump(self.today_ticks, file, indent=4)
            print(f"当日tick数据已存储为 {json_file} 文件")

    # -----------------------
    # 盘前下载数据缓存
    # -----------------------
    def _download_from_remote(
        self,
        target_codes: list,
        start: str,
        end: str,
        adjust: ExitRight,
        columns: list[str],
        data_source: DataSource,
    ):
        print(f'Prepared TIME RANGE: {start} - {end}')
        t0 = datetime.datetime.now()
        print(f'Downloading {len(target_codes)} stocks:')

        group_size = 200
        down_count = 0
        for i in range(0, len(target_codes), group_size):
            sub_codes = [sub_code for sub_code in target_codes[i:i + group_size]]
            print(i, sub_codes)  # 已更新数量

            # TUSHARE 批量下载限制总共8000天条数据，所以暂时弃用
            # if data_source == DataSource.TUSHARE:
            #     # 使用 TUSHARE 数据源批量下载
            #     dfs = get_ts_daily_histories(sub_codes, start, end, columns)
            #     self.cache_history.update(dfs)
            #     time.sleep(0.1)

            # 默认使用 AKSHARE 数据源
            for code in sub_codes:
                df = get_daily_history(code, start, end, columns=columns, adjust=adjust, data_source=data_source)
                time.sleep(0.5)
                if df is not None:
                    self.cache_history[code] = df
                    down_count += 1

        print(f'Download completed with {down_count} stock histories succeed!')
        t1 = datetime.datetime.now()
        print(f'Prepared TIME COST: {t1 - t0}')

    def _download_from_tdx(self, target_codes: list, start: str, end: str, adjust: str, columns: list[str]):
        print(f'Prepared time range: {start} - {end}')
        t0 = datetime.datetime.now()

        full_history = get_tdxzip_history(adjust=adjust)
        self.history_day_klines = full_history

        days = len(get_trading_date_list(start, end))

        i = 0
        for code in target_codes:
            if code in full_history:
                i += 1
                self.cache_history[code] = full_history[code][columns].tail(days).copy()
        print(f'[HISTORY] Find {i}/{len(target_codes)} codes returned.')

        t1 = datetime.datetime.now()
        print(f'Prepared TIME COST: {t1 - t0}')

    def download_cache_history(
        self,
        cache_path: str,  # DATA SOURCE 是tushare的时候不需要
        code_list: list[str],
        start: str,
        end: str,
        adjust: ExitRight,
        columns: list[str],
        data_source: DataSource,
    ):
        # 教学说明：下载历史K线数据缓存，为策略提供技术分析基础数据
        print(f"📊 [教学说明] 开始下载历史数据缓存，数据源: {data_source}")
        print(f"📅 [教学说明] 时间范围: {start} - {end}，股票数量: {len(code_list)}只")

        # ======== 每日一次性全量数据源 ========
        if data_source == DataSource.AKSHARE or data_source == DataSource.TDXZIP:
            print(f"🗂️ [教学说明] 检查本地缓存文件: {cache_path}")
            temp_indicators = load_pickle(cache_path)
            if temp_indicators is not None and len(temp_indicators) > 0:
                # 教学说明：优先使用本地缓存，提高启动速度并减少网络请求
                print(f"✅ [教学说明] 发现有效缓存，直接加载历史数据")
                self.cache_history.clear()
                self.cache_history = {}
                self.cache_history.update(temp_indicators)
                print(f'📈 [教学说明] 成功加载 {len(self.cache_history)} 只股票的历史数据')
                if self.messager is not None:
                    self.messager.send_text_as_md(f'[{self.account_id}]{self.strategy_name}:'
                                                  f'历史{len(self.cache_history)}支')
            else:
                # 教学说明：无有效缓存时，从远程数据源下载完整历史数据
                print(f"🌐 [教学说明] 未发现有效缓存，开始从远程下载历史数据")
                self.cache_history.clear()
                self.cache_history = {}
                if data_source == DataSource.AKSHARE:
                    print(f"📡 [教学说明] 使用AKShare数据源下载历史数据...")
                    self._download_from_remote(code_list, start, end, adjust, columns, data_source)
                else:
                    print(f"📋 [教学说明] 使用通达信ZIP数据源")
                    print('[提醒] 使用TDX ZIP文件作为数据源，请在RUN代码中添加调度任务check_xdxr_cache更新除权除息数据，建议运行时段在05:30之后。')
                    print('[提醒] 使用TDX ZIP文件作为数据源，请在RUN代码中建议在near_trade_begin中执行download_cache_history获取历史数据，避免before_trade_day执行时间太早未更新除权信息。')
                    self._download_from_tdx(code_list, start, end, adjust, columns)

                save_pickle(cache_path, self.cache_history)
                print(f'💾 [教学说明] 历史数据已缓存到本地: {len(self.cache_history)}/{len(code_list)} 只股票')
                print(f'📁 [教学说明] 缓存文件路径: {cache_path}')
                if self.messager is not None:
                    self.messager.send_text_as_md(f'[{self.account_id}]{self.strategy_name}:'
                                                  f'历史{len(self.cache_history)}支')

            if data_source == DataSource.TDXZIP and self.history_day_klines is None:
                self.history_day_klines = get_tdxzip_history(adjust=adjust)

        # ======== 预加载每日增量数据源 ========
        elif data_source == DataSource.TUSHARE or data_source == DataSource.MOOTDX:
            hc = DailyHistoryCache()
            hc.set_data_source(data_source=data_source)
            if hc.daily_history is not None:
                hc.daily_history.remove_recent_exit_right_histories(5)  # 一周数据
                hc.daily_history.download_recent_daily(20)  # 一个月数据
                # 下载后加载进内存
                start_date = datetime.datetime.strptime(start, '%Y%m%d')
                end_date = datetime.datetime.strptime(end, '%Y%m%d')
                delta = abs(end_date - start_date)
                self.cache_history = hc.daily_history.get_subset_copy(code_list, delta.days + 1)
        else:
            if self.messager is not None:
                self.messager.send_text_as_md(f'[{self.account_id}]{self.strategy_name}:\n无法识别的数据源')

    def refresh_memory_history(
        self,
        code_list: list[str],
        start: str,
        end: str,
        data_source: DataSource,
    ):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        hc = DailyHistoryCache()
        hc.set_data_source(data_source=data_source)
        if hc.daily_history is not None:
            # 重新加载进内存
            start_date = datetime.datetime.strptime(start, '%Y%m%d')
            end_date = datetime.datetime.strptime(end, '%Y%m%d')
            delta = abs(end_date - start_date)
            self.cache_history = hc.daily_history.get_subset_copy(code_list, delta.days + 1)

    # -----------------------
    # 盘后报告总结
    # -----------------------
    def daily_summary(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        curr_date = datetime.datetime.now().strftime('%Y-%m-%d')

        if self.open_today_deal_report:
            try:
                self.daily_reporter.today_deal_report(today=curr_date)
            except Exception as e:
                print('Report deal failed: ', e)
                traceback.print_exc()

        if self.open_today_hold_report:
            try:
                if self.delegate is not None:
                    positions = self.delegate.check_positions()
                    self.daily_reporter.today_hold_report(today=curr_date, positions=positions)
                else:
                    print('Missing delegate to complete reporting!')
            except Exception as e:
                print('Report position failed: ', e)
                traceback.print_exc()

        try:
            if self.delegate is not None:
                asset = self.delegate.check_asset()
                self.daily_reporter.check_asset(today=curr_date, asset=asset)
        except Exception as e:
            print('Report asset failed: ', e)
            traceback.print_exc()


    # -----------------------
    # 定时器
    # -----------------------
    def before_trade_day_wrapper(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        self.cache_quotes.clear()
        self.cache_history.clear()
        self.today_ticks.clear()
        self.history_day_klines.clear()
        self.code_list = ['000001.SH']  # 默认只有上证指数


        if self.before_trade_day is not None:
            self.before_trade_day()
            self.curr_trade_date = datetime.datetime.now().strftime('%Y-%m-%d')

    def near_trade_begin_wrapper(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        if self.near_trade_begin is not None:
            self.near_trade_begin()
            if self.before_trade_day is None:  # 没有设置before_trade_day 情况
                self.curr_trade_date = datetime.datetime.now().strftime('%Y-%m-%d')
            print(f'今日盘前准备工作已完成')

    def finish_trade_day_wrapper(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        if self.finish_trade_day is not None:
            self.finish_trade_day()

    # 检查是否完成盘前准备
    # @check_open_day
    def check_before_finished(self):
        if not check_is_open_day(datetime.datetime.now().strftime('%Y-%m-%d')):
            return

        if (
            self.before_trade_day is not None or self.near_trade_begin is not None
        ) and (
            self.curr_trade_date != datetime.datetime.now().strftime("%Y-%m-%d")
            or len(self.cache_history) < 1
        ):
            print('[ERROR]盘前准备未完成，尝试重新执行盘前函数')
            self.before_trade_day_wrapper()
            self.near_trade_begin_wrapper()
        print(f'当前交易日：[{self.curr_trade_date}]。')

    def start_scheduler_without_qmt_data(self):
        run_time_ranges = [
            # 上午时间段: 09:15:00 到 11:29:59
            {
                'hour': '9',
                'minute': '15-59',
                'second': '0-59'  # 9:15到9:59的每秒
            },
            {
                'hour': '10',
                'minute': '0-59',
                'second': '0-59'  # 10:00到10:59的每秒
            },
            {
                'hour': '11',
                'minute': '0-29',
                'second': '0-59'  # 11:00到11:29的每秒（包含59秒）
            },
            # 下午时间段: 13:00:00 到 14:59:59
            {
                'hour': '13-14',
                'minute': '0-59',
                'second': '0-59'  # 13:00到14:59的每秒
            }
        ]

        for idx, cron_params in enumerate(run_time_ranges):
            self.scheduler.add_job(self.callback_run_no_quotes, 'cron', **cron_params, id=f"run_{idx}")

        if self.before_trade_day is not None:   # 03:00 ~ 06:59
            random_hour = random.randint(0, 3) + 3
            random_minute = random.randint(0, 59)
            self.scheduler.add_job(self.before_trade_day_wrapper, 'cron', hour=random_hour, minute=random_minute)

        if self.finish_trade_day is not None:   # 16:05 ~ 16:15
            random_minute = random.randint(0, 10) + 5
            self.scheduler.add_job(self.finish_trade_day_wrapper, 'cron', hour=16, minute=random_minute)

        self.scheduler.add_job(self.prev_check_open_day, 'cron', hour=1, minute=0, second=0)
        self.scheduler.add_job(self.check_before_finished, 'cron', hour=8, minute=55) # 检查当天是否完成准备
        self.scheduler.add_job(self.callback_open_no_quotes, 'cron', hour=9, minute=14, second=59)
        self.scheduler.add_job(self.callback_close_no_quotes, 'cron', hour=11, minute=30, second=0)
        self.scheduler.add_job(self.callback_open_no_quotes, 'cron', hour=12, minute=59, second=59)
        self.scheduler.add_job(self.callback_close_no_quotes, 'cron', hour=15, minute=0, second=0)
        self.scheduler.add_job(self.daily_summary, 'cron', hour=15, minute=1, second=0)

        try:
            print('[定时器已启动]')
            self.scheduler.start()
        except KeyboardInterrupt:
            print('[手动结束进程]')
        except Exception as e:
            print('策略定时器出错：', e)
        finally:
            self.delegate.shutdown()

    def start_scheduler_with_qmt_data(self):
        # 教学说明：QMT实时数据模式的定时任务调度器
        print(f"📅 [教学说明] 配置QMT模式定时任务调度器...")

        # 教学说明：QMT调度器任务详解
        print("🔧 [教学说明] QMT调度器核心任务:")
        print("  ├─ 实时行情订阅与数据处理")
        print("  ├─ 定时交易信号执行")
        print("  ├─ 数据源稳定性监控")
        print("  └─ 异常情况自动恢复")

        print("📁 [教学说明] 相关配置文件:")
        print("  ├─ run_wencai_qmt.py  - 主策略配置 (BuyConf/SellConf)")
        print("  ├─ tools/utils_cache.py - 交易日历与缓存管理")
        print("  └─ credentials.py     - 交易账户与API配置")

        # 默认定时任务列表
        cron_jobs = [
            ['01:00', self.prev_check_open_day, None],          # 凌晨检查交易日
            ['08:30', self.near_trade_begin_wrapper, None],     # 盘前准备工作
            ['08:55', self.check_before_finished, None],        # 检查盘前准备完成情况
            ['09:14', self.subscribe_tick, None],               # 开盘前开启行情订阅
            ['11:31', self.unsubscribe_tick, (True, )],         # 午间休市暂停订阅
            ['12:59', self.subscribe_tick, (True, )],           # 午后开盘前恢复订阅
            ['15:01', self.unsubscribe_tick, None],             # 收盘后关闭订阅
            ['15:02', self.daily_summary, None],                # 盘后总结报告
        ]
        if self.open_tick:
            cron_jobs.append(['09:10', self.clean_ticks_history, None])      # 开盘前清理Tick缓存
            cron_jobs.append(['15:10', self.save_tick_history, None])       # 收盘后保存Tick数据
            print(f"📊 [教学说明] 已添加Tick数据管理任务")

        if self.before_trade_day is not None:
            cron_jobs.append([  # 03:00 ~ 06:59
                f'0{random.randint(0, 3) + 3}:{random.randint(0, 59)}',
                self.before_trade_day_wrapper,
                None,
            ])  # random 时间为了跑多个策略时防止短期预加载数据流量压力过大
            print(f"🌅 [教学说明] 已添加盘前数据预加载任务 (随机时间03:00-06:59)")

        if self.finish_trade_day is not None:
            cron_jobs.append([  # 16:05 ~ 16:15
                f'16:{random.randint(0, 10) + 5}',
                self.finish_trade_day_wrapper,
                None,
            ])
            print(f"🌆 [教学说明] 已添加盘后数据整理任务 (随机时间16:05-16:15)")

        # 教学说明：数据源中断检查时间点，确保QMT数据流的稳定性
        # 数据中断会导致策略无法正常执行，需要定期检查并重新订阅
        monitor_time_list = [
            '09:35', '09:45', '09:55', '10:05', '10:15', '10:25',
            '10:35', '10:45', '10:55', '11:05', '11:15', '11:25',
            '13:05', '13:15', '13:25', '13:35', '13:45', '13:55',
            '14:05', '14:15', '14:25', '14:35', '14:45', '14:55',
        ]
        print(f"🔍 [教学说明] 已配置数据源监控检查点，共{len(monitor_time_list)}个")
        if self.use_ap_scheduler:
            # 教学说明：使用新版 APScheduler 进行定时任务调度
            print(f"⚙️ [教学说明] 正在注册APScheduler定时任务...")
            for cron_job in cron_jobs:
                [hr, mn] = cron_job[0].split(':')
                if cron_job[2] is None:
                    self.scheduler.add_job(cron_job[1], 'cron', hour=hr, minute=mn)
                else:
                    self.scheduler.add_job(cron_job[1], 'cron', hour=hr, minute=mn, args=list(cron_job[2]))

            # 教学说明：在09:29:30重新订阅Tick数据，防止开盘后数据断流
            print(f"🔄 [教学说明] 添加Tick重订阅任务 (09:29:30)，防止开盘数据断流")
            self.scheduler.add_job(self.resubscribe_tick, 'cron', hour=9, minute=29, second=30)

            for monitor_time in monitor_time_list:
                [hr, mn] = monitor_time.split(':')
                self.scheduler.add_job(self.callback_monitor, 'cron', hour=hr, minute=mn)

            # 教学说明：启动定时调度器，开始执行所有定时任务
            try:
                print(f"🚀 [教学说明] 定时调度器启动成功，共注册{len(cron_jobs) + len(monitor_time_list) + 1}个定时任务")
                print(f"⏰ [教学说明] 系统将按预设时间表自动执行各项任务")

                # 教学说明：显示调度器执行流程
                print("\n🔄 [教学说明] =============== 调度器执行流程 =============")
                print("📡 [实时行情处理]:")
                print("  QMT数据流 → callback_sub_whole() → 行情缓存 → 策略执行")
                print("⚡ [策略执行]:")
                print("  execute_strategy() → 时间窗口判断 → 买入/卖出扫描")
                print("📊 [买入流程]:")
                print("  问财选股 → 价格检查 → 买入决策 → 委托下单")
                print("📉 [卖出流程]:")
                print("  持仓监控 → 技术分析 → 卖出信号 → 委托下单")
                print("🔍 [监控机制]:")
                print("  数据流监控 → 异常检测 → 自动重连 → 故障恢复")

                print('\n💡 [教学说明] 关键文件定位:')
                print('  调度器配置: delegate/xt_subscriber.py:639')
                print('  策略主入口: run_wencai_qmt.py:255')
                print('  买入策略: trader/buyer.py:94')
                print('  卖出策略: trader/seller_groups.py')

                print('[定时器已启动]')
                self.scheduler.start()
            except KeyboardInterrupt:
                print('🛑 [教学说明] 用户手动中断程序执行')
                print('[手动结束进程]')
            except Exception as e:
                print(f"❌ [教学说明] 定时调度器发生异常: {e}")
                print('策略定时器出错：', e)
            finally:
                print(f"🔧 [教学说明] 正在关闭交易委托连接...")
                self.delegate.shutdown()
                try:
                    import sys
                    sys.exit(0)
                except SystemExit:
                    import os
                    os._exit(0)
        else:
            # 旧版 schedule
            import schedule
            for cron_job in cron_jobs:
                if cron_job[2] is None:
                    schedule.every().day.at(cron_job[0]).do(cron_job[1])
                else:
                    schedule.every().day.at(cron_job[0]).do(cron_job[1], list(cron_job[2])[0])

            for monitor_time in monitor_time_list:
                schedule.every().day.at(monitor_time).do(self.callback_monitor)

            # 盘中执行需要补齐，旧代码都放在策略文件里了这里就不重复执行破坏老代码
            # if '08:05' < temp_time < '15:30' and check_is_open_day(temp_date):
            #     self._before_trade_day()
            #     if '09:15' < temp_time < '11:30' or '13:00' <= temp_time < '14:57':
            #         self.subscribe_tick()  # 重启时如果在交易时间则订阅Tick

            # 旧代码还有别的要执行，没有放在 before_trade_day 所以这里虽然不优雅单也先注释掉
            # try:
            #     while True:
            #         schedule.run_pending()
            #         time.sleep(1)
            # except KeyboardInterrupt:
            #     print('[手动结束进程]')
            # finally:
            #     schedule.clear()
            #     self.delegate.shutdown()

    def start_scheduler(self):
        # 教学说明：启动定时调度器，这是整个量化策略的引擎核心
        print(f"⏰ [教学说明] 正在启动策略定时调度器...")
        print(f"📋 [教学说明] 调度器模式: {'外部数据源模式' if self.use_outside_data else 'QMT实时数据模式'}")

        if self.use_ap_scheduler:
            temp_now = datetime.datetime.now()
            temp_date = temp_now.strftime('%Y-%m-%d')
            temp_time = temp_now.strftime('%H:%M')
            # 教学说明：盘中启动补丁，如果在交易时间内启动，需要补执行盘前准备
            if '08:05' < temp_time < '15:30' and check_is_open_day(temp_date):
                print(f"🔄 [教学说明] 检测到盘中启动，正在补执行盘前准备工作...")
                self.before_trade_day_wrapper()
                self.near_trade_begin_wrapper()
                if '09:15' < temp_time < '11:30' or '13:00' <= temp_time < '14:57':
                    print(f"📡 [教学说明] 检测到交易时间内，立即开启行情订阅...")
                    self.subscribe_tick()  # 重启时如果在交易时间则订阅Tick

        if self.use_outside_data:
            print(f"🌐 [教学说明] 启动外部数据源模式的调度器...")
            self.start_scheduler_without_qmt_data()
            return
        else:
            print(f"📈 [教学说明] 启动QMT实时数据模式的调度器...")
            self.start_scheduler_with_qmt_data()

    # -----------------------
    # 检查是否交易日
    # -----------------------
    def prev_check_open_day(self):
        now = datetime.datetime.now()
        curr_date = now.strftime('%Y-%m-%d')
        curr_time = now.strftime('%H:%M')
        print(f'[{curr_time}]', end='')
        is_open_day = check_is_open_day(curr_date)
        self.delegate.is_open_day = is_open_day


# -----------------------
# 持仓自动发现
# -----------------------
def update_position_held(lock: threading.Lock, delegate: XtDelegate, path: str):
    with lock:
        positions = delegate.check_positions()
        held_info = load_json(path)

        # 添加未被缓存记录的持仓：默认当日买入
        for position in positions:
            if position.can_use_volume > 0:
                if position.stock_code not in held_info.keys():
                    held_info[position.stock_code] = {InfoItem.DayCount: 0}

        # 删除已清仓的held_info记录
        if positions is not None and len(positions) > 0:
            position_codes = [position.stock_code for position in positions]
            print('当前持仓：', position_codes)
            holding_codes = list(held_info.keys())
            for code in holding_codes:
                if len(code) > 0 and code[0] != '_' and (code not in position_codes):
                    del held_info[code]
        else:
            print('当前空仓！')

        save_json(path, held_info)


# -----------------------
# 临时获取quotes
# -----------------------
def xt_get_ticks(code_list: list[str]) -> dict[str, any]:
    # http://docs.thinktrader.net/pages/36f5df/#%E8%8E%B7%E5%8F%96%E5%85%A8%E6%8E%A8%E6%95%B0%E6%8D%AE
    return xtdata.get_full_tick(code_list)
