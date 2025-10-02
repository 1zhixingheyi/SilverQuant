# SilverQuant 数据接口参考手册

**文档版本**: v1.0
**更新日期**: 2025-10-02
**维护人员**: 系统架构组

---

## 📑 目录

- [🔍 快速索引](#-快速索引)
- [1. 行情数据接口](#1-行情数据接口)
  - [1.1 AKShare 接口](#11-akshare-接口)
  - [1.2 TuShare Pro 接口](#12-tushare-pro-接口)
  - [1.3 MootDX 接口](#13-mootdx-接口)
  - [1.4 QMT(XtQuant) 接口](#14-qmtxtquant-接口)
- [2. 交易执行接口](#2-交易执行接口)
  - [2.1 QMT 交易接口](#21-qmt-交易接口)
  - [2.2 掘金量化接口](#22-掘金量化接口)
- [3. 数据存储接口](#3-数据存储接口)
  - [3.1 统一存储接口](#31-统一存储接口-抽象层)
  - [3.2 具体实现](#32-具体实现)
  - [3.3 混合存储模式](#33-混合存储模式-storagehybrid_storepy)
- [4. 选股与分析接口](#4-选股与分析接口)
  - [4.1 问财选股](#41-问财选股接口)
  - [4.2 自定义推荐服务](#42-自定义推荐服务)
  - [4.3 通达信自选股](#43-通达信自选股)
  - [4.4 历史数据管理](#44-历史数据管理-dailyhistory)
- [5. 通知推送接口](#5-通知推送接口)
  - [5.1 钉钉机器人](#51-钉钉机器人)
  - [5.2 飞书机器人](#52-飞书机器人)
- [6. 工具类接口](#6-工具类接口)
  - [6.1 数据格式转换](#61-数据格式转换-utils_basicpy)
  - [6.2 交易日期处理](#62-交易日期处理-utils_cachepy)
  - [6.3 股票名称查询](#63-股票名称查询-stocknames类)
  - [6.4 数据格式化工具](#64-数据格式化工具-utils_remotepy)

---

## 🔍 快速索引

**共 120+ 个接口** | [按功能检索](#按功能检索) | [按使用频率检索](#按使用频率检索)

### 接口统计概览

| 类别 | 数量 | 占比 | 跳转 |
|------|------|------|------|
| 行情数据接口 | 45 | 37.5% | [查看](#1-行情数据接口) |
| 交易执行接口 | 20 | 16.7% | [查看](#2-交易执行接口) |
| 数据存储接口 | 22 | 18.3% | [查看](#3-数据存储接口) |
| 选股与分析接口 | 11 | 9.2% | [查看](#4-选股与分析接口) |
| 通知推送接口 | 5 | 4.2% | [查看](#5-通知推送接口) |
| 工具类接口 | 17 | 14.2% | [查看](#6-工具类接口) |

### 核心接口快查表

| 接口名称 | 功能 | 章节 |
|---------|------|------|
| `ak.stock_zh_a_hist()` | 股票历史日线 | [1.1](#11-akshare-接口) |
| `get_ak_daily_history()` | 统一历史数据接口 | [1.1](#11-akshare-接口) |
| `get_mootdx_quotes()` | 实时行情快照 | [1.3](#13-mootdx-接口) |
| `xtdata.subscribe_whole_quote()` | 订阅全推行情 | [1.4](#14-qmtxtquant-接口) |
| `order_stock()` | 股票委托下单 | [2.1](#21-qmt-交易接口) |
| `get_cash(account)` | 查询资金 | [2.2](#22-掘金量化接口) |
| `save_held_days()` | 保存持仓天数 | [3.1](#31-统一存储接口-抽象层) |
| `query_kline()` | 查询K线数据 | [3.1](#31-统一存储接口-抽象层) |
| `pywencai.get()` | 自然语言选股 | [4.1](#41-问财选股接口) |
| `send_text_as_md()` | 发送Markdown消息 | [5.1](#51-钉钉机器人) |

### 按功能检索

- **获取历史数据**: AKShare([1.1](#11-akshare-接口)) / TuShare([1.2](#12-tushare-pro-接口)) / MootDX([1.3](#13-mootdx-接口)) / QMT([1.4](#14-qmtxtquant-接口))
- **实时行情**: MootDX实时快照([1.3](#13-mootdx-接口)) / QMT订阅([1.4](#14-qmtxtquant-接口))
- **交易下单**: QMT交易([2.1](#21-qmt-交易接口)) / 掘金量化([2.2](#22-掘金量化接口))
- **持仓管理**: 存储接口([3](#3-数据存储接口))
- **选股筛选**: 问财([4.1](#41-问财选股接口)) / 通达信自选([4.3](#43-通达信自选股)) / 历史数据([4.4](#44-历史数据管理-dailyhistory))
- **消息通知**: 钉钉([5.1](#51-钉钉机器人)) / 飞书([5.2](#52-飞书机器人))
- **工具函数**: 格式转换([6.1](#61-数据格式转换-utils_basicpy)) / 日期处理([6.2](#62-交易日期处理-utils_cachepy)) / 名称查询([6.3](#63-股票名称查询-stocknames类))

### 按使用频率检索

#### 高频接口 (每日使用)
- `get_ak_daily_history()` - 获取历史日线 → [1.1](#11-akshare-接口)
- `get_mootdx_quotes()` - 批量实时行情 → [1.3](#13-mootdx-接口)
- `save_held_days()` / `load_held_days()` - 持仓天数管理 → [3.1](#31-统一存储接口-抽象层)
- `save_trade_record()` - 保存交易记录 → [3.1](#31-统一存储接口-抽象层)
- `query_stock_positions()` - 查询持仓 → [2.1](#21-qmt-交易接口)
- `send_text_as_md()` - 发送通知 → [5.1](#51-钉钉机器人)

#### 中频接口 (每周使用)
- `download_history_data()` - 下载历史数据 → [1.4](#14-qmtxtquant-接口)
- `get_ts_daily_histories()` - 批量日线 → [1.2](#12-tushare-pro-接口)
- `save_kline()` / `query_kline()` - K线存储 → [3.1](#31-统一存储接口-抽象层)
- `pywencai.get()` - 问财选股 → [4.1](#41-问财选股接口)

#### 低频接口 (按需使用)
- `get_stock_info_a_code_name()` - 更新代码列表 → [1.1](#11-akshare-接口)
- `init_tables()` - 初始化数据库 → [3.3](#33-mysql-存储)
- `optimize_table()` - 优化ClickHouse表 → [3.4](#34-clickhouse-存储)

---

## 1. 行情数据接口

### 1.1 AKShare 接口

**平台**: AKShare (免费开源数据接口)
**代码位置**: `tools/utils_remote.py:226-272`
**官方文档**: https://akshare.akfamily.xyz

#### 股票历史日线数据

| 项目 | 内容 |
|------|------|
| **接口名称** | `ak.stock_zh_a_hist()` |
| **封装函数** | `get_ak_daily_history(code, start_date, end_date, columns, adjust)` |
| **参数说明** | `code`: 股票代码(如 `000001.SZ`)<br>`start_date`: 开始日期(`20240101`)<br>`end_date`: 结束日期(`20241231`)<br>`adjust`: 复权类型(`'qfq'`/`'hfq'`/`''`) |
| **返回字段** | `datetime`: 日期(int格式)<br>`open`: 开盘价<br>`high`: 最高价<br>`low`: 最低价<br>`close`: 收盘价<br>`volume`: 成交量(手)<br>`amount`: 成交额(元) |
| **返回类型** | `pd.DataFrame` 或 `None` |
| **配置要求** | `credentials.py` - `AKSHARE_ENABLED = True` |
| **限制说明** | 免费无限制，但有频率限制(建议0.5秒间隔) |
| **使用场景** | 日线级别历史数据回测、策略开发 |
| **注意事项** | 复权方式为全历史复权后截取，保留两位小数 |

#### ETF 基金历史数据

| 项目 | 内容 |
|------|------|
| **接口名称** | `ak.fund_etf_hist_em()` |
| **封装函数** | `get_ak_daily_history(code, start_date, end_date, columns, adjust)` |
| **参数说明** | 同股票接口，支持ETF代码(如 `510300.SH`) |
| **返回字段** | 同股票接口 |
| **注意事项** | ETF数据保留三位小数，成交量略有不同 |

#### 股票代码列表

| 项目 | 内容 |
|------|------|
| **接口名称** | `ak.stock_info_a_code_name()` |
| **封装位置** | `delegate/daily_history.py:79-82` |
| **返回字段** | `code`: 股票代码<br>`name`: 股票名称 |
| **使用场景** | 获取全市场股票列表，批量下载数据 |

#### 除权除息公告

| 项目 | 内容 |
|------|------|
| **接口名称** | `ak.news_trade_notify_dividend_baidu()` |
| **封装位置** | `delegate/daily_history.py:341-350` |
| **参数说明** | `date`: 日期字符串(`'20240101'`) |
| **返回字段** | 包含股票代码、除权除息日期等 |
| **使用场景** | 自动更新除权除息股票的复权数据 |

---

### 1.2 TuShare Pro 接口

**平台**: TuShare Pro (需积分，高频稳定)
**代码位置**: `tools/utils_remote.py:292-351`, `reader/tushare_agent.py`
**官方文档**: https://tushare.pro/document/2?doc_id=27

#### 单票日线数据

| 项目 | 内容 |
|------|------|
| **接口名称** | `pro.daily()` |
| **封装函数** | `get_ts_daily_history(code, start_date, end_date, columns)` |
| **参数说明** | `code`: TuShare格式代码(如 `000001.SZ`)<br>`start_date`: `'20240101'`<br>`end_date`: `'20241231'` |
| **返回字段** | `datetime`: 交易日期(int)<br>`open/high/low/close`: OHLC价格<br>`volume`: 成交量(股)<br>`amount`: 成交额(元) |
| **返回类型** | `pd.DataFrame` 或 `None` |
| **配置要求** | `credentials.py` - `TUSHARE_TOKEN = 'your_token'` |
| **限制说明** | 免费版每分钟200次，每天2000次<br>单次查询最多8000行数据 |
| **使用场景** | 需要稳定数据源的生产环境 |
| **注意事项** | 免费版不支持复权，需额外调用复权接口 |

#### 批量日线数据 (高效)

| 项目 | 内容 |
|------|------|
| **接口名称** | `pro.daily(ts_code='code1,code2,...')` |
| **封装函数** | `get_ts_daily_histories(codes, start_date, end_date, columns)` |
| **参数说明** | `codes`: 股票代码列表(最多990个) |
| **返回类型** | `dict[str, pd.DataFrame]` - 键为股票代码 |
| **使用场景** | 批量更新全市场数据，提升效率 |
| **限制说明** | 单次最多990个代码，总行数不超过8000 |
| **实现位置** | `delegate/daily_history.py:191-226` |

---

### 1.3 MootDX 接口

**平台**: MootDX (基于通达信本地数据)
**代码位置**: `tools/utils_remote.py:356-415`, `tools/utils_mootdx.py`
**官方文档**: https://github.com/mootdx/mootdx

#### 历史K线数据

| 项目 | 内容 |
|------|------|
| **接口名称** | `client.bars()` |
| **封装函数** | `get_mootdx_daily_history(code, start_date, end_date, columns, adjust)` |
| **参数说明** | `code`: 股票代码<br>`frequency`: K线周期(`'day'`/`'1m'`/`'5m'`)<br>`offset`: 总K线数<br>`start`: 跳过的K线数 |
| **返回字段** | 同AKShare接口 |
| **配置要求** | `credentials.py` - `TDX_FOLDER = 'E:/new_tdx'`<br>需本地安装通达信客户端 |
| **限制说明** | 依赖本地通达信数据，无网络限制 |
| **使用场景** | 本地高速数据访问，盘中实时策略 |
| **注意事项** | 北交所(920xxx)部分股票可能有脏数据<br>复权为截断后复权，保留三位小数 |

#### 实时行情快照

| 项目 | 内容 |
|------|------|
| **接口名称** | `client.quotes()` |
| **封装函数** | `get_mootdx_quotes(code_list)` |
| **参数说明** | `symbol_list`: 股票代码列表(不含市场后缀) |
| **返回字段** | `time`: 毫秒时间戳<br>`lastPrice`: 最新价<br>`open/high/low`: OHLC<br>`volume/amount`: 成交量额<br>`askPrice[1-5]`: 卖五档价格<br>`bidPrice[1-5]`: 买五档价格<br>`askVol[1-5]`: 卖五档量<br>`bidVol[1-5]`: 买五档量 |
| **返回类型** | `dict[str, dict]` - 键为股票代码 |
| **使用场景** | 盘中实时行情获取，无需QMT客户端 |
| **代码位置** | `tools/utils_remote.py:55-107` |

#### 除权除息数据

| 项目 | 内容 |
|------|------|
| **接口名称** | `client.xdxr()` |
| **使用位置** | `tools/utils_remote.py:381-394` |
| **返回字段** | `year/month/day`: 除权日期<br>其他送转配股信息 |
| **使用场景** | 配合K线数据进行前复权/后复权计算 |

---

### 1.4 QMT(XtQuant) 接口

**平台**: 国金证券QMT量化交易终端
**代码位置**: `xtquant/xtdata.py`, `delegate/xt_subscriber.py`
**配置要求**: `credentials.py` - `QMT_CLIENT_PATH`

#### 行情订阅接口

| 接口名称 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `xtdata.subscribe_quote()` | 订阅股票行情 | `stock_list`: 代码列表<br>`period`: 周期(`'tick'`/`'1m'`/`'1d'`) | 无(通过回调返回) |
| `xtdata.subscribe_whole_quote()` | 订阅全推行情 | `stock_list`: 代码列表 | 无(全量推送) |
| `xtdata.unsubscribe_quote()` | 取消订阅 | `stock_list`: 代码列表 | 无 |
| `xtdata.run()` | 启动行情接收循环 | 无 | 阻塞运行 |

**使用示例** (`delegate/xt_subscriber.py:12`):
```python
from xtquant import xtdata

xtdata.subscribe_whole_quote(stock_list=['000001.SZ', '600000.SH'])
xtdata.run()  # 启动行情接收
```

#### 历史数据下载

| 接口名称 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `xtdata.download_history_data()` | 下载历史K线 | `stock_list`: 代码列表<br>`period`: 周期<br>`start_time`: 开始时间<br>`end_time`: 结束时间 | 下载完成状态 |
| `xtdata.get_market_data()` | 获取历史数据 | `field_list`: 字段列表<br>`stock_list`: 代码列表<br>`period`: 周期<br>`start_time/end_time`: 时间范围 | `dict[stock_code, np.ndarray]` |
| `xtdata.get_local_data()` | 获取本地缓存数据 | 同上 | 同上 |

**可用字段**: `open`, `high`, `low`, `close`, `volume`, `amount`, `settle`, `openInterest`

#### Level-2 深度行情

| 接口名称 | 功能说明 | 返回字段 |
|---------|---------|---------|
| `xtdata.get_l2_quote()` | Level-2行情快照 | 十档盘口、总买卖量等 |
| `xtdata.get_l2_order()` | Level-2委托明细 | 委托价格、数量、方向 |
| `xtdata.get_l2_transaction()` | Level-2逐笔成交 | 成交价、量、时间 |
| `xtdata.get_full_tick()` | 完整Tick数据 | 全部盘口变化记录 |

#### 基础数据接口

| 接口名称 | 功能说明 | 返回值 |
|---------|---------|--------|
| `xtdata.get_trading_dates()` | 交易日历 | 交易日列表 |
| `xtdata.get_stock_list_in_sector()` | 板块成分股 | 股票代码列表 |
| `xtdata.get_sector_list()` | 板块列表 | 板块名称列表 |
| `xtdata.get_index_weight()` | 指数权重 | 成分股及权重 |
| `xtdata.get_instrument_detail()` | 合约详情 | 交易规则、乘数等 |
| `xtdata.get_financial_data()` | 财务数据 | 财报指标 |
| `xtdata.get_divid_factors()` | 除权除息因子 | 复权因子 |

---

## 2. 交易执行接口

### 2.1 QMT 交易接口

**代码位置**: `delegate/xt_delegate.py`
**配置要求**: `credentials.py` - `QMT_ACCOUNT_ID`, `QMT_CLIENT_PATH`

#### 连接管理接口

| 接口名称 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `connect(callback)` | 连接QMT交易服务器 | `callback`: 回调对象 | `(XtQuantTrader, bool)` |
| `reconnect()` | 重新连接 | 无 | `None` |
| `keep_connected()` | 保持连接(循环检测) | 无 | `None` (阻塞) |
| `shutdown()` | 关闭连接 | 无 | `None` |

#### 下单接口

| 接口名称 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `order_submit()` | 同步下单 | `stock_code`: 股票代码<br>`order_type`: 买卖方向<br>`order_volume`: 数量(股)<br>`price_type`: 价格类型<br>`price`: 委托价格<br>`strategy_name`: 策略名称<br>`order_remark`: 备注 | `bool` |
| `order_submit_async()` | 异步下单 | 同上 | `bool` |
| `order_market_open()` | 市价买入(封装) | `code`: 股票代码<br>`price`: 参考价<br>`volume`: 数量<br>`remark`: 备注<br>`strategy_name`: 策略名称 | `bool` |
| `order_market_close()` | 市价卖出(封装) | 同上 | `bool` |
| `order_limit_open()` | 限价买入(封装) | 同上 + `price`: 限价 | `bool` |
| `order_limit_close()` | 限价卖出(封装) | 同上 + `price`: 限价 | `bool` |

#### 撤单接口

| 接口名称 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `order_cancel()` | 同步撤单 | `order_id`: 委托编号 | `int` 撤单结果 |
| `order_cancel_async()` | 异步撤单 | `order_id`: 委托编号 | `int` 撤单结果 |
| `order_cancel_all()` | 撤销所有委托 | `strategy_name`: 策略名称 | `None` |
| `order_cancel_buy()` | 撤销指定股票买单 | `code`: 股票代码<br>`strategy_name`: 策略名称 | `None` |
| `order_cancel_sell()` | 撤销指定股票卖单 | `code`: 股票代码<br>`strategy_name`: 策略名称 | `None` |

#### 查询接口

| 接口名称 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `check_asset()` | 查询资金 | 无 | `XtAsset` 对象 |
| `check_order()` | 查询单个委托 | `order_id`: 委托编号 | `XtOrder` 对象 |
| `check_orders()` | 查询委托列表 | `cancelable_only`: 仅可撤单 | `List[XtOrder]` |
| `check_positions()` | 查询持仓 | 无 | `List[XtPosition]` |
| `check_ipo_data()` | 查询新股数据 | 无 | `dict` |

#### 数据结构说明

**XtAsset 字段**:
- `cash`: 可用资金
- `frozen_cash`: 冻结资金
- `market_value`: 持仓市值
- `total_asset`: 总资产

**XtOrder 字段**:
- `stock_code`: 股票代码
- `order_id`: 委托编号
- `order_volume`: 委托数量
- `price`: 委托价格
- `order_type`: 买卖方向
- `order_status`: 委托状态
- `price_type`: 价格类型

**XtPosition 字段**:
- `stock_code`: 股票代码
- `volume`: 持仓数量
- `can_use_volume`: 可用数量
- `open_price`: 开仓均价
- `market_value`: 持仓市值

**价格类型常量**:
- `xtconstant.FIX_PRICE`: 限价单
- `xtconstant.MARKET_PRICE`: 市价单
- `xtconstant.BEST_PRICE`: 对手价

**订单方向**:
- `xtconstant.STOCK_BUY`: 买入
- `xtconstant.STOCK_SELL`: 卖出

**使用示例**:
```python
from delegate.xt_delegate import XtDelegate

delegate = XtDelegate(account_id='8886163456')
delegate.connect(callback=None)

# 市价买入
delegate.order_market_open(
    code='000001.SZ',
    price=10.50,
    volume=1000,
    remark='开仓',
    strategy_name='my_strategy'
)

# 查询资金
asset = delegate.check_asset()
print(f"可用资金: {asset.cash}")

# 查询持仓
positions = delegate.check_positions()
for pos in positions:
    print(f"{pos.stock_code}: {pos.volume}股")
```

---

### 2.2 掘金量化接口

**平台**: 掘金量化模拟盘/实盘
**代码位置**: `delegate/gm_delegate.py`
**配置要求**: `credentials.py` - `GM_CLIENT_TOKEN`, `GM_ACCOUNT_ID`
**服务器**: `api.myquant.cn:9000`

#### 账户查询接口

| 接口名称 | 功能说明 | 返回值 | 封装类 |
|---------|---------|--------|--------|
| `get_cash(account)` | 查询资金账户 | `Cash` 对象 | `GmAsset` |
| `get_positions(account)` | 查询持仓 | `Position[]` | `GmPosition[]` |
| `get_orders(account)` | 查询委托 | `Order[]` | `GmOrder[]` |

**GmAsset 字段**:
- `cash`: 可用资金
- `frozen_cash`: 冻结资金
- `market_value`: 持仓市值
- `total_asset`: 总资产

**GmPosition 字段**:
- `stock_code`: 股票代码
- `volume`: 持仓数量
- `can_use_volume`: 可用数量
- `open_price`: 开仓均价
- `market_value`: 持仓市值

#### 交易下单接口

| 接口名称 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `order_volume()` | 按数量下单 | `symbol`: GM格式代码<br>`price`: 委托价格<br>`volume`: 数量<br>`side`: 买卖方向<br>`order_type`: 订单类型 | `Order` 对象 |
| `order_market_open()` | 市价买入(封装) | `code`: 股票代码<br>`price`: 参考价<br>`volume`: 数量<br>`remark`: 备注 | `Order` 对象 |
| `order_market_close()` | 市价卖出(封装) | 同上 | `Order` 对象 |

**订单类型常量**:
- `OrderType_Market`: 市价单
- `OrderType_Limit`: 限价单
- `OrderSide_Buy`: 买入
- `OrderSide_Sell`: 卖出
- `PositionEffect_Open`: 开仓
- `PositionEffect_Close`: 平仓

**代码示例** (`gm_delegate.py:124-141`):
```python
orders = order_volume(
    symbol=code_to_gmsymbol(code),
    price=price,
    volume=volume,
    side=OrderSide_Buy,
    order_type=OrderType_Market,
    order_qualifier=OrderQualifier_B5TC,  # 最优五档即时成交剩余撤销
    position_effect=PositionEffect_Open,
)
```

---

## 3. 数据存储接口

**代码位置**: `storage/` 目录
**配置文件**: `storage/config.py`, `credentials.py`

### 3.1 统一存储接口 (抽象层)

**基类**: `BaseDataStore` (`storage/base_store.py`)
**设计理念**: 所有存储后端必须实现的统一接口,确保向后兼容性

#### 持仓状态操作 (HOT layer)

| 接口方法 | 功能说明 | 参数 | 返回值 | 性能目标 |
|---------|---------|------|--------|---------|
| `get_held_days()` | 查询持仓天数 | `code`: 股票代码<br>`account_id`: 账户ID | `int` 或 `None` | <1ms |
| `update_held_days()` | 更新持仓天数 | `code`: 股票代码<br>`days`: 天数<br>`account_id`: 账户ID | `None` | <1ms |
| `all_held_inc()` | 所有持仓天数+1 | `account_id`: 账户ID | `bool` (防重复) | <10ms |
| `delete_held_days()` | 删除持仓记录 | `code`: 股票代码<br>`account_id`: 账户ID | `None` | <1ms |

**使用场景**: 每日盘前批量增加持仓天数,策略中查询止盈止损

#### 价格跟踪操作 (HOT layer)

| 接口方法 | 功能说明 | 参数 | 返回值 | 性能目标 |
|---------|---------|------|--------|---------|
| `get_max_price()` | 查询历史最高价 | `code`: 股票代码<br>`account_id`: 账户ID | `float` 或 `None` | <1ms |
| `update_max_price()` | 更新最高价 | `code`: 股票代码<br>`price`: 价格<br>`account_id`: 账户ID | `None` | <1ms |
| `get_min_price()` | 查询历史最低价 | `code`: 股票代码<br>`account_id`: 账户ID | `float` 或 `None` | <1ms |
| `update_min_price()` | 更新最低价 | `code`: 股票代码<br>`price`: 价格<br>`account_id`: 账户ID | `None` | <1ms |

**使用场景**: 实时跟踪回撤率,计算浮动盈亏

#### 交易记录操作 (WARM layer)

| 接口方法 | 功能说明 | 参数 | 返回值 | 性能目标 |
|---------|---------|------|--------|---------|
| `record_trade()` | 记录交易 | `code`: 股票代码<br>`direction`: 买卖方向<br>`price`: 成交价<br>`volume`: 数量<br>`amount`: 成交额<br>`account_id`: 账户ID<br>`trade_date`: 交易日期 | `None` | <10ms |
| `query_trades()` | 查询交易记录 | `account_id`: 账户ID<br>`code`: 股票代码(可选)<br>`start_date`: 开始日期(可选)<br>`end_date`: 结束日期(可选)<br>`limit`: 记录数限制 | `List[dict]` | <100ms |
| `aggregate_trades()` | 聚合统计 | `account_id`: 账户ID<br>`group_by`: 聚合维度(`'code'`/`'date'`)<br>`start_date`: 开始日期<br>`end_date`: 结束日期 | `pd.DataFrame` | <500ms |

**使用场景**: 记录每笔交易,生成交易报表,计算手续费

#### K线数据操作 (COOL layer)

| 接口方法 | 功能说明 | 参数 | 返回值 | 性能目标 |
|---------|---------|------|--------|---------|
| `get_kline()` | 查询K线数据 | `code`: 股票代码<br>`start_date`: 开始日期<br>`end_date`: 结束日期<br>`period`: 周期(`'1d'`/`'1m'`/`'5m'`) | `pd.DataFrame` | <100ms |
| `batch_get_kline()` | 批量查询K线 | `codes`: 股票代码列表<br>`start_date`: 开始日期<br>`end_date`: 结束日期<br>`period`: 周期 | `Dict[str, pd.DataFrame]` | <1s |

**返回字段**: `datetime`, `open`, `high`, `low`, `close`, `volume`, `amount`

**使用场景**: 回测引擎加载历史数据,策略计算技术指标

#### 账户管理操作

| 接口方法 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `create_account()` | 创建账户 | `account_id`: 账户ID<br>`initial_capital`: 初始资金<br>`account_type`: 账户类型 | `None` |
| `get_account()` | 查询账户信息 | `account_id`: 账户ID | `dict` 或 `None` |
| `update_account_capital()` | 更新资金 | `account_id`: 账户ID<br>`cash`: 可用资金<br>`market_value`: 持仓市值<br>`total_asset`: 总资产 | `None` |

**账户字段**: `account_id`, `cash`, `frozen_cash`, `market_value`, `total_asset`, `updated_at`

#### 策略参数操作

| 接口方法 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `create_strategy()` | 创建策略 | `strategy_name`: 策略名称<br>`description`: 描述<br>`account_id`: 绑定账户ID | `None` |
| `get_strategy_params()` | 获取策略参数 | `strategy_name`: 策略名称<br>`account_id`: 账户ID | `dict` |
| `save_strategy_params()` | 保存策略参数 | `strategy_name`: 策略名称<br>`params`: 参数字典<br>`account_id`: 账户ID | `None` |
| `compare_strategy_params()` | 对比参数变更 | `strategy_name`: 策略名称<br>`account_id`: 账户ID<br>`new_params`: 新参数 | `dict` (差异) |

**使用场景**: 策略参数版本管理,回测参数保存

#### 系统维护操作

| 接口方法 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `health_check()` | 健康检查 | 无 | `dict` (状态信息) |
| `close()` | 关闭连接 | 无 | `None` |

**health_check 返回字段**:
- `status`: `'healthy'` / `'degraded'` / `'unhealthy'`
- `latency_ms`: 响应延迟(毫秒)
- `storage_type`: 存储类型
- `error_message`: 错误信息(如有)

### 3.2 具体实现

#### Redis 存储 (`storage/redis_store.py`)

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `REDIS_HOST` | `localhost` | Redis服务器地址 |
| `REDIS_PORT` | `6379` | 端口 |
| `REDIS_DB` | `0` | 数据库编号 |
| `REDIS_PASSWORD` | `''` | 密码(可选) |

**数据结构**:
- `held_days`: Hash - `hset('silverquant:held_days', code, days)`
- `max_prices`: Hash - `hset('silverquant:max_prices', code, price)`
- `trade_records`: List - `lpush('silverquant:trade_records', json)`
- `kline:{code}`: List - 每个股票独立存储

#### MySQL 存储 (`storage/mysql_store.py`)

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `MYSQL_HOST` | `localhost` | MySQL服务器 |
| `MYSQL_PORT` | `3306` | 端口 |
| `MYSQL_DATABASE` | `silverquant_storage` | 数据库名 |
| `MYSQL_USER` | `root` | 用户名 |
| `MYSQL_PASSWORD` | `860721` | 密码 |

**数据表结构**:

```sql
-- 持仓天数表
CREATE TABLE held_days (
    code VARCHAR(20) PRIMARY KEY,
    days INT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 交易记录表
CREATE TABLE trade_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATE NOT NULL,
    code VARCHAR(20) NOT NULL,
    direction VARCHAR(10),
    price DECIMAL(10,3),
    volume INT,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trade_date (trade_date),
    INDEX idx_code (code)
);

-- 账户信息表
CREATE TABLE accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    cash DECIMAL(15,2),
    market_value DECIMAL(15,2),
    total_asset DECIMAL(15,2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### ClickHouse 存储 (`storage/clickhouse_store.py`)

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `CLICKHOUSE_HOST` | `127.0.0.1` | ClickHouse服务器 |
| `CLICKHOUSE_PORT` | `9000` | TCP端口 |
| `CLICKHOUSE_DATABASE` | `silverquant_storage` | 数据库名 |
| `CLICKHOUSE_USER` | `default` | 用户名 |
| `CLICKHOUSE_PASSWORD` | `860721` | 密码 |

**数据表结构** (时序优化):

```sql
-- K线数据表
CREATE TABLE kline_data (
    code String,
    datetime Date,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume UInt64,
    amount Float64,
    INDEX idx_datetime datetime TYPE minmax GRANULARITY 3
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(datetime)
ORDER BY (code, datetime);

-- 交易记录表 (时序分析)
CREATE TABLE trade_records_timeseries (
    trade_datetime DateTime,
    code String,
    direction String,
    price Float64,
    volume UInt32,
    amount Float64,
    strategy String,
    account_id String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(trade_datetime)
ORDER BY (trade_datetime, code);
```

#### MinIO 对象存储

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `MINIO_HOST` | `localhost` | MinIO服务器 |
| `MINIO_PORT` | `9001` | 端口 |
| `MINIO_ACCESS_KEY` | `lianghua_minio` | 访问密钥 |
| `MINIO_SECRET_KEY` | `liuyan860721` | 密钥 |
| `MINIO_BUCKET` | `lianghua-minio` | 存储桶名称 |

**存储路径规范**:
- `backups/{date}/held_days.json`
- `backups/{date}/trade_records.csv`
- `historical-data/{year}/{month}/{code}.parquet`

### 3.3 混合存储模式 (`storage/hybrid_store.py`)

**配置**: `DATA_STORE_MODE = 'hybrid'`

| 数据类型 | HOT (Redis) | COOL (MySQL) | WARM (ClickHouse) | COLD (MinIO) |
|---------|------------|--------------|-------------------|--------------|
| 持仓天数 | ✓ 实时读写 | ✓ 定时同步 | - | ✓ 每日备份 |
| 最高/最低价 | ✓ 实时跟踪 | ✓ 快照 | - | ✓ 归档 |
| 交易记录 | ✓ 今日记录 | ✓ 近期记录 | ✓ 全量分析 | ✓ 长期归档 |
| K线数据 | ✓ 当日Tick | - | ✓ 历史全量 | ✓ 原始文件 |
| 账户信息 | ✓ 实时状态 | ✓ 持久化 | - | ✓ 每日快照 |

**双写机制**: 写入Redis同时异步写入MySQL，保证数据一致性
**自动降级**: 数据库异常时自动降级到文件模式(`file_store.py`)

---

## 4. 选股与分析接口

### 4.1 问财选股接口

**代码位置**: `tools/utils_remote.py:115-122`, `selector/select_wencai.py`

| 项目 | 内容 |
|------|------|
| **接口名称** | `pywencai.get()` |
| **参数说明** | `query`: 自然语言查询条件<br>`perpage`: 每页数量(最大100)<br>`loop`: 是否自动翻页 |
| **查询示例** | `"市盈率小于20 且 市值大于100亿"`<br>`"连续3日涨停"`<br>`"MACD金叉 且 成交量放大"` |
| **返回字段** | `股票代码`, `股票名称`, 及查询相关指标 |
| **返回类型** | `pd.DataFrame` |
| **使用场景** | 基于条件的快速选股，策略初步筛选 |
| **限制说明** | 有反爬虫限制，建议间隔查询 |

### 4.2 自定义推荐服务

**代码位置**: `tools/utils_remote.py:130-138`
**配置**: `credentials.py` - `RECOMMEND_HOST`, `AUTHENTICATION`

| 项目 | 内容 |
|------|------|
| **接口协议** | RESTful API |
| **请求方式** | `GET` |
| **接口路径** | `/stocks/get_list/{key}` |
| **参数** | `key`: 查询键(如 `hot_20250101`)<br>`auth`: 认证token |
| **返回格式** | JSON - `["000001.SZ", "600000.SH", ...]` |
| **使用场景** | 接入自建推荐系统、第三方选股服务 |

### 4.3 通达信自选股

**代码位置**: `tools/utils_remote.py:30-47`

| 接口函数 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `get_tdx_zxg_code()` | 读取自选股 | `filename`: 自选股文件路径 | `list[str]` |
| `set_tdx_zxg_code()` | 写入自选股 | `data`: 股票代码列表<br>`filename`: 文件路径 | 无 |

**默认文件路径**: `{TDX_FOLDER}/T0002/blocknew/ZXG.blk`

### 4.4 历史数据管理 (DailyHistory)

**代码位置**: `delegate/daily_history.py`

| 接口方法 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `download_all_to_disk()` | 全量下载历史数据 | `renew_code_list`: 是否更新代码列表 | `None` |
| `download_recent_daily()` | 增量更新近期数据 | `days`: 更新天数(1-30) | `None` |
| `download_single_daily()` | 补单日数据 | `target_date`: 目标日期(`'20240101'`) | `None` |
| `load_history_from_disk_to_memory()` | 加载到内存 | `auto_update`: 自动补缺失 | `None` |
| `get_subset_copy()` | 获取子集副本 | `codes`: 代码列表<br>`days`: 天数 | `dict[str, DataFrame]` |
| `get_code_list()` | 获取代码列表 | `force_download`: 强制下载<br>`prefixes`: 前缀筛选 | `list[str]` |
| `remove_recent_exit_right_histories()` | 删除除权股票 | `days`: 回溯天数 | `None` |

**使用场景**:
- 批量下载全市场历史数据
- 每日增量更新数据
- 回测引擎加载数据到内存

**使用示例**:
```python
from delegate.daily_history import DailyHistory, DataSource

# 初始化历史数据管理器
history = DailyHistory(data_source=DataSource.MOOTDX)

# 全量下载(首次使用)
history.download_all_to_disk(renew_code_list=True)

# 增量更新近5日
history.download_recent_daily(days=5)

# 加载到内存
history.load_history_from_disk_to_memory()

# 获取指定股票的250日数据
data = history.get_subset_copy(
    codes=['000001.SZ', '600000.SH'],
    days=250
)
```

---

## 5. 通知推送接口

### 5.1 钉钉机器人

**代码位置**: `tools/utils_ding.py`
**配置**: `credentials.py` - `DING_SECRET`, `DING_TOKENS`
**申请文档**: https://github.com/silver6wings/SilverQuant#申请钉钉机器人

| 接口方法 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `send_text()` | 发送纯文本 | `text`: 消息内容 | `bool` |
| `send_text_as_md()` | 发送Markdown | `text`: Markdown内容<br>`title`: 标题 | `bool` |
| `send_link()` | 发送链接卡片 | `title`, `text`, `message_url`, `pic_url` | `bool` |

**消息格式示例**:
```python
messager.send_text_as_md(
    f'[账户ID]{strategy_name} 交易提醒\n'
    f'{datetime.now().strftime("%H:%M:%S")} 市买 000001.SZ\n'
    f'平安银行 1000股 10.50元',
    '[MB]'
)
```

### 5.2 飞书机器人

**代码位置**: `tools/utils_feishu.py`

| 接口方法 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `send_text()` | 发送文本 | `text`: 消息内容 | `bool` |
| `send_rich_text()` | 发送富文本 | `title`, `content` | `bool` |

---

## 6. 工具类接口

### 6.1 数据格式转换 (utils_basic.py)

**代码位置**: `tools/utils_basic.py`

| 接口函数 | 功能说明 | 参数 | 返回值 | 示例 |
|---------|---------|------|--------|------|
| `code_to_symbol()` | 代码转symbol | `code`: 完整代码 | `str` (6位) | `'000001.SZ'` → `'000001'` |
| `symbol_to_code()` | symbol转代码 | `symbol`: 6位代码 | `str` | `'000001'` → `'000001.SZ'` |
| `code_to_gmsymbol()` | 转掘金格式 | `code`: 完整代码 | `str` | `'000001.SZ'` → `'SZSE.000001'` |
| `gmsymbol_to_code()` | 掘金格式转代码 | `symbol`: 掘金格式 | `str` | `'SZSE.000001'` → `'000001.SZ'` |
| `code_to_tdxsymbol()` | 转通达信格式 | `code`: 完整代码 | `str` | `'000001.SZ'` → `'0#000001'` |
| `tdxsymbol_to_code()` | 通达信格式转代码 | `symbol`: 通达信格式 | `str` | `'0#000001'` → `'000001.SZ'` |
| `is_stock()` | 判断是否股票 | `code`: 代码 | `bool` | `'000001.SZ'` → `True` |
| `is_fund_etf()` | 判断是否基金/ETF | `code`: 代码 | `bool` | `'510300.SH'` → `True` |

**使用场景**:
- 对接不同数据源时统一代码格式
- 交易接口调用前的格式转换
- 判断证券类型进行分类处理

### 6.2 交易日期处理 (utils_cache.py)

**代码位置**: `tools/utils_cache.py`

| 接口函数 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `get_prev_trading_date()` | 获取前N个交易日 | `date`: 参考日期<br>`days`: 回溯天数 | `str` (`'20240101'`) |
| `check_is_open_day()` | 检查是否交易日 | `date`: 日期字符串 | `bool` |
| `get_trading_dates()` | 获取交易日列表 | `start`: 开始日期<br>`end`: 结束日期 | `list[str]` |
| `load_pickle()` | 加载pickle缓存 | `path`: 文件路径 | `Any` |
| `save_pickle()` | 保存pickle缓存 | `path`: 文件路径<br>`data`: 数据对象 | `None` |
| `load_json()` | 加载JSON文件 | `path`: 文件路径 | `dict` |
| `save_json()` | 保存JSON文件 | `path`: 文件路径<br>`data`: 数据对象 | `None` |

**使用示例**:
```python
from tools.utils_cache import get_prev_trading_date, check_is_open_day
import datetime

# 获取前5个交易日
now = datetime.datetime.now()
prev_date = get_prev_trading_date(now, 5)
print(prev_date)  # '20241225'

# 检查今天是否交易日
today = datetime.datetime.now().strftime('%Y-%m-%d')
is_open = check_is_open_day(today)
print(f"今天{'是' if is_open else '不是'}交易日")
```

### 6.3 股票名称查询 (StockNames类)

**代码位置**: `tools/utils_cache.py`

| 接口方法 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `get_name()` | 查询股票名称 | `code`: 股票代码 | `str` 或 `code`(未找到) |
| `load_codes_and_names()` | 刷新名称缓存 | 无 | `None` |
| `get_code_list()` | 获取代码列表 | 无 | `list[str]` |
| `get_name_list()` | 获取名称列表 | 无 | `list[str]` |

**使用场景**:
- 消息推送时显示股票名称
- 生成交易报表
- UI界面展示

**使用示例**:
```python
from tools.utils_cache import StockNames

names = StockNames()  # 单例模式
name = names.get_name('000001.SZ')
print(name)  # '平安银行'
```

### 6.4 数据格式化工具 (utils_remote.py)

**代码位置**: `tools/utils_remote.py`

| 接口函数 | 功能说明 | 参数 | 返回值 |
|---------|---------|------|--------|
| `qmt_quote_to_tick()` | QMT行情转Tick | `quote`: QMT行情dict | `dict` (Tick格式) |
| `qmt_quote_to_day_kline()` | QMT行情转日K | `quote`: QMT行情dict<br>`curr_date`: 日期 | `dict` (K线格式) |
| `concat_ak_quote_dict()` | 拼接AKShare行情 | `source_df`: 源DataFrame<br>`quote`: 行情dict<br>`curr_date`: 日期 | `pd.DataFrame` |
| `append_ak_daily_row()` | 追加日K行 | `source_df`: 源DataFrame<br>`row`: 日K数据dict | `pd.DataFrame` |

**使用场景**:
- 实时行情数据格式化
- 盘中数据拼接到历史数据
- 不同数据源格式统一

---

## 附录A: 数据接口选择建议

### 行情数据源对比

| 数据源 | 优势 | 劣势 | 适用场景 |
|-------|------|------|---------|
| **AKShare** | ✓ 完全免费<br>✓ 接口丰富<br>✓ 支持ETF | △ 速度一般<br>△ 稳定性依赖网络 | 个人开发、回测研究 |
| **TuShare Pro** | ✓ 数据稳定<br>✓ 批量高效<br>✓ 财务数据完整 | ✗ 需积分/付费<br>△ 免费版限制多 | 生产环境、机构使用 |
| **MootDX** | ✓ 本地速度快<br>✓ 无网络限制<br>✓ 实时行情 | ✗ 需通达信客户端<br>△ 北交所数据不全 | 盘中实时策略 |
| **QMT** | ✓ 券商官方<br>✓ Level-2数据<br>✓ 交易一体化 | ✗ 需QMT客户端<br>✗ 仅支持合作券商 | 实盘交易、高频策略 |

### 存储方案选择

| 数据特征 | 推荐方案 | 理由 |
|---------|---------|------|
| 高频读写(持仓、盘口) | Redis | 内存速度，毫秒级响应 |
| 结构化业务(账户、订单) | MySQL | 事务支持，关系查询 |
| 大量时序(K线、Tick) | ClickHouse | 列式存储，压缩率高，查询快 |
| 长期归档(历史备份) | MinIO | 成本低，容量大 |
| 混合场景 | Hybrid模式 | 自动分层，兼顾性能与成本 |

---

## 附录B: 常见问题

### Q1: 如何切换数据源?

**答**: 修改 `credentials.py` 中的 `DATA_STORE_MODE` 配置:
```python
# 切换到 TuShare
from delegate.daily_history import DataSource
daily_history = DailyHistory(data_source=DataSource.TUSHARE)
```

### Q2: TuShare接口报错 "抱歉，您每分钟最多访问该接口200次"

**答**: 免费版限流，解决方案:
1. 降低查询频率，增加 `time.sleep(0.5)`
2. 使用批量接口 `get_ts_daily_histories()` 提升效率
3. 升级TuShare积分/付费版

### Q3: ClickHouse 写入慢怎么办?

**答**: 优化建议:
1. 批量插入，每次1000-10000行
2. 使用 `INSERT INTO ... VALUES` 而非逐行插入
3. 检查分区策略是否合理
4. 异步写入 + Redis缓冲

### Q4: 如何验证数据接口配置正确?

**答**: 运行配置验证脚本:
```bash
cd e:\AI\code_2\lianghua\SilverQuant
python storage/config.py  # 验证存储配置
python test_db_connection.py  # 测试数据库连接
```

### Q5: Docker环境下如何访问数据库?

**答**:
1. 确保Docker容器运行: `podman-compose -f deployment/docker-compose.yml ps`
2. 修改 `credentials.py` 的 host 为容器名或 `localhost`
3. 端口映射已配置: Redis(6379), MySQL(3306), ClickHouse(8123/9000)

---

## 附录C: 接口调用代码示例

### 示例1: 获取股票历史数据

```python
from tools.utils_remote import get_daily_history, DataSource, ExitRight

# 使用AKShare获取前复权日线
df = get_daily_history(
    code='000001.SZ',
    start_date='20240101',
    end_date='20241231',
    columns=['datetime', 'open', 'high', 'low', 'close', 'volume'],
    adjust=ExitRight.QFQ,
    data_source=DataSource.AKSHARE
)
print(df.head())
```

### 示例2: 批量更新全市场数据

```python
from delegate.daily_history import DailyHistory, DataSource

# 初始化历史数据管理器
daily_history = DailyHistory(data_source=DataSource.TUSHARE)

# 下载最近5日数据(增量更新)
daily_history.download_recent_daily(days=5)

# 获取指定股票的最近250日数据
data = daily_history.get_subset_copy(codes=['000001.SZ', '600000.SH'], days=250)
```

### 示例3: QMT实时行情订阅

```python
from xtquant import xtdata

def on_data(datas):
    """行情回调函数"""
    for stock_code, quote in datas.items():
        print(f"{stock_code}: 最新价={quote['lastPrice']}, 成交量={quote['volume']}")

# 订阅实时行情
stock_list = ['000001.SZ', '600000.SH']
xtdata.subscribe_whole_quote(stock_list, callback=on_data)
xtdata.run()
```

### 示例4: 混合存储模式使用

```python
from storage.hybrid_store import HybridStore

store = HybridStore()

# 保存持仓天数(自动写入Redis + MySQL)
store.save_held_days({'000001.SZ': 15, '600000.SH': 8})

# 查询K线(自动从ClickHouse读取)
kline = store.query_kline('000001.SZ', start_date='20240101', end_date='20241231')

# 保存交易记录(分层存储: Redis当日 + MySQL近期 + ClickHouse全量)
store.save_trade_record({
    'trade_date': '2025-10-02',
    'code': '000001.SZ',
    'direction': 'buy',
    'price': 10.50,
    'volume': 1000,
    'amount': 10500.0
})
```

---

**文档维护说明**:
- 接口变更时请及时更新本文档
- 新增接口请补充到对应章节
- 配置项变更需同步更新 `credentials.py` 示例

**相关文档**:
- [数据存储优化方案](../specs/001-data-storage-optimization/plan.md)
- [Docker部署指南](docker-compose.yml)
- [系统架构文档](../docs/项目介绍/量化交易系统v3重构项目核心设计思路文档-完整版.md)
