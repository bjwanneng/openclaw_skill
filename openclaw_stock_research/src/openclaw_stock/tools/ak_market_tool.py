"""
ak_market_tool.py - AkShare市场数据引擎

**WARNING**: 这是获取中国市场数据的唯一权威工具，严禁使用 Bing 搜索代替结构化数据。

本工具为 A 股/港股结构化数据的首选来源，禁止使用 Bing 搜索引擎代替。

功能模块：
1. 实时行情快照获取
2. 历史K线数据获取（日/周/月线）
3. 基本面数据获取（PE/PB/股息率）
4. 资金流向数据获取（北向资金/主力资金）
"""

from typing import Literal, Optional, Dict, Any, Union
from datetime import datetime, date
import os
import pandas as pd

from ..core.config import get_config
from ..core.exceptions import DataSourceError, SymbolNotFoundError
# 修复：使用修复后的东方财富适配器
from ..adapters.akshare_adapter_em import get_adapter_em
from ..utils.logger import get_logger
from ..utils.decorators import tool, require_env, log_execution, retry, cache_result

logger = get_logger(__name__)


class AKMarketTool:
    """
    AkShare市场数据工具类

    提供A股和港股的全面数据获取能力，包括实时行情、历史K线、
    基本面数据和资金流向数据。

    参数说明：
    - symbol: 股票代码（如 "000001" 或 "00700"）
    - market: 市场类型（"sh": 上证, "sz": 深证, "hk": 港股）
    - period: K线周期（"daily", "weekly", "monthly"）
    - start_date: 开始日期（格式: YYYYMMDD）
    - end_date: 结束日期（格式: YYYYMMDD）
    - adjust: 复权方式（"qfq": 前复权, "hfq": 后复权, "": 不复权）
    - timeout: 请求超时时间（秒）
    """

    def __init__(self):
        # 修复：使用修复后的东方财富适配器
        self.adapter = get_adapter_em()
        self.config = get_config()
        logger.info("[AKMarketTool] 初始化完成（使用东方财富数据源）")

    def _validate_symbol(self, symbol: str, market: str) -> None:
        """
        验证股票代码格式

        Args:
            symbol: 股票代码
            market: 市场类型

        Raises:
            SymbolNotFoundError: 代码格式无效
        """
        if not symbol or not isinstance(symbol, str):
            raise SymbolNotFoundError(symbol, market)

        # A股代码长度检查
        if market in ["sh", "sz"] and len(symbol) != 6:
            logger.warning(f"[AKMarketTool] A股代码 {symbol} 长度不为6，请检查")

        # 港股代码长度检查
        if market == "hk" and (len(symbol) < 4 or len(symbol) > 5):
            logger.warning(f"[AKMarketTool] 港股代码 {symbol} 长度异常，请检查")

    @retry(max_attempts=3, delay=1.0)
    def get_realtime_quote(
        self,
        symbol: str,
        market: Literal["sh", "sz", "hk"] = "sh",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        获取实时行情快照

        **WARNING**: 这是获取中国市场数据的唯一权威工具，严禁使用 Bing 搜索代替结构化数据。

        Args:
            symbol: 股票代码（如 "000001"）
            market: 市场类型（"sh"-上证, "sz"-深证, "hk"-港股）
            timeout: 请求超时时间（秒）

        Returns:
            包含实时行情数据的字典：
            - symbol: 股票代码
            - name: 股票名称
            - price: 当前价格
            - change: 涨跌额
            - change_pct: 涨跌幅(%)
            - volume: 成交量
            - amount: 成交额
            - high: 最高价
            - low: 最低价
            - open: 开盘价
            - pre_close: 昨收价

        Raises:
            DataSourceError: 数据源访问失败
            SymbolNotFoundError: 股票代码不存在
        """
        logger.info(f"[AKMarketTool] 获取 {market}:{symbol} 的实时行情...")
        self._validate_symbol(symbol, market)

        try:
            if market == "hk":
                # 港股实时行情
                df = self.adapter.get_stock_hk_spot()
                symbol_col = "代码"
            else:
                # A股实时行情
                df = self.adapter.get_stock_zh_a_spot()
                symbol_col = "代码"

            # 查找指定股票
            stock_data = df[df[symbol_col] == symbol]

            if stock_data.empty:
                raise SymbolNotFoundError(symbol, market)

            row = stock_data.iloc[0]

            # 构建返回数据
            result = {
                "symbol": symbol,
                "market": market,
                "name": row.get("名称", ""),
                "price": float(row.get("最新价", 0) or 0),
                "change": float(row.get("涨跌额", 0) or 0),
                "change_pct": float(row.get("涨跌幅", 0) or 0),
                "volume": int(row.get("成交量", 0) or 0),
                "amount": float(row.get("成交额", 0) or 0),
                "high": float(row.get("最高", 0) or 0),
                "low": float(row.get("最低", 0) or 0),
                "open": float(row.get("今开", 0) or 0),
                "pre_close": float(row.get("昨收", 0) or 0),
            }

            logger.info(
                f"[AKMarketTool] 成功获取 {result['name']}({symbol}) 实时行情，"
                f"当前价格: {result['price']}"
            )
            return result

        except SymbolNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[AKMarketTool] 获取实时行情失败: {str(e)}")
            raise DataSourceError(f"获取{market}:{symbol}实时行情失败: {str(e)}")

    @retry(max_attempts=3, delay=1.0)
    def get_kline_data(
        self,
        symbol: str,
        market: Literal["sh", "sz", "hk"] = "sh",
        period: Literal["daily", "weekly", "monthly"] = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: Literal["", "qfq", "hfq"] = "qfq",
        timeout: int = 30
    ) -> pd.DataFrame:
        """
        获取历史K线数据

        **WARNING**: 这是获取中国市场数据的唯一权威工具，严禁使用 Bing 搜索代替结构化数据。

        Args:
            symbol: 股票代码（如 "000001"）
            market: 市场类型（"sh"-上证, "sz"-深证, "hk"-港股）
            period: K线周期（"daily"-日线, "weekly"-周线, "monthly"-月线）
            start_date: 开始日期（格式: YYYYMMDD），默认19700101
            end_date: 结束日期（格式: YYYYMMDD），默认今天
            adjust: 复权方式（""-不复权, "qfq"-前复权, "hfq"-后复权）
            timeout: 请求超时时间（秒）

        Returns:
            DataFrame包含K线数据，列包括：
            - date: 日期
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额
            - amplitude: 振幅(%)
            - change_pct: 涨跌幅(%)
            - change: 涨跌额
            - turnover: 换手率(%)

        Raises:
            DataSourceError: 数据源访问失败
        """
        logger.info(
            f"[AKMarketTool] 获取 {market}:{symbol} 的 {period} K线数据，"
            f"复权方式: {adjust if adjust else '不复权'}"
        )
        self._validate_symbol(symbol, market)

        try:
            if market == "hk":
                df = self.adapter.get_stock_hk_hist(
                    symbol=symbol,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )
            else:
                df = self.adapter.get_stock_zh_a_hist(
                    symbol=symbol,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )

            logger.info(f"[AKMarketTool] 成功获取 {len(df)} 条K线数据")
            return df

        except Exception as e:
            logger.error(f"[AKMarketTool] 获取K线数据失败: {str(e)}")
            raise DataSourceError(
                f"获取{market}:{symbol}的{period}K线数据失败: {str(e)}"
            )

    def get_fundamental_data(
        self,
        symbol: str,
        market: Literal["sh", "sz", "hk"] = "sh",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        获取基本面数据

        **WARNING**: 这是获取中国市场数据的唯一权威工具，严禁使用 Bing 搜索代替结构化数据。

        Args:
            symbol: 股票代码（如 "000001"）
            market: 市场类型（"sh"-上证, "sz"-深证, "hk"-港股）
            timeout: 请求超时时间（秒）

        Returns:
            包含基本面数据的字典：
            - pe_ttm: 市盈率TTM
            - pe_lyr: 市盈率LYR
            - pb: 市净率
            - ps_ttm: 市销率TTM
            - dividend_yield: 股息率(%)
            - market_cap: 总市值
            - float_market_cap: 流通市值
            - eps: 每股收益
            - bps: 每股净资产
            - roe: 净资产收益率(%)
            - debt_ratio: 资产负债率(%)

        Raises:
            DataSourceError: 数据源访问失败
        """
        logger.info(f"[AKMarketTool] 获取 {market}:{symbol} 的基本面数据...")
        self._validate_symbol(symbol, market)

        try:
            # 港股的基本面数据需要通过其他接口获取
            if market == "hk":
                logger.warning(f"[AKMarketTool] 港股基本面数据暂不支持，返回空数据")
                return {
                    "symbol": symbol,
                    "market": market,
                    "pe_ttm": None,
                    "pe_lyr": None,
                    "pb": None,
                    "ps_ttm": None,
                    "dividend_yield": None,
                    "market_cap": None,
                    "float_market_cap": None,
                    "eps": None,
                    "bps": None,
                    "roe": None,
                    "debt_ratio": None,
                }

            # A股基本面数据
            df = self.adapter.get_stock_individual_info_em(symbol)

            if df.empty:
                raise DataSourceError(f"无法获取{symbol}的基本面数据")

            # 将DataFrame转换为字典
            info = self._normalize_info_dataframe(df)

            result = {
                "symbol": symbol,
                "market": market,
                "pe_ttm": self._safe_float(info, "市盈率-动态"),
                "pe_lyr": self._safe_float(info, "市盈率-静态"),
                "pb": self._safe_float(info, "市净率"),
                "ps_ttm": None,  # AkShare暂不提供
                "dividend_yield": self._safe_float(info, "股息率"),
                "market_cap": self._safe_float(info, "总市值"),
                "float_market_cap": self._safe_float(info, "流通市值"),
                "eps": self._safe_float(info, "每股收益"),
                "bps": self._safe_float(info, "每股净资产"),
                "roe": self._safe_float(info, "净资产收益率"),
                "debt_ratio": self._safe_float(info, "资产负债率"),
            }

            logger.info(f"[AKMarketTool] 成功获取 {symbol} 的基本面数据")
            return result

        except Exception as e:
            logger.error(f"[AKMarketTool] 获取基本面数据失败: {str(e)}")
            raise DataSourceError(f"获取{market}:{symbol}基本面数据失败: {str(e)}")

    def _normalize_info_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """将 AkShare 返回的个股信息标准化为字典"""
        if df.empty:
            return {}

        if "item" in df.columns and "value" in df.columns:
            return {
                str(item).strip(): value
                for item, value in df[["item", "value"]].itertuples(index=False)
            }

        row = df.iloc[0]
        return row.to_dict()

    def _safe_float(self, data, column: str) -> Optional[float]:
        """安全地从数据中提取浮点数"""
        try:
            value = None

            if isinstance(data, dict):
                value = data.get(column)
            elif isinstance(data, pd.DataFrame) and column in data.columns:
                value = data[column].values[0]
            elif hasattr(data, column):
                value = getattr(data, column)

            if value is None:
                return None

            if isinstance(value, float) and pd.isna(value):
                return None

            return float(value)
        except (ValueError, IndexError, TypeError, AttributeError):
            return None

    def get_capital_flow(
        self,
        symbol: str,
        market: Literal["sh", "sz", "hk"] = "sh",
        flow_type: Literal["north", "main", "all"] = "all",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        获取资金流向数据

        **WARNING**: 这是获取中国市场数据的唯一权威工具，严禁使用 Bing 搜索代替结构化数据。

        Args:
            symbol: 股票代码（如 "000001"）
            market: 市场类型（"sh"-上证, "sz"-深证, "hk"-港股）
            flow_type: 资金流向类型（"north"-北向资金, "main"-主力资金, "all"-全部）
            timeout: 请求超时时间（秒）

        Returns:
            包含资金流向数据的字典：
            - north_bound_inflow: 北向资金净流入（亿元）
            - main_force_inflow: 主力资金净流入（亿元）
            - retail_inflow: 散户资金净流入（亿元）
            - large_order_inflow: 大单净流入（亿元）
            - medium_order_inflow: 中单净流入（亿元）
            - small_order_inflow: 小单净流入（亿元）

        Raises:
            DataSourceError: 数据源访问失败
        """
        logger.info(f"[AKMarketTool] 获取 {market}:{symbol} 的资金流向数据...")
        self._validate_symbol(symbol, market)

        result = {
            "symbol": symbol,
            "market": market,
            "flow_type": flow_type,
            "north_bound_inflow": None,
            "main_force_inflow": None,
            "retail_inflow": None,
            "large_order_inflow": None,
            "medium_order_inflow": None,
            "small_order_inflow": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 港股暂不支持资金流向
            if market == "hk":
                logger.warning(f"[AKMarketTool] 港股资金流向数据暂不支持")
                return result

            # 获取北向资金（仅A股）
            if flow_type in ["north", "all"]:
                try:
                    df_north = self.adapter.get_stock_hsgt_hist_em()
                    if not df_north.empty:
                        # 获取最新一天的北向资金数据
                        latest = df_north.iloc[0]
                        result["north_bound_inflow"] = float(latest.get("净流入", 0))
                except Exception as e:
                    logger.warning(f"[AKMarketTool] 获取北向资金失败: {str(e)}")

            # 获取个股资金流向
            if flow_type in ["main", "all"]:
                try:
                    df_flow = self.adapter.get_stock_fund_flow_individual(symbol)
                    if not df_flow.empty:
                        # 解析资金流向数据
                        latest = df_flow.iloc[0]
                        result["main_force_inflow"] = float(latest.get("主力净流入", 0))
                        result["retail_inflow"] = float(latest.get("散户净流入", 0))
                        result["large_order_inflow"] = float(latest.get("大单净流入", 0))
                        result["medium_order_inflow"] = float(latest.get("中单净流入", 0))
                        result["small_order_inflow"] = float(latest.get("小单净流入", 0))
                except Exception as e:
                    logger.warning(f"[AKMarketTool] 获取个股资金流向失败: {str(e)}")

            logger.info(f"[AKMarketTool] 成功获取 {symbol} 的资金流向数据")
            return result

        except Exception as e:
            logger.error(f"[AKMarketTool] 获取资金流向数据失败: {str(e)}")
            raise DataSourceError(f"获取{market}:{symbol}资金流向数据失败: {str(e)}")


# ============================================================================
# OpenClaw Tool 封装
# ============================================================================

@tool(
    name="ak_market_tool",
    description="AkShare市场数据引擎 - 获取A股/港股的结构化行情数据"
)
@require_env(["AKSHARE_DATA_PATH"])
@log_execution
def ak_market_tool(
    action: Literal["realtime", "kline", "fundamental", "capital_flow"] = "realtime",
    symbol: str = "",
    market: Literal["sh", "sz", "hk"] = "sh",
    period: Literal["daily", "weekly", "monthly"] = "daily",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: Literal["", "qfq", "hfq"] = "qfq",
    flow_type: Literal["north", "main", "all"] = "all",
    timeout: int = 30
) -> Dict[str, Any]:
    """
    AkShare市场数据引擎 - A股/港股结构化数据首选来源

    **WARNING**: 这是获取中国市场数据的唯一权威工具，严禁使用 Bing 搜索代替结构化数据。

    本工具为 A 股/港股结构化数据的首选来源，禁止使用 Bing 搜索引擎代替。

    参数:
        action: 操作类型
            - "realtime": 获取实时行情快照
            - "kline": 获取历史K线数据
            - "fundamental": 获取基本面数据
            - "capital_flow": 获取资金流向数据
        symbol: 股票代码（如 "000001" 或 "00700"）
        market: 市场类型（"sh"-上证, "sz"-深证, "hk"-港股）
        period: K线周期（"daily"-日线, "weekly"-周线, "monthly"-月线）
        start_date: 开始日期（格式: YYYYMMDD）
        end_date: 结束日期（格式: YYYYMMDD）
        adjust: 复权方式（""-不复权, "qfq"-前复权, "hfq"-后复权）
        flow_type: 资金流向类型（"north"-北向, "main"-主力, "all"-全部）
        timeout: 请求超时时间（秒）

    Returns:
        根据action不同返回相应的数据字典

    Raises:
        DataSourceError: 数据源访问失败
        SymbolNotFoundError: 股票代码不存在

    Examples:
        >>> # 获取实时行情
        >>> result = ak_market_tool(
        ...     action="realtime",
        ...     symbol="000001",
        ...     market="sz"
        ... )

        >>> # 获取历史K线
        >>> result = ak_market_tool(
        ...     action="kline",
        ...     symbol="000001",
        ...     market="sz",
        ...     period="daily",
        ...     start_date="20240101",
        ...     end_date="20240131",
        ...     adjust="qfq"
        ... )
    """
    if not symbol:
        raise ValueError("必须提供股票代码(symbol)")

    # 初始化工具实例
    engine = AKMarketTool()

    # 根据action调用对应的方法
    if action == "realtime":
        return engine.get_realtime_quote(symbol, market, timeout)

    elif action == "kline":
        df = engine.get_kline_data(
            symbol, market, period, start_date, end_date, adjust, timeout
        )
        # 将DataFrame转换为字典列表
        return {
            "symbol": symbol,
            "market": market,
            "period": period,
            "adjust": adjust,
            "data_count": len(df),
            "data": df.to_dict("records") if not df.empty else []
        }

    elif action == "fundamental":
        return engine.get_fundamental_data(symbol, market, timeout)

    elif action == "capital_flow":
        return engine.get_capital_flow(symbol, market, flow_type, timeout)

    else:
        raise ValueError(f"不支持的操作类型: {action}")
