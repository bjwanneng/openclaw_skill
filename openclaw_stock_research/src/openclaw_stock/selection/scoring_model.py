"""
评分模型模块

实现短期和长期选股的评分逻辑
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np

from ..core.exceptions import CalculationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ScoreBreakdown:
    """评分明细"""
    category: str
    max_score: int
    actual_score: int
    details: Dict[str, Any]


class ScoringModel:
    """
    评分模型基类
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(self.__class__.__name__)

    def calculate_score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算评分"""
        raise NotImplementedError


def calculate_short_term_score(
    technical_score: int,
    fund_score: int,
    sentiment_score: int,
    news_score: int,
    signals: list
) -> Dict[str, Any]:
    """
    计算短期选股评分

    参数:
        technical_score: 技术面评分
        fund_score: 资金面评分
        sentiment_score: 情绪面评分
        news_score: 消息面评分
        signals: 信号列表

    返回:
        包含详细评分的字典
    """
    total_score = technical_score + fund_score + sentiment_score + news_score

    return {
        "total_score": total_score,
        "max_score": 100,
        "breakdown": {
            "technical": {
                "score": technical_score,
                "max": 40,
                "weight": 0.4,
                "details": {
                    "ma_breakthrough": 10,
                    "macd_signal": 10,
                    "volume_price": 10,
                    "relative_strength": 10
                }
            },
            "fund": {
                "score": fund_score,
                "max": 30,
                "weight": 0.3,
                "details": {
                    "main_inflow": 15,
                    "lhb_listed": 15
                }
            },
            "sentiment": {
                "score": sentiment_score,
                "max": 20,
                "weight": 0.2,
                "details": {
                    "sector_correlation": 10,
                    "limit_up_count": 10
                }
            },
            "news": {
                "score": news_score,
                "max": 10,
                "weight": 0.1,
                "details": {
                    "positive_news": 10
                }
            }
        },
        "signals": signals,
        "rating": _get_rating(total_score),
        "recommendation": _get_recommendation(total_score)
    }


def calculate_long_term_score(
    profitability_score: int,
    valuation_score: int,
    growth_score: int,
    quality_score: int,
    shareholder_score: int,
    signals: list
) -> Dict[str, Any]:
    """
    计算中长期选股评分

    参数:
        profitability_score: 盈利能力评分
        valuation_score: 估值水平评分
        growth_score: 成长性评分
        quality_score: 财务质量评分
        shareholder_score: 股东结构评分
        signals: 信号列表

    返回:
        包含详细评分的字典
    """
    total_score = profitability_score + valuation_score + growth_score + quality_score + shareholder_score

    return {
        "total_score": total_score,
        "max_score": 100,
        "breakdown": {
            "profitability": {
                "score": profitability_score,
                "max": 30,
                "weight": 0.3,
                "details": {
                    "roe_high": 10,
                    "profit_growth": 10,
                    "gross_margin": 10
                }
            },
            "valuation": {
                "score": valuation_score,
                "max": 25,
                "weight": 0.25,
                "details": {
                    "pe_below_avg": 10,
                    "pb_low": 10,
                    "peg_low": 5
                }
            },
            "growth": {
                "score": growth_score,
                "max": 20,
                "weight": 0.2,
                "details": {
                    "revenue_growth": 10,
                    "forecast_upgrade": 10
                }
            },
            "quality": {
                "score": quality_score,
                "max": 15,
                "weight": 0.15,
                "details": {
                    "low_debt": 5,
                    "cashflow_positive": 5,
                    "receivables_improve": 5
                }
            },
            "shareholder": {
                "score": shareholder_score,
                "max": 10,
                "weight": 0.1,
                "details": {
                    "institution_increase": 5,
                    "shareholder_decrease": 5
                }
            }
        },
        "signals": signals,
        "rating": _get_rating(total_score),
        "recommendation": _get_recommendation(total_score)
    }


def _get_rating(score: int) -> str:
    """根据分数获取评级"""
    if score >= 80:
        return "A+"
    elif score >= 70:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C"
    else:
        return "D"


def _get_recommendation(score: int) -> str:
    """根据分数获取建议"""
    if score >= 80:
        return "强烈推荐"
    elif score >= 70:
        return "推荐"
    elif score >= 60:
        return "关注"
    elif score >= 50:
        return "观望"
    else:
        return "回避"
