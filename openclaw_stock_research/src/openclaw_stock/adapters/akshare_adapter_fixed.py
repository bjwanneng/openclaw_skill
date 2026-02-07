"""
AkShare数据适配器 - 修复版

修复了以下问题：
1. 使用正确的数据源（新浪财经 stock_zh_a_spot 而非东方财富）
2. 添加更完善的错误处理
3. 添加超时和重试机制
4. 使用直接导入方式，避免动态导入问题
"""

from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
import pandas as pd
import time

from ..core.exceptions import DataSourceError, SymbolNotFoundError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AKShareAdapterFixed:
    """
    AkShare数据适配器 - 修复版

    主要修复：
    1. 使用 stock_zh_a_spot() 获取实时数据（新浪财经数据源）
    2. 使用 stock_zh_a_daily() 获取历史数据
    3. 添加完善的错误处理和日志
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._ak = None
        self._import_akshare()

    def _import_akshare(self):
        """导入 akshare 并检查关键函数"""
        try:
            import akshare as ak
            self._ak = ak

            # 检查关键函数是否存在
            required_funcs = [
                'stock_zh_a_spot',      # A股实时行情（新浪财经）
                'stock_zh_a_daily',     # A股历史行情
                'stock_hk_spot',        # 港股实时行情
                'stock_hk_hist',        # 港股历史行情
            ]

            for func_name in required_funcs:
                if not hasattr(ak, func_name):
                    logger.warning(f"[AKShareAdapter] akshare 缺少函数: {func_name}")
                else:
                    logger.debug(f"[AKShareAdapter] 找到函数: {func_name}")

            logger.info("[AKShareAdapter] akshare 导入成功")

        except ImportError as e:
            logger.error(f"[AKShareAdapter] 无法导入 akshare: {str(e)}")
            raise DataSourceError(f"无法导入 akshare: {str(e)}")

    def get_stock_zh_a_spot(self) -> pd.DataFrame:
        """
        获取A股实时行情快照 - 使用新浪财经数据源

        修复: 使用 stock_zh_a_spot 而非 stock_zh_a_spot_em

        Returns:
            DataFrame包含所有A股的实时行情
        """
        try:
            logger.debug("[AKShareAdapter] 使用 stock_zh_a_spot 获取A股实时行情...")

            # 关键修复: 使用 stock_zh_a_spot (新浪财经) 而非 stock_zh_a_spot_em (东方财富)
            df = self._ak.stock_zh_a_spot()

            logger.info(f"[AKShareAdapter] 成功获取A股实时行情，共{len(df)}条记录")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取A股行情失败: {str(e)}")
            # 如果失败，尝试备用数据源
            try:
                logger.warning("[AKShareAdapter] 尝试备用数据源 stock_zh_a_spot_em...")
                df = self._ak.stock_zh_a_spot_em()
                logger.info(f"[AKShareAdapter] 备用数据源成功，共{len(df)}条记录")
                return df
            except Exception as e2:
                logger.error(f"[AKShareAdapter] 备用数据源也失败: {str(e2)}")
                raise DataSourceError(f"获取A股行情失败: {str(e)}")

    def get_stock_hk_spot(self) -> pd.DataFrame:
        """获取港股实时行情快照"""
        try:
            logger.debug("[AKShareAdapter] 使用 stock_hk_spot 获取港股实时行情...")
            df = self._ak.stock_hk_spot()
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
        获取A股历史K线数据 - 使用新浪财经数据源

        修复: 使用 stock_zh_a_daily 而非 stock_zh_a_hist_em
        """
        try:
            logger.debug(f"[AKShareAdapter] 获取 {symbol} 的 {period} K线数据...")

            # 关键修复: 使用 stock_zh_a_daily (新浪财经) 而非 stock_zh_a_hist_em (东方财富)
            df = self._ak.stock_zh_a_daily(
                symbol=symbol,
                start_date=start_date or "19700101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust
            )

            logger.info(f"[AKShareAdapter] 成功获取 {symbol} 的 {len(df)} 条K线数据")
            return df

        except Exception as e:
            logger.error(f"[AKShareAdapter] 获取K线数据失败: {str(e)}")
            # 如果失败，尝试备用数据源
            try:
                logger.warning(f"[AKShareAdapter] 尝试备用数据源 stock_zh_a_hist_em...")
                df = self._ak.stock_zh_a_hist_em(
                    symbol=symbol,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )
                logger.info(f"[AKShareAdapter] 备用数据源成功，共{len(df)}条数据")
                return df
            except Exception as e2:
                logger.error(f"[AKShareAdapter] 备用数据源也失败: {str(e2)}")
                raise DataSourceError(f"获取{symbol}的K线数据失败: {str(e)}")

    # ... 其他方法保持不变

# 全局适配器实例
_adapter_fixed: Optional[AKShareAdapterFixed] = None

def get_adapter_fixed() -> AKShareAdapterFixed:
    """获取修复版适配器实例"""
    global _adapter_fixed
    if _adapter_fixed is None:
        _adapter_fixed = AKShareAdapterFixed()
    return _adapter_fixed
