"""
行情数据采集模块

实现设计文档4.1节的接口1: 行情数据采集
"""

from typing import Literal, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import requests

from ..core.exceptions import DataSourceError, SymbolNotFoundError
from ..utils.logger import get_logger
from ..utils.decorators import retry, cache_result

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


def _get_eastmoney_realtime_quote(symbol: str, market: str = "sh") -> Dict[str, Any]:
    """
    备用方案：使用 requests 直接从东方财富获取个股实时行情

    参数:
        symbol: 股票代码 (如 '000001')
        market: 市场类型 (sh/sz/hk)

    返回:
        Dict: 实时行情数据
    """
    # 转换代码格式
    if market == "hk":
        # 港股
        secid = f"116.{symbol}"
    elif symbol.startswith('6'):
        secid = f"1.{symbol}"
    else:
        secid = f"0.{symbol}"

    # 东方财富 API
    url = "http://push2.eastmoney.com/api/qt/stock/get"

    params = {
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "fltt": "2",
        "invt": "2",
        "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f170",
        "secid": secid,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "http://quote.eastmoney.com/",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not data.get('data'):
            raise DataSourceError(f"无法获取 {market}:{symbol} 的实时行情数据")

        item = data['data']

        # 解析字段
        # f43: 最新价, f44: 涨跌额, f45: 涨跌幅, f46: 成交量, f47: 成交额
        # f48: 最高, f49: 最低, f50: 今开, f51: 昨收, f52: 换手率
        # f57: 代码, f58: 名称, f60: 总市值, f170: 流通市值

        # 解析字段
        # f43: 最新价(需除以100), f44: 涨跌额(需除以100), f45: 涨跌幅(需除以100)
        # f46: 成交量, f47: 成交额, f48: 最高(需除以100), f49: 最低(需除以100)
        # f50: 今开(需除以100), f51: 昨收(需除以100), f52: 换手率
        # f57: 代码, f58: 名称, f60: 总市值

        # 东方财富API返回的数据已经是正确的数值，不需要除以100
        result = {
            "symbol": symbol,
            "market": market,
            "name": item.get('f58', ''),
            "price": float(item.get('f43', 0)) if item.get('f43') else 0,
            "change": float(item.get('f44', 0)) if item.get('f44') else 0,
            "change_pct": float(item.get('f45', 0)) if item.get('f45') else 0,
            "volume": int(float(item.get('f46', 0))) if item.get('f46') else 0,
            "amount": float(item.get('f47', 0)) if item.get('f47') else 0,
            "high": float(item.get('f48', 0)) if item.get('f48') else 0,
            "low": float(item.get('f49', 0)) if item.get('f49') else 0,
            "open": float(item.get('f50', 0)) if item.get('f50') else 0,
            "pre_close": float(item.get('f51', 0)) if item.get('f51') else 0,
            "timestamp": datetime.now().isoformat(),
        }

        return result

    except requests.exceptions.RequestException as e:
        raise DataSourceError(f"请求东方财富API失败: {str(e)}")
    except Exception as e:
        raise DataSourceError(f"解析实时行情数据失败: {str(e)}")


MINUTE_PERIOD_MAP = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "60m": "60",
}


def _format_a_share_symbol(symbol: str, market: str) -> str:
    """将纯数字代码转换为带市场前缀的A股代码"""
    symbol = symbol.strip()
    if symbol.startswith(("sh", "sz")):
        return symbol
    if market == "sh" or symbol.startswith("6"):
        return f"sh{symbol}"
    return f"sz{symbol}"


def fetch_market_data(
    symbol: str,
    period: Literal["1m", "5m", "15m", "30m", "60m", "daily", "weekly", "monthly"] = "daily",
    adjust: Literal["", "qfq", "hfq"] = "qfq",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    market: Literal["sh", "sz", "hk"] = "sh"
) -> pd.DataFrame:
    """获取股票行情数据"""
    if ak is None:
        raise DataSourceError("akshare库未安装")

    logger.info(f"[fetch_market_data] 获取 {market}:{symbol} 的 {period} 数据")

    if not start_date:
        start_date = "19700101"
    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")

    is_minute_period = period in MINUTE_PERIOD_MAP

    try:
        if is_minute_period:
            if market == "hk":
                raise DataSourceError("港股市场暂不支持分钟级别行情数据")

            symbol_with_market = _format_a_share_symbol(symbol, market)
            minute_period = MINUTE_PERIOD_MAP[period]

            df = ak.stock_zh_a_minute(
                symbol=symbol_with_market,
                period=minute_period,
                adjust=adjust or ""
            )

            if df.empty:
                raise DataSourceError(f"未获取到{symbol}的分钟级别数据")

            df = df.rename(columns={"day": "date"})
            df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            start_dt = datetime.strptime(start_date, "%Y%m%d")
            end_dt = datetime.strptime(end_date, "%Y%m%d") + timedelta(days=1)
            df = df[(df["date"] >= start_dt) & (df["date"] < end_dt)]
            df["date"] = df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif market == "hk":
            symbol_clean = symbol.lstrip("0") or "0"
            df = ak.stock_hk_hist(
                symbol=symbol_clean,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
        else:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

        if df is None or df.empty:
            raise DataSourceError(f"未获取到{market}:{symbol}的数据")

        column_mapping = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "change_pct",
            "涨跌额": "change",
            "换手率": "turnover",
        }

        if not is_minute_period:
            df = df.rename(columns=column_mapping)
        else:
            df = df.rename(columns={**column_mapping, "day": "date"})

        for col in [
            "date", "open", "high", "low", "close",
            "volume", "amount", "amplitude", "change_pct", "change", "turnover"
        ]:
            if col not in df.columns:
                df[col] = None

        logger.info(f"[fetch_market_data] 成功获取 {len(df)} 条数据")
        return df

    except SymbolNotFoundError:
        raise
    except Exception as e:
        logger.error(f"[fetch_market_data] 获取数据失败: {str(e)}")
        raise DataSourceError(f"获取{market}:{symbol}数据失败: {str(e)}")


@retry(max_attempts=3, delay=1.0)
@cache_result(ttl=300)
def fetch_realtime_quote(
    symbol: str,
    market: Literal["sh", "sz", "hk"] = "sh"
) -> Dict[str, Any]:
    """获取实时行情快照"""
    if ak is None:
        raise DataSourceError("akshare库未安装")

    logger.info(f"[fetch_realtime_quote] 获取 {market}:{symbol} 实时行情")

    try:
        # 首先尝试使用 akshare 获取实时行情
        try:
            if market == "hk":
                df = ak.stock_hk_spot_em()
                symbol_col = "代码"
                name_col = "名称"
            else:
                df = ak.stock_zh_a_spot_em()
                symbol_col = "代码"
                name_col = "名称"

            stock_data = df[df[symbol_col] == symbol]
            if stock_data.empty:
                raise SymbolNotFoundError(symbol, market)

            row = stock_data.iloc[0]
            result = {
                "symbol": symbol,
                "market": market,
                "name": row.get(name_col, ""),
                "price": float(row.get("最新价", 0) or 0),
                "change": float(row.get("涨跌额", 0) or 0),
                "change_pct": float(row.get("涨跌幅", 0) or 0),
                "volume": int(row.get("成交量", 0) or 0),
                "amount": float(row.get("成交额", 0) or 0),
                "high": float(row.get("最高", 0) or 0),
                "low": float(row.get("最低", 0) or 0),
                "open": float(row.get("今开", 0) or 0),
                "pre_close": float(row.get("昨收", 0) or 0),
                "timestamp": datetime.now().isoformat(),
            }
            logger.info(f"[fetch_realtime_quote] 成功获取 {result['name']} 实时行情 (akshare)")
            return result

        except Exception as ak_error:
            # akshare 失败，尝试备用方案
            logger.warning(f"[fetch_realtime_quote] akshare获取失败，尝试备用方案: {str(ak_error)}")
            return _get_eastmoney_realtime_quote(symbol, market)

    except SymbolNotFoundError:
        raise
    except Exception as e:
        logger.error(f"[fetch_realtime_quote] 获取实时行情失败: {str(e)}")
        raise DataSourceError(f"获取{market}:{symbol}实时行情失败: {str(e)}")


def fetch_kline_data(
    symbol: str,
    market: Literal["sh", "sz", "hk"] = "sh",
    period: Literal["daily", "weekly", "monthly"] = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: Literal["", "qfq", "hfq"] = "qfq"
) -> pd.DataFrame:
    """fetch_market_data 的别名"""
    return fetch_market_data(
        symbol=symbol,
        period=period,
        adjust=adjust,
        start_date=start_date,
        end_date=end_date,
        market=market
    )


class MarketDataCollector:
    """行情数据采集器"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def get_market_data(self, **kwargs) -> pd.DataFrame:
        return fetch_market_data(**kwargs)

    def get_realtime_quote(self, **kwargs) -> Dict[str, Any]:
        return fetch_realtime_quote(**kwargs)

    def get_kline_data(self, **kwargs) -> pd.DataFrame:
        return fetch_kline_data(**kwargs)
