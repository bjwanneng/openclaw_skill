"""
限售解禁数据采集模块

获取个股限售股解禁计划，分析解禁压力
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


def fetch_restricted_shares_data(symbol: str) -> Dict[str, Any]:
    """
    获取个股限售解禁数据

    参数:
        symbol: 股票代码（如 '601127'）

    返回:
        {
            'schedule': 解禁计划列表,
            'upcoming': 近期解禁信息,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[restricted] akshare未安装")
        return _empty_result()

    result = {
        "schedule": [],
        "upcoming": {},
        "analysis": {}
    }

    try:
        df = ak.stock_restricted_release_queue_em(symbol=symbol)
        if df is not None and not df.empty:
            records = []
            for _, row in df.iterrows():
                record = {
                    "date": str(row.get("解禁时间", "")),
                    "shareholder_count": int(row.get("解禁股东数", 0) or 0),
                    "shares": float(row.get("解禁数量", 0) or 0),
                    "actual_shares": float(row.get("实际解禁数量", 0) or 0),
                    "unreleased_shares": float(row.get("未解禁数量", 0) or 0),
                    "market_value": float(row.get("实际解禁数量市值", 0) or 0),
                    "total_ratio": float(row.get("占总市值比例", 0) or 0),
                    "float_ratio": float(row.get("占流通市值比例", 0) or 0),
                    "type": str(row.get("限售股类型", "")),
                    "pre_close": float(row.get("解禁前一交易日收盘价", 0) or 0),
                }
                records.append(record)

            result["schedule"] = records

            # 找出未来的解禁
            now = datetime.now()
            upcoming = []
            for r in records:
                try:
                    release_date = datetime.strptime(r["date"], "%Y-%m-%d")
                    if release_date > now:
                        upcoming.append(r)
                except (ValueError, TypeError):
                    continue

            if upcoming:
                # 按日期排序，最近的在前
                upcoming.sort(key=lambda x: x["date"])
                result["upcoming"] = upcoming[0]  # 最近一次解禁
                result["upcoming_list"] = upcoming[:3]  # 最近3次

            logger.info(f"[restricted] {symbol} 共{len(records)}次解禁记录，未来{len(upcoming)}次")
    except Exception as e:
        logger.warning(f"[restricted] 获取限售解禁数据失败: {e}")

    # 分析
    result["analysis"] = _analyze_restricted(result)

    return result


def _analyze_restricted(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析限售解禁数据"""
    analysis = {
        "pressure_level": "无",
        "upcoming_pressure": "无近期解禁",
        "summary": "无限售解禁数据"
    }

    schedule = data.get("schedule", [])
    upcoming = data.get("upcoming", {})
    upcoming_list = data.get("upcoming_list", [])

    if not schedule:
        return analysis

    parts = [f"共{len(schedule)}次解禁记录"]

    # 近期解禁压力
    if upcoming:
        release_date = upcoming.get("date", "")
        float_ratio = upcoming.get("float_ratio", 0)
        market_value = upcoming.get("market_value", 0)
        share_type = upcoming.get("type", "")

        try:
            days_until = (datetime.strptime(release_date, "%Y-%m-%d") - datetime.now()).days
        except (ValueError, TypeError):
            days_until = -1

        if days_until > 0:
            parts.append(f"最近一次解禁: {release_date}（{days_until}天后）")

            if float_ratio > 10:
                analysis["pressure_level"] = "高"
                analysis["upcoming_pressure"] = "解禁压力大"
                parts.append(f"解禁占流通市值{float_ratio:.2f}%，压力较大")
            elif float_ratio > 3:
                analysis["pressure_level"] = "中等"
                analysis["upcoming_pressure"] = "解禁压力中等"
                parts.append(f"解禁占流通市值{float_ratio:.2f}%")
            elif float_ratio > 0:
                analysis["pressure_level"] = "低"
                analysis["upcoming_pressure"] = "解禁压力较小"
                parts.append(f"解禁占流通市值{float_ratio:.2f}%，压力较小")

            if market_value > 0:
                parts.append(f"解禁市值约{market_value/1e8:.2f}亿元")
            if share_type:
                parts.append(f"类型: {share_type}")

            # 30天内解禁预警
            if days_until <= 30:
                analysis["warning"] = f"注意：{days_until}天后有解禁"
        else:
            analysis["upcoming_pressure"] = "近期无解禁"
            parts.append("近期无解禁计划")
    else:
        analysis["upcoming_pressure"] = "无未来解禁"
        parts.append("无未来解禁计划")

    # 未来总解禁量
    if upcoming_list:
        total_ratio = sum(u.get("float_ratio", 0) for u in upcoming_list)
        if total_ratio > 0:
            parts.append(f"未来{len(upcoming_list)}次解禁合计占流通市值{total_ratio:.2f}%")

    analysis["summary"] = "，".join(parts)

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "schedule": [],
        "upcoming": {},
        "analysis": {
            "pressure_level": "无",
            "upcoming_pressure": "无近期解禁",
            "summary": "限售解禁数据获取失败"
        }
    }
