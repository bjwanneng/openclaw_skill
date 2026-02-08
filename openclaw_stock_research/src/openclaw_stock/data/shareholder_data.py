"""
股东人数变化数据采集模块

获取个股股东户数变化、户均持股等数据，分析筹码集中度
"""

from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

from ..utils.logger import get_logger

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


def fetch_shareholder_data(symbol: str) -> Dict[str, Any]:
    """
    获取个股股东人数变化数据

    参数:
        symbol: 股票代码（如 '601127'）

    返回:
        {
            'latest': 最新股东数据,
            'history': 历史变化列表,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[shareholder] akshare未安装")
        return _empty_result()

    result = {
        "latest": {},
        "history": [],
        "analysis": {}
    }

    try:
        df = ak.stock_zh_a_gdhs_detail_em(symbol=symbol)
        if df is not None and not df.empty:
            records = []
            for _, row in df.iterrows():
                record = {
                    "date": str(row.get("股东户数统计截止日", "")),
                    "holder_count": int(row.get("股东户数-本次", 0) or 0),
                    "holder_count_prev": int(row.get("股东户数-上次", 0) or 0),
                    "holder_change": int(row.get("股东户数-增减", 0) or 0),
                    "holder_change_pct": float(row.get("股东户数-增减比例", 0) or 0),
                    "avg_hold_value": float(row.get("户均持股市值", 0) or 0),
                    "avg_hold_shares": float(row.get("户均持股数量", 0) or 0),
                    "total_market_cap": float(row.get("总市值", 0) or 0),
                    "total_shares": float(row.get("总股本", 0) or 0),
                    "price_change_pct": float(row.get("区间涨跌幅", 0) or 0),
                }
                records.append(record)

            # 按日期排序（最新在前）
            records.sort(key=lambda x: x["date"], reverse=True)

            if records:
                result["latest"] = records[0]
                result["history"] = records[:8]  # 最近8期

            logger.info(f"[shareholder] {symbol} 获取到 {len(records)} 期股东数据")
    except Exception as e:
        logger.warning(f"[shareholder] 获取股东人数数据失败: {e}")

    # 分析
    result["analysis"] = _analyze_shareholder(result)

    return result


def _analyze_shareholder(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析股东人数变化"""
    analysis = {
        "chip_concentration": "未知",
        "trend": "未知",
        "summary": "股东人数数据不足"
    }

    latest = data.get("latest", {})
    history = data.get("history", [])

    if not latest:
        return analysis

    holder_count = latest.get("holder_count", 0)
    holder_change_pct = latest.get("holder_change_pct", 0)
    avg_hold_value = latest.get("avg_hold_value", 0)

    parts = []

    # 最新股东户数
    if holder_count > 0:
        parts.append(f"最新股东户数{holder_count:,}户")

    # 户均持股市值
    if avg_hold_value > 0:
        parts.append(f"户均持股市值{avg_hold_value:,.0f}元")

    # 变化趋势
    if holder_change_pct < -10:
        analysis["chip_concentration"] = "快速集中"
        analysis["signal"] = "看多"
        parts.append(f"股东人数大幅减少{holder_change_pct:.2f}%，筹码快速集中")
    elif holder_change_pct < -3:
        analysis["chip_concentration"] = "逐步集中"
        analysis["signal"] = "偏多"
        parts.append(f"股东人数减少{holder_change_pct:.2f}%，筹码逐步集中")
    elif holder_change_pct < 3:
        analysis["chip_concentration"] = "基本稳定"
        analysis["signal"] = "中性"
        parts.append(f"股东人数变化{holder_change_pct:.2f}%，筹码基本稳定")
    elif holder_change_pct < 10:
        analysis["chip_concentration"] = "逐步分散"
        analysis["signal"] = "偏空"
        parts.append(f"股东人数增加{holder_change_pct:.2f}%，筹码逐步分散")
    else:
        analysis["chip_concentration"] = "快速分散"
        analysis["signal"] = "看空"
        parts.append(f"股东人数大幅增加{holder_change_pct:.2f}%，筹码快速分散")

    # 连续趋势
    if len(history) >= 3:
        recent_changes = [h.get("holder_change_pct", 0) for h in history[:3]]
        if all(c < 0 for c in recent_changes):
            analysis["trend"] = "连续集中"
            parts.append("连续多期股东人数减少")
        elif all(c > 0 for c in recent_changes):
            analysis["trend"] = "连续分散"
            parts.append("连续多期股东人数增加")
        else:
            analysis["trend"] = "波动"

    analysis["summary"] = "，".join(parts) if parts else "股东人数数据不足"

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "latest": {},
        "history": [],
        "analysis": {
            "chip_concentration": "未知",
            "trend": "未知",
            "summary": "股东人数数据获取失败"
        }
    }
