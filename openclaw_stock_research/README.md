# OpenClaw 股票分析与选股系统

基于 OpenClaw 框架的 A股/港股投研分析工具集，提供完整的股票分析、选股和预警功能。

## 项目概述

本项目基于 akshare 开源数据库，为个人投资者提供一套完整的股票分析和选股系统，涵盖：

- **股票后市研判**：个股全方位分析（技术+基本面+资金流向）
- **短期选股**（1-15个交易日）：技术突破/资金驱动/事件催化/情绪共振策略
- **中长期选股**（1-12个月）：价值投资/成长投资/趋势投资/困境反转策略
- **实时预警**：价格/成交量/技术指标/新闻事件预警

## 核心功能

### 10个标准接口

本项目实现了设计文档中定义的全部10个接口：

| 接口编号 | 接口名称 | 功能说明 |
|---------|---------|---------|
| 4.1-1 | `fetch_market_data()` | 获取股票历史K线数据 |
| 4.1-2 | `fetch_financial_data()` | 获取财务报表数据 |
| 4.1-3 | `fetch_fund_flow()` | 获取资金流向数据 |
| 4.2-4 | `calculate_technical_indicators()` | 计算技术指标（MA/MACD/KDJ/RSI/布林带等） |
| 4.2-5 | `calculate_fundamental_indicators()` | 计算基本面指标（PE/PB/ROE等） |
| 4.3-6 | `short_term_stock_selector()` | 短期选股器（1-15个交易日） |
| 4.3-7 | `long_term_stock_selector()` | 中长期选股器（1-12个月） |
| 4.4-8 | `analyze_stock()` | 个股综合分析（技术+基本面+资金流向+风险评估+预测） |
| 4.4-9 | `calculate_support_resistance()` | 计算支撑压力位 |
| 4.5-10 | `setup_alert()` | 设置实时预警 |

## 目录结构

```
Stock_analysis_laozhang/
├── SKILL.md                      # OpenClaw Skill 定义文件
├── scripts/                      # 可执行脚本
│   └── stock_analyzer.py         # 命令行工具
├── src/                          # 源代码目录
│   └── openclaw_stock/           # 主包（包含10个接口实现）
│       ├── __init__.py           # 统一导出所有接口
│       ├── data/                 # 数据采集模块（3个接口）
│       │   ├── market_data.py
│       │   ├── financial_data.py
│       │   └── fund_flow.py
│       ├── analysis/             # 分析模块（4个接口）
│       │   ├── technical_analysis.py
│       │   ├── fundamental_analysis.py
│       │   └── stock_analyzer.py
│       ├── selection/            # 选股模块（2个接口）
│       │   ├── short_term.py
│       │   ├── long_term.py
│       │   └── scoring_model.py
│       ├── alert/                # 预警模块（1个接口）
│       │   └── alert_system.py
│       ├── core/                 # 核心模块
│       ├── adapters/             # 数据源适配器
│       ├── tools/                # 工具模块
│       └── utils/                # 工具函数
├── tests/                        # 测试目录
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── e2e/                      # 端到端测试
├── design_doc/                   # 设计文档
├── FEATURES.md                   # 功能清单
├── PROJECT_STRUCTURE.md          # 项目结构说明
└── pyproject.toml               # Python 项目配置
```

## 安装说明

### 1. 克隆仓库

```bash
git clone https://github.com/bjwanneng/openclaw-stock-research.git
cd openclaw-stock-research
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -e .
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量
```

## 使用方式

### 1. Python 模块导入

```python
from src.openclaw_stock import (
    fetch_market_data,
    fetch_realtime_quote,
    calculate_technical_indicators,
    analyze_stock,
    short_term_stock_selector,
    long_term_stock_selector,
    setup_alert
)

# 获取实时行情
quote = fetch_realtime_quote(symbol='000001', market='sz')

# 个股综合分析
result = analyze_stock(symbol='000001', market='sz')

# 短期选股
df = short_term_stock_selector(top_n=50)
```

### 2. 命令行工具

```bash
# 分析个股
python scripts/stock_analyzer.py analyze 000001 --market sz

# 短期选股
python scripts/stock_analyzer.py select-short --top-n 50

# 设置预警
python scripts/stock_analyzer.py alert-setup 000001 price "above:15.0"
```

### 3. OpenClaw Skill

```
/stock-analysis analyze 000001
/stock-analysis select-short
/stock-analysis alert-setup 000001 price above:15
```

## 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 带覆盖率报告
pytest --cov=src/openclaw_stock --cov-report=html
```

## 项目文档

- `design_doc/stock_anlysis_design.md` - 设计文档（含10个接口定义）
- `SKILL.md` - OpenClaw Skill 定义
- `FEATURES.md` - 功能清单
- `PROJECT_STRUCTURE.md` - 项目结构说明

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- [AkShare](https://www.akshare.xyz/) - 强大的金融数据接口库
- [OpenClaw](https://github.com/openclaw) - 智能助手框架
- [东方财富](https://www.eastmoney.com/) - 数据来源
- [腾讯财经](https://finance.qq.com/) - 数据来源
- [新浪财经](https://finance.sina.com.cn/) - 数据来源

## 联系方式

- 项目主页: https://github.com/bjwanneng/openclaw-stock-research
- 问题反馈: https://github.com/bjwanneng/openclaw-stock-research/issues
- 邮箱: bjzhangwn@gmail.com

---

**免责声明**: 本工具仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。
