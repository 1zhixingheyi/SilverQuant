"""
卖出策略组合模块

提供多种卖出策略的灵活组合功能：
- 策略组合：多个独立卖出策略的组合管理
- 优先级控制：策略执行的优先级和短路机制
- 动态初始化：基于继承关系的策略自动初始化
- 参数传递：统一的参数传递给所有子策略
- 执行控制：策略执行的协调和控制逻辑

策略组合架构：
- 基础框架：GroupSellers提供策略组合的基础框架
- 多重继承：通过多重继承实现策略的组合
- 自动初始化：基于继承关系的策略组件自动初始化
- 执行协调：协调多个策略的执行顺序和逻辑

核心功能特性：
- 短路机制：一旦有策略触发卖出，后续策略不再执行
- 自动发现：基于继承关系的策略组件自动发现
- 参数透传：统一参数传递给所有策略组件
- 状态管理：策略执行状态的统一管理
- 扩展性：支持新的策略组合和组件扩展

预设策略组合：
- ClassicGroupSeller：传统三重卖出策略（硬止损+回落止盈+收益率）
- ClassicMAGroupSeller：均线增强策略（传统+均线卖出）
- ShieldGroupSeller：监控型策略（硬止损+回落止盈）
- WencaiGroupSeller：问财策略（硬止损+回落止盈+收益率+换仓）
- DeepseekGroupSeller：DeepSeek AI策略（硬止损+换仓+回落止盈）

专业策略组合：
- LTT2GroupSeller：龙抬头策略（开盘日+换仓+收益率+CCI+均线）
- T3BLGroupSeller：三倍量突破策略（硬止损+换仓+回落止盈+均线）
- PTLSGroupSeller：平台绿缩策略（硬止损+上涨阻断+回落止盈+收益率+换仓+均线）
- JQTPGroupSeller：金雀突破策略（回落止盈+下跌卖出+硬止损+威廉斯+收益率）

策略执行逻辑：
- 优先级顺序：按照继承列表的顺序执行策略
- 短路控制：第一个策略触发卖出后立即停止
- 参数传递：统一的参数接口传递给所有策略
- 状态反馈：策略执行结果的统一返回

与其他模块的关系：
- trader/seller_components.py: 独立卖出策略组件的基础实现
- trader/buyer.py: 与买入策略的协调配合
- delegate/*: 交易委托的执行接口
- tools/utils_ding.py: 卖出信号的消息通知
"""

from trader.seller_components import *


class GroupSellers:
    def __init__(self):
        pass

    def group_init(self, strategy_name, delegate, parameters):
        for parent in self.__class__.__bases__:
            if parent.__name__ != 'GroupSellers':
                parent.__init__(self, strategy_name, delegate, parameters)
        print('>> 初始化完成')

    def group_check_sell(
            self, code: str, quote: Dict, curr_date: str, curr_time: str,
            position: XtPosition, held_day: int, max_price: Optional[float],
            history: Optional[pd.DataFrame], ticks: Optional[list[list]], extra: any,
    ) -> bool:
        sold = False
        for parent in self.__class__.__bases__:
            if parent.__name__ != 'GroupSellers':
                if sold:
                    break
                else:
                    sold = parent.check_sell(
                        self, code=code, quote=quote, curr_date=curr_date, curr_time=curr_time,
                        position=position, held_day=held_day, max_price=max_price,
                        history=history, ticks=ticks, extra=extra,
                    )
        return sold


# 传统卖出
class ClassicGroupSeller(GroupSellers, HardSeller, FallSeller, ReturnSeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)


# 均线卖出
class ClassicMAGroupSeller(GroupSellers, HardSeller, FallSeller, ReturnSeller, MASeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)


# 监控卖出
class ShieldGroupSeller(GroupSellers, HardSeller, FallSeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)


# 问财卖出
class WencaiGroupSeller(GroupSellers, HardSeller, FallSeller, ReturnSeller, SwitchSeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)


# Deepseek
class DeepseekGroupSeller(GroupSellers, HardSeller, SwitchSeller, FallSeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)


# 龙抬头
class LTT2GroupSeller(GroupSellers, HardSeller, OpenDaySeller, SwitchSeller, ReturnSeller, CCISeller, MASeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)


# 三倍量突破
class T3BLGroupSeller(GroupSellers, HardSeller, SwitchSeller, FallSeller, MASeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)


# 平台绿缩
class PTLSGroupSeller(GroupSellers, HardSeller, UppingBlocker, FallSeller, ReturnSeller, SwitchSeller, MASeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)


# 金雀突破
class JQTPGroupSeller(GroupSellers, FallSeller, DropSeller, HardSeller, WRSeller, ReturnSeller):
    def __init__(self, strategy_name, delegate, parameters):
        super().__init__()
        self.group_init(strategy_name, delegate, parameters)

    def check_sell(self, code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra):
        self.group_check_sell(code, quote, curr_date, curr_time, position, held_day, max_price, history, ticks, extra)
