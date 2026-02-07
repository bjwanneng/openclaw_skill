# 项目结构说明

## 目录结构

```
Stock_analysis_laozhang/
├── skill/                          # Skill 定义目录
│   ├── SKILL.md                   # Skill 配置文件（符合 OpenClaw 规范）
│   └── scripts/                   # 可执行脚本
│       └── stock_analyzer.py      # 股票分析命令行工具
│
├── src/                           # 源代码目录
│   └── openclaw_stock/            # 主包
│       ├── __init__.py            # 统一导出所有10个接口
│       ├── core/                  # 核心模块
│       │   ├── config.py          # 配置管理
│       │   ├── exceptions.py      # 自定义异常
│       │   └── models.py          # Pydantic 数据模型
│       ├── adapters/              # 数据源适配器
│       │   ├── akshare_adapter.py
│       │   ├── akshare_adapter_em.py
│       │   └── akshare_adapter_fixed.py
│       ├── data/                  # 数据采集模块（3个接口）
│       │   ├── __init__.py
│       │   ├── market_data.py     # 接口1: fetch_market_data
│       │   ├── financial_data.py  # 接口2: fetch_financial_data
│       │   └── fund_flow.py       # 接口3: fetch_fund_flow
│       ├── analysis/              # 分析模块（4个接口）
│       │   ├── __init__.py
│       │   ├── technical_analysis.py    # 接口4, 9
│       │   ├── fundamental_analysis.py  # 接口5
│       │   └── stock_analyzer.py          # 接口8
│       ├── selection/             # 选股模块（2个接口）
│       │   ├── __init__.py
│       │   ├── short_term.py      # 接口6
│       │   ├── long_term.py       # 接口7
│       │   └── scoring_model.py
│       ├── alert/                 # 预警模块（1个接口）
│       │   ├── __init__.py
│       │   └── alert_system.py    # 接口10
│       ├── tools/                 # 工具模块
│       │   ├── ak_market_tool.py
│       │   └── web_quote_validator.py
│       └── utils/                 # 工具函数
│           ├── decorators.py
│           ├── logger.py
│           └── venv_helper.py
│
├── tests/                         # 测试目录
│   ├── unit/                      # 单元测试
│   │   └── test_stock_modules.py
│   ├── integration/               # 集成测试
│   │   ├── test_ak_market_tool.py
│   │   ├── test_web_quote_validator.py
│   │   └── test_stock_modules.py
│   ├── e2e/                       # 端到端测试
│   ├── __init__.py
│   ├── conftest.py                # pytest 配置
│   └── README.md                  # 测试说明
│
├── design_doc/                    # 设计文档
│   ├── stock_anlysis_design.md  # 设计文档（含10个接口定义）
│   ├── skill_spec.md            # Skill 规范
│   └── refence_skill/           # 参考 Skill
│
├── FEATURES.md                  # 功能清单
├── PROJECT_STRUCTURE.md         # 本文件
├── readme.md                    # 项目说明
└── pyproject.toml               # Python 项目配置
```

## 10个核心接口位置

| 接口编号 | 接口名称 | 实现文件 |
|---------|---------|---------|
| 4.1-1 | `fetch_market_data()` | `src/openclaw_stock/data/market_data.py` |
| 4.1-2 | `fetch_financial_data()` | `src/openclaw_stock/data/financial_data.py` |
| 4.1-3 | `fetch_fund_flow()` | `src/openclaw_stock/data/fund_flow.py` |
| 4.2-4 | `calculate_technical_indicators()` | `src/openclaw_stock/analysis/technical_analysis.py` |
| 4.2-5 | `calculate_fundamental_indicators()` | `src/openclaw_stock/analysis/fundamental_analysis.py` |
| 4.3-6 | `short_term_stock_selector()` | `src/openclaw_stock/selection/short_term.py` |
| 4.3-7 | `long_term_stock_selector()` | `src/openclaw_stock/selection/long_term.py` |
| 4.4-8 | `analyze_stock()` | `src/openclaw_stock/analysis/stock_analyzer.py` |
| 4.4-9 | `calculate_support_resistance()` | `src/openclaw_stock/analysis/technical_analysis.py` |
| 4.5-10 | `setup_alert()` | `src/openclaw_stock/alert/alert_system.py` |

## 使用方式

### 1. 作为 Python 模块导入

```python
from src.openclaw_stock import (
    analyze_stock,
    short_term_stock_selector,
    long_term_stock_selector,
    setup_alert
)

# 个股分析
result = analyze_stock(symbol='000001', market='sz')

# 短期选股
df = short_term_stock_selector(top_n=50)

# 设置预警
alert_id = setup_alert(
    symbol='000001',
    alert_type='price',
    condition={'operator': 'above', 'value': 15.0}
)
```

### 2. 使用命令行工具

```bash
# 分析个股
python skill/scripts/stock_analyzer.py analyze 000001 --market sz

# 短期选股
python skill/scripts/stock_analyzer.py select-short --top-n 50

# 中长期选股
python skill/scripts/stock_analyzer.py select-long --min-roe 15 --max-pe 30

# 设置预警
python skill/scripts/stock_analyzer.py alert-setup 000001 price "above:15.0"
```

### 3. 作为 OpenClaw Skill 使用

```
/stock-analysis analyze 000001
/stock-analysis select-short
/stock-analysis alert-setup 000001 price above:15
```

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行端到端测试
pytest tests/e2e/
```
