"""
机构持仓数据采集模块

获取个股机构持仓、机构调研等数据
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


def fetch_institution_data(symbol: str) -> Dict[str, Any]:
    """
    获取个股机构持仓数据

    参数:
        symbol: 股票代码（如 '601127'）

    返回:
        {
            'holding': 机构持仓数据,
            'research': 机构调研数据,
            'analysis': 分析结论
        }
    """
    if ak is None:
        logger.warning("[institution] akshare未安装")
        return _empty_result()

    result = {
        "holding": {},
        "research": [],
        "analysis": {}
    }

    # 1. 获取机构持仓数据（尝试最近几个季度）
    now = datetime.now()
    year = now.year
    quarter = (now.month - 1) // 3  # 0-3, 上一季度

    for attempt in range(4):  # 尝试最近4个季度
        q = quarter - attempt
        y = year
        while q <= 0:
            q += 4
            y -= 1
        quarter_str = f"{y}{q}"

        try:
            df = ak.stock_institute_hold(symbol=quarter_str)
            if df is not None and not df.empty and '证券代码' in df.columns:
                df_stock = df[df['证券代码'] == symbol]
                if not df_stock.empty:
                    row = df_stock.iloc[0]
                    result["holding"] = {
                        "quarter": quarter_str,
                        "institution_count": int(row.get("机构数", 0) or 0),
                        "institution_change": int(row.get("机构数变化", 0) or 0),
                        "hold_ratio": float(row.get("持股比例", 0) or 0),
                        "hold_ratio_change": float(row.get("持股比例增幅", 0) or 0),
                        "float_ratio": float(row.get("占流通股比例", 0) or 0),
                        "float_ratio_change": float(row.get("占流通股比例增幅", 0) or 0),
                    }
                    logger.info(f"[institution] {symbol} {quarter_str}季度 机构数: {result['holding']['institution_count']}")
                    break
        except Exception as e:
            logger.debug(f"[institution] 获取{quarter_str}季度机构持仓失败: {e}")
            continue

    # 2. 获取机构调研数据
    try:
        # stock_jgdy_tj_em 按日期查询，获取最近的调研统计
        start_date = (datetime.now() - pd.Timedelta(days=180)).strftime("%Y%m%d")
        df_dy = ak.stock_jgdy_tj_em(date=start_date)
        if df_dy is not None and not df_dy.empty and '代码' in df_dy.columns:
            df_dy_stock = df_dy[df_dy['代码'] == symbol]
            if not df_dy_stock.empty:
                research_list = []
                for _, row in df_dy_stock.iterrows():
                    research_list.append({
                        "name": str(row.get("名称", "")),
                        "research_org_count": int(row.get("接待机构数量", 0) or 0),
                        "research_date": str(row.get("最近调研日期", "")),
                        "research_count": int(row.get("调研次数", 0) or 0),
                    })
                result["research"] = research_list
                logger.info(f"[institution] {symbol} 机构调研记录: {len(research_list)}")
    except Exception as e:
        logger.warning(f"[institution] 获取机构调研数据失败: {e}")

    # 3. 分析
    result["analysis"] = _analyze_institution(result)

    return result


def _analyze_institution(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析机构持仓数据"""
    analysis = {
        "institution_interest": "未知",
        "holding_trend": "未知",
        "summary": "机构持仓数据不足"
    }

    holding = data.get("holding", {})
    research = data.get("research", [])

    parts = []

    if holding:
        inst_count = holding.get("institution_count", 0)
        inst_change = holding.get("institution_change", 0)
        hold_ratio = holding.get("hold_ratio", 0)
        hold_ratio_change = holding.get("hold_ratio_change", 0)
        quarter = holding.get("quarter", "")

        # 机构关注度
        if inst_count >= 50:
            analysis["institution_interest"] = "高关注"
        elif inst_count >= 10:
            analysis["institution_interest"] = "中等关注"
        elif inst_count > 0:
            analysis["institution_interest"] = "低关注"
        else:
            analysis["institution_interest"] = "无机构持仓"

        parts.append(f"{quarter}季度{inst_count}家机构持仓")

        # 持仓变化
        if inst_change > 5:
            analysis["holding_trend"] = "机构大幅增持"
            parts.append(f"机构数增加{inst_change}家")
        elif inst_change > 0:
            analysis["holding_trend"] = "机构小幅增持"
            parts.append(f"机构数增加{inst_change}家")
        elif inst_change < -5:
            analysis["holding_trend"] = "机构大幅减持"
            parts.append(f"机构数减少{abs(inst_change)}家")
        elif inst_change < 0:
            analysis["holding_trend"] = "机构小幅减持"
            parts.append(f"机构数减少{abs(inst_change)}家")
        else:
            analysis["holding_trend"] = "持平"

        if hold_ratio > 0:
            parts.append(f"持股比例{hold_ratio:.2f}%")
        if hold_ratio_change != 0:
            parts.append(f"持股比例变化{hold_ratio_change:+.2f}%")

    # 调研情况
    if research:
        total_research = sum(r.get("research_count", 0) for r in research)
        total_orgs = sum(r.get("research_org_count", 0) for r in research)
        if total_research > 0:
            parts.append(f"近半年被调研{total_research}次，接待{total_orgs}家机构")

    analysis["summary"] = "，".join(parts) if parts else "机构持仓数据不足"

    return analysis


def _empty_result() -> Dict[str, Any]:
    """返回空结果"""
    return {
        "holding": {},
        "research": [],
        "analysis": {
            "institution_interest": "未知",
            "holding_trend": "未知",
            "summary": "机构持仓数据获取失败"
        }
    }
