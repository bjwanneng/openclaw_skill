"""
数据工具函数模块

提供股票代码验证、格式化等通用工具函数
"""

from typing import Literal, Optional
from ..core.exceptions import SymbolNotFoundError


def validate_symbol(symbol: str, market: Literal["sh", "sz", "hk", "bj"] = "sh") -> bool:
    """
    验证股票代码格式

    Args:
        symbol: 股票代码
        market: 市场类型（sh-上证, sz-深证, hk-港股, bj-北交所）

    Returns:
        bool: 是否有效

    Raises:
        SymbolNotFoundError: 代码格式无效
    """
    if not symbol or not isinstance(symbol, str):
        raise SymbolNotFoundError(symbol, market)

    # A股代码长度检查
    if market in ["sh", "sz"] and len(symbol) != 6:
        raise SymbolNotFoundError(symbol, market)

    # 北交所代码检查
    if market == "bj" and len(symbol) != 6:
        raise SymbolNotFoundError(symbol, market)

    # 港股代码长度检查
    if market == "hk" and (len(symbol) < 4 or len(symbol) > 5):
        raise SymbolNotFoundError(symbol, market)

    return True


def format_symbol(symbol: str, market: Literal["sh", "sz", "hk", "bj"] = "sh") -> str:
    """
    格式化股票代码

    Args:
        symbol: 股票代码
        market: 市场类型

    Returns:
        str: 格式化后的代码
    """
    symbol = symbol.strip()

    # 港股去除前导零
    if market == "hk":
        return symbol.lstrip("0") or "0"

    return symbol


def get_market_by_symbol(symbol: str) -> Literal["sh", "sz", "bj", "hk"]:
    """
    根据股票代码判断所属市场

    Args:
        symbol: 股票代码

    Returns:
        str: 市场类型（sh, sz, bj, hk）
    """
    symbol = symbol.strip()

    # 港股（通常4-5位数字）
    if len(symbol) <= 5 and symbol.isdigit():
        return "hk"

    # A股和北交所（6位数字）
    if len(symbol) == 6 and symbol.isdigit():
        # 北交所（8开头）
        if symbol.startswith("8") or symbol.startswith("4"):
            return "bj"
        # 上证（6开头）
        if symbol.startswith("6"):
            return "sh"
        # 深证（0、3开头）
        if symbol.startswith("0") or symbol.startswith("3"):
            return "sz"

    return "sh"  # 默认为上证


def normalize_symbol(symbol: str) -> tuple[str, str]:
    """
    标准化股票代码，返回(代码, 市场)元组

    Args:
        symbol: 股票代码（可能包含市场前缀，如sh600000）

    Returns:
        tuple: (symbol, market)
    """
    symbol = symbol.strip().lower()

    # 检查是否包含市场前缀
    if symbol.startswith("sh"):
        return symbol[2:], "sh"
    if symbol.startswith("sz"):
        return symbol[2:], "sz"
    if symbol.startswith("bj"):
        return symbol[2:], "bj"
    if symbol.startswith("hk"):
        return symbol[2:], "hk"

    # 没有前缀，自动判断
    market = get_market_by_symbol(symbol)
    return symbol, market
