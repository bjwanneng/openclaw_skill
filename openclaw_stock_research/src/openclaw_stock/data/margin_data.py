"""
融资融券数据采集模块

获取个股融资融券余额、买入额等数据，分析市场杠杆资金动向
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

from ..utils.logger import get_logger

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


def fetch_margin_data(symbol: str, days: int = 30) -> Dict[str, Any]:
    """
    获取个股融资融券数据

    参数:
        symbol: 股票代码（如 '601127'）
        days: 回看天数，默认30天

    返回:
        {
            'latest': 最新融资融券数据,
            'trend': 近期趋势数据列表,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[margin] akshare未安装")
        return _empty_result()

    result = {
        "latest": {},
        "trend": [],
        "analysis": {}
    }

    # 获取多天数据以构建趋势
    records = []
    end_date = datetime.now()

    # 尝试获取最近几个交易日的数据
    for i in range(min(days, 10)):
        date = end_date - timedelta(days=i)
        date_str = date.strftime("%Y%m%d")
        try:
            df = ak.stock_margin_detail_sse(date=date_str)
            if df is not None and not df.empty and '标的证券代码' in df.columns:
                df_stock = df[df['标的证券代码'] == symbol]
                if not df_stock.empty:
                    row = df_stock.iloc[0]
                    record = {
                        "date": date_str,
                        "margin_balance": float(row.get("融资余额", 0) or 0),
                        "margin_buy": float(row.get("融资买入额", 0) or 0),
                        "margin_repay": float(row.get("融资偿还额", 0) or 0),
                        "short_balance": float(row.get("融券余量", 0) or 0),
                        "short_sell": float(row.get("融券卖出量", 0) or 0),
                        "short_repay": float(row.get("融券偿还量", 0) or 0),
                    }
                    records.append(record)
        except Exception as e:
            # 非交易日或数据不可用，跳过
            continue

    if not records:
        # 尝试深市接口
        try:
            df = ak.stock_margin_detail_szse(date=end_date.strftime("%Y%m%d"))
            if df is not None and not df.empty:
                for col in df.columns:
                    if '代码' in col:
                        df_stock = df[df[col].astype(str) == symbol]
                        if not df_stock.empty:
                            row = df_stock.iloc[0]
                            record = {
                                "date": end_date.strftime("%Y%m%d"),
                                "margin_balance": float(row.get("融资余额", 0) or 0),
                                "margin_buy": float(row.get("融资买入额", 0) or 0),
                                "short_balance": float(row.get("融券余量", 0) or 0),
                                "short_sell": float(row.get("融券卖出量", 0) or 0),
                            }
                            records.append(record)
                            break
        except Exception as e:
            logger.warning(f"[margin] 深市融资融券获取失败: {e}")

    if records:
        # 按日期排序（最新在前）
        records.sort(key=lambda x: x["date"], reverse=True)
        result["latest"] = records[0]
        result["trend"] = records

    # 分析
    result["analysis"] = _analyze_margin(result)

    return result


def _analyze_margin(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析融资融券数据"""
    analysis = {
        "margin_trend": "无数据",
        "leverage_level": "未知",
        "summary": "融资融券数据获取失败"
    }

    latest = data.get("latest", {})
    trend = data.get("trend", [])

    if not latest:
        return analysis

    margin_balance = latest.get("margin_balance", 0)
    short_balance = latest.get("short_balance", 0)

    # 融资余额描述
    if margin_balance > 0:
        margin_balance_yi = margin_balance / 1e8
        analysis["margin_balance_desc"] = f"{margin_balance_yi:.2f}亿元"
    else:
        analysis["margin_balance_desc"] = "无数据"

    # 融资融券比
    if short_balance > 0 and margin_balance > 0:
        # 注意：融券余量是股数，融资余额是金额，不能直接比
        analysis["margin_short_info"] = f"融资余额{margin_balance/1e8:.2f}亿，融券余量{short_balance}股"

    # 趋势分析
    if len(trend) >= 2:
        latest_balance = trend[0].get("margin_balance", 0)
        prev_balance = trend[-1].get("margin_balance", 0)

        if prev_balance > 0:
            change_pct = (latest_balance - prev_balance) / prev_balance * 100
            if change_pct > 5:
                analysis["margin_trend"] = "融资余额显著增加"
                analysis["signal"] = "看多"
            elif change_pct > 0:
                analysis["margin_trend"] = "融资余额小幅增加"
                analysis["signal"] = "偏多"
            elif change_pct > -5:
                analysis["margin_trend"] = "融资余额小幅减少"
                analysis["signal"] = "偏空"
            else:
                analysis["margin_trend"] = "融资余额显著减少"
                analysis["signal"] = "看空"
            analysis["change_pct"] = round(change_pct, 2)
        else:
            analysis["margin_trend"] = "稳定"
            analysis["signal"] = "中性"
    else:
        analysis["margin_trend"] = "数据不足"
        analysis["signal"] = "中性"

    # 综合总结
    parts = []
    if margin_balance > 0:
        parts.append(f"融资余额{margin_balance/1e8:.2f}亿元")
    if analysis.get("margin_trend") and analysis["margin_trend"] != "无数据":
        parts.append(analysis["margin_trend"])
    if analysis.get("signal"):
        parts.append(f"杠杆资金信号: {analysis['signal']}")

    analysis["summary"] = "，".join(parts) if parts else "融资融券数据不足"

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "latest": {},
        "trend": [],
        "analysis": {
            "margin_trend": "无数据",
            "leverage_level": "未知",
            "summary": "融资融券数据获取失败"
        }
    }
