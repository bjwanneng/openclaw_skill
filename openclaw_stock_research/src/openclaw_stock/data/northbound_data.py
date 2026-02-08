"""
北向资金（沪深港通）数据采集模块

获取北向资金持股数据和整体资金流向
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


def fetch_northbound_data(symbol: str, market: str = "sh") -> Dict[str, Any]:
    """
    获取个股北向资金数据

    参数:
        symbol: 股票代码（如 '601127'）
        market: 市场类型 'sh' 或 'sz'

    返回:
        {
            'individual': 个股北向持股数据,
            'overall_flow': 北向资金整体流向,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[northbound] akshare未安装")
        return _empty_result()

    result = {
        "individual": {},
        "overall_flow": [],
        "analysis": {}
    }

    # 1. 获取个股北向持股数据
    try:
        market_name = "沪股通" if market == "sh" else "深股通"
        df = ak.stock_hsgt_hold_stock_em(market=market_name, indicator="今日排行")
        if df is not None and not df.empty and '代码' in df.columns:
            df_stock = df[df['代码'] == symbol]
            if not df_stock.empty:
                row = df_stock.iloc[0]
                result["individual"] = {
                    "name": str(row.get("名称", "")),
                    "close_price": float(row.get("今日收盘价", 0) or 0),
                    "change_pct": float(row.get("今日涨跌幅", 0) or 0),
                    "hold_shares": float(row.get("今日持股-股数", 0) or 0),
                    "hold_value": float(row.get("今日持股-市值", 0) or 0),
                    "hold_ratio_float": float(row.get("今日持股-占流通股比", 0) or 0),
                    "hold_ratio_total": float(row.get("今日持股-占总股本比", 0) or 0),
                    "change_shares": float(row.get("今日增持估计-股数", 0) or 0),
                    "change_value": float(row.get("今日增持估计-市值", 0) or 0),
                    "change_value_pct": float(row.get("今日增持估计-市值增幅", 0) or 0),
                    "board": str(row.get("所属板块", "")),
                    "date": str(row.get("日期", "")),
                }
                logger.info(f"[northbound] {symbol} 北向持股占流通股比: {result['individual'].get('hold_ratio_float', 0)}%")
    except Exception as e:
        logger.warning(f"[northbound] 获取个股北向持股失败: {e}")

    # 2. 获取北向资金整体流向（最近几天）
    try:
        df_flow = ak.stock_hsgt_hist_em(symbol="北向资金")
        if df_flow is not None and not df_flow.empty:
            recent = df_flow.tail(10)
            flow_list = []
            for _, row in recent.iterrows():
                flow_list.append({
                    "date": str(row.get("日期", "")),
                    "net_buy": float(row.get("当日成交净买额", 0) or 0),
                    "buy_amount": float(row.get("买入成交额", 0) or 0),
                    "sell_amount": float(row.get("卖出成交额", 0) or 0),
                    "cumulative": float(row.get("历史累计净买额", 0) or 0),
                })
            result["overall_flow"] = flow_list
    except Exception as e:
        logger.warning(f"[northbound] 获取北向资金整体流向失败: {e}")

    # 3. 分析
    result["analysis"] = _analyze_northbound(result)

    return result


def _analyze_northbound(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析北向资金数据"""
    analysis = {
        "foreign_attitude": "中性",
        "hold_level": "未知",
        "flow_trend": "未知",
        "summary": "北向资金数据不足"
    }

    individual = data.get("individual", {})
    overall_flow = data.get("overall_flow", [])

    parts = []

    # 个股持股分析
    if individual:
        hold_ratio = individual.get("hold_ratio_float", 0)
        change_shares = individual.get("change_shares", 0)
        hold_value = individual.get("hold_value", 0)

        # 持股水平
        if hold_ratio > 10:
            analysis["hold_level"] = "重仓"
            parts.append(f"北向资金重仓持有（占流通股{hold_ratio:.2f}%）")
        elif hold_ratio > 3:
            analysis["hold_level"] = "中等持仓"
            parts.append(f"北向资金中等持仓（占流通股{hold_ratio:.2f}%）")
        elif hold_ratio > 0:
            analysis["hold_level"] = "轻仓"
            parts.append(f"北向资金轻仓持有（占流通股{hold_ratio:.2f}%）")

        # 增减持
        if change_shares > 0:
            analysis["foreign_attitude"] = "增持"
            change_value = individual.get("change_value", 0)
            parts.append(f"今日增持{change_shares:.0f}股（约{change_value:.2f}万元）")
        elif change_shares < 0:
            analysis["foreign_attitude"] = "减持"
            parts.append(f"今日减持{abs(change_shares):.0f}股")
        else:
            analysis["foreign_attitude"] = "持平"

    # 整体北向资金流向
    if overall_flow:
        recent_5d = overall_flow[-5:] if len(overall_flow) >= 5 else overall_flow
        total_net = sum(f.get("net_buy", 0) for f in recent_5d)

        if total_net > 50:
            analysis["flow_trend"] = "大幅净流入"
            parts.append(f"近期北向资金大幅净流入{total_net:.2f}亿元")
        elif total_net > 0:
            analysis["flow_trend"] = "小幅净流入"
            parts.append(f"近期北向资金净流入{total_net:.2f}亿元")
        elif total_net > -50:
            analysis["flow_trend"] = "小幅净流出"
            parts.append(f"近期北向资金净流出{abs(total_net):.2f}亿元")
        else:
            analysis["flow_trend"] = "大幅净流出"
            parts.append(f"近期北向资金大幅净流出{abs(total_net):.2f}亿元")

    analysis["summary"] = "，".join(parts) if parts else "北向资金数据不足"

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "individual": {},
        "overall_flow": [],
        "analysis": {
            "foreign_attitude": "中性",
            "hold_level": "未知",
            "flow_trend": "未知",
            "summary": "北向资金数据获取失败"
        }
    }
