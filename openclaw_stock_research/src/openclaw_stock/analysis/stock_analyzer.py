"""
股票综合分析模块

实现设计文档4.4节的接口8: 个股综合分析
"""

from typing import Literal, Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..core.exceptions import DataSourceError, CalculationError
from ..utils.logger import get_logger
from ..data.market_data import fetch_market_data, fetch_realtime_quote
from ..data.financial_data import fetch_financial_data
from ..data.fund_flow import fetch_fund_flow, fetch_capital_flow
from ..data.news_data import fetch_stock_news
from ..data.lhb_data import fetch_lhb_data
from ..data.margin_data import fetch_margin_data
from ..data.northbound_data import fetch_northbound_data
from ..data.block_trade_data import fetch_block_trade_data
from ..data.shareholder_data import fetch_shareholder_data
from ..data.institution_data import fetch_institution_data
from ..data.restricted_shares_data import fetch_restricted_shares_data
from ..data.industry_compare_data import fetch_industry_compare_data
from ..data.dividend_data import fetch_dividend_data
from ..analysis.technical_analysis import (
    calculate_technical_indicators,
    calculate_support_resistance,
    TechnicalAnalyzer
)
from ..analysis.fundamental_analysis import (
    calculate_fundamental_indicators,
    FundamentalAnalyzer
)
from ..analysis.chip_analysis import analyze_chip_distribution

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


@dataclass
class PredictionResult:
    """后市预测结果"""
    trend: str  # up/down/sideways
    probability: float  # 概率 0-1
    target_price_high: Optional[float] = None
    target_price_low: Optional[float] = None
    time_horizon: str = "短期(1-2周)"
    risk_level: str = "中等"
    key_factors: List[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """风险评估"""
    overall_risk: str  # low/medium/high
    volatility_risk: str
    liquidity_risk: str
    fundamental_risk: str
    market_risk: str
    max_drawdown_estimate: Optional[float] = None
    risk_factors: List[str] = field(default_factory=list)


def analyze_stock(
    symbol: str,
    market: Literal["sh", "sz", "hk"] = "sh",
    lookback_days: int = 250
) -> Dict[str, Any]:
    """
    个股全方位分析（接口8实现）

    参数:
        symbol: 股票代码
        market: 市场类型
        lookback_days: 回看天数

    返回:
        {
            'basic_info': 基本信息,
            'technical_analysis': 技术分析结果,
            'fundamental_analysis': 基本面分析,
            'fund_flow_analysis': 资金流向分析,
            'risk_assessment': 风险评估,
            'prediction': 后市预测
        }

    异常:
        DataSourceError: 数据源访问失败
        CalculationError: 计算失败
    """
    if ak is None:
        raise DataSourceError("akshare库未安装")

    logger.info(f"[analyze_stock] 开始分析 {market}:{symbol}")

    try:
        result = {
            "symbol": symbol,
            "market": market,
            "analysis_time": datetime.now().isoformat(),
            "basic_info": {},
            "technical_analysis": {},
            "fundamental_analysis": {},
            "fund_flow_analysis": {},
            "news_analysis": {},
            "chip_analysis": {},
            # === 新增9大数据源 ===
            "lhb_analysis": {},
            "margin_analysis": {},
            "northbound_analysis": {},
            "block_trade_analysis": {},
            "shareholder_analysis": {},
            "institution_analysis": {},
            "restricted_shares_analysis": {},
            "industry_compare_analysis": {},
            "dividend_analysis": {},
            # === END ===
            "risk_assessment": {},
            "prediction": {}
        }

        # 1. 获取基本信息
        try:
            # 获取实时行情
            realtime_data = fetch_realtime_quote(symbol=symbol, market=market)
            result["basic_info"] = {
                "symbol": symbol,
                "name": realtime_data.get("name", ""),
                "current_price": realtime_data.get("price", 0),
                "change": realtime_data.get("change", 0),
                "change_pct": realtime_data.get("change_pct", 0),
                "volume": realtime_data.get("volume", 0),
                "turnover": realtime_data.get("amount", 0),
                "high": realtime_data.get("high", 0),
                "low": realtime_data.get("low", 0),
                "open": realtime_data.get("open", 0),
                "pre_close": realtime_data.get("pre_close", 0)
            }
        except Exception as e:
            logger.warning(f"[{symbol}] 获取基本信息失败: {e}")

        # 2. 技术分析
        try:
            # 获取历史K线数据
            df_kline = fetch_market_data(
                symbol=symbol,
                period="daily",
                start_date=(datetime.now() - timedelta(days=lookback_days)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                market=market
            )

            if not df_kline.empty:
                # 计算技术指标
                df_tech = calculate_technical_indicators(df_kline)

                # 检测交易信号
                analyzer = TechnicalAnalyzer()
                signals = analyzer.detect_signals(df_tech)

                # 计算支撑压力位
                sr_data = calculate_support_resistance(symbol, df_tech)

                # 趋势判断
                current_price = df_tech["close"].iloc[-1]
                ma20 = df_tech["ma20"].iloc[-1] if "ma20" in df_tech.columns else current_price
                ma60 = df_tech["ma60"].iloc[-1] if "ma60" in df_tech.columns else current_price

                if current_price > ma20 > ma60:
                    trend = "上升趋势"
                elif current_price < ma20 < ma60:
                    trend = "下降趋势"
                else:
                    trend = "震荡整理"

                result["technical_analysis"] = {
                    "current_price": current_price,
                    "trend": trend,
                    "signals": signals,
                    "support_resistance": sr_data,
                    "indicators": {
                        "ma5": df_tech["ma5"].iloc[-1] if "ma5" in df_tech.columns else None,
                        "ma10": df_tech["ma10"].iloc[-1] if "ma10" in df_tech.columns else None,
                        "ma20": df_tech["ma20"].iloc[-1] if "ma20" in df_tech.columns else None,
                        "ma60": df_tech["ma60"].iloc[-1] if "ma60" in df_tech.columns else None,
                        "rsi6": df_tech["rsi6"].iloc[-1] if "rsi6" in df_tech.columns else None,
                        "macd_hist": df_tech["macd_hist"].iloc[-1] if "macd_hist" in df_tech.columns else None,
                    }
                }
        except Exception as e:
            logger.warning(f"[{symbol}] 技术分析失败: {e}")

        # 3. 基本面分析
        try:
            # 获取基本面数据
            fundamental_data = calculate_fundamental_indicators(symbol)

            # 使用FundamentalAnalyzer进行分析
            analyzer = FundamentalAnalyzer()
            valuation_level = analyzer.analyze_valuation(fundamental_data)
            profitability_level = analyzer.analyze_profitability(fundamental_data)
            growth_level = analyzer.analyze_growth(fundamental_data)

            # 估值评价
            if valuation_level == "undervalued":
                valuation_desc = "低估值"
            elif valuation_level == "overvalued":
                valuation_desc = "高估值"
            else:
                valuation_desc = "合理估值"

            result["fundamental_analysis"] = {
                "valuation": fundamental_data.get("valuation", {}),
                "profitability": fundamental_data.get("profitability", {}),
                "growth": fundamental_data.get("growth", {}),
                "quality": fundamental_data.get("quality", {}),
                "analysis": {
                    "valuation_level": valuation_desc,
                    "profitability_level": profitability_level,
                    "growth_level": growth_level,
                }
            }
        except Exception as e:
            logger.warning(f"[{symbol}] 基本面分析失败: {e}")

        # 4. 资金流向分析
        try:
            # 获取资金流向数据
            capital_flow = fetch_capital_flow(symbol=symbol, market=market, days=5)

            result["fund_flow_analysis"] = {
                "recent_flow": capital_flow,
                "main_inflow_5d": capital_flow.get("main_inflow", 0),
                "retail_inflow_5d": capital_flow.get("retail_inflow", 0),
            }
        except Exception as e:
            logger.warning(f"[{symbol}] 资金流向分析失败: {e}")

        # 5. 新闻分析
        try:
            # 获取股票名称
            stock_name = result.get("basic_info", {}).get("name", "")
            
            # 获取新闻数据
            news_data = fetch_stock_news(symbol=symbol, stock_name=stock_name, limit=10)
            
            result["news_analysis"] = {
                "news_count": news_data.get("news_count", 0),
                "news_list": news_data.get("news_list", []),
                "summary": news_data.get("summary", ""),
                "fetch_time": news_data.get("fetch_time", "")
            }
            
            logger.info(f"[{symbol}] 获取到 {news_data.get('news_count', 0)} 条新闻")
        except Exception as e:
            logger.warning(f"[{symbol}] 新闻分析失败: {e}")
            result["news_analysis"] = {
                "news_count": 0,
                "news_list": [],
                "summary": "新闻获取失败",
                "error": str(e)
            }

        # 6. 筹码分布分析
        try:
            current_price = result.get("basic_info", {}).get("current_price", None)
            chip_data = analyze_chip_distribution(
                symbol=symbol,
                current_price=current_price,
                adjust="qfq"
            )
            result["chip_analysis"] = chip_data
            logger.info(f"[{symbol}] 筹码分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 筹码分析失败: {e}")
            result["chip_analysis"] = {
                "latest": {},
                "trend": {},
                "assessment": {
                    "chip_status": "unknown",
                    "summary": f"筹码分析失败: {e}"
                },
                "error": str(e)
            }

        # === 7-15: 新增9大数据源 ===

        # 7. 龙虎榜
        try:
            lhb_data = fetch_lhb_data(symbol=symbol, days=90)
            result["lhb_analysis"] = lhb_data
            logger.info(f"[{symbol}] 龙虎榜分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 龙虎榜分析失败: {e}")

        # 8. 融资融券
        try:
            margin_data = fetch_margin_data(symbol=symbol, days=30)
            result["margin_analysis"] = margin_data
            logger.info(f"[{symbol}] 融资融券分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 融资融券分析失败: {e}")

        # 9. 北向资金
        try:
            northbound_data = fetch_northbound_data(symbol=symbol, market=market)
            result["northbound_analysis"] = northbound_data
            logger.info(f"[{symbol}] 北向资金分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 北向资金分析失败: {e}")

        # 10. 大宗交易
        try:
            block_trade_data = fetch_block_trade_data(symbol=symbol, days=90)
            result["block_trade_analysis"] = block_trade_data
            logger.info(f"[{symbol}] 大宗交易分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 大宗交易分析失败: {e}")

        # 11. 股东人数
        try:
            shareholder_data = fetch_shareholder_data(symbol=symbol)
            result["shareholder_analysis"] = shareholder_data
            logger.info(f"[{symbol}] 股东人数分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 股东人数分析失败: {e}")

        # 12. 机构持仓
        try:
            institution_data = fetch_institution_data(symbol=symbol)
            result["institution_analysis"] = institution_data
            logger.info(f"[{symbol}] 机构持仓分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 机构持仓分析失败: {e}")

        # 13. 限售解禁
        try:
            restricted_data = fetch_restricted_shares_data(symbol=symbol)
            result["restricted_shares_analysis"] = restricted_data
            logger.info(f"[{symbol}] 限售解禁分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 限售解禁分析失败: {e}")

        # 14. 行业对比
        try:
            industry_data = fetch_industry_compare_data(symbol=symbol)
            result["industry_compare_analysis"] = industry_data
            logger.info(f"[{symbol}] 行业对比分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 行业对比分析失败: {e}")

        # 15. 分红送转
        try:
            dividend_data = fetch_dividend_data(symbol=symbol)
            result["dividend_analysis"] = dividend_data
            logger.info(f"[{symbol}] 分红送转分析完成")
        except Exception as e:
            logger.warning(f"[{symbol}] 分红送转分析失败: {e}")

        # === END 9大数据源 ===

        # 16. 风险评估
        try:
            risk_factors = []

            # 根据波动率评估
            volatility = "medium"
            if "technical_analysis" in result and result["technical_analysis"]:
                indicators = result["technical_analysis"].get("indicators", {})
                rsi = indicators.get("rsi6")
                if rsi and (rsi > 80 or rsi < 20):
                    volatility = "high"
                    risk_factors.append("RSI超买/超卖")

            # 根据估值评估
            valuation_risk = "medium"
            if "fundamental_analysis" in result and result["fundamental_analysis"]:
                valuation = result["fundamental_analysis"].get("valuation", {})
                pe = valuation.get("pe_ttm")
                if pe and pe > 50:
                    valuation_risk = "high"
                    risk_factors.append("估值偏高")
                elif pe and pe < 10:
                    valuation_risk = "low"

            # 根据趋势评估
            trend_risk = "medium"
            if "technical_analysis" in result and result["technical_analysis"]:
                trend = result["technical_analysis"].get("trend", "")
                if "下降" in trend:
                    trend_risk = "high"
                    risk_factors.append("下降趋势")
                elif "上升" in trend:
                    trend_risk = "low"

            # 综合风险等级
            risk_levels = [volatility, valuation_risk, trend_risk]
            high_count = risk_levels.count("high")
            low_count = risk_levels.count("low")

            if high_count >= 2:
                overall_risk = "high"
            elif low_count >= 2:
                overall_risk = "low"
            else:
                overall_risk = "medium"

            result["risk_assessment"] = {
                "overall_risk": overall_risk,
                "volatility_risk": volatility,
                "valuation_risk": valuation_risk,
                "trend_risk": trend_risk,
                "risk_factors": risk_factors,
                "max_drawdown_estimate": None  # 需要历史数据计算
            }
        except Exception as e:
            logger.warning(f"[{symbol}] 风险评估失败: {e}")

        # 8. 后市预测
        try:
            # 基于技术和基本面综合判断
            trend_probability = 0.5
            predicted_trend = "sideways"
            target_high = None
            target_low = None
            key_factors = []

            # 技术面判断
            if "technical_analysis" in result and result["technical_analysis"]:
                tech = result["technical_analysis"]
                trend = tech.get("trend", "")
                signals = tech.get("signals", {})

                if "上升" in trend:
                    trend_probability += 0.2
                    key_factors.append("技术趋势向上")
                elif "下降" in trend:
                    trend_probability -= 0.2
                    key_factors.append("技术趋势向下")

                overall_signal = signals.get("overall", "neutral") if isinstance(signals, dict) else "neutral"
                if overall_signal in ["buy", "strong_buy"]:
                    trend_probability += 0.15
                    key_factors.append("技术指标买入信号")
                elif overall_signal in ["sell", "strong_sell"]:
                    trend_probability -= 0.15
                    key_factors.append("技术指标卖出信号")

            # 基本面判断
            if "fundamental_analysis" in result and result["fundamental_analysis"]:
                fund = result["fundamental_analysis"]
                analysis = fund.get("analysis", {})

                profitability = analysis.get("profitability_level", "moderate")
                if profitability == "strong":
                    trend_probability += 0.1
                    key_factors.append("盈利能力强")

                growth = analysis.get("growth_level", "moderate")
                if growth == "high":
                    trend_probability += 0.1
                    key_factors.append("成长性高")

                valuation = analysis.get("valuation_level", "合理估值")
                if "低估值" in valuation:
                    trend_probability += 0.1
                    key_factors.append("估值偏低")
                elif "高估值" in valuation:
                    trend_probability -= 0.1
                    key_factors.append("估值偏高")

            # 资金流向判断
            if "fund_flow_analysis" in result and result["fund_flow_analysis"]:
                flow = result["fund_flow_analysis"]
                main_inflow = flow.get("main_inflow_5d", 0)

                if main_inflow > 0:
                    trend_probability += 0.1
                    key_factors.append("主力资金净流入")
                elif main_inflow < 0:
                    trend_probability -= 0.1
                    key_factors.append("主力资金净流出")

            # 筹码面判断
            if "chip_analysis" in result and result["chip_analysis"]:
                chip = result["chip_analysis"]
                chip_assessment = chip.get("assessment", {})
                chip_trend = chip.get("trend", {})

                chip_status = chip_assessment.get("chip_status", "neutral")
                if chip_status in ("highly_concentrated", "concentrated"):
                    trend_probability += 0.05
                    key_factors.append("筹码集中")
                elif chip_status == "dispersed":
                    trend_probability -= 0.05
                    key_factors.append("筹码分散")

                conc_trend = chip_trend.get("concentration_trend", "stable")
                if conc_trend == "concentrating":
                    trend_probability += 0.05
                    key_factors.append("筹码趋于集中")
                elif conc_trend == "dispersing":
                    trend_probability -= 0.05
                    key_factors.append("筹码趋于分散")

                chip_latest = chip.get("latest", {})
                winner_rate = chip_latest.get("winner_rate", 0.5)
                if winner_rate > 0.90:
                    trend_probability -= 0.05
                    key_factors.append("获利盘压力大")
                elif winner_rate < 0.10:
                    key_factors.append("套牢盘较重")

                # 主力行为推断
                inst_signal = chip_trend.get("institutional_signal", "neutral")
                if inst_signal == "accumulating":
                    trend_probability += 0.05
                    key_factors.append("筹码分析研判主力吸筹")
                elif inst_signal == "distributing":
                    trend_probability -= 0.05
                    key_factors.append("筹码分析研判主力派发")

            # === 新增数据源纳入预测 ===

            # 龙虎榜判断
            if result.get("lhb_analysis"):
                lhb = result["lhb_analysis"]
                lhb_analysis = lhb.get("analysis", {})
                inst_att = lhb_analysis.get("institution_attitude", "中性")
                if "净买入" in inst_att:
                    trend_probability += 0.05
                    key_factors.append("龙虎榜机构净买入")
                elif "净卖出" in inst_att:
                    trend_probability -= 0.05
                    key_factors.append("龙虎榜机构净卖出")

            # 融资融券判断
            if result.get("margin_analysis"):
                margin = result["margin_analysis"]
                margin_analysis = margin.get("analysis", {})
                margin_trend = margin_analysis.get("margin_trend", "stable")
                if margin_trend == "increasing":
                    trend_probability += 0.05
                    key_factors.append("融资余额增加（杠杆看多）")
                elif margin_trend == "decreasing":
                    trend_probability -= 0.05
                    key_factors.append("融资余额减少（杠杆看空）")

            # 北向资金判断
            if result.get("northbound_analysis"):
                nb = result["northbound_analysis"]
                nb_analysis = nb.get("analysis", {})
                nb_direction = nb_analysis.get("direction", "neutral")
                if nb_direction == "inflow":
                    trend_probability += 0.05
                    key_factors.append("北向资金净流入")
                elif nb_direction == "outflow":
                    trend_probability -= 0.05
                    key_factors.append("北向资金净流出")

            # 大宗交易判断
            if result.get("block_trade_analysis"):
                bt = result["block_trade_analysis"]
                bt_analysis = bt.get("analysis", {})
                bt_premium = bt_analysis.get("avg_premium", 0)
                if bt_analysis.get("records_count", 0) > 0:
                    if bt_premium > 0:
                        trend_probability += 0.03
                        key_factors.append("大宗交易溢价成交")
                    elif bt_premium < -5:
                        trend_probability -= 0.03
                        key_factors.append("大宗交易大幅折价")

            # 股东人数判断
            if result.get("shareholder_analysis"):
                sh = result["shareholder_analysis"]
                sh_analysis = sh.get("analysis", {})
                sh_trend = sh_analysis.get("shareholder_trend", "stable")
                if sh_trend == "decreasing":
                    trend_probability += 0.05
                    key_factors.append("股东人数减少（筹码集中）")
                elif sh_trend == "increasing":
                    trend_probability -= 0.03
                    key_factors.append("股东人数增加（筹码分散）")

            # 限售解禁判断
            if result.get("restricted_shares_analysis"):
                rs = result["restricted_shares_analysis"]
                rs_analysis = rs.get("analysis", {})
                rs_pressure = rs_analysis.get("pressure_level", "low")
                if rs_pressure == "high":
                    trend_probability -= 0.05
                    key_factors.append("近期有大额限售解禁")
                elif rs_pressure == "medium":
                    trend_probability -= 0.02
                    key_factors.append("近期有限售解禁")

            # 机构持仓判断
            if result.get("institution_analysis"):
                inst = result["institution_analysis"]
                inst_analysis = inst.get("analysis", {})
                inst_trend = inst_analysis.get("holding_trend", "stable")
                if inst_trend == "increasing":
                    trend_probability += 0.05
                    key_factors.append("机构持仓增加")
                elif inst_trend == "decreasing":
                    trend_probability -= 0.03
                    key_factors.append("机构持仓减少")

            # === END 新增数据源 ===

            # 确定趋势方向
            if trend_probability > 0.6:
                predicted_trend = "up"
            elif trend_probability < 0.4:
                predicted_trend = "down"
            else:
                predicted_trend = "sideways"

            # 计算目标价格区间
            current_price = 0
            if "basic_info" in result and result["basic_info"]:
                current_price = result["basic_info"].get("current_price", 0)

            if current_price > 0:
                if predicted_trend == "up":
                    target_high = round(current_price * 1.15, 2)  # 上涨15%
                    target_low = round(current_price * 1.05, 2)   # 上涨5%
                elif predicted_trend == "down":
                    target_high = round(current_price * 0.98, 2)  # 下跌2%
                    target_low = round(current_price * 0.85, 2)   # 下跌15%
                else:
                    target_high = round(current_price * 1.08, 2)  # 上涨8%
                    target_low = round(current_price * 0.95, 2)   # 下跌5%

            # 确定风险等级
            risk_level = "中等"
            if "risk_assessment" in result and result["risk_assessment"]:
                risk_level_map = {
                    "low": "低",
                    "medium": "中等",
                    "high": "高"
                }
                risk_level = risk_level_map.get(
                    result["risk_assessment"].get("overall_risk", "medium"),
                    "中等"
                )

            result["prediction"] = {
                "trend": predicted_trend,
                "trend_cn": "上涨" if predicted_trend == "up" else ("下跌" if predicted_trend == "down" else "震荡"),
                "probability": round(trend_probability, 2),
                "target_price_high": target_high,
                "target_price_low": target_low,
                "time_horizon": "短期(1-2周)",
                "risk_level": risk_level,
                "key_factors": key_factors if key_factors else ["综合分析"],
                "recommendation": _get_prediction_recommendation(predicted_trend, trend_probability, risk_level)
            }

        except Exception as e:
            logger.warning(f"[{symbol}] 后市预测失败: {e}")
            result["prediction"] = {
                "error": str(e),
                "trend": "unknown",
                "probability": 0.5
            }

        logger.info(f"[analyze_stock] 分析完成: {symbol}")
        return result

    except Exception as e:
        logger.error(f"[analyze_stock] 分析失败: {e}")
        raise CalculationError(f"分析{symbol}失败: {e}")


def _get_prediction_recommendation(trend: str, probability: float, risk_level: str) -> str:
    """获取预测建议"""
    if trend == "up":
        if probability > 0.7:
            if risk_level == "高":
                return "建议谨慎买入，注意风险控制"
            return "建议买入"
        elif probability > 0.5:
            return "建议关注，等待更好的入场时机"
        else:
            return "建议观望"
    elif trend == "down":
        if probability > 0.7:
            return "建议卖出或观望"
        elif probability > 0.5:
            return "建议减仓或观望"
        else:
            return "建议观望"
    else:
        return "建议观望，等待趋势明朗"


class StockAnalyzer:
    """
    股票综合分析器类

    提供股票分析的统一接口
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.fundamental_analyzer = FundamentalAnalyzer()

    def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """执行分析"""
        return analyze_stock(symbol, **kwargs)

    def generate_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成分析报告文本

        参数:
            analysis_result: 分析结果字典

        返回:
            分析报告文本
        """
        symbol = analysis_result.get("symbol", "")
        basic_info = analysis_result.get("basic_info", {})
        technical = analysis_result.get("technical_analysis", {})
        fundamental = analysis_result.get("fundamental_analysis", {})
        fund_flow = analysis_result.get("fund_flow_analysis", {})
        news = analysis_result.get("news_analysis", {})
        chip = analysis_result.get("chip_analysis", {})
        risk = analysis_result.get("risk_assessment", {})
        prediction = analysis_result.get("prediction", {})

        lines = [
            f"=" * 60,
            f"                {symbol} ({basic_info.get('name', '')}) 综合分析报告",
            f"=" * 60,
            "",
            f"【当前价格】{basic_info.get('current_price', 'N/A')} 元",
            f"【涨跌幅度】{basic_info.get('change', 'N/A')} ({basic_info.get('change_pct', 'N/A')}%)",
            f"【成交量】{basic_info.get('volume', 'N/A'):,}",
            "",
            "-" * 60,
            "【一、技术面分析】",
            "-" * 60,
        ]

        if technical:
            lines.extend([
                f"趋势判断：{technical.get('trend', 'N/A')}",
                f"",
                f"主要技术指标：",
            ])

            indicators = technical.get("indicators", {})
            if indicators:
                if indicators.get("ma5"):
                    lines.append(f"  MA5: {indicators['ma5']:.2f}")
                if indicators.get("ma20"):
                    lines.append(f"  MA20: {indicators['ma20']:.2f}")
                if indicators.get("rsi6"):
                    lines.append(f"  RSI6: {indicators['rsi6']:.2f}")

            signals = technical.get("signals", {})
            if signals and isinstance(signals, dict):
                lines.append(f"")
                lines.append(f"交易信号：")
                for signal_name, signal_value in signals.items():
                    if signal_value and signal_value != "none":
                        lines.append(f"  {signal_name}: {signal_value}")

        lines.extend([
            "",
            "-" * 60,
            "【二、基本面分析】",
            "-" * 60,
        ])

        if fundamental:
            valuation = fundamental.get("valuation", {})
            profitability = fundamental.get("profitability", {})
            growth = fundamental.get("growth", {})
            quality = fundamental.get("quality", {})
            analysis = fundamental.get("analysis", {})

            lines.extend([
                f"估值水平：{analysis.get('valuation_level', 'N/A')}",
                f"  PE(TTM): {valuation.get('pe_ttm', 'N/A')}",
                f"  PB: {valuation.get('pb', 'N/A')}",
                f"  ROE: {valuation.get('roe', 'N/A')}%",
                f"",
                f"盈利能力：{analysis.get('profitability_level', 'N/A')}",
                f"  净利率: {profitability.get('net_margin', 'N/A')}%",
                f"",
                f"成长性：{analysis.get('growth_level', 'N/A')}",
                f"  营收增长率: {growth.get('revenue_growth', 'N/A')}%",
                f"  利润增长率: {growth.get('profit_growth', 'N/A')}%",
                f"",
                f"财务质量：",
                f"  资产负债率: {quality.get('debt_ratio', 'N/A')}%",
            ])

        lines.extend([
            "",
            "-" * 60,
            "【三、资金流向分析】",
            "-" * 60,
        ])

        if fund_flow:
            main_inflow = fund_flow.get("main_inflow_5d", 0)
            retail_inflow = fund_flow.get("retail_inflow_5d", 0)

            lines.extend([
                f"近5日主力资金净流入：{main_inflow:.2f} 万元",
                f"近5日散户资金净流入：{retail_inflow:.2f} 万元",
            ])

            if main_inflow > 0:
                lines.append("资金面相符：主力资金持续流入")
            elif main_inflow < 0:
                lines.append("资金面警示：主力资金持续流出")

        lines.extend([
            "",
            "-" * 60,
            "【四、新闻面分析】",
            "-" * 60,
        ])

        if news and news.get("news_count", 0) > 0:
            lines.append(f"近期相关新闻：{news.get('news_count', 0)} 条")
            lines.append("")
            
            news_list = news.get("news_list", [])
            for i, item in enumerate(news_list[:5], 1):  # 只显示前5条
                time_str = f"[{item.get('time', '')}] " if item.get('time') else ""
                lines.append(f"{i}. {time_str}{item.get('title', '')}")
                if item.get('summary'):
                    lines.append(f"   {item.get('summary', '')[:80]}...")
                lines.append("")
            
            if len(news_list) > 5:
                lines.append(f"... 还有 {len(news_list) - 5} 条新闻")
        else:
            lines.append("暂无相关新闻或新闻获取失败")

        lines.extend([
            "",
            "-" * 60,
            "【五、筹码分布分析】",
            "-" * 60,
        ])

        if chip and chip.get("latest"):
            chip_latest = chip.get("latest", {})
            chip_trend = chip.get("trend", {})
            chip_assessment = chip.get("assessment", {})

            lines.extend([
                f"数据日期：{chip_latest.get('date', 'N/A')}",
                f"",
                f"筹码概况：",
                f"  获利比例：{chip_latest.get('winner_rate', 0)*100:.2f}%",
                f"  平均成本：{chip_latest.get('average_cost', 'N/A')} 元",
                f"",
                f"筹码集中度：",
                f"  90%成本区间：{chip_latest.get('cost_90_low', 'N/A')} - {chip_latest.get('cost_90_high', 'N/A')} 元（集中度 {chip_latest.get('concentration_90', 0)*100:.2f}%）",
                f"  70%成本区间：{chip_latest.get('cost_70_low', 'N/A')} - {chip_latest.get('cost_70_high', 'N/A')} 元（集中度 {chip_latest.get('concentration_70', 0)*100:.2f}%）",
            ])

            # 趋势信息
            if chip_trend:
                conc_trend_map = {
                    "concentrating": "趋于集中",
                    "dispersing": "趋于分散",
                    "stable": "保持稳定"
                }
                cost_trend_map = {
                    "rising": "上移",
                    "falling": "下移",
                    "stable": "稳定"
                }
                lines.extend([
                    f"",
                    f"筹码趋势：",
                    f"  集中度变化：{conc_trend_map.get(chip_trend.get('concentration_trend', 'stable'), '稳定')}",
                    f"  成本中心：{cost_trend_map.get(chip_trend.get('cost_center_trend', 'stable'), '稳定')}",
                ])

            # 综合评估
            if chip_assessment:
                lines.extend([
                    f"",
                    f"筹码评估：{chip_assessment.get('summary', 'N/A')}",
                ])
                chip_signals = chip_assessment.get("signals", [])
                if chip_signals:
                    for signal in chip_signals:
                        lines.append(f"  - {signal}")
        elif chip and chip.get("error"):
            lines.append(f"筹码数据获取失败: {chip.get('error', '未知错误')}")
        else:
            lines.append("暂无筹码分布数据")

        # === 新增9大数据源报告章节 ===

        # 六、龙虎榜
        lhb = analysis_result.get("lhb_analysis", {})
        lines.extend(["", "-" * 60, "【六、龙虎榜分析】", "-" * 60])
        lhb_records = lhb.get("records", [])
        lhb_inst = lhb.get("institution_summary", {})
        lhb_a = lhb.get("analysis", {})
        if lhb_records:
            lines.append(f"近期上榜次数：{len(lhb_records)} 次")
            lines.append(f"机构态度：{lhb_a.get('institution_attitude', '中性')}")
            if lhb_inst:
                lines.append(f"  机构买入总额：{lhb_inst.get('total_buy', 0):.2f} 万元")
                lines.append(f"  机构卖出总额：{lhb_inst.get('total_sell', 0):.2f} 万元")
                lines.append(f"  机构净买入：{lhb_inst.get('net_buy', 0):.2f} 万元")
            lines.append("")
            for i, rec in enumerate(lhb_records[:3], 1):
                lines.append(f"  {i}. [{rec.get('date','')}] {rec.get('reason','')}")
                lines.append(f"     净买入 {rec.get('net_buy',0):.2f}万 | 上榜后1日 {rec.get('after_1d',0):.2f}% | 5日 {rec.get('after_5d',0):.2f}%")
            if len(lhb_records) > 3:
                lines.append(f"  ... 还有 {len(lhb_records)-3} 条记录")
            lines.append(f"综合：{lhb_a.get('summary', '')}")
        else:
            lines.append("近期未上龙虎榜")

        # 七、融资融券
        margin = analysis_result.get("margin_analysis", {})
        lines.extend(["", "-" * 60, "【七、融资融券分析】", "-" * 60])
        margin_a = margin.get("analysis", {})
        margin_latest = margin.get("latest", {})
        if margin_latest:
            lines.append(f"融资余额：{margin_latest.get('margin_balance', 'N/A')} 元")
            lines.append(f"融券余额：{margin_latest.get('short_balance', 'N/A')} 元")
            lines.append(f"融资买入额：{margin_latest.get('margin_buy', 'N/A')} 元")
            margin_trend = margin_a.get("margin_trend", "stable")
            trend_map = {"increasing": "融资余额增加（看多）", "decreasing": "融资余额减少（看空）", "stable": "融资余额稳定"}
            lines.append(f"趋势：{trend_map.get(margin_trend, '稳定')}")
            lines.append(f"综合：{margin_a.get('summary', '')}")
        else:
            lines.append("暂无融资融券数据（可能非两融标的）")

        # 八、北向资金
        nb = analysis_result.get("northbound_analysis", {})
        lines.extend(["", "-" * 60, "【八、北向资金分析】", "-" * 60])
        nb_a = nb.get("analysis", {})
        nb_holding = nb.get("holding", {})
        if nb_holding or nb_a:
            if nb_holding:
                lines.append(f"北向持股数量：{nb_holding.get('shares', 'N/A')}")
                lines.append(f"北向持股市值：{nb_holding.get('market_value', 'N/A')}")
                lines.append(f"占流通股比：{nb_holding.get('ratio', 'N/A')}")
            nb_dir = nb_a.get("direction", "neutral")
            dir_map = {"inflow": "净流入", "outflow": "净流出", "neutral": "中性"}
            lines.append(f"资金方向：{dir_map.get(nb_dir, '中性')}")
            lines.append(f"综合：{nb_a.get('summary', '')}")
        else:
            lines.append("暂无北向资金数据")

        # 九、大宗交易
        bt = analysis_result.get("block_trade_analysis", {})
        lines.extend(["", "-" * 60, "【九、大宗交易分析】", "-" * 60])
        bt_a = bt.get("analysis", {})
        bt_records = bt.get("records", [])
        if bt_records:
            lines.append(f"近期大宗交易：{bt_a.get('records_count', len(bt_records))} 笔")
            lines.append(f"平均折溢价率：{bt_a.get('avg_premium', 0):.2f}%")
            lines.append(f"总成交金额：{bt_a.get('total_amount', 0):.2f} 万元")
            lines.append("")
            for i, rec in enumerate(bt_records[:3], 1):
                lines.append(f"  {i}. [{rec.get('date','')}] 成交价 {rec.get('price','N/A')} 元 | 折溢价 {rec.get('premium',0):.2f}%")
            if len(bt_records) > 3:
                lines.append(f"  ... 还有 {len(bt_records)-3} 笔")
            lines.append(f"综合：{bt_a.get('summary', '')}")
        else:
            lines.append("近期无大宗交易")

        # 十、股东人数变化
        sh = analysis_result.get("shareholder_analysis", {})
        lines.extend(["", "-" * 60, "【十、股东人数变化】", "-" * 60])
        sh_a = sh.get("analysis", {})
        sh_latest = sh.get("latest", {})
        if sh_latest:
            lines.append(f"最新股东户数：{sh_latest.get('holder_count', 'N/A')} 户")
            lines.append(f"户均持股：{sh_latest.get('avg_holding', 'N/A')} 股")
            lines.append(f"较上期变化：{sh_latest.get('change_pct', 'N/A')}%")
            sh_trend = sh_a.get("shareholder_trend", "stable")
            trend_map = {"decreasing": "股东减少（筹码集中）", "increasing": "股东增加（筹码分散）", "stable": "股东人数稳定"}
            lines.append(f"趋势：{trend_map.get(sh_trend, '稳定')}")
            lines.append(f"综合：{sh_a.get('summary', '')}")
        else:
            lines.append("暂无股东人数数据")

        # 十一、机构持仓
        inst = analysis_result.get("institution_analysis", {})
        lines.extend(["", "-" * 60, "【十一、机构持仓分析】", "-" * 60])
        inst_a = inst.get("analysis", {})
        inst_holdings = inst.get("holdings", [])
        if inst_holdings:
            lines.append(f"持仓机构数：{len(inst_holdings)}")
            inst_trend = inst_a.get("holding_trend", "stable")
            trend_map = {"increasing": "机构增持", "decreasing": "机构减持", "stable": "持仓稳定"}
            lines.append(f"趋势：{trend_map.get(inst_trend, '稳定')}")
            for i, h in enumerate(inst_holdings[:5], 1):
                lines.append(f"  {i}. {h.get('name', 'N/A')} | 持股 {h.get('shares', 'N/A')} | 占比 {h.get('ratio', 'N/A')}%")
            if len(inst_holdings) > 5:
                lines.append(f"  ... 还有 {len(inst_holdings)-5} 家机构")
            lines.append(f"综合：{inst_a.get('summary', '')}")
        else:
            lines.append("暂无机构持仓数据")

        # 十二、限售解禁
        rs = analysis_result.get("restricted_shares_analysis", {})
        lines.extend(["", "-" * 60, "【十二、限售解禁】", "-" * 60])
        rs_a = rs.get("analysis", {})
        rs_upcoming = rs.get("upcoming", [])
        if rs_upcoming:
            lines.append(f"近期解禁批次：{len(rs_upcoming)}")
            rs_pressure = rs_a.get("pressure_level", "low")
            pressure_map = {"high": "高（大额解禁）", "medium": "中等", "low": "低"}
            lines.append(f"解禁压力：{pressure_map.get(rs_pressure, '低')}")
            for i, item in enumerate(rs_upcoming[:3], 1):
                lines.append(f"  {i}. [{item.get('date','')}] 解禁数量 {item.get('shares','N/A')} 股 | 市值 {item.get('market_value','N/A')}")
            lines.append(f"综合：{rs_a.get('summary', '')}")
        else:
            lines.append("近期无限售解禁")

        # 十三、行业对比
        ind = analysis_result.get("industry_compare_analysis", {})
        lines.extend(["", "-" * 60, "【十三、行业对比】", "-" * 60])
        ind_a = ind.get("analysis", {})
        if ind.get("industry_name"):
            lines.append(f"所属行业：{ind.get('industry_name', 'N/A')}")
            lines.append(f"行业排名：{ind_a.get('rank_desc', 'N/A')}")
            lines.append(f"行业平均PE：{ind_a.get('industry_avg_pe', 'N/A')}")
            lines.append(f"综合：{ind_a.get('summary', '')}")
        else:
            lines.append("暂无行业对比数据")

        # 十四、分红送转
        div = analysis_result.get("dividend_analysis", {})
        lines.extend(["", "-" * 60, "【十四、分红送转历史】", "-" * 60])
        div_a = div.get("analysis", {})
        div_records = div.get("records", [])
        if div_records:
            lines.append(f"分红记录：{len(div_records)} 次")
            lines.append(f"股息率：{div_a.get('dividend_yield', 'N/A')}%")
            lines.append(f"分红稳定性：{div_a.get('stability', 'N/A')}")
            for i, rec in enumerate(div_records[:3], 1):
                lines.append(f"  {i}. [{rec.get('year','')}] {rec.get('plan', 'N/A')}")
            if len(div_records) > 3:
                lines.append(f"  ... 还有 {len(div_records)-3} 条记录")
            lines.append(f"综合：{div_a.get('summary', '')}")
        else:
            lines.append("暂无分红送转记录")

        # === END 新增报告章节 ===

        lines.extend([
            "",
            "-" * 60,
            "【十五、风险评估】",
            "-" * 60,
        ])

        if risk:
            overall = risk.get("overall_risk", "medium")
            risk_cn = {"low": "低", "medium": "中等", "high": "高"}.get(overall, "中等")

            lines.extend([
                f"综合风险等级：{risk_cn}",
                f"",
                f"各项风险：",
                f"  波动风险：{risk.get('volatility_risk', 'medium')}",
                f"  流动性风险：{risk.get('liquidity_risk', 'medium')}",
                f"  基本面风险：{risk.get('fundamental_risk', 'medium')}",
            ])

            risk_factors = risk.get("risk_factors", [])
            if risk_factors:
                lines.extend([
                    f"",
                    f"风险因素：",
                ])
                for factor in risk_factors:
                    lines.append(f"  - {factor}")

        lines.extend([
            "",
            "-" * 60,
            "【十六、后市预测】",
            "-" * 60,
        ])

        if prediction:
            trend = prediction.get("trend", "sideways")
            trend_cn = prediction.get("trend_cn", "震荡")
            probability = prediction.get("probability", 0.5)

            lines.extend([
                f"预测趋势：{trend_cn}",
                f"概率：{probability * 100:.0f}%",
                f"",
                f"目标价格区间：",
                f"  上限：{prediction.get('target_price_high', 'N/A')} 元",
                f"  下限：{prediction.get('target_price_low', 'N/A')} 元",
                f"",
                f"时间周期：{prediction.get('time_horizon', '短期')}",
                f"风险等级：{prediction.get('risk_level', '中等')}",
            ])

            key_factors = prediction.get("key_factors", [])
            if key_factors:
                lines.extend([
                    f"",
                    f"关键影响因素：",
                ])
                for factor in key_factors:
                    lines.append(f"  - {factor}")

            lines.extend([
                f"",
                f"操作建议：{prediction.get('recommendation', '观望')}",
            ])

        lines.extend([
            "",
            "=" * 60,
            f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ])

        return "\n".join(lines)
