"""
分红送转数据采集模块

获取个股历史分红记录、股息率等数据
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


def fetch_dividend_data(symbol: str) -> Dict[str, Any]:
    """
    获取个股分红送转数据

    参数:
        symbol: 股票代码（如 '601127'）

    返回:
        {
            'detail': 分红送转详情列表,
            'history': 历史分红记录,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[dividend] akshare未安装")
        return _empty_result()

    result = {
        "detail": [],
        "history": [],
        "analysis": {}
    }

    # 1. 获取分红送转详情（含股息率）
    try:
        df = ak.stock_fhps_detail_em(symbol=symbol)
        if df is not None and not df.empty:
            records = []
            for _, row in df.iterrows():
                record = {
                    "report_date": str(row.get("报告期", "")),
                    "disclosure_date": str(row.get("业绩披露日期", "")),
                    "bonus_ratio": float(row.get("送转股份-送转总比例", 0) or 0),
                    "send_ratio": float(row.get("送转股份-送股比例", 0) or 0),
                    "transfer_ratio": float(row.get("送转股份-转股比例", 0) or 0),
                    "cash_dividend": float(row.get("现金分红-现金分红比例", 0) or 0),
                    "cash_desc": str(row.get("现金分红-现金分红比例描述", "")),
                    "dividend_yield": float(row.get("现金分红-股息率", 0) or 0),
                    "eps": float(row.get("每股收益", 0) or 0),
                    "bps": float(row.get("每股净资产", 0) or 0),
                    "profit_growth": float(row.get("净利润同比增长", 0) or 0),
                    "progress": str(row.get("方案进度", "")),
                    "ex_date": str(row.get("除权除息日", "")),
                    "record_date": str(row.get("股权登记日", "")),
                }
                records.append(record)
            result["detail"] = records
            logger.info(f"[dividend] {symbol} 获取到 {len(records)} 条分红送转记录")
    except Exception as e:
        logger.warning(f"[dividend] 获取分红送转详情失败: {e}")

    # 2. 获取历史分红记录
    try:
        df_hist = ak.stock_history_dividend_detail(symbol=symbol, indicator="分红")
        if df_hist is not None and not df_hist.empty:
            history = []
            for _, row in df_hist.iterrows():
                record = {
                    "announce_date": str(row.get("公告日期", "")),
                    "send_shares": float(row.get("送股", 0) or 0),
                    "transfer_shares": float(row.get("转增", 0) or 0),
                    "cash_per_share": float(row.get("派息", 0) or 0),
                    "progress": str(row.get("进度", "")),
                    "ex_date": str(row.get("除权除息日", "")),
                    "record_date": str(row.get("股权登记日", "")),
                }
                history.append(record)
            result["history"] = history
    except Exception as e:
        logger.warning(f"[dividend] 获取历史分红记录失败: {e}")

    # 3. 分析
    result["analysis"] = _analyze_dividend(result)

    return result


def _analyze_dividend(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析分红送转数据"""
    analysis = {
        "dividend_stability": "未知",
        "dividend_yield_level": "未知",
        "summary": "分红数据不足"
    }

    detail = data.get("detail", [])
    history = data.get("history", [])

    if not detail and not history:
        return analysis

    parts = []

    # 分红稳定性分析（基于detail）
    if detail:
        # 统计实际分红的年份
        dividend_years = [d for d in detail if d.get("cash_dividend", 0) > 0 and d.get("progress") == "实施分配"]
        no_dividend_years = [d for d in detail if d.get("progress") == "不分配"]
        total_years = len(detail)

        if total_years > 0:
            dividend_ratio = len(dividend_years) / total_years
            if dividend_ratio >= 0.8:
                analysis["dividend_stability"] = "稳定分红"
                parts.append(f"分红记录稳定（{len(dividend_years)}/{total_years}年分红）")
            elif dividend_ratio >= 0.5:
                analysis["dividend_stability"] = "较稳定"
                parts.append(f"分红较稳定（{len(dividend_years)}/{total_years}年分红）")
            elif dividend_ratio > 0:
                analysis["dividend_stability"] = "偶尔分红"
                parts.append(f"偶尔分红（{len(dividend_years)}/{total_years}年分红）")
            else:
                analysis["dividend_stability"] = "不分红"
                parts.append("历史无分红记录")

        # 最新股息率
        latest_with_yield = None
        for d in detail:
            if d.get("dividend_yield", 0) > 0:
                latest_with_yield = d
                break

        if latest_with_yield:
            dy = latest_with_yield["dividend_yield"]
            analysis["latest_dividend_yield"] = dy
            if dy >= 5:
                analysis["dividend_yield_level"] = "高股息"
                parts.append(f"最新股息率{dy:.2f}%（高股息）")
            elif dy >= 3:
                analysis["dividend_yield_level"] = "中等股息"
                parts.append(f"最新股息率{dy:.2f}%（中等）")
            elif dy >= 1:
                analysis["dividend_yield_level"] = "低股息"
                parts.append(f"最新股息率{dy:.2f}%（偏低）")
            else:
                analysis["dividend_yield_level"] = "极低股息"
                parts.append(f"最新股息率{dy:.2f}%")

        # 最近一次分红
        if dividend_years:
            latest = dividend_years[0]
            cash = latest.get("cash_dividend", 0)
            desc = latest.get("cash_desc", "")
            report = latest.get("report_date", "")
            if desc:
                parts.append(f"最近分红: {report} {desc}")
            elif cash > 0:
                parts.append(f"最近分红: {report} 每10股派{cash:.2f}元")

    # 历史分红趋势
    if history:
        actual_dividends = [h for h in history if h.get("cash_per_share", 0) > 0 and h.get("progress") == "实施"]
        if len(actual_dividends) >= 3:
            recent_3 = actual_dividends[:3]
            amounts = [d["cash_per_share"] for d in recent_3]
            if all(amounts[i] >= amounts[i+1] for i in range(len(amounts)-1)):
                analysis["dividend_trend"] = "分红递增"
                parts.append("近年分红金额递增")
            elif all(amounts[i] <= amounts[i+1] for i in range(len(amounts)-1)):
                analysis["dividend_trend"] = "分红递减"
                parts.append("近年分红金额递减")
            else:
                analysis["dividend_trend"] = "分红波动"

    analysis["summary"] = "，".join(parts) if parts else "分红数据不足"

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "detail": [],
        "history": [],
        "analysis": {
            "dividend_stability": "未知",
            "dividend_yield_level": "未知",
            "summary": "分红数据获取失败"
        }
    }
