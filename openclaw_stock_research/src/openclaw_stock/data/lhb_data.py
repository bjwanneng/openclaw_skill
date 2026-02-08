"""
龙虎榜数据采集模块

获取个股龙虎榜上榜记录、机构买卖统计等数据
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

from ..utils.logger import get_logger

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


def fetch_lhb_data(symbol: str, days: int = 90) -> Dict[str, Any]:
    """
    获取个股龙虎榜数据

    参数:
        symbol: 股票代码（如 '601127'）
        days: 回看天数，默认90天

    返回:
        {
            'records': 上榜记录列表,
            'institution_summary': 机构买卖汇总,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[lhb] akshare未安装")
        return _empty_result()

    result = {
        "records": [],
        "institution_summary": {},
        "analysis": {}
    }

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    # 1. 获取龙虎榜明细
    try:
        df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
        if not df.empty and '代码' in df.columns:
            df_stock = df[df['代码'] == symbol]
            if not df_stock.empty:
                records = []
                for _, row in df_stock.iterrows():
                    records.append({
                        "date": str(row.get("上榜日", "")),
                        "reason": str(row.get("上榜原因", "")),
                        "close_price": float(row.get("收盘价", 0) or 0),
                        "change_pct": float(row.get("涨跌幅", 0) or 0),
                        "net_buy": float(row.get("龙虎榜净买额", 0) or 0),
                        "buy_amount": float(row.get("龙虎榜买入额", 0) or 0),
                        "sell_amount": float(row.get("龙虎榜卖出额", 0) or 0),
                        "turnover": float(row.get("龙虎榜成交额", 0) or 0),
                        "after_1d": float(row.get("上榜后1日", 0) or 0),
                        "after_5d": float(row.get("上榜后5日", 0) or 0),
                    })
                result["records"] = records
                logger.info(f"[lhb] {symbol} 近{days}天上榜 {len(records)} 次")
    except Exception as e:
        logger.warning(f"[lhb] 获取龙虎榜明细失败: {e}")

    # 2. 获取机构买卖统计
    try:
        df_jg = ak.stock_lhb_jgmmtj_em(start_date=start_date, end_date=end_date)
        if not df_jg.empty and '代码' in df_jg.columns:
            df_jg_stock = df_jg[df_jg['代码'] == symbol]
            if not df_jg_stock.empty:
                total_buy = df_jg_stock['机构买入总额'].sum() if '机构买入总额' in df_jg_stock.columns else 0
                total_sell = df_jg_stock['机构卖出总额'].sum() if '机构卖出总额' in df_jg_stock.columns else 0
                net_buy = df_jg_stock['机构买入净额'].sum() if '机构买入净额' in df_jg_stock.columns else 0
                buy_count = df_jg_stock['买方机构数'].sum() if '买方机构数' in df_jg_stock.columns else 0
                sell_count = df_jg_stock['卖方机构数'].sum() if '卖方机构数' in df_jg_stock.columns else 0

                result["institution_summary"] = {
                    "total_buy": float(total_buy),
                    "total_sell": float(total_sell),
                    "net_buy": float(net_buy),
                    "buy_institution_count": int(buy_count),
                    "sell_institution_count": int(sell_count),
                    "records_count": len(df_jg_stock),
                }
                logger.info(f"[lhb] {symbol} 机构净买入: {net_buy:.2f}万元")
    except Exception as e:
        logger.warning(f"[lhb] 获取机构买卖统计失败: {e}")

    # 3. 分析
    result["analysis"] = _analyze_lhb(result)

    return result


def _analyze_lhb(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析龙虎榜数据"""
    analysis = {
        "lhb_frequency": "无",
        "institution_attitude": "中性",
        "summary": "近期未上龙虎榜"
    }

    records = data.get("records", [])
    inst = data.get("institution_summary", {})

    if not records:
        return analysis

    # 上榜频率
    count = len(records)
    if count >= 5:
        analysis["lhb_frequency"] = "频繁上榜"
    elif count >= 2:
        analysis["lhb_frequency"] = "偶尔上榜"
    else:
        analysis["lhb_frequency"] = "少量上榜"

    # 龙虎榜净买入
    total_net_buy = sum(r.get("net_buy", 0) for r in records)
    if total_net_buy > 0:
        analysis["lhb_direction"] = "净买入"
    else:
        analysis["lhb_direction"] = "净卖出"

    # 机构态度
    net_buy = inst.get("net_buy", 0)
    if net_buy > 0:
        analysis["institution_attitude"] = "机构净买入"
    elif net_buy < 0:
        analysis["institution_attitude"] = "机构净卖出"

    # 上榜后表现
    avg_after_1d = sum(r.get("after_1d", 0) for r in records) / len(records) if records else 0
    avg_after_5d = sum(r.get("after_5d", 0) for r in records) / len(records) if records else 0

    # 综合总结
    parts = [f"近期上榜{count}次"]
    if total_net_buy > 0:
        parts.append(f"龙虎榜累计净买入{total_net_buy:.2f}万元")
    else:
        parts.append(f"龙虎榜累计净卖出{abs(total_net_buy):.2f}万元")

    if net_buy != 0:
        parts.append(analysis["institution_attitude"])

    if avg_after_1d != 0:
        parts.append(f"上榜后1日平均涨跌{avg_after_1d:.2f}%")

    analysis["summary"] = "，".join(parts)

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "records": [],
        "institution_summary": {},
        "analysis": {
            "lhb_frequency": "无",
            "institution_attitude": "中性",
            "summary": "数据获取失败"
        }
    }
