"""
掘金交易委托代理

提供基于掘金平台的交易委托执行功能：
- 完整交易支持：市价/限价、买入/卖出、撤单等交易操作
- 实时查询：资产、订单、持仓信息的实时查询
- 消息通知：交易结果的钉钉消息推送
- 状态管理：交易状态和持仓状态的跟踪管理
- 回调机制：支持交易事件回调注册

委托代理架构：
- 接口实现：实现BaseDelegate抽象基类的所有交易接口
- 数据封装：掘金原生数据到标准格式的转换
- 消息集成：与钉钉消息推送的无缝集成
- 错误处理：交易异常和网络异常的容错机制

核心功能特性：
- 多订单类型：市价单、限价单支持
- 实时通知：交易执行结果的实时消息推送
- 账户管理：支持多账户的资产和持仓管理
- 订单管理：订单查询、撤单、批量撤单功能
- 持仓筛选：有效持仓的智能筛选和统计

交易操作支持：
- 市价买入/卖出：order_market_open/close
- 限价买入/卖出：order_limit_open/close
- 撤单操作：order_cancel_all/buy/sell
- 资产查询：check_asset
- 订单查询：check_orders
- 持仓查询：check_positions

数据模型转换：
- GmAsset：掘金Cash到标准资产格式
- GmOrder：掘金Order到标准订单格式
- GmPosition：掘金Position到标准持仓格式
- 代码转换：股票代码与掘金符号互转

消息通知格式：
- 标准格式：包含账户ID、策略名称、操作类型
- 详细信息：股票代码、名称、数量、价格
- 时间戳：精确到秒的交易时间
- 状态标识：买卖类型和操作状态的简短标识

与其他模块的关系：
- delegate/base_delegate.py: 继承交易委托抽象基类
- delegate/gm_callback.py: 交易回调事件处理
- credentials.py: 掘金账户和令牌配置
- tools/utils_ding.py: 交易消息通知推送
- tools/utils_cache.py: 股票名称缓存查询
"""

import datetime
from typing import List

from gmtrade.api import *
from gmtrade.pb.account_pb2 import Cash, Position, Order

from delegate.base_delegate import BaseDelegate
from delegate.gm_callback import GmCallback

from credentials import GM_ACCOUNT_ID, GM_CLIENT_TOKEN

from tools.constants import MSG_OUTER_SEPARATOR, MSG_INNER_SEPARATOR
from tools.utils_basic import code_to_gmsymbol, gmsymbol_to_code
from tools.utils_cache import StockNames
from tools.utils_ding import BaseMessager


DEFAULT_GM_SERVER_HOST = 'api.myquant.cn:9000'
DEFAULT_GM_STRATEGY_NAME = '模拟策略'


class GmAsset:
    def __init__(self, cash: Cash, account_id: str = ''):
        self.account_type = 0
        self.account_id = account_id
        self.cash = round(cash.available, 3)
        self.frozen_cash = round(cash.order_frozen, 3)
        self.market_value = round(cash.frozen, 3)
        self.total_asset = round(cash.nav, 3)


class GmOrder:
    def __init__(self, order: Order):
        self.account_id = order.account_id
        self.stock_code = gmsymbol_to_code(order.symbol)
        self.order_id = order.order_id
        self.order_volume = order.volume
        self.price = order.price
        self.order_type = order.order_type
        self.order_status = order.status


class GmPosition:
    def __init__(self, position: Position):
        self.account_id = position.account_id
        self.stock_code = gmsymbol_to_code(position.symbol)
        self.volume = position.volume
        self.can_use_volume = position.available
        self.open_price = position.vwap
        self.market_value = position.amount


class GmDelegate(BaseDelegate):
    def __init__(
        self,
        account_id: str = None,
        callback: GmCallback = None,
        ding_messager: BaseMessager = None,
    ):
        super().__init__()
        self.ding_messager = ding_messager
        self.stock_names = StockNames()

        self.account_id = '**' + str(account_id)[-4:]

        set_endpoint(DEFAULT_GM_SERVER_HOST)
        set_token(GM_CLIENT_TOKEN)

        self.account = account(account_id=GM_ACCOUNT_ID, account_alias='')
        login(self.account)

        if callback is not None:
            self.callback = callback
            self.callback.register_callback()

    def shutdown(self):
        self.callback.unregister_callback()

    def check_asset(self) -> GmAsset:
        cash: Cash = get_cash(self.account)
        return GmAsset(cash, GM_ACCOUNT_ID)

    def check_orders(self) -> List[GmOrder]:
        orders = get_orders(self.account)
        return [GmOrder(order) for order in orders]

    def check_positions(self) -> List[GmPosition]:
        positions = get_positions(self.account)
        return [GmPosition(position) for position in positions if position.volume > 0]

    def order_market_open(
        self,
        code: str,
        price: float,
        volume: int,
        remark: str,
        strategy_name: str = DEFAULT_GM_STRATEGY_NAME,
    ):
        """
        [
            account_id: "189ca421-49db-11ef-9fa8-00163e022aa6"
            cl_ord_id: "83fe1b04-4afa-11ef-97f5-00163e022aa6"
            order_id: "83fe1b0b-4afa-11ef-97f5-00163e022aa6"
            ex_ord_id: "83fe1b0b-4afa-11ef-97f5-00163e022aa6"
            symbol: "SHSE.600000"
            side: 1
            position_effect: 1
            order_type: 2
            order_qualifier: 3
            status: 1
            order_style: 1
            volume: 100
            created_at {
              seconds: 1721962528
              nanos: 852249292
            }
            updated_at {
              seconds: 1721962528
              nanos: 852249292
            }
        ]
        """
        orders = order_volume(
            symbol=code_to_gmsymbol(code),
            price=price,
            volume=volume,
            side=OrderSide_Buy,
            order_type=OrderType_Market,
            order_qualifier=OrderQualifier_B5TC,
            position_effect=PositionEffect_Open,
        )
        print(f'[{remark}]{code}')
        if self.ding_messager is not None:
            name = self.stock_names.get_name(code)
            self.ding_messager.send_text_as_md(
                f'[{self.account_id}]{strategy_name} {remark}{MSG_OUTER_SEPARATOR}'
                f'{datetime.datetime.now().strftime("%H:%M:%S")} 市买 {code}{MSG_INNER_SEPARATOR}'
                f'{name} {volume}股 {price:.2f}元',
                '[MB]')
        return orders

    def order_market_close(
        self,
        code: str,
        price: float,
        volume: int,
        remark: str,
        strategy_name: str = DEFAULT_GM_STRATEGY_NAME,
    ):
        orders = order_volume(
            symbol=code_to_gmsymbol(code),
            price=price,
            volume=volume,
            side=OrderSide_Sell,
            order_type=OrderType_Market,
            order_qualifier=OrderQualifier_B5TC,
            position_effect=PositionEffect_Close,
        )
        print(f'[{remark}]{code}')
        if self.ding_messager is not None:
            name = self.stock_names.get_name(code)
            self.ding_messager.send_text_as_md(
                f'[{self.account_id}]{strategy_name} {remark}{MSG_OUTER_SEPARATOR}'
                f'{datetime.datetime.now().strftime("%H:%M:%S")} 市卖 {code}{MSG_INNER_SEPARATOR}'
                f'{name} {volume}股 {price:.2f}元',
                '[MS]')
        return orders

    def order_limit_open(
        self,
        code: str,
        price: float,
        volume: int,
        remark: str,
        strategy_name: str = DEFAULT_GM_STRATEGY_NAME,
    ):
        """
        [
            account_id: "189ca421-49db-11ef-9fa8-00163e022aa6"
            cl_ord_id: "83fe1b04-4afa-11ef-97f5-00163e022aa6"
            order_id: "83fe1b0b-4afa-11ef-97f5-00163e022aa6"
            ex_ord_id: "83fe1b0b-4afa-11ef-97f5-00163e022aa6"
            symbol: "SHSE.600000"
            side: 1
            position_effect: 1
            order_type: 2
            order_qualifier: 3
            status: 1
            order_style: 1
            volume: 100
            created_at {
              seconds: 1721962528
              nanos: 852249292
            }
            updated_at {
              seconds: 1721962528
              nanos: 852249292
            }
        ]
        """
        orders = order_volume(
            symbol=code_to_gmsymbol(code),
            price=price,
            volume=volume,
            side=OrderSide_Buy,
            order_type=OrderType_Limit,
            position_effect=PositionEffect_Open,
        )
        print(f'[{remark}]{code}')
        if self.ding_messager is not None:
            name = self.stock_names.get_name(code)
            self.ding_messager.send_text_as_md(
                f'[{self.account_id}]{strategy_name} {remark}{MSG_OUTER_SEPARATOR}'
                f'{datetime.datetime.now().strftime("%H:%M:%S")} 限买 {code}{MSG_INNER_SEPARATOR}'
                f'{name} {volume}股 {price:.2f}元',
                '[LB]')
        return orders

    def order_limit_close(
        self,
        code: str,
        price: float,
        volume: int,
        remark: str,
        strategy_name: str = DEFAULT_GM_STRATEGY_NAME,
    ):
        orders = order_volume(
            symbol=code_to_gmsymbol(code),
            price=price,
            volume=volume,
            side=OrderSide_Sell,
            order_type=OrderType_Limit,
            position_effect=PositionEffect_Close,
        )
        print(f'[{remark}]{code}')
        if self.ding_messager is not None:
            name = self.stock_names.get_name(code)
            self.ding_messager.send_text_as_md(
                f'[{self.account_id}]{strategy_name} {remark}{MSG_OUTER_SEPARATOR}'
                f'{datetime.datetime.now().strftime("%H:%M:%S")} 限卖 {code}{MSG_INNER_SEPARATOR}'
                f'{name} {volume}股 {price:.2f}元',
                '[LS]')
        return orders

    def order_cancel_all(self, strategy_name: str = DEFAULT_GM_STRATEGY_NAME):
        if self.ding_messager is not None:
            self.ding_messager.send_text_as_md(
                f'{datetime.datetime.now().strftime("%H:%M:%S")} 全撤'
                '[CA]')
        order_cancel_all()

    # order_1 = {'symbol': 'SHSE.600000', 'cl_ord_id': 'cl_ord_id_1', 'price': 11, 'side': 1, 'order_type': 1}
    # order_2 = {'symbol': 'SHSE.600004', 'cl_ord_id': 'cl_ord_id_2', 'price': 11, 'side': 1, 'order_type': 1}
    # orders = [order_1, order_2]
    # order_cancel(wait_cancel_orders=orders)

    def order_cancel_buy(self, code: str, strategy_name: str = DEFAULT_GM_STRATEGY_NAME):
        if self.ding_messager is not None:
            name = self.stock_names.get_name(code)
            self.ding_messager.send_text_as_md(
                f'[{self.account_id}]{strategy_name} {name}{MSG_OUTER_SEPARATOR}'
                f'{datetime.datetime.now().strftime("%H:%M:%S")} 撤买 {code}'
                '[CB]')

        orders = get_orders()
        candidate = []
        for order in orders:
            if order.side == OrderSide_Buy:
                candidate.append({
                    'symbol': code_to_gmsymbol(code),
                    'cl_ord_id': order.cl_ord_id,
                })
        order_cancel(candidate)

    def order_cancel_sell(self, code: str, strategy_name: str = DEFAULT_GM_STRATEGY_NAME):
        if self.ding_messager is not None:
            name = self.stock_names.get_name(code)
            self.ding_messager.send_text_as_md(
                f'[{self.account_id}]{strategy_name} {name}{MSG_OUTER_SEPARATOR}'
                f'{datetime.datetime.now().strftime("%H:%M:%S")} 撤卖 {code}'
                '[CS]')

        orders = get_orders()
        candidate = []
        for order in orders:
            if order.side == OrderSide_Sell:
                candidate.append({
                    'symbol': code_to_gmsymbol(code),
                    'cl_ord_id': order.cl_ord_id,
                })
        order_cancel(candidate)

    @staticmethod
    def is_position_holding(position: GmPosition) -> bool:
        return position.volume > 0

    def get_holding_position_count(self, positions: List[GmPosition]) -> int:
        return sum(1 for position in positions if self.is_position_holding(position))
