"""
中长期选股模块

实现设计文档4.3节的接口7: 中长期选股
"""

from typing import Literal, Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..core.exceptions import DataSourceError, CalculationError
from ..utils.logger import get_logger
from ..utils.decorators import retry
from ..data.financial_data import fetch_financial_data
from ..data.market_data import fetch_market_data

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


@dataclass
class LongTermStock:
    """中长期选股结果"""
    symbol: str
    name: str
    price: float
    pe_ttm: float
    pb: float
    roe: float
    profit_growth: float
    score: float
    signals: List[str]


def long_term_stock_selector(
    min_roe: float = 15,
    max_pe: float = 30,
    min_profit_growth: float = 20,
    industry: Optional[str] = None,
    top_n: int = 30,
    max_stocks: int = 1000,
    use_screening: bool = True
) -> pd.DataFrame:
    """
    中长期选股器（接口7实现）

    参数:
        min_roe: 最小ROE
        max_pe: 最大PE
        min_profit_growth: 最小利润增长率
        industry: 行业筛选
        top_n: 返回前N只股票
        max_stocks: 最大分析股票数量，默认1000只
        use_screening: 是否使用预筛选优化性能

    返回:
        DataFrame: 符合条件的股票及评分

    评分维度:
    1. 盈利能力(30分)
       - ROE > 15% +10
       - 净利润增长率 > 20% +10
       - 毛利率 > 30% +10

    2. 估值水平(25分)
       - PE < 行业平均 +10
       - PB < 2 +10
       - PEG < 1 +5

    3. 成长性(20分)
       - 营收增长率 > 20% +10
       - 业绩预告上调 +10

    4. 财务质量(15分)
       - 资产负债率 < 50% +5
       - 经营现金流 > 净利润 +5
       - 应收账款周转率改善 +5

    5. 股东结构(10分)
       - 机构持仓增加 +5
       - 股东户数减少 +5
    """
    if ak is None:
        raise DataSourceError("akshare库未安装")

    logger.info("[long_term_stock_selector] 开始中长期选股")

    try:
        # 获取全市场A股列表
        df_spot = ak.stock_zh_a_spot_em()

        if df_spot.empty:
            raise DataSourceError("无法获取全市场A股列表")

        logger.info(f"[long_term_stock_selector] 全市场共 {len(df_spot)} 只股票")

        # 行业筛选
        if industry:
            df_spot = df_spot[df_spot["行业"].str.contains(industry, na=False)]
            logger.info(f"[long_term_stock_selector] 行业筛选后剩余 {len(df_spot)} 只股票")

        # 性能优化：预筛选，优先分析基本面良好的股票
        if use_screening and len(df_spot) > max_stocks:
            # 根据PE和ROE进行初步筛选
            # 优先选择PE较低、ROE较高的股票
            if "市盈率-动态" in df_spot.columns:
                df_spot["pe_temp"] = pd.to_numeric(df_spot["市盈率-动态"], errors="coerce").fillna(999)
                # 筛选PE为正的，且不过高的股票
                df_spot = df_spot[df_spot["pe_temp"] > 0]
                df_spot = df_spot[df_spot["pe_temp"] < max_pe * 2]  # 放宽条件初步筛选

            if "净资产收益率" in df_spot.columns:
                df_spot["roe_temp"] = pd.to_numeric(df_spot["净资产收益率"], errors="coerce").fillna(0)
                # 优先选择ROE为正的股票
                df_spot = df_spot[df_spot["roe_temp"] > 0]

            # 根据换手率排序，优先分析活跃股票
            if "换手率" in df_spot.columns:
                df_spot = df_spot.sort_values("换手率", ascending=False)

            # 限制分析数量
            df_spot = df_spot.head(max_stocks)
            logger.info(f"[long_term_stock_selector] 预筛选后分析前 {len(df_spot)} 只股票")

        # 初始化候选列表
        candidates = []

        # 遍历股票进行筛选
        for _, row in df_spot.iterrows():
            try:
                symbol = str(row.get("代码", "")).strip()
                name = str(row.get("名称", "")).strip()
                price = float(row.get("最新价", 0) or 0)
                pe_ttm = float(row.get("市盈率-动态", 0) or 0)
                pb = float(row.get("市净率", 0) or 0)

                if not symbol or not name or price <= 0:
                    continue

                # 初步估值筛选
                if max_pe and pe_ttm > max_pe:
                    continue

                # 获取详细财务数据
                try:
                    financial_data = fetch_financial_data(symbol, report_type="all")
                except:
                    financial_data = {}

                # 初始化评分
                profitability_score = 0
                valuation_score = 0
                growth_score = 0
                quality_score = 0
                shareholder_score = 0
                signals = []

                # 1. 盈利能力评分(30分)
                valuation = financial_data.get("valuation", {})
                profitability = financial_data.get("profitability", {})
                growth = financial_data.get("growth", {})

                roe = valuation.get("roe") or profitability.get("roe")
                if roe and roe >= min_roe:
                    profitability_score += 10
                    signals.append(f"ROE达标({roe:.1f}%)")
                elif roe:
                    profitability_score += max(0, int(roe / min_roe * 10))

                # 净利润增长率
                profit_growth = growth.get("profit_growth")
                if profit_growth and profit_growth >= min_profit_growth:
                    profitability_score += 10
                    signals.append(f"利润高增长({profit_growth:.1f}%)")

                # 毛利率
                gross_margin = profitability.get("gross_margin")
                if gross_margin and gross_margin > 30:
                    profitability_score += 10
                    signals.append("高毛利率")

                # 2. 估值评分(25分)
                pe_ttm = valuation.get("pe_ttm") or pe_ttm
                pb = valuation.get("pb") or pb

                if pe_ttm and pe_ttm < 20:
                    valuation_score += 10
                    signals.append("低PE")
                elif pe_ttm and pe_ttm < max_pe:
                    valuation_score += 5

                if pb and pb < 2:
                    valuation_score += 10
                    signals.append("低PB")

                # PEG
                if pe_ttm and profit_growth and profit_growth > 0:
                    peg = pe_ttm / profit_growth
                    if peg < 1:
                        valuation_score += 5
                        signals.append("PEG<1")

                # 3. 成长性评分(20分)
                revenue_growth = growth.get("revenue_growth")
                if revenue_growth and revenue_growth > 20:
                    growth_score += 10
                    signals.append(f"营收高增长({revenue_growth:.1f}%)")

                # 业绩预告
                try:
                    df_yjyg = ak.stock_yjyg_em(date=datetime.now().strftime("%Y%m"))
                    if not df_yjyg.empty and symbol in df_yjyg["股票代码"].values:
                        stock_yjyg = df_yjyg[df_yjyg["股票代码"] == symbol]
                        if not stock_yjyg.empty:
                            change_type = stock_yjyg.iloc[0].get("变动类型", "")
                            if "预增" in change_type or "预盈" in change_type:
                                growth_score += 10
                                signals.append("业绩预增")
                except:
                    pass

                # 4. 财务质量评分(15分)
                quality = financial_data.get("quality", {})
                debt_ratio = quality.get("debt_ratio")
                if debt_ratio and debt_ratio < 50:
                    quality_score += 5

                # 5. 股东结构评分(10分)
                # 简化处理，暂不计算

                # 计算总分
                total_score = profitability_score + valuation_score + growth_score + quality_score + shareholder_score

                # 添加到候选列表
                candidates.append({
                    "symbol": symbol,
                    "name": name,
                    "price": price,
                    "pe_ttm": pe_ttm,
                    "pb": pb,
                    "roe": roe,
                    "profit_growth": profit_growth,
                    "profitability_score": profitability_score,
                    "valuation_score": valuation_score,
                    "growth_score": growth_score,
                    "quality_score": quality_score,
                    "shareholder_score": shareholder_score,
                    "total_score": total_score,
                    "signals": "; ".join(signals) if signals else ""
                })

            except Exception as e:
                logger.warning(f"[{symbol}] 处理失败: {e}")
                continue

        # 按总分排序
        candidates.sort(key=lambda x: x["total_score"], reverse=True)

        # 取前N个
        top_candidates = candidates[:top_n]

        # 转换为DataFrame
        df_result = pd.DataFrame(top_candidates)

        logger.info(f"[long_term_stock_selector] 选股完成，返回 {len(df_result)} 只股票")
        return df_result

    except Exception as e:
        logger.error(f"[long_term_stock_selector] 选股失败: {e}")
        raise DataSourceError(f"中长期选股失败: {e}")


# 策略类定义
class ValueInvestingStrategy:
    """价值投资策略"""

    def __init__(self):
        self.name = "价值投资"
        self.description = "低估值+稳定盈利+高分红"

    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """筛选价值股"""
        return df[
            (df["pe_ttm"] < 15) &
            (df["pb"] < 2) &
            (df["roe"] > 10)
        ]


class GrowthInvestingStrategy:
    """成长投资策略"""

    def __init__(self):
        self.name = "成长投资"
        self.description = "业绩高增长+行业景气+竞争优势"

    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """筛选成长股"""
        return df[
            (df["profit_growth"] > 30) &
            (df["roe"] > 15)
        ]


class TrendInvestingStrategy:
    """趋势投资策略"""

    def __init__(self):
        self.name = "趋势投资"
        self.description = "长期上升趋势+基本面改善"

    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """筛选趋势股"""
        return df[df["profit_growth"] > 0]


class DistressReversalStrategy:
    """困境反转策略"""

    def __init__(self):
        self.name = "困境反转"
        self.description = "业绩拐点+估值修复"

    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """筛选困境反转股"""
        return df[
            (df["pe_ttm"] > 0) &
            (df["pb"] < 1.5)
        ]


class LongTermSelector:
    """
    中长期选股器类

    提供中长期选股的统一接口
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.strategies = [
            ValueInvestingStrategy(),
            GrowthInvestingStrategy(),
            TrendInvestingStrategy(),
            DistressReversalStrategy()
        ]

    def select(self, **kwargs) -> pd.DataFrame:
        """执行选股"""
        return long_term_stock_selector(**kwargs)

    def get_strategies(self) -> List[Any]:
        """获取所有策略"""
        return self.strategies
