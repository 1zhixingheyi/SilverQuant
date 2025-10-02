# 第三方平台数据接口缺失清单

> **对比基准**: E:\1-WPS云文档\2-编程\docs-shared\API接口文档
> **生成日期**: 2025-10-02
> **项目状态**: SilverQuant当前实现 vs 外部API网关标准

---

## 📊 缺失接口统计

| 数据源 | 已实现 | 缺失 | 完成度 |
|--------|--------|------|--------|
| **AKShare** | 2个 | 13个 | 13% |
| **TuShare** | 2个 | 16个 | 11% |
| **QMT** | 2个 | 1个 | 67% |
| **总计** | 6个 | 30个 | 17% |

---

## 🔴 P0级 - 核心功能缺失 (必须实现)

### 1. TuShare财务数据接口 (需2000积分)

#### 1.1 财务指标查询
```python
# 缺失接口: fina_indicator()
# 外部路径: GET /api/v1/financial/indicators/{symbol}
# 功能: 获取ROE、毛利率、净利率等关键财务指标
# 使用场景: 价值投资选股、财务健康度评估
```

**必需性**: ⭐⭐⭐⭐⭐ 量化选股的基础数据

#### 1.2 每日估值指标
```python
# 缺失接口: daily_basic()
# 外部路径: GET /api/v1/financial/daily-basic
# 功能: PE、PB、PS、市值、流通市值
# 使用场景: 估值分析、市场过热/低估判断
```

**必需性**: ⭐⭐⭐⭐⭐ 日常交易决策依据

#### 1.3 综合财务数据
```python
# 缺失接口: 并行获取多种财务数据
# 外部路径: POST /api/v1/financial/comprehensive
# 功能: 一次性获取利润表、资产负债表、现金流量表
# 使用场景: 生成完整财务报告
```

**必需性**: ⭐⭐⭐⭐ 提升查询效率

#### 1.4 配额管理
```python
# 缺失接口: 查询TuShare积分配额使用情况
# 外部路径: GET /api/v1/financial/quota/status
# 功能: 监控每日2000次配额使用
# 使用场景: 避免配额耗尽导致策略停止
```

**必需性**: ⭐⭐⭐⭐⭐ 生产环境稳定性保障

---

## 🟡 P1级 - 重要功能缺失 (高优先级)

### 2. AKShare市场情绪接口

#### 2.1 涨停跌停分析
```python
# 缺失接口: stock_zt_pool_em() + stock_dt_pool_em()
# 外部路径: GET /api/v1/akshare/sentiment/limit-analysis
# 功能: 实时涨停板/跌停板股票池
# 使用场景: 追涨杀跌策略、市场情绪监控
```

**必需性**: ⭐⭐⭐⭐ 短线交易核心信号

#### 2.2 概念板块分析
```python
# 缺失接口: stock_board_concept_name_em()
# 外部路径: GET /api/v1/akshare/sentiment/concept-analysis
# 功能: 概念板块热度排行、成分股
# 使用场景: 题材炒作、板块轮动策略
```

**必需性**: ⭐⭐⭐⭐ 题材投资必备

#### 2.3 资金流向监控
```python
# 缺失接口: stock_individual_fund_flow_rank()
# 外部路径: GET /api/v1/akshare/sentiment/fund-flow
# 功能: 个股/板块主力资金流向
# 使用场景: 主力行为追踪、资金面分析
```

**必需性**: ⭐⭐⭐⭐ 资金驱动策略核心

#### 2.4 综合市场情绪
```python
# 缺失接口: 综合情绪指数计算
# 外部路径: GET /api/v1/akshare/sentiment/comprehensive
# 功能: 整合涨停、概念、资金流数据的综合评分
# 使用场景: 仓位管理、风险控制
```

**必需性**: ⭐⭐⭐⭐ 择时策略依据

#### 2.5 龙虎榜数据
```python
# 缺失接口: stock_lhb_detail_em()
# 外部路径: GET /api/v1/akshare/lhb/detail
# 功能: 龙虎榜上榜股票、营业部席位
# 使用场景: 游资动向追踪
```

**必需性**: ⭐⭐⭐ 超短线交易参考

---

### 3. TuShare专业数据接口 (需2000积分)

#### 3.1 机构评级
```python
# 缺失接口: stk_surv()
# 外部路径: GET /api/v1/tushare/professional/ratings/{symbol}
# 功能: 券商研报评级、目标价
# 使用场景: 机构一致预期分析
```

**必需性**: ⭐⭐⭐⭐ 中长线投资决策

#### 3.2 股票回购
```python
# 缺失接口: repurchase()
# 外部路径: GET /api/v1/tushare/professional/repurchases/{symbol}
# 功能: 公司回购计划、进度
# 使用场景: 正面信号捕捉、价值发现
```

**必需性**: ⭐⭐⭐ 事件驱动策略

#### 3.3 限售解禁
```python
# 缺失接口: share_float()
# 外部路径: GET /api/v1/tushare/professional/float-schedule/{symbol}
# 功能: 限售股解禁时间表
# 使用场景: 风险规避、负面事件预警
```

**必需性**: ⭐⭐⭐⭐ 风险管理必备

#### 3.4 期权数据
```python
# 缺失接口: opt_basic() + opt_daily()
# 外部路径: GET /api/v1/tushare/professional/options/*
# 功能: 期权基础信息、行情
# 使用场景: 期权策略、波动率交易
```

**必需性**: ⭐⭐ 高阶策略需求

#### 3.5 综合投资分析
```python
# 缺失接口: 综合专业数据分析
# 外部路径: GET /api/v1/tushare/professional/analysis/comprehensive/{symbol}
# 功能: 一键生成完整投研报告
# 使用场景: 深度研究、决策支持
```

**必需性**: ⭐⭐⭐⭐ 提升研究效率

---

## 🟢 P2级 - 增强功能缺失 (中优先级)

### 4. TuShare其他数据接口

#### 4.1 公告数据
```python
# 缺失接口: anns() 系列
# 外部路径: /api/v1/tushare/anns/*
# 功能: 上市公司公告全文
# 使用场景: 事件驱动交易
```

**必需性**: ⭐⭐⭐ 信息优势获取

#### 4.2 分红送股
```python
# 缺失接口: dividend() 系列
# 外部路径: /api/v1/tushare/dividend/*
# 功能: 分红送股方案、实施进度
# 使用场景: 股息策略、除权除息处理
```

**必需性**: ⭐⭐⭐ 长期投资数据

#### 4.3 融资融券
```python
# 缺失接口: margin() 系列
# 外部路径: /api/v1/tushare/margin/*
# 功能: 融资融券余额、标的
# 使用场景: 市场情绪、杠杆监控
```

**必需性**: ⭐⭐⭐ 市场结构分析

#### 4.4 股东增减持
```python
# 缺失接口: holdertrade()
# 外部路径: /api/v1/tushare/holdertrade/*
# 功能: 大股东、高管增减持记录
# 使用场景: 内部人交易信号
```

**必需性**: ⭐⭐⭐ 信号挖掘

#### 4.5 停复牌信息
```python
# 缺失接口: suspend()
# 外部路径: /api/v1/tushare/suspend/*
# 功能: 停牌、复牌时间表
# 使用场景: 流动性风险管理
```

**必需性**: ⭐⭐⭐ 风险控制

---

### 5. AKShare技术分析接口

#### 5.1 市场宽度指标
```python
# 缺失接口: stock_a_indicator_lg()
# 外部路径: GET /api/v1/akshare/technical/market-breadth
# 功能: 涨跌家数、新高新低数量
# 使用场景: 市场趋势判断
```

**必需性**: ⭐⭐⭐ 择时指标

#### 5.2 技术指标计算
```python
# 缺失接口: 批量计算MA/MACD/KDJ/RSI
# 外部路径: POST /api/v1/market/indicators
# 功能: 常用技术指标快速计算
# 使用场景: 技术分析策略
```

**必需性**: ⭐⭐⭐ 技术面策略基础

#### 5.3 今日市场概览
```python
# 缺失接口: 综合今日数据
# 外部路径: GET /api/v1/akshare/quick/today-overview
# 功能: 涨跌分布、成交额、板块表现
# 使用场景: 每日开盘前快速了解市场
```

**必需性**: ⭐⭐⭐ 交易日常工具

---

### 6. QMT实时数据增强

#### 6.1 QMT实时K线
```python
# 缺失接口: QMT券商级实时K线推送
# 外部路径: POST /api/v1/market/qmt/realtime/kline
# 功能: <10秒延迟的分钟级K线
# 使用场景: 高频交易、精确入场
```

**必需性**: ⭐⭐⭐ 高频策略核心

---

## 🔵 P3级 - 可选功能缺失 (低优先级)

### 7. 期货与外汇数据

#### 7.1 期货行情
```python
# 缺失接口: fut_daily() 系列
# 外部路径: /api/v1/tushare/futures/*
# 功能: 商品期货、股指期货行情
# 使用场景: CTA策略、跨市场套利
```

**必需性**: ⭐⭐ 扩展品种需求

#### 7.2 外汇汇率
```python
# 缺失接口: forex_daily()
# 外部路径: /api/v1/tushare/forex/*
# 功能: 人民币汇率、主要货币对
# 使用场景: 跨境投资、汇率风险对冲
```

**必需性**: ⭐ 特殊场景需求

---

## 📋 实现建议

### 阶段1: 核心数据补全 (1-2周)
- [ ] TuShare财务数据接口 (4个)
- [ ] TuShare配额管理 (1个)
- [ ] 实现对应的存储层支持 (ClickHouse表结构)

### 阶段2: 市场情绪监控 (1周)
- [ ] AKShare涨停跌停分析 (1个)
- [ ] AKShare资金流向 (1个)
- [ ] AKShare龙虎榜 (1个)
- [ ] AKShare概念板块 (1个)

### 阶段3: 专业数据增强 (2周)
- [ ] TuShare机构评级 (1个)
- [ ] TuShare限售解禁 (1个)
- [ ] TuShare股票回购 (1个)
- [ ] TuShare综合分析接口 (1个)

### 阶段4: 辅助数据完善 (1周)
- [ ] 公告数据 (1个)
- [ ] 分红送股 (1个)
- [ ] 融资融券 (1个)
- [ ] 技术指标计算 (1个)

---

## 🔧 技术实现要点

### 1. 认证与配额管理
```python
# 需要实现TuShare Token池轮换机制
# 当前: reader/tushare_agent.py 已有基础Token管理
# 待补充: 配额监控、自动降级到AKShare
```

### 2. 数据存储策略
```python
# 财务数据: ClickHouse WARM层 (季度更新)
# 市场情绪: Redis HOT层 (日内更新)
# 龙虎榜/公告: MySQL COOL层 (T+1更新)
# 历史回测: MinIO COLD层 (归档)
```

### 3. 接口调用优化
```python
# 批量接口优先: 减少API调用次数
# 并行请求: AKShare/TuShare可并行
# 缓存策略:
#   - 财务数据: 缓存1天
#   - 实时情绪: 缓存10秒
#   - 历史数据: 缓存1小时
```

---

## 📊 对比项目现有实现

### 当前已实现的第三方接口
1. **AKShare**
   - ✅ `get_ak_daily_history()` - 历史日K线
   - ✅ `stock_info_a_code_name()` - 股票代码列表

2. **TuShare**
   - ✅ `get_ts_daily_history()` - 历史日K线
   - ✅ `get_ts_daily_histories()` - 批量历史K线

3. **MootDX**
   - ✅ `get_mootdx_daily_history()` - 本地历史K线
   - ✅ `get_mootdx_quotes()` - 实时行情快照

4. **QMT**
   - ✅ `xtdata.get_market_data()` - 历史行情
   - ✅ `xtdata.subscribe_quote()` - 实时行情订阅

### 缺失功能占比
- **行情数据**: 已实现60% (历史K线完整，实时推送部分缺失)
- **财务数据**: 已实现0% (完全缺失)
- **市场情绪**: 已实现0% (完全缺失)
- **专业数据**: 已实现0% (完全缺失)

---

**维护信息**:
- 文档版本: v1.0
- 生成日期: 2025-10-02
- 总缺失接口: 30个
- 建议实施周期: 5-6周
- 预计提升系统完整度: 从17% → 100%
