"""
问财QMT策略主程序

提供基于问财选股和QMT交易平台的量化交易策略：
- 智能选股：基于同花顺问财的自然语言选股
- 多平台支持：QMT实盘和掘金模拟盘双模式
- 完整交易流程：选股→买入→持仓→卖出的闭环管理
- 风险控制：多层次止损止盈和仓位管理
- 实时监控：交易过程的实时钉钉通知

策略架构设计：
- 模块化设计：选股器、股票池、买入器、卖出器的独立模块
- 配置驱动：通过配置类控制策略参数和运行模式
- 环境隔离：生产环境和测试环境的路径和配置分离
- 状态管理：持仓、交易记录的文件持久化

核心功能特性：
- 问财选股：支持自然语言描述的选股条件
- 黑名单过滤：ST股票和退市风险股的自动过滤
- 价格筛选：涨幅限制和最低价格的双重筛选
- 时间控制：买入卖出时间窗口的精确控制
- 仓位管理：最大持仓数和资金分配的限制

买入策略配置：
- 时间窗口：早盘选股时间段的配置
- 扫描间隔：选股扫描频率的合理设置
- 仓位控制：总仓位和单仓资金的上限
- 价格限制：涨幅限制和最低价格的保护
- 数量控制：单日买入和单次选股的数量限制

卖出策略配置：
- 硬性止损：固定比例的不可绕过止损
- 换仓策略：基于持仓天数的轮动机制
- 回落止盈：从最高点回撤的动态止盈
- 收益率管理：分层级的收益率目标管理

风险控制机制：
- 多层止损：硬性止损、换仓止损、回落止盈
- 仓位限制：总持仓数和单仓资金的双重限制
- 时间控制：买入卖出的精确时间窗口
- 价格保护：涨幅限制和最低价格的风险控制

与其他模块的关系：
- selector/select_wencai.py: 问财选股的核心实现
- delegate/xt_delegate.py: QMT实盘交易委托
- delegate/gm_delegate.py: 掘金模拟盘交易委托
- trader/pools.py: 股票池的构建和管理
- tools/utils_ding.py: 交易消息的通知推送
"""

import logging

from credentials import *
from tools.utils_basic import logging_init, is_symbol, debug
from tools.utils_cache import *
from tools.utils_ding import DingMessager
from tools.utils_remote import get_wencai_codes

from delegate.xt_subscriber import XtSubscriber, update_position_held, xt_get_ticks

from trader.pools import StocksPoolBlackWencai as Pool
from trader.buyer import BaseBuyer as Buyer
from trader.seller_groups import ClassicGroupSeller as Seller

from selector.select_wencai import get_prompt


STRATEGY_NAME = '问财QMT'
SELECT_PROMPT = get_prompt()
DING_MESSAGER = DingMessager(DING_SECRET, DING_TOKENS)
IS_PROD = False     # 生产环境标志：False 表示使用掘金模拟盘 True 表示使用QMT账户下单交易
IS_DEBUG = True     # 日志输出标记：控制台是否打印debug方法的输出

PATH_BASE = CACHE_PROD_PATH if IS_PROD else CACHE_TEST_PATH

PATH_ASSETS = PATH_BASE + '/assets.csv'         # 记录历史净值
PATH_DEAL = PATH_BASE + '/deal_hist.csv'        # 记录历史成交
PATH_HELD = PATH_BASE + '/positions.json'       # 记录持仓信息
PATH_MAXP = PATH_BASE + '/max_price.json'       # 记录建仓后历史最高
PATH_MINP = PATH_BASE + '/min_price.json'       # 记录建仓后历史最低
PATH_LOGS = PATH_BASE + '/logs.txt'             # 用来存储选股和委托操作

disk_lock = threading.Lock()                    # 操作磁盘文件缓存的锁

cache_selected: Dict[str, Set] = {}             # 记录选股历史，去重


class PoolConf:
    # white_indexes = []
    black_prompts = ['ST', '退市']
    # 教学说明：股票池配置类，定义选股的黑名单过滤条件
    # - black_prompts: 排除ST股票和退市风险股票，保护资金安全
    # - 这些股票通常具有较高的退市风险或交易限制


class BuyConf:
    # 教学说明：买入策略配置类，控制买入行为的风险和时机
    time_ranges = [['09:30', '10:30']]
    # time_ranges: 买入时间窗口，早盘开盘后30分钟是选股的黄金时间
    # 选择这个时间段的原因：开盘后价格相对稳定，有足够的时间消化信息

    # wencai 尽可能时间长些，不然会被封IP
    interval = 30           # 扫描买入间隔，60的约数：1-6, 10, 12, 15, 20, 30
    # 教学说明：interval控制选股频率，30秒间隔平衡了选股效果和API限制
    # 间隔太短容易被问财平台限制IP，太长可能错过好的买入时机

    order_premium = 0.02    # 保证市价单成交的溢价，单位（元）
    # 教学说明：order_premium是为了确保市价单能够成功成交
    # 在A股市场中，市价单需要稍微高于当前价格才能确保买入

    slot_count = 10         # 持股数量上限
    # 教学说明：slot_count控制最大持仓股票数量，分散投资风险
    # 10只股票是比较适中的数量，既能分散风险又便于管理

    slot_capacity = 10000   # 每个仓的资金上限
    # 教学说明：slot_capacity控制单个股票的最大投资金额
    # 1万元的仓位设置适合中小资金量的投资者

    daily_buy_max = 10      # 单日买入股票上限
    # 教学说明：daily_buy_max控制单日最大买入数量，避免冲动交易
    # 与slot_count配合使用，确保不会一次性买满所有仓位

    once_buy_limit = 10     # 单次选股最多买入股票数量
    # 教学说明：once_buy_limit控制单次选股的买入数量，避免追高
    # 即使选到很多好股票，也要分批买入，控制风险

    inc_limit = 1.07        # 相对于昨日收盘的涨幅限制
    # 教学说明：inc_limit设置7%的涨幅限制，避免追高
    # 涨幅过高的股票风险较大，容易回调

    min_price = 3.00        # 限制最低可买入股票的现价
    # 教学说明：min_price避免买入低价股，这些股票通常风险较高
    # 3元以下的公司多为基本面较差或经营困难的企业


class SellConf:
    time_ranges = [['09:31', '11:30'], ['13:00', '14:57']]
    interval = 1                    # 扫描卖出间隔，60的约数：1-6, 10, 12, 15, 20, 30
    order_premium = 0.02            # 保证市价单成交的溢价，单位（元）

    hard_time_range = ['09:31', '14:57']
    earn_limit = 9.999              # 硬性止盈率
    risk_limit = 1 - 0.04           # 硬性止损率
    risk_tight = 0.002              # 硬性止损率每日上移

    switch_time_range = ['09:35', '14:57']
    switch_hold_days = 1            # 持仓天数
    switch_demand_daily_up = 0.01   # 换仓上限乘数

    # 利润从最高点回落卖出
    fall_time_range = ['09:31', '14:57']
    fall_from_top = [
        (1.08, 9.99, 0.03),
        (1.02, 1.08, 0.05),
    ]

    # 涨幅超过建仓价xA，并小于建仓价xB 时，回撤涨幅的C倍卖出
    # (A, B, C)
    return_time_range = ['09:31', '14:57']
    return_of_profit = [
        (1.20, 9.99, 0.300),
        (1.08, 1.20, 0.400),
        (1.05, 1.08, 0.500),
        (1.03, 1.05, 0.600),
        (1.02, 1.03, 0.700),
    ]


# ======== 盘前 ========


def before_trade_day() -> None:
    # 教学说明：盘前准备函数，在每个交易日开始前执行必要的初始化工作
    # 这是策略正常运行的基础，确保数据状态正确

    # held_increase() -> None:
    # 教学说明：更新所有持仓股票的持有天数，这是换仓策略的重要依据
    update_position_held(disk_lock, my_delegate, PATH_HELD)
    if all_held_inc(disk_lock, PATH_HELD):
        # 教学说明：当所有股票的持仓天数都成功+1后，输出日志确认
        # 这一步对于换仓卖出策略的执行时间判断至关重要
        logging.warning('===== 所有持仓计数 +1 =====')
        print(f'All held stock day +1!')

    # refresh_code_list() -> None:
    # 教学说明：刷新股票池，获取最新的可交易股票列表
    # 股票池的动态更新确保策略能够适应市场变化
    my_pool.refresh()

    # 教学说明：获取当前持仓列表，用于行情订阅和选股过滤
    # 避免重复买入已经持有的股票
    positions = my_delegate.check_positions()
    hold_list = [position.stock_code for position in positions if is_symbol(position.stock_code)]

    # 教学说明：更新订阅器的股票代码列表，确保只订阅需要监控的股票行情
    # 这一步优化了系统资源使用，避免订阅不必要的行情数据
    my_suber.update_code_list(hold_list)


# ======== 买点 ========


def pull_stock_codes() -> List[str]:
    # 教学说明：开始执行选股流程，这是买入决策的第一步
    print("📊 [教学说明] 开始执行问财选股，获取符合条件的股票列表")
    print(f"📝 [教学说明] 选股条件: {SELECT_PROMPT}")

    # 调用问财API获取选股结果
    codes_wencai = get_wencai_codes([SELECT_PROMPT])
    print(f"📋 [教学说明] 问财返回原始选股结果: {len(codes_wencai)}只股票")

    codes_top = []

    # 教学说明：过滤黑名单股票，这是风险控制的重要环节
    print("🛡️ [教学说明] 开始黑名单过滤，排除高风险股票...")
    for code in codes_wencai:
        if code not in my_pool.cache_blacklist:
            codes_top.append(code)

    filtered_count = len(codes_wencai) - len(codes_top)
    print(f"📉 [教学说明] 黑名单过滤掉 {filtered_count}只股票，剩余 {len(codes_top)}只候选股票")

    return codes_top


def check_stock_codes(selected_codes: list[str], quotes: dict) -> dict[str, dict]:
    # 教学说明：对选出的股票进行详细的价格和条件检查
    print(f"🔍 [教学说明] 开始对 {len(selected_codes)}只候选股票进行价格和条件检查")
    selections = {}

    checked_count = 0
    passed_count = 0

    for code in selected_codes:
        checked_count += 1
        if code not in quotes:
            print(f"⚠️ [教学说明] {code} 缺少实时行情数据，跳过检查")
            debug(code, f'本次quotes没数据')
            continue

        quote = quotes[code]
        curr_price = quote['lastPrice']
        curr_open = quote['open']
        prev_close = quote['lastClose']

        # 教学说明：价格过滤检查，避免买入低价高风险股票
        if not curr_price > BuyConf.min_price:
            print(f"💰 [教学说明] {code} 当前价格 {curr_price:.2f}元 < 最低价格限制 {BuyConf.min_price}元，跳过")
            debug(code, f'价格小于{BuyConf.min_price}')
            continue

        # 教学说明：涨幅检查，避免追高风险
        increase_rate = (curr_price - prev_close) / prev_close
        if not curr_open * 0.97 <= curr_price <= prev_close * BuyConf.inc_limit:
            print(f"📈 [教学说明] {code} 涨幅 {increase_rate:.2%} 超出限制范围，跳过")
            debug(code, f'涨幅不符合区间 {curr_open} <= {curr_price} <= {prev_close * BuyConf.inc_limit}')
            continue

        # 教学说明：股票通过所有检查，加入买入候选列表
        passed_count += 1
        buy_price = max(quote['askPrice'] + [quote['lastPrice']])
        print(f"✅ [教学说明] {code} 通过检查，买入价: {buy_price:.2f}元，涨幅: {increase_rate:.2%}")

        selections[code] = {
            'price': buy_price,
            'lastClose': quote['lastClose'],
        }

    print(f"📊 [教学说明] 价格检查完成: 检查了 {checked_count}只股票，通过 {passed_count}只股票")
    return selections


def scan_buy(quotes: Dict, curr_date: str, positions: List) -> None:
    # 教学说明：买入扫描主函数，这是策略买入决策的入口点
    print(f"🚀 [教学说明] ========== 开始执行买入扫描 ({curr_date} {datetime.datetime.now().strftime('%H:%M:%S')}) ==========")

    # 获取选股结果
    selected_codes = pull_stock_codes()
    print(f'📋 [教学说明] 初步选股结果: {len(selected_codes)}只候选股票', end='')

    # 教学说明：获取实时行情数据进行详细检查
    selections = {}
    if selected_codes is not None and len(selected_codes) > 0:
        print(f"\n📡 [教学说明] 获取 {len(selected_codes)}只股票的实时行情数据...")
        once_quotes = xt_get_ticks(selected_codes)
        print(f"📡 [教学说明] 成功获取 {len(once_quotes)}只股票的行情数据")

        # 教学说明：对股票进行价格和条件检查
        selections = check_stock_codes(selected_codes, once_quotes)
    else:
        print("❌ [教学说明] 没有候选股票，跳过买入流程")

    # 教学说明：执行买入决策和下单
    global cache_selected
    print(f"💰 [教学说明] 开始执行买入决策，当前候选股票数: {len(selections)}")

    # 显示当前持仓状态
    current_positions = len([p for p in positions if is_symbol(p.stock_code)])
    print(f"📊 [教学说明] 当前持仓状态: {current_positions}/{BuyConf.slot_count} 个仓位")

    cache_selected = my_buyer.buy_selections(selections, cache_selected, curr_date, positions)
    print(f"✅ [教学说明] 买入扫描完成")


# ======== 卖点 ========


def scan_sell(quotes: Dict, curr_date: str, curr_time: str, positions: List) -> None:
    # 教学说明：卖出扫描主函数，执行所有持仓股票的卖出检查
    print(f"🔍 [教学说明] ========== 开始执行卖出扫描 ({curr_time}) ==========")

    if not positions:
        print("💼 [教学说明] 当前无持仓，跳过卖出检查")
        return

    # 教学说明：显示当前持仓状态
    holding_positions = [p for p in positions if is_symbol(p.stock_code)]
    print(f"📊 [教学说明] 当前持仓股票数: {len(holding_positions)}只")

    # 教学说明：更新历史最高价和最低价，这是回落止盈策略的基础数据
    print("📈 [教学说明] 更新持仓股票的历史最高价和最低价...")
    max_prices, held_info = update_max_prices(disk_lock, quotes, positions, PATH_MAXP, PATH_MINP, PATH_HELD)

    # 教学说明：执行多策略卖出检查
    print("⚡ [教学说明] 开始执行卖出策略检查 (硬止损+回落止盈+收益率管理+换仓)...")
    my_seller.execute_sell(quotes, curr_date, curr_time, positions, held_info, max_prices, my_suber.cache_history)
    print("✅ [教学说明] 卖出扫描完成")


# ======== 框架 ========


def execute_strategy(curr_date: str, curr_time: str, curr_seconds: str, curr_quotes: Dict) -> bool:
    # 教学说明：策略执行主函数，根据时间判断执行买入或卖出操作
    positions = my_delegate.check_positions()

    # 教学说明：检查是否在卖出时间窗口内
    for time_range in SellConf.time_ranges:
        if time_range[0] <= curr_time <= time_range[1]:
            if int(curr_seconds) % SellConf.interval == 0:
                print(f"⏰ [教学说明] 当前时间 {curr_time} 在卖出窗口内，执行卖出检查")
                scan_sell(curr_quotes, curr_date, curr_time, positions)

    # 教学说明：检查是否在买入时间窗口内
    for time_range in BuyConf.time_ranges:
        if time_range[0] <= curr_time <= time_range[1]:
            if int(curr_seconds) % BuyConf.interval == 0:
                print(f"⏰ [教学说明] 当前时间 {curr_time} 在买入窗口内，执行买入检查")
                scan_buy(curr_quotes, curr_date, positions)
                return True

    return False


if __name__ == '__main__':
    # 教学说明：程序入口点，初始化日志和启动配置
    logging_init(path=PATH_LOGS, level=logging.INFO)
    STRATEGY_NAME = STRATEGY_NAME if IS_PROD else STRATEGY_NAME + "[测]"

    # 教学说明：显示启动信息和运行模式
    print("=" * 80)
    print(f"🚀 [教学说明] 正在启动 {STRATEGY_NAME}...")
    print(f"📊 [教学说明] 运行模式: {'实盘交易' if IS_PROD else '模拟盘交易'}")
    print(f"📝 [教学说明] 选股策略: {SELECT_PROMPT}")
    print(f"⏰ [教学说明] 买入时间窗口: {BuyConf.time_ranges}")
    print(f"⏰ [教学说明] 卖出时间窗口: {SellConf.time_ranges}")
    print(f"💰 [教学说明] 最大持仓数: {BuyConf.slot_count}只")
    print(f"💰 [教学说明] 单仓资金: {BuyConf.slot_capacity}元")

    # 教学说明：系统架构总览
    print("\n🏗️ [教学说明] ================ 系统架构总览 ================")
    print("📁 [核心文件架构]")
    print("  ├─ run_wencai_qmt.py           # 策略主程序入口")
    print("  ├─ delegate/xt_subscriber.py   # QMT行情订阅和定时调度核心")
    print("  ├─ delegate/xt_delegate.py     # QMT实盘交易委托实现")
    print("  ├─ trader/buyer.py             # 买入策略管理器")
    print("  ├─ trader/seller_groups.py     # 卖出策略组合器")
    print("  ├─ trader/pools.py             # 股票池管理器")
    print("  └─ selector/select_wencai.py   # 问财智能选股工具")

    print("\n⚙️ [调度器核心组件]")
    print("  ├─ 策略执行主函数: execute_strategy()")
    print("  ├─ 盘前准备: before_trade_day()")
    print("  ├─ 行情订阅管理: subscribe_tick() / unsubscribe_tick()")
    print("  ├─ 买入扫描: scan_buy()")
    print("  ├─ 卖出扫描: scan_sell()")
    print("  └─ 盘后总结: daily_summary()")

    print("\n📅 [定时任务调度系统]")
    print("  ├─ 01:00  - 检查交易日状态")
    print("  ├─ 08:30  - 盘前数据准备")
    print("  ├─ 08:55  - 检查盘前准备状态")
    print("  ├─ 09:14  - 开启行情订阅")
    print("  ├─ 09:29:30 - Tick重订阅(防断流)")
    print("  ├─ 11:31  - 午间休市暂停订阅")
    print("  ├─ 12:59  - 午后开盘恢复订阅")
    print("  ├─ 15:01  - 收盘后关闭订阅")
    print("  ├─ 15:02  - 盘后总结报告")
    print("  └─ 每10分钟 - 数据源监控检查(24个时间点)")

    print("\n🔄 [数据流架构]")
    print("  问财选股 → 黑名单过滤 → 价格检查 → 买入决策 → 委托执行")
    print("  持仓监控 → 技术分析 → 卖出信号 → 委托执行 → 持仓更新")

    print("\n📡 [实时数据源]")
    print("  ├─ QMT实时行情数据 (主数据源)")
    print("  ├─ 同花顺问财API (选股数据)")
    print("  ├─ AKShare/TDXZIP (历史数据)")
    print("  └─ 钉钉机器人 (消息通知)")

    print("=" * 80)
    # 教学说明：根据运行模式选择不同的交易平台
    if IS_PROD:
        # 教学说明：生产模式 - 使用QMT实盘交易平台
        print("🏦 [教学说明] 初始化QMT实盘交易系统...")
        from delegate.xt_callback import XtCustomCallback
        from delegate.xt_delegate import XtDelegate

        my_callback = XtCustomCallback(
            account_id=QMT_ACCOUNT_ID,
            strategy_name=STRATEGY_NAME,
            ding_messager=DING_MESSAGER,
            disk_lock=disk_lock,
            path_deal=PATH_DEAL,
            path_held=PATH_HELD,
            path_max_prices=PATH_MAXP,
            path_min_prices=PATH_MINP,
        )
        my_delegate = XtDelegate(
            account_id=QMT_ACCOUNT_ID,
            client_path=QMT_CLIENT_PATH,
            callback=my_callback,
        )
        print("✅ [教学说明] QMT实盘交易系统初始化完成")
    else:
        # 教学说明：测试模式 - 使用掘金模拟盘交易平台
        print("🎮 [教学说明] 初始化掘金模拟盘交易系统...")
        from delegate.gm_callback import GmCallback
        from delegate.gm_delegate import GmDelegate

        my_callback = GmCallback(
            account_id=QMT_ACCOUNT_ID,
            strategy_name=STRATEGY_NAME,
            ding_messager=DING_MESSAGER,
            disk_lock=disk_lock,
            path_deal=PATH_DEAL,
            path_held=PATH_HELD,
            path_max_prices=PATH_MAXP,
            path_min_prices=PATH_MINP,
        )
        my_delegate = GmDelegate(
            account_id=QMT_ACCOUNT_ID,
            callback=my_callback,
            ding_messager=DING_MESSAGER,
        )
        print("✅ [教学说明] 掘金模拟盘交易系统初始化完成")

    # 教学说明：初始化策略组件
    print("🔧 [教学说明] 初始化策略组件...")

    print("🏊 [教学说明] 初始化股票池管理器...")
    my_pool = Pool(
        account_id=QMT_ACCOUNT_ID,
        strategy_name=STRATEGY_NAME,
        parameters=PoolConf,
        ding_messager=DING_MESSAGER,
    )

    print("💰 [教学说明] 初始化买入策略管理器...")
    my_buyer = Buyer(
        strategy_name=STRATEGY_NAME,
        delegate=my_delegate,
        parameters=BuyConf,
    )

    print("📉 [教学说明] 初始化卖出策略组合器...")
    my_seller = Seller(
        strategy_name=STRATEGY_NAME,
        delegate=my_delegate,
        parameters=SellConf,
    )

    print("📅 [教学说明] 初始化定时调度器和行情订阅器...")
    my_suber = XtSubscriber(
        account_id=QMT_ACCOUNT_ID,
        strategy_name=STRATEGY_NAME,
        delegate=my_delegate,
        path_deal=PATH_DEAL,
        path_assets=PATH_ASSETS,
        execute_strategy=execute_strategy,
        before_trade_day=before_trade_day,
        use_ap_scheduler=True,
        ding_messager=DING_MESSAGER,
        open_today_deal_report=True,
        open_today_hold_report=True,
    )

    # 教学说明：启动定时调度器，开始策略运行
    print("=" * 60)
    print("🎯 [教学说明] 策略组件初始化完成，开始启动定时调度器...")
    print("⚡ [教学说明] 系统将按照配置的时间窗口自动执行买卖扫描")
    print("📢 [教学说明] 重要交易事件将通过钉钉机器人实时通知")
    print("📚 [教学说明] 详细操作日志将保存到日志文件中")
    print("=" * 60)

    my_suber.start_scheduler()
