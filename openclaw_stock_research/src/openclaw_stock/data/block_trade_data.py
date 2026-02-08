"""
大宗交易数据采集模块

获取个股大宗交易明细和统计数据
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


def fetch_block_trade_data(symbol: str, days: int = 90) -> Dict[str, Any]:
    """
    获取个股大宗交易数据

    参数:
        symbol: 股票代码（如 '601127'）
        days: 回看天数，默认90天

    返回:
        {
            'trades': 交易明细列表,
            'statistics': 统计汇总,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[block_trade] akshare未安装")
        return _empty_result()

    result = {
        "trades": [],
        "statistics": {},
        "analysis": {}
    }

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    # 1. 获取大宗交易明细
    try:
        df = ak.stock_dzjy_mrmx(symbol='A股', start_date=start_date, end_date=end_date)
        if df is not None and not df.empty and '证券代码' in df.columns:
            df_stock = df[df['证券代码'] == symbol]
            if not df_stock.empty:
                trades = []
                for _, row in df_stock.iterrows():
                    trades.append({
                        "date": str(row.get("交易日期", "")),
                        "close_price": float(row.get("收盘价", 0) or 0),
                        "trade_price": float(row.get("成交价", 0) or 0),
                        "premium_rate": float(row.get("折溢率", 0) or 0),
                        "volume": float(row.get("成交量", 0) or 0),
                        "amount": float(row.get("成交额", 0) or 0),
                        "buyer": str(row.get("买方营业部", "")),
                        "seller": str(row.get("卖方营业部", "")),
                    })
                result["trades"] = trades
                logger.info(f"[block_trade] {symbol} 近{days}天大宗交易 {len(trades)} 笔")
    except Exception as e:
        logger.warning(f"[block_trade] 获取大宗交易明细失败: {e}")

    # 2. 获取大宗交易统计
    try:
        df_tj = ak.stock_dzjy_mrtj(start_date=start_date, end_date=end_date)
        if df_tj is not None and not df_tj.empty and '证券代码' in df_tj.columns:
            df_tj_stock = df_tj[df_tj['证券代码'] == symbol]
            if not df_tj_stock.empty:
                total_amount = df_tj_stock['成交总额'].sum() if '成交总额' in df_tj_stock.columns else 0
                total_volume = df_tj_stock['成交总量'].sum() if '成交总量' in df_tj_stock.columns else 0
                avg_premium = df_tj_stock['折溢率'].mean() if '折溢率' in df_tj_stock.columns else 0
                trade_count = df_tj_stock['成交笔数'].sum() if '成交笔数' in df_tj_stock.columns else len(df_tj_stock)

                result["statistics"] = {
                    "total_amount": float(total_amount),
                    "total_volume": float(total_volume),
                    "avg_premium_rate": float(avg_premium),
                    "trade_count": int(trade_count),
                    "trade_days": len(df_tj_stock),
                }
    except Exception as e:
        logger.warning(f"[block_trade] 获取大宗交易统计失败: {e}")

    # 3. 分析
    result["analysis"] = _analyze_block_trade(result)

    return result


def _analyze_block_trade(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析大宗交易数据"""
    analysis = {
        "trade_frequency": "无",
        "premium_status": "无数据",
        "summary": "近期无大宗交易"
    }

    trades = data.get("trades", [])
    stats = data.get("statistics", {})

    if not trades:
        return analysis

    # 交易频率
    count = len(trades)
    if count >= 10:
        analysis["trade_frequency"] = "频繁"
    elif count >= 3:
        analysis["trade_frequency"] = "较多"
    else:
        analysis["trade_frequency"] = "偶尔"

    # 折溢价分析
    premiums = [t.get("premium_rate", 0) for t in trades if t.get("premium_rate") is not None]
    if premiums:
        avg_premium = sum(premiums) / len(premiums)
        if avg_premium > 2:
            analysis["premium_status"] = "溢价成交"
            analysis["signal"] = "看多"
        elif avg_premium > -2:
            analysis["premium_status"] = "平价成交"
            analysis["signal"] = "中性"
        elif avg_premium > -5:
            analysis["premium_status"] = "小幅折价"
            analysis["signal"] = "偏空"
        else:
            analysis["premium_status"] = "大幅折价"
            analysis["signal"] = "看空"
        analysis["avg_premium_rate"] = round(avg_premium, 2)

    # 总成交额
    total_amount = stats.get("total_amount", sum(t.get("amount", 0) for t in trades))

    # 综合总结
    parts = [f"近期大宗交易{count}笔"]
    if total_amount > 0:
        parts.append(f"累计成交{total_amount:.2f}万元")
    if premiums:
        avg_p = sum(premiums) / len(premiums)
        parts.append(f"平均折溢率{avg_p:.2f}%")
        parts.append(analysis["premium_status"])

    analysis["summary"] = "，".join(parts)

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "trades": [],
        "statistics": {},
        "analysis": {
            "trade_frequency": "无",
            "premium_status": "无数据",
            "summary": "大宗交易数据获取失败"
        }
    }
