"""
行业对比数据采集模块

获取个股所属行业信息，与同行业股票进行估值和涨跌幅对比
"""

from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
import time

from ..utils.logger import get_logger

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


def fetch_industry_compare_data(symbol: str) -> Dict[str, Any]:
    """
    获取个股行业对比数据

    参数:
        symbol: 股票代码（如 '601127'）

    返回:
        {
            'stock_info': 个股基本信息（含行业）,
            'industry_peers': 同行业股票列表,
            'comparison': 行业对比数据,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[industry] akshare未安装")
        return _empty_result()

    result = {
        "stock_info": {},
        "industry_name": "",
        "industry_peers": [],
        "comparison": {},
        "analysis": {}
    }

    # 1. 获取个股基本信息（含行业）
    industry_name = ""
    try:
        df_info = ak.stock_individual_info_em(symbol=symbol)
        if df_info is not None and not df_info.empty:
            info_dict = {}
            for _, row in df_info.iterrows():
                info_dict[str(row.get("item", ""))] = row.get("value", "")

            result["stock_info"] = {
                "name": info_dict.get("股票简称", ""),
                "industry": info_dict.get("行业", ""),
                "total_shares": info_dict.get("总股本", ""),
                "float_shares": info_dict.get("流通股", ""),
                "total_market_cap": info_dict.get("总市值", ""),
                "float_market_cap": info_dict.get("流通市值", ""),
            }
            industry_name = info_dict.get("行业", "")
            result["industry_name"] = industry_name
            logger.info(f"[industry] {symbol} 所属行业: {industry_name}")
    except Exception as e:
        logger.warning(f"[industry] 获取个股信息失败: {e}")

    # 2. 获取同行业成分股
    if industry_name:
        max_retries = 2
        for attempt in range(max_retries):
            try:
                df_cons = ak.stock_board_industry_cons_em(symbol=industry_name)
                if df_cons is not None and not df_cons.empty:
                    peers = []
                    for _, row in df_cons.iterrows():
                        peer = {
                            "code": str(row.get("代码", "")),
                            "name": str(row.get("名称", "")),
                            "price": float(row.get("最新价", 0) or 0),
                            "change_pct": float(row.get("涨跌幅", 0) or 0),
                            "pe": float(row.get("市盈率-动态", 0) or 0),
                            "pb": float(row.get("市净率", 0) or 0),
                            "total_market_cap": float(row.get("总市值", 0) or 0),
                            "turnover_rate": float(row.get("换手率", 0) or 0),
                        }
                        peers.append(peer)

                    result["industry_peers"] = peers
                    logger.info(f"[industry] {industry_name} 共{len(peers)}只成分股")

                    # 3. 计算行业对比
                    result["comparison"] = _calculate_comparison(symbol, peers)
                    break
            except Exception as e:
                logger.warning(f"[industry] 获取行业成分股失败(尝试{attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)

    # 4. 分析
    result["analysis"] = _analyze_industry(result)

    return result


def _calculate_comparison(symbol: str, peers: List[Dict]) -> Dict[str, Any]:
    """计算行业对比数据"""
    if not peers:
        return {}

    # 过滤有效数据
    valid_pe = [p["pe"] for p in peers if p["pe"] and p["pe"] > 0 and p["pe"] < 1000]
    valid_pb = [p["pb"] for p in peers if p["pb"] and p["pb"] > 0 and p["pb"] < 100]
    valid_change = [p["change_pct"] for p in peers if p["change_pct"] is not None]
    valid_cap = [p["total_market_cap"] for p in peers if p["total_market_cap"] and p["total_market_cap"] > 0]

    # 找到目标股票
    target = None
    for p in peers:
        if p["code"] == symbol:
            target = p
            break

    comparison = {
        "total_peers": len(peers),
        "industry_avg_pe": round(sum(valid_pe) / len(valid_pe), 2) if valid_pe else 0,
        "industry_median_pe": round(sorted(valid_pe)[len(valid_pe)//2], 2) if valid_pe else 0,
        "industry_avg_pb": round(sum(valid_pb) / len(valid_pb), 2) if valid_pb else 0,
        "industry_median_pb": round(sorted(valid_pb)[len(valid_pb)//2], 2) if valid_pb else 0,
        "industry_avg_change": round(sum(valid_change) / len(valid_change), 2) if valid_change else 0,
    }

    if target:
        comparison["stock_pe"] = target["pe"]
        comparison["stock_pb"] = target["pb"]
        comparison["stock_change_pct"] = target["change_pct"]
        comparison["stock_market_cap"] = target["total_market_cap"]

        # PE排名
        if target["pe"] and target["pe"] > 0 and valid_pe:
            pe_rank = sum(1 for pe in valid_pe if pe <= target["pe"])
            comparison["pe_rank"] = pe_rank
            comparison["pe_rank_pct"] = round(pe_rank / len(valid_pe) * 100, 1)

        # PB排名
        if target["pb"] and target["pb"] > 0 and valid_pb:
            pb_rank = sum(1 for pb in valid_pb if pb <= target["pb"])
            comparison["pb_rank"] = pb_rank
            comparison["pb_rank_pct"] = round(pb_rank / len(valid_pb) * 100, 1)

        # 市值排名
        if target["total_market_cap"] and target["total_market_cap"] > 0 and valid_cap:
            cap_rank = sum(1 for cap in valid_cap if cap >= target["total_market_cap"])
            comparison["cap_rank"] = cap_rank
            comparison["cap_rank_total"] = len(valid_cap)

    return comparison


def _analyze_industry(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析行业对比数据"""
    analysis = {
        "valuation_position": "未知",
        "industry_rank": "未知",
        "summary": "行业对比数据不足"
    }

    comparison = data.get("comparison", {})
    industry_name = data.get("industry_name", "")

    if not comparison:
        return analysis

    parts = []
    if industry_name:
        parts.append(f"所属行业: {industry_name}（共{comparison.get('total_peers', 0)}只股票）")

    # PE估值位置
    pe_rank_pct = comparison.get("pe_rank_pct")
    stock_pe = comparison.get("stock_pe", 0)
    avg_pe = comparison.get("industry_avg_pe", 0)

    if pe_rank_pct is not None and stock_pe > 0:
        if pe_rank_pct <= 25:
            analysis["valuation_position"] = "行业低估值"
            parts.append(f"PE {stock_pe:.1f}（行业均值{avg_pe:.1f}），处于行业低估值区间（{pe_rank_pct:.0f}%分位）")
        elif pe_rank_pct <= 50:
            analysis["valuation_position"] = "行业中低估值"
            parts.append(f"PE {stock_pe:.1f}（行业均值{avg_pe:.1f}），处于行业中低估值区间（{pe_rank_pct:.0f}%分位）")
        elif pe_rank_pct <= 75:
            analysis["valuation_position"] = "行业中高估值"
            parts.append(f"PE {stock_pe:.1f}（行业均值{avg_pe:.1f}），处于行业中高估值区间（{pe_rank_pct:.0f}%分位）")
        else:
            analysis["valuation_position"] = "行业高估值"
            parts.append(f"PE {stock_pe:.1f}（行业均值{avg_pe:.1f}），处于行业高估值区间（{pe_rank_pct:.0f}%分位）")

    # 市值排名
    cap_rank = comparison.get("cap_rank")
    cap_total = comparison.get("cap_rank_total")
    if cap_rank and cap_total:
        parts.append(f"市值排名行业第{cap_rank}/{cap_total}")
        if cap_rank <= 3:
            analysis["industry_rank"] = "行业龙头"
        elif cap_rank <= cap_total * 0.2:
            analysis["industry_rank"] = "行业前列"
        elif cap_rank <= cap_total * 0.5:
            analysis["industry_rank"] = "行业中游"
        else:
            analysis["industry_rank"] = "行业后段"

    # 涨跌幅对比
    stock_change = comparison.get("stock_change_pct", 0)
    avg_change = comparison.get("industry_avg_change", 0)
    if stock_change is not None and avg_change is not None:
        diff = stock_change - avg_change
        if diff > 3:
            parts.append(f"今日涨跌幅{stock_change:.2f}%，跑赢行业均值{diff:.2f}个百分点")
        elif diff < -3:
            parts.append(f"今日涨跌幅{stock_change:.2f}%，跑输行业均值{abs(diff):.2f}个百分点")

    analysis["summary"] = "，".join(parts) if parts else "行业对比数据不足"

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "stock_info": {},
        "industry_name": "",
        "industry_peers": [],
        "comparison": {},
        "analysis": {
            "valuation_position": "未知",
            "industry_rank": "未知",
            "summary": "行业对比数据获取失败"
        }
    }
