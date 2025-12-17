"""
买入策略管理模块

提供量化交易系统的智能买入策略功能：
- 仓位控制：基于总仓位和单仓资金的买入管理
- 资金管理：可用资金计算和买入数量的精确控制
- 风险控制：多层次的风险控制机制和买入限制
- 订单管理：市价单和限价单的智能选择
- 历史记录：买入历史的记录和去重机制

买入策略架构：
- 基础买入器：BaseBuyer提供标准买入策略实现
- 限额买入器：LimitedBuyer提供按比例买入功能
- 参数驱动：通过配置参数控制买入行为
- 委托适配：适配不同交易平台的委托接口

核心功能特性：
- 智能仓位：基于当前持仓和可用资金的仓位计算
- 涨跌停保护：自动识别涨停并切换为限价单
- 多重限制：总仓位、单日买入、单次买入的多重限制
- 去重机制：当日已买入股票的自动去重
- 风险控制：可配置的风险控制和资金管理

买入限制机制：
- 总仓位限制：slot_count控制最大持仓股票数量
- 资金限制：slot_capacity控制每仓最大资金投入
- 单日限制：daily_buy_max控制单日最大买入数量
- 单次限制：once_buy_limit控制单次选股买入数量
- 持仓检查：避免重复买入已持仓股票

价格控制策略：
- 市价优先：优先使用市价单确保成交
- 溢价保护：通过order_premium确保市价单成交
- 涨跌停处理：自动识别涨停并使用限价单
- 价格限制：买入价格不超过涨停价格
- 精确计算：基于昨收价的精确涨停价计算

订单类型处理：
- 市价买入：normal情况下使用市价单快速成交
- 限价买入：涨停时自动切换为限价单
- 记录回调：买入成功后记录到交易回调系统
- 日志输出：详细的买入操作日志记录

风险控制功能：
- 资金保护：确保买入不超过可用资金
- 仓位保护：避免超出总仓位限制
- 涨跌停保护：防止在涨停价无效买入
- 重复保护：避免同日重复买入同一股票
- 零头处理：可选的全仓买入零头处理

与其他模块的关系：
- delegate/base_delegate.py: 交易委托的执行接口
- tools/utils_basic.py: 涨停价格计算工具
- trader/pools.py: 选股结果的数据来源
- callback系统：买入记录的回调处理
"""

import math
import datetime
import logging

from delegate.base_delegate import BaseDelegate

from tools.utils_basic import get_limit_up_price, debug


DEFAULT_BUY_REMARK = '买入委托'


class SelectionItem:
    BUY_PRICE = 'price'
    BUY_VOLUME = 'volume'
    LAST_CLOSE = 'lastClose'    # 昨日收盘价主要用来判断涨跌停


class BaseBuyer:
    def __init__(
        self,
        strategy_name: str,
        delegate: BaseDelegate,
        parameters,     # Buy Configuration
    ):
        self.strategy_name = strategy_name
        self.delegate = delegate

        self.order_premium = parameters.order_premium
        self.slot_capacity = parameters.slot_capacity
        self.slot_count = parameters.slot_count
        self.daily_buy_max = parameters.daily_buy_max
        self.once_buy_limit = parameters.once_buy_limit

        self.risk_control = parameters.risk_control if hasattr(parameters, 'risk_control') else False

    def buy_selections(
        self,
        selections: dict[str, dict],    # { code: quote } 注意 Python 3.7 之前的dict不按照插入序遍历
        today_buy: dict[str, set],      # 当日已买入记录
        curr_date: str,
        positions: list,
        remark: str = DEFAULT_BUY_REMARK,
        available_cash: float = 0.0,
        all_in_buy: bool = False,   # 最后一点零头不够也要尝试买入
        all_market: bool = True,    # 全部都是市价单
    ) -> dict[str, set]:
        # 教学说明：买入决策主函数，执行智能买入策略
        if len(selections) > 0:
            print(f"💰 [教学说明] 开始买入决策流程，候选股票: {len(selections)}只")
            final_capacity = self.slot_capacity

            # 教学说明：获取当前持仓状态和资金信息
            position_codes = [position.stock_code for position in positions]
            position_count = self.delegate.get_holding_position_count(positions)
            print(f"📊 [教学说明] 当前持仓: {position_count}/{self.slot_count} 个仓位")

            # 教学说明：检查可用资金
            if available_cash <= 0.0:
                available_cash = self.delegate.check_asset().cash
            print(f"💵 [教学说明] 可用资金: {available_cash:.2f}元")
            available_slot = available_cash // final_capacity
            print(f"🏠 [教学说明] 资金可买仓位: {available_slot}个")

            # 教学说明：处理资金不足的特殊情况
            if available_slot == 0 and all_in_buy:
                print(f"💸 [教学说明] 资金不足，启用全仓买入模式")
                final_capacity = available_cash - 1.00
                available_slot = 1

            # 教学说明：初始化当日买入记录
            if curr_date not in today_buy:
                today_buy[curr_date] = set()
            today_bought_count = len(today_buy[curr_date])
            remaining_daily_limit = self.daily_buy_max - today_bought_count
            print(f"📅 [教学说明] 当日已买入: {today_bought_count}只，剩余可买: {remaining_daily_limit}只")
            available_slot = min(available_slot, remaining_daily_limit)

            # 教学说明：计算最终可买入数量
            empty_slots = self.slot_count - position_count
            print(f"🏠 [教学说明] 空余仓位: {empty_slots}个")

            buy_count = max(0, empty_slots)                           # 确认剩余的仓位
            buy_count = min(buy_count, available_slot)                  # 确认现金够用
            buy_count = min(buy_count, len(selections))               # 确认选出的股票够用
            buy_count = min(buy_count, self.once_buy_limit)           # 限制一秒内下单数量
            buy_count = int(buy_count)

            print(f"🎯 [教学说明] 最终决定买入: {buy_count}只股票")

            # 教学说明：开始逐只股票执行买入操作
            bought_count = 0
            for code in selections:  # 依次买入
                if buy_count > 0:
                    if code in today_buy[curr_date]:
                        print(f"🚫 [教学说明] {code} 今日已买入，跳过")
                        continue

                    selection = selections[code]
                    price = round(selection[SelectionItem.BUY_PRICE], 4)
                    last_close = round(selection[SelectionItem.LAST_CLOSE], 4)

                    # 教学说明：计算买入数量
                    if SelectionItem.BUY_VOLUME in selection:
                        buy_volume = selection[SelectionItem.BUY_VOLUME]
                    else:
                        buy_volume = math.floor(final_capacity / price / 100) * 100

                    # 教学说明：检查买入条件
                    if buy_volume <= 0:
                        print(f"💸 [教学说明] {code} 资金不足一手，跳过")
                        debug(f'[{code} 不够一手]')
                    elif code in position_codes:
                        print(f"📊 [教学说明] {code} 已在持仓中，跳过")
                        debug(f'[{code} 正在持仓]')
                    else:
                        # 教学说明：执行买入下单
                        buy_count = buy_count - 1
                        increase_rate = (price - last_close) / last_close
                        print(f"✅ [教学说明] 买入 {code}: 价格 {price:.2f}元, 数量 {buy_volume}股, 涨幅 {increase_rate:.2%}")

                        # 如果今天未被选股过 and 目前没有持仓则记录（意味着不会加仓
                        self.order_buy(
                            code=code, price=price, last_close=last_close,
                            volume=buy_volume, remark=remark, market=all_market)

                        # 记录买入历史
                        if code not in today_buy[curr_date]:
                            today_buy[curr_date].add(code)
                            bought_count += 1
                            logging.warning(f"记录选股 {code}\t现价: {price:.2f}")
                else:
                    break

            print(f"📈 [教学说明] 本轮买入完成，实际买入 {bought_count}只股票")
        else:
            print("❌ [教学说明] 没有候选股票，跳过买入流程")
        return today_buy

    def order_buy(
        self,
        code: str,
        price: float,
        last_close: float,
        volume: int,
        remark: str,
        market: bool = True,
        log: bool = True,
    ):
        # 教学说明：执行具体买入下单操作
        print(f"🛒 [教学说明] 开始执行 {code} 的买入下单操作")

        buy_volume = volume
        # 教学说明：风险控制检查，确保不超过单仓资金限制
        if self.risk_control and buy_volume > self.slot_capacity / price:
            original_volume = buy_volume
            buy_volume = math.floor(self.slot_capacity / price / 100) * 100
            print(f"🛡️ [教学说明] 风险控制：{code} 超过单仓限制，买入量从 {original_volume}股 调整为 {buy_volume}股")
            logging.warning(f'{code} 超过风险控制，买入量调整为 {buy_volume} 股')

        if buy_volume > 0:
            order_price = price + self.order_premium
            limit_price = get_limit_up_price(code, last_close)
            total_amount = order_price * buy_volume

            print(f"💰 [教学说明] 订单信息: 买入价 {order_price:.2f}元, 数量 {buy_volume}股, 总金额 {total_amount:.2f}元")

            # 教学说明：判断是否为涨停状态
            is_limit_up = order_price > limit_price
            if is_limit_up:
                print(f"📈 [教学说明] {code} 已涨停或接近涨停，使用限价单买入")

            if market:
                buy_type = '市买'
                if is_limit_up:
                    # 如果涨停了只能挂限价单
                    print(f"🔒 [教学说明] 执行限价买入委托 (涨停价: {limit_price:.2f}元)")
                    self.delegate.order_limit_open(
                        code=code,
                        price=limit_price,
                        volume=buy_volume,
                        remark=remark,
                        strategy_name=self.strategy_name)
                else:
                    print(f"⚡ [教学说明] 执行市价买入委托")
                    self.delegate.order_market_open(
                        code=code,
                        price=min(order_price, limit_price),
                        volume=buy_volume,
                        remark=remark,
                        strategy_name=self.strategy_name)
            else:
                buy_type = '限买'
                print(f"🔒 [教学说明] 执行限价买入委托")
                self.delegate.order_limit_open(
                    code=code,
                    price=min(order_price, limit_price),
                    volume=buy_volume,
                    remark=remark,
                    strategy_name=self.strategy_name)

            # 教学说明：记录委托信息
            if log:
                logging.warning(f'{buy_type}委托 {code} \t现价:{price:.3f} {buy_volume}股')

            # 教学说明：回调记录
            if self.delegate.callback is not None:
                self.delegate.callback.record_order(
                    order_time=datetime.datetime.now().timestamp(),
                    code=code,
                    price=price,
                    volume=buy_volume,
                    side=f'{buy_type}委托',
                    remark=remark)

            print(f"✅ [教学说明] {code} 买入委托已提交")
        else:
            print(f"❌ [教学说明] {code} 挂单买量为0，不执行委托")


class LimitedBuyer(BaseBuyer):
    def __init__(
        self,
        strategy_name: str,
        delegate: BaseDelegate,
        parameters,
        volume_ratio: float = 1.00,  # 每次下单的 volume 是 capacity 的百分比可以调整
    ):
        super().__init__(
            strategy_name,
            delegate,
            parameters,
        )
        self.volume_ratio = volume_ratio

    def order_buy(
        self,
        code: str,
        price: float,
        last_close: float,
        volume: int,
        remark: str,
        market: bool = True,
        log: bool = True,
    ):
        volume = math.floor(volume / 100 * self.volume_ratio) * 100     # 向下取整
        super().order_buy(code, price, last_close, volume, remark, market, log)
