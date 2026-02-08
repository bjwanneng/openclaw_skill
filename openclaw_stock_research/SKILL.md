---
name: stock-analysis
description: Professional stock analysis and selection system for A-share and Hong Kong stocks. Provides real-time market data, technical analysis, fundamental analysis, chip distribution analysis, institutional behavior inference, Dragon-Tiger list, margin trading, northbound capital flow, block trades, shareholder changes, institutional holdings, restricted share unlocking, industry comparison, dividend history, short-term and long-term stock selection, comprehensive stock analysis, support/resistance calculation, and real-time alerts. Based on akshare open-source database. Use when analyzing Chinese stocks, getting stock quotes, selecting stocks, or generating investment research reports.
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

```bash
./venv/bin/python -m pytest tests/ -v
./venv/bin/python scripts/stock_analyzer.py analyze 000001
```

### Skill 执行检查清单

执行本技能前，请确认：

1. [ ] 虚拟环境目录 `venv/` 存在
2. [ ] 使用 `./run.sh` 或 `./venv/bin/python` 运行命令
3. [ ] 项目已安装：`pip install -e .`
4. [ ] 环境变量文件 `.env` 已配置（如需要）

## 工具位置

```
${PROJECT_ROOT}/src/openclaw_stock/
├── __init__.py                      # 统一导出所有接口
├── data/                            # 数据采集模块
│   ├── market_data.py               # 行情数据（实时+历史K线）
│   ├── financial_data.py            # 财务数据
│   ├── fund_flow.py                 # 资金流向
│   ├── news_data.py                 # 新闻数据
│   ├── lhb_data.py                  # 🆕 龙虎榜数据
│   ├── margin_data.py               # 🆕 融资融券数据
│   ├── northbound_data.py           # 🆕 北向资金（沪深港通）
│   ├── block_trade_data.py          # 🆕 大宗交易数据
│   ├── shareholder_data.py          # 🆕 股东人数变化
│   ├── institution_data.py          # 🆕 机构持仓+调研
│   ├── restricted_shares_data.py    # 🆕 限售解禁
│   ├── industry_compare_data.py     # 🆕 行业对比
│   └── dividend_data.py             # 🆕 分红送转历史
├── analysis/                        # 分析模块
│   ├── technical_analysis.py        # 技术分析+支撑压力位
│   ├── fundamental_analysis.py      # 基本面分析
│   ├── chip_analysis.py             # 🆕 筹码分布+主力行为推断
│   └── stock_analyzer.py            # 综合分析（14维度）
├── selection/                       # 选股模块
│   ├── short_term.py                # 短期选股
│   ├── long_term.py                 # 中长期选股
│   └── scoring_model.py
└── alert/                           # 预警模块
    └── alert_system.py
```

## 简介

本技能为个人投资者提供一套完整的股票分析和选股系统，基于 akshare 开源数据库，涵盖 **14个分析维度**：

### 核心分析维度

| # | 维度 | 数据来源 | 分析内容 |
|---|------|----------|----------|
| 1 | 📈 技术面 | 历史K线 | 均线/MACD/KDJ/RSI/布林带/支撑压力位 |
| 2 | 📊 基本面 | 财务报表 | PE/PB/ROE/利润率/成长性 |
| 3 | 💰 资金流向 | 东方财富 | 主力/散户净流入 |
| 4 | 📰 新闻面 | 新浪财经 | 近期新闻+消息面 |
| 5 | 🎯 筹码分布 | 东方财富 | 获利比例/集中度/主力行为推断 |
| 6 | 🐉 龙虎榜 | 东方财富 | 上榜记录/机构买卖/游资动向 |
| 7 | 💳 融资融券 | 上交所/深交所 | 融资余额趋势/杠杆情绪 |
| 8 | 🌏 北向资金 | 沪深港通 | 外资持股/净买入方向 |
| 9 | 📦 大宗交易 | 东方财富 | 折溢价率/成交频率 |
| 10 | 👥 股东人数 | 东方财富 | 户数变化/筹码集中度验证 |
| 11 | 🏦 机构持仓 | 东方财富 | 基金持仓/机构调研 |
| 12 | 🔓 限售解禁 | 东方财富 | 解禁日期/数量/抛压预警 |
| 13 | 📊 行业对比 | 东方财富 | 行业定位/估值对比 |
| 14 | 💰 分红送转 | 东方财富 | 分红历史/股息率/稳定性 |

所有维度数据均纳入后市预测模型，综合评分给出趋势判断和操作建议。

## 触发条件

用户需要以下任何一项服务时触发：
1. 查询股票实时行情或历史数据
2. 对单只股票进行全方位分析（14维度）
3. 计算技术指标或支撑压力位
4. 获取基本面数据（PE/PB/ROE等）
5. 分析筹码分布和主力行为
6. 查看龙虎榜、融资融券、北向资金等数据
7. 进行短期选股（技术突破/资金驱动等策略）
8. 进行中长期选股（价值投资/成长投资等策略）
9. 设置股票实时预警

## 执行逻辑

### 1. 个股综合分析（核心功能）

```bash
# 命令行方式（推荐）
cd /root/.openclaw/workspace/skills/openclaw_stock_research
PYTHONPATH=. ./run.sh analyze 601127 --market sh --output /root/.openclaw/workspace/report.json
```

```python
# Python 方式
from src.openclaw_stock import analyze_stock
result = analyze_stock(symbol='601127', market='sh')
```

输出包含全部14个维度的分析结果，以及综合后市预测。

### 2. 数据采集接口

```python
# 实时行情
from src.openclaw_stock import fetch_realtime_quote
quote = fetch_realtime_quote(symbol='000001', market='sz')

# 历史K线
from src.openclaw_stock import fetch_market_data
df = fetch_market_data(symbol='000001', period='daily', market='sz')

# 财务数据
from src.openclaw_stock import fetch_financial_data
financial = fetch_financial_data(symbol='000001')

# 资金流向
from src.openclaw_stock import fetch_fund_flow
flow = fetch_fund_flow(symbol='000001', days=5)

# 新闻
from src.openclaw_stock import fetch_stock_news
news = fetch_stock_news(symbol='601127', stock_name='赛力斯', limit=10)
```

### 3. 新增数据采集接口

```python
# 龙虎榜
from src.openclaw_stock.data.lhb_data import fetch_lhb_data
lhb = fetch_lhb_data(symbol='601127', days=90)

# 融资融券
from src.openclaw_stock.data.margin_data import fetch_margin_data
margin = fetch_margin_data(symbol='601127', days=30)

# 北向资金
from src.openclaw_stock.data.northbound_data import fetch_northbound_data
nb = fetch_northbound_data(symbol='601127', market='sh')

# 大宗交易
from src.openclaw_stock.data.block_trade_data import fetch_block_trade_data
bt = fetch_block_trade_data(symbol='601127', days=90)

# 股东人数变化
from src.openclaw_stock.data.shareholder_data import fetch_shareholder_data
sh = fetch_shareholder_data(symbol='601127')

# 机构持仓
from src.openclaw_stock.data.institution_data import fetch_institution_data
inst = fetch_institution_data(symbol='601127')

# 限售解禁
from src.openclaw_stock.data.restricted_shares_data import fetch_restricted_shares_data
rs = fetch_restricted_shares_data(symbol='601127')

# 行业对比
from src.openclaw_stock.data.industry_compare_data import fetch_industry_compare_data
ind = fetch_industry_compare_data(symbol='601127')

# 分红送转
from src.openclaw_stock.data.dividend_data import fetch_dividend_data
div = fetch_dividend_data(symbol='601127')
```

### 4. 分析接口

```python
# 技术分析
from src.openclaw_stock import calculate_technical_indicators, calculate_support_resistance
df_tech = calculate_technical_indicators(df)
sr = calculate_support_resistance(symbol='000001', df=df)

# 基本面分析
from src.openclaw_stock import calculate_fundamental_indicators
fundamental = calculate_fundamental_indicators(symbol='000001')

# 筹码分布分析（含主力行为推断）
from src.openclaw_stock import analyze_chip_distribution
chip = analyze_chip_distribution(symbol='601127', current_price=109.08)
```

### 5. 选股

```python
from src.openclaw_stock import short_term_stock_selector, long_term_stock_selector

# 短期选股
df_short = short_term_stock_selector(top_n=50)

# 中长期选股
df_long = long_term_stock_selector(min_roe=15, max_pe=30, top_n=30)
```

## 报告格式

综合分析报告包含以下章节：

```
【一、技术面分析】    趋势/均线/MACD/KDJ/RSI/支撑压力位
【二、基本面分析】    PE/PB/ROE/利润率/成长性
【三、资金流向分析】  主力/散户净流入
【四、新闻面分析】    近期新闻列表
【五、筹码分布分析】  获利比例/集中度/主力行为推断/多周期趋势
【六、龙虎榜分析】    上榜记录/机构买卖/上榜后表现
【七、融资融券分析】  融资余额/融券余额/趋势
【八、北向资金分析】  持股数量/市值/占比/流向
【九、大宗交易分析】  成交记录/折溢价率
【十、股东人数变化】  户数/户均持股/变化趋势
【十一、机构持仓分析】持仓机构数/调研记录/增减持
【十二、限售解禁】    解禁日期/数量/市值/压力评估
【十三、行业对比】    行业定位/估值对比
【十四、分红送转历史】分红记录/股息率/稳定性
【十五、风险评估】    综合风险等级/各项风险因素
【十六、后市预测】    趋势/概率/目标价/关键因素/操作建议
```

## 筹码分析特色功能

筹码分析模块提供增强版主力行为推断：

- **多周期对比**：短期(5日)、中期(10日)、长期(20日)三维度
- **集中度变化速率**：线性回归计算筹码集中/分散速度
- **8种交叉信号**：集中度×获利比例×成本中心交叉分析
- **主力行为推断**：吸筹/派发/中性，附信号强度（强/中/弱）

示例输出：
```
🟢 筹码集中+获利比例下降：典型的主力低位吸筹信号
🔴 筹码分散+获利比例上升：主力高位派发信号
🟡 筹码分散+获利比例下降：可能是恐慌抛售或主力洗盘
```

## 后市预测模型

预测模型综合以下因素评分：

| 因素 | 权重 | 说明 |
|------|------|------|
| 技术趋势 | ±0.20 | 上升/下降趋势 |
| 技术信号 | ±0.15 | 买入/卖出信号 |
| 盈利能力 | +0.10 | 强盈利加分 |
| 成长性 | +0.10 | 高成长加分 |
| 估值水平 | ±0.10 | 低估/高估 |
| 资金流向 | ±0.10 | 主力净流入/流出 |
| 筹码状态 | ±0.05 | 集中/分散 |
| 筹码趋势 | ±0.05 | 集中化/分散化 |
| 主力行为 | ±0.05 | 吸筹/派发 |
| 龙虎榜 | ±0.05 | 机构净买入/卖出 |
| 融资融券 | ±0.05 | 融资余额增/减 |
| 北向资金 | ±0.05 | 净流入/流出 |
| 大宗交易 | ±0.03 | 溢价/折价 |
| 股东人数 | ±0.05 | 减少/增加 |
| 限售解禁 | -0.05 | 大额解禁减分 |
| 机构持仓 | ±0.05 | 增持/减持 |

最终概率 > 0.6 → 看涨，< 0.4 → 看跌，其余 → 震荡

## 性能说明

- 完整14维度分析耗时约 **3-5分钟**（受网络和API响应影响）
- 行业对比模块受东方财富API限制，可能返回部分数据（优雅降级）
- 机构持仓已优化为只获取最近季度数据，控制在30秒内

## 注意事项

1. **执行环境**：确保在 `run.sh` 所在目录执行，加上 `PYTHONPATH=.`
2. **数据深度**：`analyze` 命令默认返回简要总结。使用 `--output` 保存 JSON 获取完整数据
3. **数据延迟**：实时行情可能有15分钟延迟（交易所规定）
4. **港股限制**：部分功能（北向资金、融资融券等）仅适用于A股
5. **风险提示**：本系统仅供参考，不构成投资建议

## 版本信息

- **Version**: 2.0.0
- **Last Updated**: 2026-02-08
- **Dependencies**: akshare, pandas, numpy
- **Changelog**:
  - v2.0.0: 新增9大数据源（龙虎榜/融资融券/北向资金/大宗交易/股东人数/机构持仓/限售解禁/行业对比/分红送转），增强筹码分析（主力行为推断+多周期对比），14维度综合预测模型
  - v1.1.0: 新增筹码分布分析
  - v1.0.0: 初始版本（技术面/基本面/资金流向/新闻面/选股/预警）
