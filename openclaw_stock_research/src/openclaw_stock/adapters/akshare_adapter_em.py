"""
AkShare数据适配器 - 东方财富版本

使用东方财富数据源（更稳定）
"""

from typing import Optional, Literal, Dict, Any
from datetime import datetime
import pandas as pd

from ..core.exceptions import DataSourceError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AKShareAdapterEM:
    """使用东方财富数据源的适配器"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._ak = None
        self._import_akshare()

    def _import_akshare(self):
        """导入 akshare"""
        try:
            import akshare as ak
            self._ak = ak
            logger.info("[AKShareAdapterEM] akshare 导入成功")
        except ImportError as e:
            logger.error(f"[AKShareAdapterEM] 无法导入 akshare: {e}")
            raise DataSourceError(f"无法导入 akshare: {e}")

    def _format_symbol_for_em(self, symbol: str, market: str) -> str:
        """格式化股票代码为东方财富格式"""
        if market == "hk":
            # 港股不需要前导零
            return symbol.lstrip("0") or "0"
        # A股直接使用代码
        return symbol

    def get_stock_zh_a_spot(self) -> pd.DataFrame:
        """使用东方财富获取A股实时行情

        注意: 新浪财经数据源经常被限制，所以直接使用东方财富数据源
        """
        try:
            logger.debug("[AKShareAdapterEM] 使用 stock_zh_a_spot_em (东方财富) 获取A股实时行情...")
            df = self._ak.stock_zh_a_spot_em()
            logger.info(f"[AKShareAdapterEM] 成功从东方财富获取A股实时行情，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"[AKShareAdapterEM] 东方财富数据源失败: {e}")
            raise DataSourceError(f"获取A股行情失败: {e}")

    def get_stock_hk_spot(self) -> pd.DataFrame:
        """使用东方财富获取港股实时行情"""
        try:
            logger.debug("[AKShareAdapterEM] 使用 stock_hk_spot_em 获取港股实时行情...")
            df = self._ak.stock_hk_spot_em()
            logger.info(f"[AKShareAdapterEM] 成功获取港股实时行情，共{len(df)}条记录")
            return df
        except Exception as e:
            logger.error(f"[AKShareAdapterEM] 获取港股行情失败: {e}")
            raise DataSourceError(f"获取港股行情失败: {e}")

    def get_stock_zh_a_hist(
        self,
        symbol: str,
        period: Literal["daily", "weekly", "monthly"] = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: Literal["", "qfq", "hfq"] = "qfq"
    ) -> pd.DataFrame:
        """使用东方财富获取A股历史K线数据

        使用 stock_zh_a_hist 函数（东方财富数据源）
        """
        try:
            logger.debug(f"[AKShareAdapterEM] 使用 stock_zh_a_hist 获取 {symbol} 的K线数据...")

            # 直接使用 akshare 的 stock_zh_a_hist 函数
            df = self._ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date or "19700101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust
            )

            logger.info(f"[AKShareAdapterEM] 成功获取 {symbol} 的 {len(df)} 条K线数据")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapterEM] 获取K线数据失败: {e}")
            raise DataSourceError(f"获取{symbol}的K线数据失败: {e}")

    def get_stock_hk_hist(
        self,
        symbol: str,
        period: Literal["daily", "weekly", "monthly"] = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: Literal["", "qfq", "hfq"] = "qfq"
    ) -> pd.DataFrame:
        """使用东方财富获取港股历史K线数据"""
        try:
            logger.debug(f"[AKShareAdapterEM] 使用 stock_hk_hist_em 获取 {symbol} 的K线数据...")

            # 港股需要去除前导零
            symbol_clean = self._format_symbol_for_em(symbol, "hk")

            df = self._ak.stock_hk_hist_em(
                symbol=symbol_clean,
                period=period,
                start_date=start_date or "19700101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust
            )

            logger.info(f"[AKShareAdapterEM] 成功获取港股 {symbol} 的 {len(df)} 条K线数据")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapterEM] 获取港股K线数据失败: {e}")
            raise DataSourceError(f"获取港股{symbol}的K线数据失败: {e}")

    def get_stock_individual_info_em(self, symbol: str) -> pd.DataFrame:
        """
        获取个股基本信息

        使用 akshare 的 stock_individual_info_em 函数获取个股基本信息

        参数:
            symbol: 股票代码（如 "000001"）

        返回:
            DataFrame: 个股基本信息
        """
        try:
            logger.debug(f"[AKShareAdapterEM] 获取 {symbol} 的基本信息...")

            df = self._ak.stock_individual_info_em(symbol=symbol)

            logger.info(f"[AKShareAdapterEM] 成功获取 {symbol} 的基本信息")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapterEM] 获取个股基本信息失败: {e}")
            raise DataSourceError(f"获取{symbol}基本信息失败: {e}")

    def get_stock_hsgt_hist_em(self) -> pd.DataFrame:
        """
        获取沪深港通历史数据（北向资金）

        使用 akshare 的 stock_hsgt_hist_em 函数获取北向资金历史数据

        返回:
            DataFrame: 北向资金历史数据
        """
        try:
            logger.debug("[AKShareAdapterEM] 获取北向资金历史数据...")

            df = self._ak.stock_hsgt_hist_em()

            logger.info(f"[AKShareAdapterEM] 成功获取北向资金历史数据，共{len(df)}条")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapterEM] 获取北向资金数据失败: {e}")
            raise DataSourceError(f"获取北向资金数据失败: {e}")

    def get_stock_fund_flow_individual(self, symbol: str) -> pd.DataFrame:
        """
        获取个股资金流向数据

        使用 akshare 的 stock_fund_flow_individual 函数获取个股资金流向

        参数:
            symbol: 股票代码（如 "000001"）

        返回:
            DataFrame: 个股资金流向数据
        """
        try:
            logger.debug(f"[AKShareAdapterEM] 获取 {symbol} 的资金流向数据...")

            symbol_clean = symbol.strip()
            if symbol_clean.startswith(('sh', 'sz')):
                symbol_for_request = symbol_clean
            elif symbol_clean.startswith('6'):
                symbol_for_request = f"sh{symbol_clean}"
            else:
                symbol_for_request = f"sz{symbol_clean}"

            df = self._ak.stock_fund_flow_individual(symbol=symbol_for_request)

            logger.info(f"[AKShareAdapterEM] 成功获取 {symbol} 的资金流向数据")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapterEM] 获取个股资金流向失败: {e}")
            raise DataSourceError(f"获取{symbol}资金流向失败: {e}")


# 全局适配器实例
_adapter_em: Optional[AKShareAdapterEM] = None


def get_adapter_em() -> AKShareAdapterEM:
    """获取东方财富版本适配器实例"""
    global _adapter_em
    if _adapter_em is None:
        _adapter_em = AKShareAdapterEM()
    return _adapter_em
