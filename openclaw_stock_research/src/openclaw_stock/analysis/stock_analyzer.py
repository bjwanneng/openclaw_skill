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
from ..analysis.technical_analysis import (
    calculate_technical_indicators,
    calculate_support_resistance,
    TechnicalAnalyzer
)
from ..analysis.fundamental_analysis import (
    calculate_fundamental_indicators,
    FundamentalAnalyzer
)

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

        # 6. 风险评估
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

        # 6. 后市预测
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
            "【五、风险评估】",
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
            "【六、后市预测】",
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
