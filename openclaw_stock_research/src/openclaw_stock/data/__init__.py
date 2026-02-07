"""
数据采集模块

提供股票行情、财务数据、资金流向、新闻等数据的采集功能
"""

from .market_data import (
    fetch_market_data,
    fetch_realtime_quote,
    fetch_kline_data,
    MarketDataCollector
)
from .financial_data import (
    fetch_financial_data,
    fetch_financial_report,
    FinancialDataCollector
)
from .fund_flow import (
    fetch_fund_flow,
    fetch_capital_flow,
    fetch_north_bound_flow,
    FundFlowCollector
)
from .news_data import (
    fetch_stock_news,
    NewsDataCollector
)

__all__ = [
    # 市场数据
    'fetch_market_data',
    'fetch_realtime_quote',
    'fetch_kline_data',
    'MarketDataCollector',
    # 财务数据
    'fetch_financial_data',
    'fetch_financial_report',
    'FinancialDataCollector',
    # 资金流向
    'fetch_fund_flow',
    'fetch_capital_flow',
    'fetch_north_bound_flow',
    'FundFlowCollector',
    # 新闻数据
    'fetch_stock_news',
    'NewsDataCollector',
]
