# OpenClaw Stock Research - 功能清单

## 项目概述

基于 akshare 开源数据库的股票分析和选股系统，涵盖股票后市研判、短期选股和中长期选股三大核心功能。

---

## 一、模块结构

```
src/openclaw_stock/
├── __init__.py              # 统一导出所有接口
├── core/                    # 核心模块
│   ├── config.py            # 配置管理（单例模式）
│   ├── exceptions.py        # 自定义异常类
│   └── models.py            # Pydantic 数据模型
├── adapters/                # 数据源适配器
│   ├── akshare_adapter.py         # 原始 AkShare 适配器
│   ├── akshare_adapter_em.py      # 东方财富数据源适配器
│   └── akshare_adapter_fixed.py   # 修复版适配器
├── data/                    # 数据采集模块
│   ├── __init__.py
│   ├── market_data.py       # 接口1：行情数据采集
│   ├── financial_data.py    # 接口2：财务数据采集
│   └── fund_flow.py         # 接口3：资金流向采集
├── analysis/                # 分析模块
│   ├── __init__.py
│   ├── technical_analysis.py    # 接口4、9：技术指标与支撑压力位
│   ├── fundamental_analysis.py # 接口5：基本面指标
│   └── stock_analyzer.py        # 接口8：个股综合分析
├── selection/               # 选股模块
│   ├── __init__.py
│   ├── short_term.py        # 接口6：短期选股
│   ├── long_term.py         # 接口7：中长期选股
│   └── scoring_model.py     # 评分模型
├── alert/                   # 预警模块
│   ├── __init__.py
│   └── alert_system.py      # 接口10：实时预警
├── tools/                   # 工具模块
│   ├── ak_market_tool.py         # AkShare 市场数据引擎
│   └── web_quote_validator.py    # Web 价格验证器
└── utils/                   # 工具函数
    ├── decorators.py       # 装饰器（@tool, @retry, @cache等）
    ├── logger.py           # 日志配置
    └── venv_helper.py      # 虚拟环境自动激活工具
```

---

## 二、接口实现清单

### 4.1 数据采集接口

#### 接口1: `fetch_market_data()` - 行情数据采集
- **文件**: `src/openclaw_stock/data/market_data.py`
- **功能**: 获取股票历史K线数据
- **参数**:
  - `symbol`: 股票代码
  - `period`: 周期(1m/5m/15m/30m/60m/daily/weekly/monthly)
  - `adjust`: 复权方式(qfq/hfq/None)
  - `start_date/end_date`: 日期范围
  - `market`: 市场类型(sh/sz/hk)
- **返回**: DataFrame(开高低收量等数据)

#### 接口2: `fetch_financial_data()` - 财务数据采集
- **文件**: `src/openclaw_stock/data/financial_data.py`
- **功能**: 获取财务报表数据
- **参数**:
  - `symbol`: 股票代码
  - `report_type`: 报表类型(profit/balance/cashflow/all)
- **返回**: 包含财务数据的字典

#### 接口3: `fetch_fund_flow()` - 资金流向采集
- **文件**: `src/openclaw_stock/data/fund_flow.py`
- **功能**: 获取资金流向数据
- **参数**:
  - `symbol`: 股票代码(None表示全市场)
  - `days`: 天数
  - `market`: 市场类型
  - `flow_type`: 资金流向类型(main/retail/north/all)
- **返回**: DataFrame(主力/超大单/大单/中单/小单资金流向)

### 4.2 指标计算接口

#### 接口4: `calculate_technical_indicators()` - 技术指标计算
- **文件**: `src/openclaw_stock/analysis/technical_analysis.py`
- **功能**: 计算技术指标
- **参数**:
  - `df`: K线数据
  - `indicators`: 需要计算的指标列表
- **返回**: 添加了技术指标列的DataFrame
- **计算指标**:
  - 均线系统: MA5/10/20/60/120/250
  - MACD: DIF/DEA/HIST
  - KDJ: K/D/J
  - RSI: RSI6/12/24
  - 布林带: UPPER/MID/LOWER
  - 成交量指标: VOL_MA5/VOL_MA10/VOL_RATIO

#### 接口5: `calculate_fundamental_indicators()` - 基本面指标计算
- **文件**: `src/openclaw_stock/analysis/fundamental_analysis.py`
- **功能**: 计算基本面指标
- **参数**:
  - `symbol`: 股票代码
  - `include_history`: 是否包含历史数据
- **返回**: 包含基本面指标的字典
- **指标维度**:
  - 估值指标: PE/PB/PS/PEG/EV_EBITDA
  - 盈利能力: ROE/ROA/毛利率/净利率/EPS/BPS
  - 成长性: 营收增长率/利润增长率/ROE增长率
  - 财务质量: 资产负债率/流动比率/速动比率
  - 股东回报: 股息率/分红率
  - 市场指标: 市值/流通市值/换手率

### 4.3 选股接口

#### 接口6: `short_term_stock_selector()` - 短期选股
- **文件**: `src/openclaw_stock/selection/short_term.py`
- **功能**: 短期选股器(1-15个交易日)
- **参数**:
  - `min_price/max_price`: 价格区间
  - `min_volume`: 最小成交量
  - `fund_flow_days`: 资金流向天数
  - `technical_signals`: 技术信号列表
  - `top_n`: 返回前N只股票
- **返回**: DataFrame(符合条件的股票及评分)
- **评分模型**:
  - 技术面(40分): 均线突破/MACD金叉/量价配合/相对强弱
  - 资金面(30分): 主力净流入/龙虎榜上榜
  - 情绪面(20分): 板块联动/涨停板数量
  - 消息面(10分): 利好公告
- **选股策略**:
  - 技术突破型: 突破关键压力位、均线多头排列
  - 资金驱动型: 主力资金持续流入、龙虎榜游资接力
  - 事件催化型: 利好消息、业绩超预期、政策刺激
  - 情绪共振型: 板块联动、题材热点

#### 接口7: `long_term_stock_selector()` - 中长期选股
- **文件**: `src/openclaw_stock/selection/long_term.py`
- **功能**: 中长期选股器(1-12个月)
- **参数**:
  - `min_roe`: 最小ROE
  - `max_pe`: 最大PE
  - `min_profit_growth`: 最小利润增长率
  - `industry`: 行业筛选
  - `top_n`: 返回前N只股票
- **返回**: DataFrame(符合条件的股票及评分)
- **评分模型**:
  - 盈利能力(30分): ROE>15%/净利润增长率>20%/毛利率>30%
  - 估值水平(25分): PE<行业平均/PB<2/PEG<1
  - 成长性(20分): 营收增长率>20%/业绩预告上调
  - 财务质量(15分): 资产负债率<50%/经营现金流>净利润
  - 股东结构(10分): 机构持仓增加/股东户数减少
- **选股策略**:
  - 价值投资: 低估值+稳定盈利+高分红
  - 成长投资: 业绩高增长+行业景气+竞争优势
  - 趋势投资: 长期上升趋势+基本面改善
  - 困境反转: 业绩拐点+估值修复

### 4.4 分析接口

#### 接口8: `analyze_stock()` - 个股综合分析
- **文件**: `src/openclaw_stock/analysis/stock_analyzer.py`
- **功能**: 个股全方位分析
- **参数**:
  - `symbol`: 股票代码
  - `market`: 市场类型
  - `lookback_days`: 回看天数
- **返回**: 包含以下内容的字典:
  - `basic_info`: 基本信息
  - `technical_analysis`: 技术分析结果(趋势/信号/支撑压力位/指标)
  - `fundamental_analysis`: 基本面分析(估值/盈利能力/成长性/质量)
  - `fund_flow_analysis`: 资金流向分析
  - `risk_assessment`: 风险评估
  - `prediction`: 后市预测(趋势/概率/目标价/建议)

#### 接口9: `calculate_support_resistance()` - 支撑压力位计算
- **文件**: `src/openclaw_stock/analysis/technical_analysis.py`
- **功能**: 计算支撑压力位
- **参数**:
  - `symbol`: 股票代码
  - `df`: K线数据
  - `method`: 计算方法(fibonacci/pivot/ma/historical)
  - `lookback`: 回看周期数
- **返回**: 包含以下内容的字典:
  - `current_price`: 当前价格
  - `method`: 计算方法
  - `pivot_point`: 枢轴点
  - `support_levels`: 支撑位列表
  - `resistance_levels`: 压力位列表
  - `recommendation`: 建议

### 4.5 预警接口

#### 接口10: `setup_alert()` - 实时预警
- **文件**: `src/openclaw_stock/alert/alert_system.py`
- **功能**: 设置股票预警
- **参数**:
  - `symbol`: 股票代码
  - `alert_type`: 预警类型(price/volume/technical/news)
  - `condition`: 条件字典
  - `notification_method`: 通知方式(console/email/wechat/dingtalk)
  - `expires_in_hours`: 过期时间(小时)
- **返回**: 预警ID
- **预警类型**:
  - 价格预警: 价格突破/跌破指定价位
  - 成交量预警: 成交量异常放大/缩小
  - 技术指标预警: MACD金叉/死叉、RSI超买/超卖等
  - 新闻预警: 重要公告/利好利空消息
- **通知方式**:
  - 控制台输出(console)
  - 邮件通知(email)
  - 微信通知(wechat)
  - 钉钉通知(dingtalk)

## 三、使用示例

### 1. 数据采集

```python
from openclaw_stock import (
    fetch_market_data,
    fetch_realtime_quote,
    fetch_financial_data,
    fetch_fund_flow
)

# 获取历史K线数据
df = fetch_market_data(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    market="sz"
)

# 获取实时行情
quote = fetch_realtime_quote(symbol="000001", market="sz")
print(f"当前价格: {quote['price']}, 涨跌幅: {quote['change_pct']}%")

# 获取财务数据
financial = fetch_financial_data(symbol="000001", report_type="all")
print(f"PE: {financial['valuation']['pe_ttm']}, ROE: {financial['profitability']['roe']}")

# 获取资金流向
flow = fetch_fund_flow(symbol="000001", days=5)
print(f"主力净流入: {flow['main_inflow'].sum()}")
```

### 2. 技术分析

```python
from openclaw_stock import calculate_technical_indicators, calculate_support_resistance

# 计算技术指标
df_with_indicators = calculate_technical_indicators(df)
print(df_with_indicators[['close', 'ma5', 'ma20', 'macd_hist', 'rsi6']].tail())

# 计算支撑压力位
sr = calculate_support_resistance(
    symbol="000001",
    df=df,
    method="fibonacci",
    lookback=60
)
print(f"支撑位: {sr['support_levels']}")
print(f"压力位: {sr['resistance_levels']}")
```

### 3. 基本面分析

```python
from openclaw_stock import calculate_fundamental_indicators
from openclaw_stock.analysis import FundamentalAnalyzer

# 计算基本面指标
fundamental = calculate_fundamental_indicators("000001")
print(f"估值: PE={fundamental['valuation']['pe_ttm']}, PB={fundamental['valuation']['pb']}")
print(f"盈利能力: ROE={fundamental['profitability']['roe']}, 毛利率={fundamental['profitability']['gross_margin']}")
print(f"成长性: 营收增长={fundamental['growth']['revenue_growth']}, 利润增长={fundamental['growth']['profit_growth']}")

# 使用分析器
analyzer = FundamentalAnalyzer()
valuation = analyzer.analyze_valuation(fundamental)
profitability = analyzer.analyze_profitability(fundamental)
growth = analyzer.analyze_growth(fundamental)
print(f"估值水平: {valuation}, 盈利能力: {profitability}, 成长性: {growth}")
```

### 4. 选股

```python
from openclaw_stock import short_term_stock_selector, long_term_stock_selector

# 短期选股(1-15个交易日)
df_short = short_term_stock_selector(
    min_price=5,
    max_price=50,
    min_volume=1000000,
    fund_flow_days=5,
    top_n=50
)
print("短期选股结果:")
print(df_short[['symbol', 'name', 'price', 'total_score', 'signals']].head(10))

# 中长期选股(1-12个月)
df_long = long_term_stock_selector(
    min_roe=15,
    max_pe=30,
    min_profit_growth=20,
    top_n=30
)
print("\n中长期选股结果:")
print(df_long[['symbol', 'name', 'price', 'pe_ttm', 'roe', 'total_score']].head(10))
```

### 5. 个股综合分析

```python
from openclaw_stock import analyze_stock

# 个股全方位分析
result = analyze_stock('000001', market='sz', lookback_days=250)

# 基本信息
print("=== 基本信息 ===")
print(f"股票: {result['basic_info']['name']}({result['basic_info']['symbol']})")
print(f"当前价格: {result['basic_info']['current_price']} 元")
print(f"涨跌幅: {result['basic_info']['change_pct']}%")

# 技术分析
print("\n=== 技术分析 ===")
print(f"趋势: {result['technical_analysis']['trend']}")
signals = result['technical_analysis'].get('signals', {})
print(f"交易信号: {signals}")

# 基本面分析
print("\n=== 基本面分析 ===")
if result['fundamental_analysis']:
    valuation = result['fundamental_analysis'].get('valuation', {})
    print(f"PE: {valuation.get('pe_ttm')}, PB: {valuation.get('pb')}")

# 风险评估
print("\n=== 风险评估 ===")
if result['risk_assessment']:
    print(f"综合风险: {result['risk_assessment'].get('overall_risk')}")

# 后市预测
print("\n=== 后市预测 ===")
if result['prediction']:
    prediction = result['prediction']
    print(f"预测趋势: {prediction.get('trend_cn')} (概率: {prediction.get('probability')})")
    print(f"目标价格区间: {prediction.get('target_price_low')} - {prediction.get('target_price_high')} 元")
    print(f"操作建议: {prediction.get('recommendation')}")
    print(f"关键影响因素: {prediction.get('key_factors')}")
```

### 6. 预警系统

```python
from openclaw_stock import setup_alert, remove_alert, list_alerts

# 设置价格预警
alert_id_1 = setup_alert(
    symbol='000001',
    alert_type='price',
    condition={'operator': 'above', 'value': 15.0},
    notification_method='console',
    expires_in_hours=24
)
print(f"价格预警已设置: {alert_id_1}")

# 设置技术指标预警(MACD金叉)
alert_id_2 = setup_alert(
    symbol='600519',
    alert_type='technical',
    condition={'indicator': 'macd', 'operator': 'golden_cross'},
    notification_method='console',
    expires_in_hours=48
)
print(f"技术指标预警已设置: {alert_id_2}")

# 列出所有预警
alerts = list_alerts()
print(f"\n当前共有 {len(alerts)} 个预警:")
for alert in alerts:
    print(f"  - {alert['id']}: {alert['symbol']} ({alert['alert_type']}) - {alert['status']}")

# 移除预警
remove_alert(alert_id_1)
print(f"\n已移除预警: {alert_id_1}")
```

---

## 四、快速开始

### 1. 安装依赖

```bash
pip install akshare pandas numpy
```

### 2. 导入模块

```python
from openclaw_stock import (
    fetch_realtime_quote,
    analyze_stock,
    short_term_stock_selector,
    setup_alert
)
```

### 3. 开始使用

```python
# 获取实时行情
quote = fetch_realtime_quote('000001', market='sz')
print(f"当前价格: {quote['price']}")

# 个股分析
result = analyze_stock('000001', market='sz')
print(f"预测趋势: {result['prediction']['trend_cn']}")

# 短期选股
df = short_term_stock_selector(top_n=20)
print(df[['symbol', 'name', 'total_score']])
```

---

## 五、更多信息

- **项目文档**: 请参阅 `design_doc/stock_anlysis_design.md`
- **API文档**: 各模块的 `__init__.py` 文件中有详细说明
- **测试用例**: 请参阅 `tests/test_new_modules.py`

---

**版本**: 1.0.0
**作者**: OpenClaw Team
**最后更新**: 2026-02-05
