---
name: stock-analysis
description: Professional stock analysis and selection system for A-share and Hong Kong stocks. Provides real-time market data, technical analysis, fundamental analysis, short-term and long-term stock selection, comprehensive stock analysis, support/resistance calculation, and real-time alerts. Based on akshare open-source database. Use when analyzing Chinese stocks, getting stock quotes, selecting stocks, or generating investment research reports.
disable-model-invocation: false
allowed-tools: [Read, Grep, Glob, Bash, Task]
---

# 股票分析与选股系统

## 虚拟环境配置（重要）

本技能依赖 Python 虚拟环境。Skill 执行前必须确保虚拟环境已激活，或使用虚拟环境的 Python 解释器。

### 自动激活方案

项目提供了 `run.sh` 脚本，自动处理虚拟环境激活。**重要：在某些环境下执行可能需要先运行 `chmod +x run.sh` 授予执行权限，并使用 `PYTHONPATH=.` 确保模块导入正确。**

```bash
# 授予执行权限（仅需一次）
chmod +x run.sh

# 使用 run.sh 运行分析（推荐带上 PYTHONPATH）
PYTHONPATH=. ./run.sh analyze 000001 --market sz

# 导出完整分析报告到 JSON
PYTHONPATH=. ./run.sh analyze 000001 --market sz --output /root/.openclaw/workspace/report.json
```

### 手动指定 Python 路径

如果不想使用 run.sh，可直接使用虚拟环境的 Python：

```bash
# 直接使用虚拟环境的 Python 运行
./venv/bin/python -m pytest tests/ -v

# 或运行脚本
./venv/bin/python scripts/stock_analyzer.py analyze 000001
```

### 传统方式（手动激活）

```bash
# 手动激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 然后运行命令
pytest tests/ -v
```

### Skill 执行检查清单

执行本技能前，请确认：

1. [ ] 虚拟环境目录 `venv/` 存在
2. [ ] 使用 `./run.sh` 或 `./venv/bin/python` 运行命令
3. [ ] 项目已安装：`pip install -e .`
4. [ ] 环境变量文件 `.env` 已配置（如需要）

## 工具位置

本技能依赖的 Python 模块位于项目源代码目录：

```
${PROJECT_ROOT}/src/openclaw_stock/
├── __init__.py              # 统一导出所有10个接口
├── data/                    # 数据采集模块（3个接口）
│   ├── market_data.py       # 接口1: fetch_market_data
│   ├── financial_data.py    # 接口2: fetch_financial_data
│   └── fund_flow.py         # 接口3: fetch_fund_flow
├── analysis/                # 分析模块（4个接口）
│   ├── technical_analysis.py    # 接口4, 9
│   ├── fundamental_analysis.py  # 接口5
│   └── stock_analyzer.py        # 接口8
├── selection/               # 选股模块（2个接口）
│   ├── short_term.py        # 接口6
│   ├── long_term.py         # 接口7
│   └── scoring_model.py
└── alert/                   # 预警模块（1个接口）
    └── alert_system.py      # 接口10
```

### 命令行工具

项目还提供了命令行工具脚本，位于 `scripts/` 目录：

```
${PROJECT_ROOT}/scripts/
└── stock_analyzer.py        # 命令行分析工具
```

该脚本提供了以下命令：

1. **单股票分析**
   ```bash
   python scripts/stock_analyzer.py analyze <股票代码> [--market <市场>]
   ```
   示例：
   ```bash
   python scripts/stock_analyzer.py analyze 000001 --market sz
   ```

2. **短期选股**
   ```bash
   python scripts/stock_analyzer.py select-short [--top-n <数量>]
   ```
   示例：
   ```bash
   python scripts/stock_analyzer.py select-short --top-n 50
   ```

3. **长期选股**
   ```bash
   python scripts/stock_analyzer.py select-long [--min-roe <ROE>] [--max-pe <PE>]
   ```
   示例：
   ```bash
   python scripts/stock_analyzer.py select-long --min-roe 15 --max-pe 30
   ```

4. **设置预警**
   ```bash
   python scripts/stock_analyzer.py alert-setup <股票代码> <类型> <条件>
   ```
   示例：
   ```bash
   python scripts/stock_analyzer.py alert-setup 000001 price "above:15.0"
   ```

## 简介

本技能为个人投资者提供一套完整的股票分析和选股系统，基于 akshare 开源数据库，涵盖：
- 股票后市研判（个股全方位分析，含技术面、基本面、资金流向、新闻面）
- 短期选股（1-15个交易日）
- 中长期选股（1-12个月）
- 实时预警

## 触发条件

用户需要以下任何一项服务时触发：
1. 查询股票实时行情或历史数据
2. 对单只股票进行全方位分析
3. 计算技术指标或支撑压力位
4. 获取基本面数据（PE/PB/ROE等）
5. 进行短期选股（技术突破/资金驱动等策略）
6. 进行中长期选股（价值投资/成长投资等策略）
7. 设置股票实时预警

## 执行逻辑

当用户请求股票相关服务时，按以下流程执行：

### 1. 解析用户需求

分析用户的输入 $ARGUMENTS，确定：
- 股票代码（symbol）
- 市场类型（market: sh/sz/hk）
- 请求类型（行情/分析/选股/预警）

### 2. 数据采集

使用 akshare 获取数据：

```python
# 获取实时行情
from src.openclaw_stock import fetch_realtime_quote
quote = fetch_realtime_quote(symbol='000001', market='sz')

# 获取历史K线
from src.openclaw_stock import fetch_market_data
df = fetch_market_data(symbol='000001', period='daily', market='sz')

# 获取财务数据
from src.openclaw_stock import fetch_financial_data
financial = fetch_financial_data(symbol='000001')

# 获取资金流向
from src.openclaw_stock import fetch_fund_flow
flow = fetch_fund_flow(symbol='000001', days=5)

# 获取股票新闻
from src.openclaw_stock import fetch_stock_news
news = fetch_stock_news(symbol='601127', stock_name='赛力斯', limit=10)
```

### 3. 分析处理

根据需求执行相应分析：

#### 技术分析
```python
from src.openclaw_stock import calculate_technical_indicators, calculate_support_resistance

# 计算技术指标
df_with_indicators = calculate_technical_indicators(df)

# 计算支撑压力位
sr = calculate_support_resistance(symbol='000001', df=df)
```

#### 基本面分析
```python
from src.openclaw_stock import calculate_fundamental_indicators

# 计算基本面指标
fundamental = calculate_fundamental_indicators(symbol='000001')
```

#### 个股综合分析
```python
from src.openclaw_stock import analyze_stock

# 全方位分析（包含技术面、基本面、资金流向、新闻面）
result = analyze_stock(symbol='000001', market='sz')
```

#### 选股
```python
from src.openclaw_stock import short_term_stock_selector, long_term_stock_selector

# 短期选股
df_short = short_term_stock_selector(top_n=50)

# 中长期选股
df_long = long_term_stock_selector(min_roe=15, max_pe=30, top_n=30)
```

### 4. 预警设置（可选）

```python
from src.openclaw_stock import setup_alert

# 设置价格预警
alert_id = setup_alert(
    symbol='000001',
    alert_type='price',
    condition={'operator': 'above', 'value': 15.0},
    notification_method='console'
)

# 设置技术指标预警
alert_id = setup_alert(
    symbol='600519',
    alert_type='technical',
    condition={'indicator': 'macd', 'operator': 'golden_cross'},
    notification_method='console'
)
```

### 5. 生成报告

将分析结果格式化为报告：

```markdown
=== 股票代码: 000001 综合分析报告 ===

【基本信息】
股票名称: 平安银行
当前价格: 10.25 元
涨跌幅: 1.48%

【技术面分析】
趋势判断: 上升趋势
主要技术指标:
  MA5: 10.12
  MA20: 9.85
  RSI6: 58.32
交易信号: MACD金叉, 放量上涨

【基本面分析】
估值水平: 合理估值
  PE(TTM): 4.52
  PB: 0.52
  ROE: 11.32%
盈利能力: strong
  净利率: 28.45%
成长性: high
  营收增长率: 15.23%
  利润增长率: 22.18%

【资金流向分析】
近5日主力资金净流入：1234567.89 万元
近5日散户资金净流入：-987654.32 万元
资金面相符：主力资金持续流入

【新闻面分析】
近期相关新闻：7 条

1. [2026-02-06 22:35:23] 阿联酋宝马、劳斯莱斯经销商开卖AITO问界，赛力斯海外市场迎来豪门盛宴｜快讯
   根据协议，ADM将全面负责AITO问界在阿联酋的销售、交付及售后服务，规划建设品牌体验中心与服务中心...

2. [2026-02-06 21:13:35] 赛力斯：股价波动受多方面因素综合影响
   证券日报网讯2月6日，赛力斯在互动平台回答投资者提问时表示，二级市场股价波动受市场情绪、行业变化...

3. [2026-02-06 10:36:26] 2026开门红 赛力斯做对了什么？
   从行业来看，伴随2025年底新能源汽车购置税免征政策结束、车企年终促销提前透支需求，2026年初新能源车市...

... 还有 4 条新闻

【风险评估】
综合风险等级：中等
各项风险：
  波动风险：medium
  估值风险：low
  趋势风险：low

【后市预测】
预测趋势：上涨
概率：75%
目标价格区间：
  上限：11.79 元
  下限：10.76 元
时间周期：短期(1-2周)
风险等级：中等
关键影响因素：
  - 技术趋势向上
  - 盈利能力强
  - 成长性高
  - 主力资金净流入
操作建议：推荐

报告生成时间：2024-01-15 14:30:00
```

## 数据输出格式

### 实时行情
```json
{
  "symbol": "000001",
  "market": "sz",
  "name": "平安银行",
  "price": 10.25,
  "change": 0.15,
  "change_pct": 1.48,
  "volume": 152345600,
  "amount": 1562345678.90,
  "high": 10.35,
  "low": 10.12,
  "open": 10.18,
  "pre_close": 10.10
}
```

### 技术分析结果
```json
{
  "current_price": 10.25,
  "trend": "上升趋势",
  "signals": {
    "macd_signal": "golden_cross",
    "kdj_signal": "none",
    "rsi_signal": "none",
    "ma_signal": "bullish",
    "boll_signal": "within_band",
    "overall": "buy"
  },
  "indicators": {
    "ma5": 10.12,
    "ma10": 9.98,
    "ma20": 9.85,
    "rsi6": 58.32
  }
}
```

### 基本面分析结果
```json
{
  "valuation": {
    "pe_ttm": 4.52,
    "pb": 0.52,
    "roe": 11.32
  },
  "profitability": {
    "gross_margin": 35.2,
    "net_margin": 28.45
  },
  "growth": {
    "revenue_growth": 15.23,
    "profit_growth": 22.18
  },
  "analysis": {
    "valuation_level": "合理估值",
    "profitability_level": "strong",
    "growth_level": "high"
  }
}
```

### 选股结果
```json
{
  "symbol": "000001",
  "name": "平安银行",
  "price": 10.25,
  "change_pct": 1.48,
  "volume": 152345600,
  "turnover_rate": 7.85,
  "technical_score": 35,
  "fund_score": 25,
  "sentiment_score": 18,
  "news_score": 8,
  "total_score": 86,
  "signals": "突破均线多头排列; MACD金叉; 放量上涨"
}
```

### 新闻数据结果
```json
{
  "symbol": "601127",
  "stock_name": "赛力斯",
  "news_count": 7,
  "news_list": [
    {
      "title": "阿联酋宝马、劳斯莱斯经销商开卖AITO问界，赛力斯海外市场迎来豪门盛宴｜快讯",
      "url": "https://cj.sina.com.cn/articles/view/...",
      "time": "2026-02-06 22:35:23",
      "summary": "根据协议，ADM将全面负责AITO问界在阿联酋的销售、交付及售后服务...",
      "source": "新浪财经"
    }
  ],
  "summary": "找到 7 条关于 赛力斯 的新闻：\n1. [2026-02-06 22:35:23] 阿联酋宝马、劳斯莱斯经销商开卖AITO问界...",
  "fetch_time": "2026-02-07 09:32:06"
}
```

### 预警结果
```json
{
  "id": "000001_price_20240115143000",
  "symbol": "000001",
  "alert_type": "price",
  "status": "triggered",
  "created_at": "2024-01-15T14:30:00",
  "triggered_at": "2024-01-15T14:35:00",
  "triggered_value": 15.0,
  "notification_methods": ["console"]
}
```

## 错误处理

### 数据源错误
```json
{
  "status": "error",
  "error_code": "DATA_SOURCE_ERROR",
  "message": "无法访问数据源，请检查网络连接或代理设置",
  "symbol": "000001",
  "market": "sz"
}
```

### 股票代码不存在
```json
{
  "status": "error",
  "error_code": "SYMBOL_NOT_FOUND",
  "message": "股票代码不存在: sz:999999",
  "symbol": "999999",
  "market": "sz"
}
```

### 价格偏差警告
```json
{
  "status": "warning",
  "warning_code": "PRICE_MISMATCH",
  "message": "[DATA_MISMATCH_WARNING] 价格偏差超过0.5%！Web价格(10.25)与参考价格(10.35)差异为0.9662%",
  "symbol": "000001",
  "web_price": 10.25,
  "reference_price": 10.35,
  "diff_pct": 0.9662
}
```

## 注意事项

1. **执行环境**：确保在 `run.sh` 所在目录执行，或使用绝对路径。执行时建议加上 `PYTHONPATH=.` 以解决 `src` 模块导入问题。
2. **数据深度**：`analyze` 命令默认返回简要总结。如需深度研判（均线数值、详细指标、资金明细、新闻详情），必须使用 `--output` 参数保存 JSON 报告并读取其中的 `technical_analysis`、`fund_flow_analysis` 和 `news_analysis` 字段。
3. **新闻数据**：新闻数据来自新浪财经搜索，提供最新的市场动态和消息面分析，帮助综合研判股票走势。
4. **公开信息结合**：本技能提供技术面、基本面、资金流向和新闻面的量化数据。在给出最终建议前，应综合考虑所有维度进行研判。
5. **数据延迟**: 实时行情数据可能有15分钟延迟（交易所规定）
6. **港股限制**: 部分功能（如北向资金）仅适用于A股
7. **风险提示**: 本系统仅供参考，不构成投资建议

## 版本信息

- **Version**: 1.0.0
- **Author**: OpenClaw Team
- **Last Updated**: 2024-02-05
- **Dependencies**: akshare, pandas, numpy
