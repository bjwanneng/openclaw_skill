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
from .lhb_data import fetch_lhb_data
from .margin_data import fetch_margin_data
from .northbound_data import fetch_northbound_data
from .block_trade_data import fetch_block_trade_data
from .shareholder_data import fetch_shareholder_data
from .institution_data import fetch_institution_data
from .restricted_shares_data import fetch_restricted_shares_data
from .industry_compare_data import fetch_industry_compare_data
from .dividend_data import fetch_dividend_data

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
    # === 新增9大数据源 ===
    # 龙虎榜
    'fetch_lhb_data',
    # 融资融券
    'fetch_margin_data',
    # 北向资金
    'fetch_northbound_data',
    # 大宗交易
    'fetch_block_trade_data',
    # 股东人数
    'fetch_shareholder_data',
    # 机构持仓
    'fetch_institution_data',
    # 限售解禁
    'fetch_restricted_shares_data',
    # 行业对比
    'fetch_industry_compare_data',
    # 分红送转
    'fetch_dividend_data',
]
