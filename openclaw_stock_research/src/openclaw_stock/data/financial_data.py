"""
财务数据采集模块

实现设计文档4.1节的接口2: 财务数据采集
"""

from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
import pandas as pd
import numpy as np

from ..core.exceptions import DataSourceError, SymbolNotFoundError
from ..utils.logger import get_logger
from ..utils.decorators import retry, cache_result

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


def fetch_financial_data(
    symbol: str,
    report_type: Literal["profit", "balance", "cashflow", "all"] = "all"
) -> Dict[str, Any]:
    """
    获取财务报表数据（接口2实现）

    参数:
        symbol: 股票代码
        report_type: 报表类型(profit/balance/cashflow/all)

    返回:
        包含财务数据的字典:
        {
            'symbol': 股票代码,
            'report_date': 报告期,
            'profit': {  # 利润表数据
                'revenue': 营业收入,
                'operating_profit': 营业利润,
                'net_profit': 净利润,
                'eps': 每股收益,
            },
            'balance': {  # 资产负债表数据
                'total_assets': 总资产,
                'total_liabilities': 总负债,
                'equity': 股东权益,
            },
            'cashflow': {  # 现金流量表数据
                'operating_cashflow': 经营活动现金流,
                'investing_cashflow': 投资活动现金流,
                'financing_cashflow': 筹资活动现金流,
            }
        }

    异常:
        DataSourceError: 数据源访问失败
        SymbolNotFoundError: 股票代码不存在
    """
    if ak is None:
        raise DataSourceError("akshare库未安装")

    logger.info(f"[fetch_financial_data] 获取 {symbol} 的财务数据")

    try:
        result = {
            "symbol": symbol,
            "report_date": None,
            "profit": None,
            "balance": None,
            "cashflow": None
        }

        # 获取利润表
        if report_type in ["profit", "all"]:
            try:
                df_profit = ak.stock_profit_sheet_by_report_em(symbol=symbol)
                if not df_profit.empty:
                    latest = df_profit.iloc[0]
                    result["profit"] = {
                        "revenue": _safe_get_float(latest, "营业收入"),
                        "operating_profit": _safe_get_float(latest, "营业利润"),
                        "net_profit": _safe_get_float(latest, "净利润"),
                        "eps": _safe_get_float(latest, "基本每股收益"),
                    }
                    result["report_date"] = latest.get("报告期", result["report_date"])
            except Exception as e:
                logger.warning(f"[fetch_financial_data] 获取利润表失败: {e}")

        # 获取资产负债表
        if report_type in ["balance", "all"]:
            try:
                df_balance = ak.stock_balance_sheet_by_report_em(symbol=symbol)
                if not df_balance.empty:
                    latest = df_balance.iloc[0]
                    result["balance"] = {
                        "total_assets": _safe_get_float(latest, "资产总计"),
                        "total_liabilities": _safe_get_float(latest, "负债合计"),
                        "equity": _safe_get_float(latest, "所有者权益合计"),
                    }
            except Exception as e:
                logger.warning(f"[fetch_financial_data] 获取资产负债表失败: {e}")

        # 获取现金流量表
        if report_type in ["cashflow", "all"]:
            try:
                df_cashflow = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
                if not df_cashflow.empty:
                    latest = df_cashflow.iloc[0]
                    result["cashflow"] = {
                        "operating_cashflow": _safe_get_float(latest, "经营活动产生的现金流量净额"),
                        "investing_cashflow": _safe_get_float(latest, "投资活动产生的现金流量净额"),
                        "financing_cashflow": _safe_get_float(latest, "筹资活动产生的现金流量净额"),
                    }
            except Exception as e:
                logger.warning(f"[fetch_financial_data] 获取现金流量表失败: {e}")

        logger.info(f"[fetch_financial_data] 成功获取 {symbol} 的财务数据")
        return result

    except Exception as e:
        logger.error(f"[fetch_financial_data] 获取财务数据失败: {e}")
        raise DataSourceError(f"获取{symbol}财务数据失败: {e}")


def fetch_financial_report(
    symbol: str,
    report_type: Literal["income", "balance", "cashflow"] = "income"
) -> pd.DataFrame:
    """
    获取详细财务报表数据

    参数:
        symbol: 股票代码
        report_type: 报表类型(income-利润表/balance-资产负债表/cashflow-现金流量表)

    返回:
        DataFrame包含完整报表数据
    """
    if ak is None:
        raise DataSourceError("akshare库未安装")

    try:
        if report_type == "income":
            df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
        elif report_type == "balance":
            df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
        elif report_type == "cashflow":
            df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
        else:
            raise ValueError(f"不支持的报表类型: {report_type}")

        return df
    except Exception as e:
        logger.error(f"[fetch_financial_report] 获取报表失败: {e}")
        raise DataSourceError(f"获取{symbol}的{report_type}报表失败: {e}")


def _safe_get_float(row, column: str) -> Optional[float]:
    """安全获取浮点数值"""
    try:
        if column in row.index:
            value = row[column]
            if pd.isna(value):
                return None
            return float(value)
    except (ValueError, TypeError):
        pass
    return None


class FinancialDataCollector:
    """
    财务数据采集器类

    提供更灵活的财务数据采集方式
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def get_financial_data(self, **kwargs) -> Dict[str, Any]:
        """获取财务数据"""
        return fetch_financial_data(**kwargs)

    def get_financial_report(self, **kwargs) -> pd.DataFrame:
        """获取财务报表"""
        return fetch_financial_report(**kwargs)

    def get_valuation_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        获取估值指标

        返回:
            包含PE/PB/PS/ROE等估值指标的字典
        """
        try:
            # 使用 stock_value_em 获取全市场估值数据，然后筛选
            try:
                df_all = ak.stock_value_em()
                if not df_all.empty:
                    # 查找匹配的股票代码
                    df_match = df_all[df_all['代码'] == symbol]
                    if not df_match.empty:
                        row = df_match.iloc[0]
                        return {
                            "pe_ttm": float(row.get("市盈率-动态", 0) or 0),
                            "pb": float(row.get("市净率", 0) or 0),
                            "ps_ttm": float(row.get("市销率", 0) or 0),
                            "roe": float(row.get("净资产收益率", 0) or 0),
                            "market_cap": float(row.get("总市值", 0) or 0),
                        }
            except Exception as e1:
                self.logger.debug(f"[get_valuation_indicators] stock_value_em 失败: {e1}")

            # 备选方案：从个股信息接口获取
            try:
                df_info = ak.stock_individual_info_em(symbol=symbol)
                if not df_info.empty:
                    # 转换为字典便于查找
                    info_dict = dict(zip(df_info['item'], df_info['value']))
                    return {
                        "pe_ttm": float(info_dict.get('市盈率-动态', 0) or 0),
                        "pb": float(info_dict.get('市净率', 0) or 0),
                        "ps_ttm": float(info_dict.get('市销率', 0) or 0),
                        "roe": 0.0,  # 个股信息接口可能没有ROE
                        "market_cap": float(info_dict.get('总市值', 0) or 0),
                    }
            except Exception as e2:
                self.logger.debug(f"[get_valuation_indicators] stock_individual_info_em 失败: {e2}")

            self.logger.warning(f"[get_valuation_indicators] 所有估值指标接口都失败，返回空数据")
            return {}

        except Exception as e:
            self.logger.error(f"[get_valuation_indicators] 获取估值指标失败: {e}")
            return {}

    def get_profit_forecast(self, symbol: str) -> pd.DataFrame:
        """
        获取盈利预测

        返回:
            DataFrame包含机构对该股票的盈利预测
        """
        try:
            df = ak.stock_profit_forecast(symbol=symbol)
            return df
        except Exception as e:
            self.logger.error(f"[get_profit_forecast] 获取盈利预测失败: {e}")
            return pd.DataFrame()
