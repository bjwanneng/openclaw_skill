"""
基本面分析模块

实现设计文档4.2节的接口5: 基本面指标计算
"""

from typing import Literal, Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np

from ..core.exceptions import DataSourceError, CalculationError
from ..utils.logger import get_logger
from ..data.financial_data import fetch_financial_data, fetch_financial_report

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


@dataclass
class FundamentalIndicators:
    """基本面指标数据类"""

    # 估值指标
    pe_ttm: Optional[float] = None  # 市盈率TTM
    pe_lyr: Optional[float] = None  # 市盈率LYR
    pb: Optional[float] = None  # 市净率
    ps_ttm: Optional[float] = None  # 市销率TTM
    peg: Optional[float] = None  # PEG比率
    ev_ebitda: Optional[float] = None  # 企业价值倍数

    # 盈利能力指标
    roe: Optional[float] = None  # 净资产收益率(%)
    roa: Optional[float] = None  # 总资产收益率(%)
    gross_margin: Optional[float] = None  # 毛利率(%)
    net_margin: Optional[float] = None  # 净利率(%)
    eps: Optional[float] = None  # 每股收益
    bps: Optional[float] = None  # 每股净资产

    # 成长性指标
    revenue_growth: Optional[float] = None  # 营收增长率(%)
    profit_growth: Optional[float] = None  # 净利润增长率(%)
    roe_growth: Optional[float] = None  # ROE增长率(%)

    # 财务质量指标
    debt_ratio: Optional[float] = None  # 资产负债率(%)
    current_ratio: Optional[float] = None  # 流动比率
    quick_ratio: Optional[float] = None  # 速动比率
    cash_ratio: Optional[float] = None  # 现金比率
    inventory_turnover: Optional[float] = None  # 存货周转率
    receivables_turnover: Optional[float] = None  # 应收账款周转率

    # 股东回报指标
    dividend_yield: Optional[float] = None  # 股息率(%)
    payout_ratio: Optional[float] = None  # 分红率(%)

    # 市场指标
    market_cap: Optional[float] = None  # 总市值
    float_market_cap: Optional[float] = None  # 流通市值
    turnover_rate: Optional[float] = None  # 换手率


def calculate_fundamental_indicators(
    symbol: str,
    include_history: bool = False
) -> Dict[str, Any]:
    """
    计算基本面指标（接口5实现）

    参数:
        symbol: 股票代码
        include_history: 是否包含历史数据

    返回:
        包含基本面指标的字典:
        {
            'valuation': {PE, PB, PS, PEG等估值指标},
            'profitability': {ROE, ROA, 净利率等盈利指标},
            'growth': {营收增长率, 利润增长率等成长指标},
            'quality': {资产负债率, 现金流等质量指标}
        }

    异常:
        DataSourceError: 数据源访问失败
        CalculationError: 计算失败
    """
    if ak is None:
        raise DataSourceError("akshare库未安装")

    logger.info(f"[calculate_fundamental_indicators] 计算 {symbol} 的基本面指标")

    try:
        result = {
            "symbol": symbol,
            "valuation": {},
            "profitability": {},
            "growth": {},
            "quality": {},
            "market": {},
            "timestamp": datetime.now().isoformat()
        }

        # 1. 获取估值指标
        try:
            df_valuation = ak.stock_a_lg_indicator(symbol=symbol)
            if not df_valuation.empty:
                row = df_valuation.iloc[0]
                result["valuation"] = {
                    "pe_ttm": _safe_float(row, "市盈率(TTM)"),
                    "pe_lyr": _safe_float(row, "市盈率(静)"),
                    "pb": _safe_float(row, "市净率"),
                    "ps_ttm": _safe_float(row, "市销率"),
                    "roe": _safe_float(row, "净资产收益率"),
                }
                result["market"] = {
                    "market_cap": _safe_float(row, "总市值"),
                    "float_market_cap": _safe_float(row, "流通市值"),
                }
        except Exception as e:
            logger.warning(f"[calculate_fundamental_indicators] 获取估值指标失败: {e}")

        # 2. 获取财务摘要
        try:
            df_finance = ak.stock_financial_abstract(symbol=symbol)
            if not df_finance.empty:
                # 取最近一期数据
                latest = df_finance.iloc[0]

                # 盈利能力
                result["profitability"]["gross_margin"] = _safe_float(latest, "销售毛利率")
                result["profitability"]["net_margin"] = _safe_float(latest, "销售净利率")
                result["profitability"]["roa"] = _safe_float(latest, "总资产净利率")

                # 成长性
                result["growth"]["revenue_growth"] = _safe_float(latest, "营业总收入同比增长率")
                result["growth"]["profit_growth"] = _safe_float(latest, "净利润同比增长率")
                result["growth"]["roe_growth"] = _safe_float(latest, "净资产收益率同比增长率")

                # 财务质量
                result["quality"]["debt_ratio"] = _safe_float(latest, "资产负债率")
                result["quality"]["current_ratio"] = _safe_float(latest, "流动比率")
                result["quality"]["quick_ratio"] = _safe_float(latest, "速动比率")
        except Exception as e:
            logger.warning(f"[calculate_fundamental_indicators] 获取财务摘要失败: {e}")

        # 3. 计算PEG
        pe_ttm = result["valuation"].get("pe_ttm")
        profit_growth = result["growth"].get("profit_growth")
        if pe_ttm and profit_growth and profit_growth > 0:
            result["valuation"]["peg"] = round(pe_ttm / profit_growth, 2)

        logger.info(f"[calculate_fundamental_indicators] 计算完成: {symbol}")
        return result

    except Exception as e:
        logger.error(f"[calculate_fundamental_indicators] 计算失败: {e}")
        raise CalculationError(f"计算{symbol}基本面指标失败: {e}")


def _safe_float(row: pd.Series, column: str) -> Optional[float]:
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


class FundamentalAnalyzer:
    """
    基本面分析器类

    提供基本面分析的统一接口
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def calculate_indicators(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """计算基本面指标"""
        return calculate_fundamental_indicators(symbol, **kwargs)

    def analyze_valuation(self, indicators: Dict[str, Any]) -> str:
        """
        分析估值水平

        返回:
            "undervalued"/"fair"/"overvalued"/"unknown"
        """
        valuation = indicators.get("valuation", {})
        pe = valuation.get("pe_ttm")
        pb = valuation.get("pb")

        if pe is None or pb is None:
            return "unknown"

        # 简单估值判断
        if pe < 10 and pb < 1:
            return "undervalued"
        elif pe > 50 or pb > 5:
            return "overvalued"
        else:
            return "fair"

    def analyze_profitability(self, indicators: Dict[str, Any]) -> str:
        """
        分析盈利能力

        返回:
            "strong"/"moderate"/"weak"/"unknown"
        """
        profitability = indicators.get("profitability", {})
        roe = profitability.get("roe")
        net_margin = profitability.get("net_margin")

        if roe is None:
            return "unknown"

        if roe > 15 and net_margin > 10:
            return "strong"
        elif roe > 8:
            return "moderate"
        else:
            return "weak"

    def analyze_growth(self, indicators: Dict[str, Any]) -> str:
        """
        分析成长性

        返回:
            "high"/"moderate"/"low"/"unknown"
        """
        growth = indicators.get("growth", {})
        profit_growth = growth.get("profit_growth")
        revenue_growth = growth.get("revenue_growth")

        if profit_growth is None:
            return "unknown"

        if profit_growth > 30 and revenue_growth > 20:
            return "high"
        elif profit_growth > 10:
            return "moderate"
        else:
            return "low"

    def generate_report(self, symbol: str, indicators: Dict[str, Any]) -> str:
        """
        生成基本面分析报告

        参数:
            symbol: 股票代码
            indicators: 基本面指标

        返回:
            分析报告文本
        """
        lines = [
            f"=== {symbol} 基本面分析报告 ===",
            "",
            "【估值分析】",
            f"  PE(TTM): {indicators.get('valuation', {}).get('pe_ttm', 'N/A')}",
            f"  PB: {indicators.get('valuation', {}).get('pb', 'N/A')}",
            f"  估值水平: {self.analyze_valuation(indicators)}",
            "",
            "【盈利能力】",
            f"  ROE: {indicators.get('profitability', {}).get('roe', 'N/A')}%",
            f"  净利率: {indicators.get('profitability', {}).get('net_margin', 'N/A')}%",
            f"  盈利水平: {self.analyze_profitability(indicators)}",
            "",
            "【成长性】",
            f"  营收增长率: {indicators.get('growth', {}).get('revenue_growth', 'N/A')}%",
            f"  利润增长率: {indicators.get('growth', {}).get('profit_growth', 'N/A')}%",
            f"  成长水平: {self.analyze_growth(indicators)}",
            "",
            "【财务质量】",
            f"  资产负债率: {indicators.get('quality', {}).get('debt_ratio', 'N/A')}%",
            f"  流动比率: {indicators.get('quality', {}).get('current_ratio', 'N/A')}",
            "",
            "=== 报告结束 ==="
        ]

        return "\n".join(lines)
