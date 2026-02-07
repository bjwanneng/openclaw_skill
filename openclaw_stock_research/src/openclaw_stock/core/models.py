"""
数据模型定义（纯Python字典版本）

不使用Pydantic，避免v1/v2兼容性问题
参考akshare的设计，使用纯Python字典和pandas DataFrame
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from decimal import Decimal


def create_stock_symbol(
    symbol: str,
    market: Literal["sh", "sz", "hk"],
    name: Optional[str] = None
) -> Dict[str, Any]:
    """创建股票代码字典"""
    return {
        "symbol": symbol.strip().upper(),
        "market": market,
        "name": name,
        "__type__": "StockSymbol"
    }


def create_realtime_quote(
    source: str,
    symbol: str,
    market: str,
    name: str,
    price: float,
    change: float,
    change_pct: float,
    volume: int,
    amount: float,
    open_price: float,
    high_price: float,
    low_price: float,
    pre_close: float,
    timestamp: Optional[datetime] = None
) -> Dict[str, Any]:
    """创建实时行情字典"""
    return {
        "source": source,
        "symbol": symbol,
        "market": market,
        "name": name,
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "volume": volume,
        "amount": amount,
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "pre_close": pre_close,
        "timestamp": timestamp or datetime.now(),
        "__type__": "RealtimeQuote"
    }


def create_fundamental_data(
    symbol: str,
    pe_ttm: Optional[float] = None,
    pe_lyr: Optional[float] = None,
    pb: Optional[float] = None,
    ps_ttm: Optional[float] = None,
    dividend_yield: Optional[float] = None,
    market_cap: Optional[float] = None,
    float_market_cap: Optional[float] = None,
    eps: Optional[float] = None,
    bps: Optional[float] = None,
    roe: Optional[float] = None,
    debt_ratio: Optional[float] = None,
) -> Dict[str, Any]:
    """创建基本面数据字典"""
    return {
        "symbol": symbol,
        "pe_ttm": pe_ttm,
        "pe_lyr": pe_lyr,
        "pb": pb,
        "ps_ttm": ps_ttm,
        "dividend_yield": dividend_yield,
        "market_cap": market_cap,
        "float_market_cap": float_market_cap,
        "eps": eps,
        "bps": bps,
        "roe": roe,
        "debt_ratio": debt_ratio,
        "__type__": "FundamentalData"
    }


def create_capital_flow_data(
    symbol: str,
    north_bound_inflow: Optional[float] = None,
    main_force_inflow: Optional[float] = None,
    retail_inflow: Optional[float] = None,
    large_order_inflow: Optional[float] = None,
    medium_order_inflow: Optional[float] = None,
    small_order_inflow: Optional[float] = None,
) -> Dict[str, Any]:
    """创建资金流向数据字典"""
    return {
        "symbol": symbol,
        "north_bound_inflow": north_bound_inflow,
        "main_force_inflow": main_force_inflow,
        "retail_inflow": retail_inflow,
        "large_order_inflow": large_order_inflow,
        "medium_order_inflow": medium_order_inflow,
        "small_order_inflow": small_order_inflow,
        "__type__": "CapitalFlowData"
    }
