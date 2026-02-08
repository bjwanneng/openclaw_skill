# OpenClaw 股票分析与选股系统 v2.0

基于 OpenClaw 框架的 A股/港股投研分析工具集，提供 **14维度** 综合股票分析、选股和预警功能。

## ✨ 项目亮点

- 🎯 **14维度综合分析** — 技术面、基本面、资金流向、新闻面、筹码分布、龙虎榜、融资融券、北向资金、大宗交易、股东人数、机构持仓、限售解禁、行业对比、分红送转
- 🧠 **主力行为推断** — 基于筹码集中度×获利比例×成本中心交叉分析，8种信号组合判断主力吸筹/派发
- 📊 **多周期趋势分析** — 短期(5日)、中期(10日)、长期(20日)三维度对比
- 🔮 **综合预测模型** — 16个因子加权评分，给出趋势判断和操作建议
- 📦 **开箱即用** — 基于 akshare 开源数据，无需付费API

## 核心分析维度

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

## 目录结构

```
src/openclaw_stock/
├── __init__.py                      # 统一导出所有接口
├── data/                            # 数据采集模块
│   ├── market_data.py               # 行情数据（实时+历史K线）
│   ├── financial_data.py            # 财务数据
│   ├── fund_flow.py                 # 资金流向
│   ├── news_data.py                 # 新闻数据
│   ├── lhb_data.py                  # 龙虎榜数据
│   ├── margin_data.py               # 融资融券数据
│   ├── northbound_data.py           # 北向资金（沪深港通）
│   ├── block_trade_data.py          # 大宗交易数据
│   ├── shareholder_data.py          # 股东人数变化
│   ├── institution_data.py          # 机构持仓+调研
│   ├── restricted_shares_data.py    # 限售解禁
│   ├── industry_compare_data.py     # 行业对比
│   └── dividend_data.py             # 分红送转历史
├── analysis/                        # 分析模块
│   ├── technical_analysis.py        # 技术分析+支撑压力位
│   ├── fundamental_analysis.py      # 基本面分析
│   ├── chip_analysis.py             # 筹码分布+主力行为推断
│   └── stock_analyzer.py            # 综合分析引擎（14维度）
├── selection/                       # 选股模块
│   ├── short_term.py                # 短期选股（1-15个交易日）
│   ├── long_term.py                 # 中长期选股（1-12个月）
│   └── scoring_model.py             # 评分模型
└── alert/                           # 预警模块
    └── alert_system.py              # 实时预警
```

## 安装

```bash
# 克隆仓库
git clone https://github.com/bjwanneng/openclaw_skill.git
cd openclaw_skill/openclaw_stock_research

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -e .
```

## 快速开始

### 命令行方式（推荐）

```bash
# 个股14维度综合分析
PYTHONPATH=. ./run.sh analyze 601127 --market sh

# 导出完整JSON报告
PYTHONPATH=. ./run.sh analyze 601127 --market sh --output report.json

# 短期选股
PYTHONPATH=. ./run.sh select-short --top-n 50

# 中长期选股
PYTHONPATH=. ./run.sh select-long --min-roe 15 --max-pe 30
```

### Python 方式

```python
from src.openclaw_stock import analyze_stock

# 一键14维度综合分析
result = analyze_stock(symbol='601127', market='sh')

# 结果包含：
# result['technical_analysis']     - 技术面
# result['fundamental_analysis']   - 基本面
# result['fund_flow_analysis']     - 资金流向
# result['news_analysis']          - 新闻面
# result['chip_analysis']          - 筹码分布+主力行为
# result['lhb_analysis']           - 龙虎榜
# result['margin_analysis']        - 融资融券
# result['northbound_analysis']    - 北向资金
# result['block_trade_analysis']   - 大宗交易
# result['shareholder_analysis']   - 股东人数
# result['institution_analysis']   - 机构持仓
# result['restricted_shares_analysis'] - 限售解禁
# result['industry_compare_analysis']  - 行业对比
# result['dividend_analysis']      - 分红送转
# result['risk_assessment']        - 风险评估
# result['prediction']             - 后市预测
```

### 单独使用各模块

```python
# 筹码分析（含主力行为推断）
from src.openclaw_stock import analyze_chip_distribution
chip = analyze_chip_distribution(symbol='601127', current_price=109.08)

# 龙虎榜
from src.openclaw_stock.data.lhb_data import fetch_lhb_data
lhb = fetch_lhb_data(symbol='601127', days=90)

# 融资融券
from src.openclaw_stock.data.margin_data import fetch_margin_data
margin = fetch_margin_data(symbol='601127', days=30)

# 北向资金
from src.openclaw_stock.data.northbound_data import fetch_northbound_data
nb = fetch_northbound_data(symbol='601127', market='sh')

# 股东人数变化
from src.openclaw_stock.data.shareholder_data import fetch_shareholder_data
sh = fetch_shareholder_data(symbol='601127')

# 更多接口详见 SKILL.md
```

## 后市预测模型

综合16个因子加权评分：

| 因素 | 权重 | 说明 |
|------|------|------|
| 技术趋势 | ±0.20 | 上升/下降趋势 |
| 技术信号 | ±0.15 | 买入/卖出信号 |
| 盈利能力 | +0.10 | 强盈利加分 |
| 成长性 | +0.10 | 高成长加分 |
| 估值水平 | ±0.10 | 低估/高估 |
| 资金流向 | ±0.10 | 主力净流入/流出 |
| 筹码+主力行为 | ±0.15 | 集中度/趋势/吸筹派发 |
| 龙虎榜 | ±0.05 | 机构净买入/卖出 |
| 融资融券 | ±0.05 | 融资余额增/减 |
| 北向资金 | ±0.05 | 净流入/流出 |
| 大宗交易 | ±0.03 | 溢价/折价 |
| 股东人数 | ±0.05 | 减少/增加 |
| 限售解禁 | -0.05 | 大额解禁减分 |
| 机构持仓 | ±0.05 | 增持/减持 |

## 报告示例

```
【一、技术面分析】    趋势/均线/MACD/KDJ/RSI/支撑压力位
【二、基本面分析】    PE/PB/ROE/利润率/成长性
【三、资金流向分析】  主力/散户净流入
【四、新闻面分析】    近期新闻列表
【五、筹码分布分析】  获利比例/集中度/主力行为推断
【六、龙虎榜分析】    上榜记录/机构买卖
【七、融资融券分析】  融资余额/趋势
【八、北向资金分析】  持股/流向
【九、大宗交易分析】  折溢价率
【十、股东人数变化】  户数/趋势
【十一、机构持仓】    持仓/调研
【十二、限售解禁】    解禁预警
【十三、行业对比】    行业定位
【十四、分红送转】    股息率/稳定性
【十五、风险评估】    综合风险等级
【十六、后市预测】    趋势/概率/目标价/操作建议
```

## 版本历史

- **v2.0.0** (2026-02-08) — 新增9大数据源，14维度综合分析，增强筹码主力行为推断
- **v1.1.0** — 新增筹码分布分析
- **v1.0.0** — 初始版本（技术面/基本面/资金流向/新闻面/选股/预警）

## 致谢

- [AkShare](https://www.akshare.xyz/) — 金融数据接口库
- [OpenClaw](https://github.com/openclaw/openclaw) — 智能助手框架
- [东方财富](https://www.eastmoney.com/) / [新浪财经](https://finance.sina.com.cn/) — 数据来源

## 许可证

MIT License

---

**⚠️ 免责声明**: 本工具仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
