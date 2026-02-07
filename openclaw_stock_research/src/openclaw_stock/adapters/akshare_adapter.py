"""
AkShare数据适配器

封装AkShare库的调用，统一数据格式和错误处理
"""

from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None

from ..core.exceptions import DataSourceError, SymbolNotFoundError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AKShareAdapter:
    """
    AkShare数据适配器类

    封装所有AkShare原始调用，提供统一的接口和数据格式
    """

    # 市场代码映射
    MARKET_MAP = {
        "sh": "sh",
        "sz": "sz",
        "hk": "hk"
    }

    # K线周期映射
    PERIOD_MAP = {
        "daily": "daily",
        "weekly": "weekly",
        "monthly": "monthly"
    }

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._ak = None  # 延迟导入akshare


def _get_ak(self):
    """延迟导入akshare"""
    global ak
    if self._ak is None:
        if ak is not None:
            self._ak = ak
        else:
            try:
                import akshare as ak_module
            except ImportError as e:
                logger.error(f"[AKShareAdapter] 无法导入AkShare: {str(e)}")
                raise DataSourceError(f"无法导入AkShare： {str(e)}")
            else:
                ak = ak_module
                self._ak = ak_module
        if self._ak:
            logger.debug("[AKShareAdapter] AkShare库加载成功")
    return self._ak

    def _format_hk_symbol(self, symbol: str) -> str:
        """
        格式化港股代码

        港股代码需去除前导零（如"00700"传为"700"）

        Args:
            symbol: 原始股票代码

        Returns:
            格式化后的代码
        """
        return symbol.lstrip("0") or "0"

    def get_stock_zh_a_spot(self) -> pd.DataFrame:
        """
        获取A股实时行情快照

        Returns:
            DataFrame包含所有A股的实时行情
        """
        try:
            ak = self._get_ak()
            logger.debug("[AKShareAdapter] 获取A股实时行情...")
            df = ak.stock_zh_a_spot_em()
            logger.info(f"[AKShareAdapter] 成功获取A股实时行情，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取A股行情失败: {str(e)}")
            raise DataSourceError(f"获取A股行情失败: {str(e)}")

    def get_stock_hk_spot(self) -> pd.DataFrame:
        """
        获取港股实时行情快照

        Returns:
            DataFrame包含港股的实时行情
        """
        try:
            ak = self._get_ak()
            logger.debug("[AKShareAdapter] 获取港股实时行情...")
            df = ak.stock_hk_spot_em()
            logger.info(f"[AKShareAdapter] 成功获取港股实时行情，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取港股行情失败: {str(e)}")
            raise DataSourceError(f"获取港股行情失败: {str(e)}")

    def get_stock_zh_a_hist(
        self,
        symbol: str,
        period: Literal["daily", "weekly", "monthly"] = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: Literal["", "qfq", "hfq"] = "qfq"
    ) -> pd.DataFrame:
        """
        获取A股历史K线数据

        Args:
            symbol: 股票代码（如 "000001"）
            period: K线周期（daily/weekly/monthly）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            adjust: 复权方式（""-不复权, qfq-前复权, hfq-后复权）

        Returns:
            DataFrame包含K线数据
        """
        try:
            ak = self._get_ak()
            logger.debug(f"[AKShareAdapter] 获取 {symbol} 的 {period} K线数据...")

            # 设置默认日期范围
            if not start_date:
                start_date = "19700101"
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")

            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=self.PERIOD_MAP.get(period, "daily"),
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            logger.info(f"[AKShareAdapter] 成功获取 {symbol} 的 {len(df)} 条K线数据")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取K线数据失败: {str(e)}")
            raise DataSourceError(f"获取{symbol}的K线数据失败: {str(e)}")

    def get_stock_hk_hist(
        self,
        symbol: str,
        period: Literal["daily", "weekly", "monthly"] = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: Literal["", "qfq", "hfq"] = "qfq"
    ) -> pd.DataFrame:
        """
        获取港股历史K线数据

        Args:
            symbol: 股票代码（如 "00700"）
            period: K线周期
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）
            adjust: 复权方式

        Returns:
            DataFrame包含K线数据
        """
        try:
            ak = self._get_ak()
            logger.debug(f"[AKShareAdapter] 获取港股 {symbol} 的 {period} K线数据...")

            # 设置默认日期范围
            if not start_date:
                start_date = "19700101"
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")

            # 港股代码处理（去除前导零）
            symbol_clean = self._format_hk_symbol(symbol)

            df = ak.stock_hk_hist(
                symbol=symbol_clean,
                period=self.PERIOD_MAP.get(period, "daily"),
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            logger.info(f"[AKShareAdapter] 成功获取港股 {symbol} 的 {len(df)} 条K线数据")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取港股K线数据失败: {str(e)}")
            raise DataSourceError(f"获取港股{symbol}的K线数据失败: {str(e)}")

    def get_stock_individual_info_em(self, symbol: str) -> pd.DataFrame:
        """
        获取个股基本信息（PE/PB/股息率等）

        Args:
            symbol: 股票代码

        Returns:
            DataFrame包含个股信息
        """
        try:
            ak = self._get_ak()
            logger.debug(f"[AKShareAdapter] 获取 {symbol} 的基本面数据...")
            df = ak.stock_individual_info_em(symbol=symbol)
            logger.info(f"[AKShareAdapter] 成功获取 {symbol} 的基本面数据")
            return df
        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取基本面数据失败: {str(e)}")
            raise DataSourceError(f"获取{symbol}的基本面数据失败: {str(e)}")

    def get_stock_hsgt_hist_em(self) -> pd.DataFrame:
        """
        获取北向资金历史数据

        Returns:
            DataFrame包含北向资金数据
        """
        try:
            ak = self._get_ak()
            logger.debug("[AKShareAdapter] 获取北向资金数据...")
            df = ak.stock_hsgt_hist_em()
            logger.info(f"[AKShareAdapter] 成功获取北向资金数据，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取北向资金数据失败: {str(e)}")
            raise DataSourceError(f"获取北向资金数据失败: {str(e)}")

    def get_stock_fund_flow_individual(self, symbol: str) -> pd.DataFrame:
        """
        获取个股资金流向数据

        Args:
            symbol: 股票代码

        Returns:
            DataFrame包含资金流向数据
        """
        try:
            ak = self._get_ak()
            logger.debug(f"[AKShareAdapter] 获取 {symbol} 的资金流向数据...")

            # 市场前缀处理
            if symbol.startswith("6"):
                symbol_full = f"sh{symbol}"
            else:
                symbol_full = f"sz{symbol}"

            df = ak.stock_fund_flow_individual(symbol=symbol_full)
            logger.info(f"[AKShareAdapter] 成功获取 {symbol} 的资金流向数据")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取资金流向数据失败: {str(e)}")
            raise DataSourceError(f"获取{symbol}的资金流向数据失败: {str(e)}")


# 全局适配器实例
_adapter: Optional[AKShareAdapter] = None


def get_adapter() -> AKShareAdapter:
    """
    获取全局AKShare适配器实例

    使用单例模式确保适配器只被初始化一次

    Returns:
        AKShareAdapter实例
    """
    global _adapter
    if _adapter is None:
        _adapter = AKShareAdapter()
    return _adapter


def reset_adapter():
    """
    重置适配器实例

    主要用于测试场景，清除适配器缓存
    """
    global _adapter
    _adapter = None
