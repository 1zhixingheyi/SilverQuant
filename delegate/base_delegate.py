"""
交易委托抽象基类

提供量化交易系统的统一交易委托接口：
- 抽象接口：定义所有交易平台必须实现的标准接口
- 交易操作：市价/限价、买入/卖出、撤单等完整交易功能
- 查询功能：资产、订单、持仓信息的标准查询接口
- 策略支持：支持多策略并发运行的参数化设计
- 扩展性：为新交易平台的接入提供标准规范

委托代理设计模式：
- 策略模式：不同交易平台的统一接口抽象
- 模板方法：定义交易操作的标准流程
- 适配器模式：不同平台API的统一适配
- 工厂模式：支持不同委托代理的创建

核心抽象接口：
- 资产查询：check_asset - 获取账户资金信息
- 订单查询：check_orders - 获取当前委托状态
- 持仓查询：check_positions - 获取当前持仓信息
- 市价交易：order_market_open/close - 市价买入卖出
- 限价交易：order_limit_open/close - 限价买入卖出

撤单操作接口：
- 全部撤单：order_cancel_all - 撤销所有 pending 订单
- 买入撤单：order_cancel_buy - 撤销指定股票的买单
- 卖出撤单：order_cancel_sell - 撤销指定股票的卖单

持仓管理功能：
- 持仓判断：is_position_holding - 判断是否为有效持仓
- 持仓统计：get_holding_position_count - 统计持仓数量
- 筛选支持：支持仅统计股票持仓的选项

接口设计原则：
- 统一性：所有交易平台使用相同的接口签名
- 扩展性：支持新的交易平台和功能扩展
- 参数化：策略名称和备注的参数化支持
- 错误处理：统一的异常处理和错误返回机制

实现类要求：
- 必须实现所有抽象方法
- 保证线程安全性
- 处理网络异常和平台异常
- 提供详细的错误信息
- 支持实时数据更新

与其他模块的关系：
- delegate/*: 具体交易平台委托实现的基类
- trader/*: 交易策略调用的统一接口
- tools/utils_ding.py: 交易结果通知的回调接口
- 回调系统：通过callback属性实现事件回调
"""

from abc import ABC, abstractmethod


DEFAULT_STRATEGY_NAME = '空白策略'


class BaseDelegate(ABC):
    def __init__(self):
        self.callback = None

    @abstractmethod
    def check_asset(self):
        pass

    @abstractmethod
    def check_orders(self):
        pass

    @abstractmethod
    def check_positions(self):
        pass

    @abstractmethod
    def order_market_open(
        self,
        code: str,
        price: float,
        volume: int,
        remark: str,
        strategy_name: str = DEFAULT_STRATEGY_NAME,
    ):
        pass

    @abstractmethod
    def order_market_close(
        self,
        code: str,
        price: float,
        volume: int,
        remark: str,
        strategy_name: str = DEFAULT_STRATEGY_NAME,
    ):
        pass

    @abstractmethod
    def order_limit_open(
        self,
        code: str,
        price: float,
        volume: int,
        remark: str,
        strategy_name: str = DEFAULT_STRATEGY_NAME,
    ):
        pass

    @abstractmethod
    def order_limit_close(
        self,
        code: str,
        price: float,
        volume: int,
        remark: str,
        strategy_name: str = DEFAULT_STRATEGY_NAME,
    ):
        pass

    @abstractmethod
    def order_cancel_all(self, strategy_name: str = DEFAULT_STRATEGY_NAME):
        pass

    @abstractmethod
    def order_cancel_buy(self, code: str, strategy_name: str = DEFAULT_STRATEGY_NAME):
        pass

    @abstractmethod
    def order_cancel_sell(self, code: str, strategy_name: str = DEFAULT_STRATEGY_NAME):
        pass

    @staticmethod
    def is_position_holding(position: any) -> bool:
        return False

    @abstractmethod
    def get_holding_position_count(self, positions: list, only_stock: bool = False) -> int:
        return 0
