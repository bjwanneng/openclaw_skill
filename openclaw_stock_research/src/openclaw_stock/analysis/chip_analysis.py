"""
筹码分布（成本分布）分析模块

基于东方财富网筹码分布数据，提供：
- 获利比例分析（当前价格下盈利筹码占比）
- 平均成本计算
- 筹码集中度分析（90%和70%成本区间）
- 筹码趋势判断

数据来源: akshare stock_cyq_em 接口（东方财富网-概念板-行情中心-日K-筹码分布）
"""

from typing import Literal, Optional, Dict, Any, List
from datetime import datetime
import pandas as pd
import numpy as np

from ..core.exceptions import DataSourceError, CalculationError
from ..utils.logger import get_logger

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


def fetch_chip_distribution(
    symbol: str,
    adjust: Literal["qfq", "hfq", ""] = "qfq"
) -> pd.DataFrame:
    """
    获取筹码分布数据

    参数:
        symbol: 股票代码（纯数字，如 '601127'）
        adjust: 复权方式 - "qfq"前复权, "hfq"后复权, ""不复权

    返回:
        DataFrame，包含列:
        - 日期, 获利比例, 平均成本
        - 90成本-低, 90成本-高, 90集中度
        - 70成本-低, 70成本-高, 70集中度

    异常:
        DataSourceError: 数据获取失败
    """
    if ak is None:
        raise DataSourceError("akshare库未安装")

    try:
        df = ak.stock_cyq_em(symbol=symbol, adjust=adjust)
        if df is None or df.empty:
            raise DataSourceError(f"未获取到 {symbol} 的筹码分布数据")
        return df
    except DataSourceError:
        raise
    except Exception as e:
        raise DataSourceError(f"获取 {symbol} 筹码分布数据失败: {e}")


def analyze_chip_distribution(
    symbol: str,
    current_price: Optional[float] = None,
    adjust: Literal["qfq", "hfq", ""] = "qfq"
) -> Dict[str, Any]:
    """
    筹码分布综合分析

    参数:
        symbol: 股票代码（纯数字，如 '601127'）
        current_price: 当前价格（可选，用于辅助判断）
        adjust: 复权方式

    返回:
        {
            'latest': {最新一日筹码数据},
            'trend': {筹码趋势分析},
            'assessment': {综合评估}
        }

    异常:
        DataSourceError: 数据获取失败
        CalculationError: 计算失败
    """
    logger.info(f"[chip_analysis] 开始分析 {symbol} 的筹码分布")

    try:
        df = fetch_chip_distribution(symbol, adjust=adjust)
    except DataSourceError as e:
        logger.warning(f"[chip_analysis] 获取筹码数据失败: {e}")
        return _empty_chip_result(str(e))

    try:
        result = {}

        # --- 1. 最新一日筹码数据 ---
        latest = df.iloc[-1]
        result["latest"] = {
            "date": str(latest["日期"]),
            "winner_rate": _safe_float(latest["获利比例"]),
            "average_cost": _safe_float(latest["平均成本"]),
            "cost_90_low": _safe_float(latest["90成本-低"]),
            "cost_90_high": _safe_float(latest["90成本-高"]),
            "concentration_90": _safe_float(latest["90集中度"]),
            "cost_70_low": _safe_float(latest["70成本-低"]),
            "cost_70_high": _safe_float(latest["70成本-高"]),
            "concentration_70": _safe_float(latest["70集中度"]),
        }

        # 计算90%和70%成本区间宽度
        cost_90_range = result["latest"]["cost_90_high"] - result["latest"]["cost_90_low"]
        cost_70_range = result["latest"]["cost_70_high"] - result["latest"]["cost_70_low"]
        result["latest"]["cost_90_range"] = round(cost_90_range, 2)
        result["latest"]["cost_70_range"] = round(cost_70_range, 2)

        # --- 2. 筹码趋势分析（对比近期变化） ---
        result["trend"] = _analyze_chip_trend(df)

        # --- 3. 综合评估 ---
        result["assessment"] = _assess_chip_status(
            result["latest"], result["trend"], current_price
        )

        logger.info(f"[chip_analysis] {symbol} 筹码分析完成")
        return result

    except Exception as e:
        logger.error(f"[chip_analysis] 筹码分析计算失败: {e}")
        raise CalculationError(f"筹码分析计算失败: {e}")


def _safe_float(value) -> float:
    """安全转换为float，处理NaN等情况"""
    try:
        v = float(value)
        return round(v, 4) if not np.isnan(v) else 0.0
    except (ValueError, TypeError):
        return 0.0


def _analyze_chip_trend(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析筹码变化趋势

    对比最近数据与早期数据，判断筹码集中/发散趋势
    """
    trend = {
        "concentration_trend": "stable",  # concentrating / dispersing / stable
        "cost_center_trend": "stable",    # rising / falling / stable
        "winner_rate_trend": "stable",    # rising / falling / stable
        "period_days": 0,
        "details": {}
    }

    if len(df) < 5:
        return trend

    trend["period_days"] = len(df)

    # 取最近5日和前5日（或可用的早期数据）对比
    recent_n = min(5, len(df))
    early_start = max(0, len(df) - 20)
    early_end = max(recent_n, len(df) - 10)

    if early_end <= early_start:
        return trend

    recent = df.iloc[-recent_n:]
    early = df.iloc[early_start:early_end]

    # 集中度趋势（90集中度越小越集中）
    recent_conc_90 = recent["90集中度"].mean()
    early_conc_90 = early["90集中度"].mean()

    if recent_conc_90 < early_conc_90 * 0.95:
        trend["concentration_trend"] = "concentrating"
    elif recent_conc_90 > early_conc_90 * 1.05:
        trend["concentration_trend"] = "dispersing"
    else:
        trend["concentration_trend"] = "stable"

    trend["details"]["recent_concentration_90"] = round(float(recent_conc_90), 4)
    trend["details"]["early_concentration_90"] = round(float(early_conc_90), 4)

    # 成本中心趋势
    recent_avg_cost = recent["平均成本"].mean()
    early_avg_cost = early["平均成本"].mean()

    if recent_avg_cost > early_avg_cost * 1.02:
        trend["cost_center_trend"] = "rising"
    elif recent_avg_cost < early_avg_cost * 0.98:
        trend["cost_center_trend"] = "falling"
    else:
        trend["cost_center_trend"] = "stable"

    trend["details"]["recent_avg_cost"] = round(float(recent_avg_cost), 2)
    trend["details"]["early_avg_cost"] = round(float(early_avg_cost), 2)

    # 获利比例趋势
    recent_winner = recent["获利比例"].mean()
    early_winner = early["获利比例"].mean()

    if recent_winner > early_winner + 0.05:
        trend["winner_rate_trend"] = "rising"
    elif recent_winner < early_winner - 0.05:
        trend["winner_rate_trend"] = "falling"
    else:
        trend["winner_rate_trend"] = "stable"

    trend["details"]["recent_winner_rate"] = round(float(recent_winner), 4)
    trend["details"]["early_winner_rate"] = round(float(early_winner), 4)

    return trend


def _assess_chip_status(
    latest: Dict[str, Any],
    trend: Dict[str, Any],
    current_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    综合评估筹码状态

    基于筹码集中度、获利比例、趋势等综合判断
    """
    assessment = {
        "chip_status": "neutral",       # concentrated / dispersed / neutral
        "pressure_level": "medium",     # low / medium / high
        "support_level": "medium",      # low / medium / high
        "signals": [],
        "summary": ""
    }

    winner_rate = latest["winner_rate"]
    concentration_90 = latest["concentration_90"]
    concentration_70 = latest["concentration_70"]
    avg_cost = latest["average_cost"]

    # --- 筹码集中度评估 ---
    # 90集中度 < 10% 表示筹码高度集中
    if concentration_90 < 0.10:
        assessment["chip_status"] = "highly_concentrated"
        assessment["signals"].append("筹码高度集中，主力控盘明显")
    elif concentration_90 < 0.20:
        assessment["chip_status"] = "concentrated"
        assessment["signals"].append("筹码较为集中")
    elif concentration_90 > 0.40:
        assessment["chip_status"] = "dispersed"
        assessment["signals"].append("筹码分散，持仓分歧较大")
    else:
        assessment["chip_status"] = "neutral"

    # --- 获利比例评估 ---
    if winner_rate > 0.90:
        assessment["pressure_level"] = "high"
        assessment["signals"].append(f"获利比例极高({winner_rate*100:.1f}%)，存在较大获利回吐压力")
    elif winner_rate > 0.70:
        assessment["pressure_level"] = "medium_high"
        assessment["signals"].append(f"获利比例较高({winner_rate*100:.1f}%)，注意获利盘压力")
    elif winner_rate < 0.10:
        assessment["pressure_level"] = "low"
        assessment["support_level"] = "low"
        assessment["signals"].append(f"获利比例极低({winner_rate*100:.1f}%)，多数筹码被套")
    elif winner_rate < 0.30:
        assessment["pressure_level"] = "low"
        assessment["signals"].append(f"获利比例较低({winner_rate*100:.1f}%)，套牢盘较多")

    # --- 当前价格与平均成本的关系 ---
    if current_price and avg_cost > 0:
        price_vs_cost = (current_price - avg_cost) / avg_cost
        if price_vs_cost > 0.15:
            assessment["signals"].append(
                f"当前价格高于平均成本{price_vs_cost*100:.1f}%，获利盘较多"
            )
        elif price_vs_cost < -0.15:
            assessment["signals"].append(
                f"当前价格低于平均成本{abs(price_vs_cost)*100:.1f}%，套牢盘压力大"
            )
            assessment["support_level"] = "low"
        else:
            assessment["signals"].append("当前价格接近平均成本，多空博弈区间")

    # --- 趋势信号 ---
    conc_trend = trend.get("concentration_trend", "stable")
    cost_trend = trend.get("cost_center_trend", "stable")

    if conc_trend == "concentrating":
        assessment["signals"].append("筹码趋于集中，可能有主力吸筹")
    elif conc_trend == "dispersing":
        assessment["signals"].append("筹码趋于分散，可能有主力派发")

    if cost_trend == "rising":
        assessment["signals"].append("成本中心上移，市场换手充分")
    elif cost_trend == "falling":
        assessment["signals"].append("成本中心下移，持仓成本降低")

    # --- 生成总结 ---
    summary_parts = []

    # 集中度描述
    status_map = {
        "highly_concentrated": "筹码高度集中",
        "concentrated": "筹码较集中",
        "dispersed": "筹码分散",
        "neutral": "筹码分布适中"
    }
    summary_parts.append(status_map.get(assessment["chip_status"], "筹码分布适中"))

    # 获利比例描述
    summary_parts.append(f"获利比例{winner_rate*100:.1f}%")

    # 平均成本
    summary_parts.append(f"平均成本{avg_cost:.2f}元")

    # 趋势描述
    trend_desc_map = {
        "concentrating": "筹码趋于集中",
        "dispersing": "筹码趋于分散",
        "stable": "筹码分布稳定"
    }
    summary_parts.append(trend_desc_map.get(conc_trend, ""))

    assessment["summary"] = "，".join(filter(None, summary_parts)) + "。"

    return assessment


def _empty_chip_result(error_msg: str) -> Dict[str, Any]:
    """返回空的筹码分析结果（数据获取失败时使用）"""
    return {
        "latest": {},
        "trend": {},
        "assessment": {
            "chip_status": "unknown",
            "pressure_level": "unknown",
            "support_level": "unknown",
            "signals": [],
            "summary": f"筹码数据获取失败: {error_msg}"
        },
        "error": error_msg
    }


class ChipAnalyzer:
    """
    筹码分布分析器类

    提供筹码分析的面向对象接口
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def analyze(
        self,
        symbol: str,
        current_price: Optional[float] = None,
        adjust: Literal["qfq", "hfq", ""] = "qfq"
    ) -> Dict[str, Any]:
        """执行筹码分析"""
        return analyze_chip_distribution(symbol, current_price, adjust)

    def get_raw_data(
        self,
        symbol: str,
        adjust: Literal["qfq", "hfq", ""] = "qfq"
    ) -> pd.DataFrame:
        """获取原始筹码分布数据"""
        return fetch_chip_distribution(symbol, adjust)
