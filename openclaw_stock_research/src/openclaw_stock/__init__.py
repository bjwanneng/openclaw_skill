"""
OpenClaw Stock Research - 股票分析与选股系统

基于akshare开源数据库的股票分析和选股系统skill，
涵盖股票后市研判、短期选股和中长期选股三大核心功能。

主要模块:
- data: 数据采集模块（行情、财务、资金流向）
- analysis: 分析模块（技术面、基本面、综合分析）
- selection: 选股模块（短期选股、中长期选股）
- alert: 预警模块（实时预警）

使用示例:
    from openclaw_stock import (
        analyze_stock,
        short_term_stock_selector,
        long_term_stock_selector,
        setup_alert
    )

    # 个股分析
    result = analyze_stock('000001', market='sz')

    # 短期选股
    df = short_term_stock_selector(top_n=50)

    # 设置预警
    alert_id = setup_alert('000001', 'price', {'operator': 'above', 'value': 15.0})

版本: 1.0.0
作者: OpenClaw Team
"""

__version__ = "1.0.0"
__author__ = "OpenClaw Team"

# 核心接口导出

# 数据采集接口 (4.1节)
from .data import (
    # 行情数据
    fetch_market_data,
    fetch_realtime_quote,
    fetch_kline_data,
    MarketDataCollector,
    # 财务数据
    fetch_financial_data,
    fetch_financial_report,
    FinancialDataCollector,
    # 资金流向
    fetch_fund_flow,
    fetch_capital_flow,
    fetch_north_bound_flow,
    FundFlowCollector,
    # 新闻数据
    fetch_stock_news,
    NewsDataCollector,
)

# 指标计算接口 (4.2节)
from .analysis import (
    # 技术指标
    calculate_technical_indicators,
    calculate_support_resistance,
    TechnicalAnalyzer,
    # 基本面指标
    calculate_fundamental_indicators,
    FundamentalAnalyzer,
    # 综合分析
    analyze_stock,
    StockAnalyzer,
    PredictionResult,
)

# 选股接口 (4.3节)
from .selection import (
    # 短期选股
    short_term_stock_selector,
    ShortTermSelector,
    TechnicalBreakthroughStrategy,
    CapitalDrivenStrategy,
    EventDrivenStrategy,
    SentimentResonanceStrategy,
    # 中长期选股
    long_term_stock_selector,
    LongTermSelector,
    ValueInvestingStrategy,
    GrowthInvestingStrategy,
    TrendInvestingStrategy,
    DistressReversalStrategy,
    # 评分模型
    ScoringModel,
)

# 预警接口 (4.5节)
from .alert import (
    setup_alert,
    remove_alert,
    list_alerts,
    AlertSystem,
    PriceAlert,
    VolumeAlert,
    TechnicalAlert,
)

# 数据模型（纯字典版本）
from .core.models import (
    create_stock_symbol,
    create_realtime_quote,
    create_fundamental_data,
    create_capital_flow_data,
)

__all__ = [
    # 版本信息
    "__version__",
    "__author__",

    # 数据采集接口 (4.1节)
    "fetch_market_data",
    "fetch_realtime_quote",
    "fetch_kline_data",
    "MarketDataCollector",
    "fetch_financial_data",
    "fetch_financial_report",
    "FinancialDataCollector",
    "fetch_fund_flow",
    "fetch_capital_flow",
    "fetch_north_bound_flow",
    "FundFlowCollector",
    "fetch_stock_news",
    "NewsDataCollector",

    # 指标计算接口 (4.2节)
    "calculate_technical_indicators",
    "calculate_support_resistance",
    "TechnicalAnalyzer",
    "calculate_fundamental_indicators",
    "FundamentalAnalyzer",
    "analyze_stock",
    "StockAnalyzer",
    "PredictionResult",

    # 选股接口 (4.3节)
    "short_term_stock_selector",
    "ShortTermSelector",
    "TechnicalBreakthroughStrategy",
    "CapitalDrivenStrategy",
    "EventDrivenStrategy",
    "SentimentResonanceStrategy",
    "long_term_stock_selector",
    "LongTermSelector",
    "ValueInvestingStrategy",
    "GrowthInvestingStrategy",
    "TrendInvestingStrategy",
    "DistressReversalStrategy",
    "ScoringModel",

    # 预警接口 (4.5节)
    "setup_alert",
    "remove_alert",
    "list_alerts",
    "AlertSystem",
    "PriceAlert",
    "VolumeAlert",
    "TechnicalAlert",

    # 数据模型（纯字典版本）
    "create_stock_symbol",
    "create_realtime_quote",
    "create_fundamental_data",
    "create_capital_flow_data",
]
