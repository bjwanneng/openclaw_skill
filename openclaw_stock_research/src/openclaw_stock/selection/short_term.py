"""
短期选股模块

实现设计文档4.3节的接口6: 短期选股
"""

from typing import Literal, Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..core.exceptions import DataSourceError, CalculationError
from ..utils.logger import get_logger
from ..utils.decorators import retry
from ..data.market_data import fetch_market_data, fetch_realtime_quote
from ..data.fund_flow import fetch_fund_flow
from ..analysis.technical_analysis import calculate_technical_indicators, calculate_ma

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


@dataclass
class ShortTermStock:
    """短期选股结果"""
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: int
    turnover_rate: float
    score: float
    signals: List[str]


def short_term_stock_selector(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_volume: Optional[int] = None,
    fund_flow_days: int = 5,
    technical_signals: List[str] = None,
    top_n: int = 50,
    max_stocks: int = 500,
    batch_size: int = 50
) -> pd.DataFrame:
    """
    短期选股器（接口6实现）

    参数:
        min_price/max_price: 价格区间
        min_volume: 最小成交量
        fund_flow_days: 资金流向天数
        technical_signals: 技术信号列表
        top_n: 返回前N只股票

    返回:
        DataFrame: 符合条件的股票及评分

    评分维度:
    1. 技术面(40分)
       - 突破关键均线 +10
       - MACD金叉 +10
       - 量价配合 +10
       - 相对强弱 +10

    2. 资金面(30分)
       - 主力净流入 +15
       - 龙虎榜上榜 +15

    3. 情绪面(20分)
       - 板块联动 +10
       - 涨停板数量 +10

    4. 消息面(10分)
       - 利好公告 +10

    性能优化:
    - max_stocks: 最大分析股票数量，默认500只（避免遍历全市场）
    - batch_size: 批处理大小，默认50只（减少API调用频率）
    """
    if ak is None:
        raise DataSourceError("akshare库未安装")

    logger.info(f"[short_term_stock_selector] 开始短期选股，最大分析数量: {max_stocks}")

    try:
        # 获取全市场实时行情
        df_spot = ak.stock_zh_a_spot_em()

        if df_spot.empty:
            raise DataSourceError("无法获取全市场实时行情")

        # 性能优化：限制分析股票数量，优先分析高成交量、高波动的活跃股票
        # 根据换手率排序，选取最活跃的股票
        if "换手率" in df_spot.columns:
            df_spot = df_spot.sort_values("换手率", ascending=False)

        # 限制分析数量
        df_spot = df_spot.head(max_stocks)
        logger.info(f"[short_term_stock_selector] 从全市场筛选出 {len(df_spot)} 只活跃股票进行分析")

        # 初始化结果列表
        candidates = []

        # 遍历股票进行筛选
        for _, row in df_spot.iterrows():
            try:
                symbol = str(row.get("代码", "")).strip()
                name = str(row.get("名称", "")).strip()
                price = float(row.get("最新价", 0) or 0)
                change_pct = float(row.get("涨跌幅", 0) or 0)
                volume = int(row.get("成交量", 0) or 0)
                turnover_rate = float(row.get("换手率", 0) or 0)

                # 基本条件筛选
                if not symbol or not name:
                    continue

                # 价格筛选
                if min_price is not None and price < min_price:
                    continue
                if max_price is not None and price > max_price:
                    continue

                # 成交量筛选
                if min_volume is not None and volume < min_volume:
                    continue

                # 初始化评分
                technical_score = 0
                fund_score = 0
                sentiment_score = 0
                news_score = 0
                signals = []

                # 技术面分析(40分)
                try:
                    # 获取K线数据
                    df_kline = fetch_market_data(
                        symbol=symbol,
                        period="daily",
                        start_date=(datetime.now() - timedelta(days=60)).strftime("%Y%m%d"),
                        end_date=datetime.now().strftime("%Y%m%d"),
                        market="sh" if symbol.startswith("6") else "sz"
                    )

                    if not df_kline.empty and len(df_kline) >= 20:
                        # 均线分析
                        df_kline = calculate_technical_indicators(df_kline)

                        # 突破关键均线
                        current_price = df_kline["close"].iloc[-1]
                        ma5 = df_kline["ma5"].iloc[-1] if "ma5" in df_kline.columns else None
                        ma20 = df_kline["ma20"].iloc[-1] if "ma20" in df_kline.columns else None

                        if ma5 and ma20:
                            if current_price > ma5 > ma20:
                                technical_score += 10
                                signals.append("突破均线多头排列")
                            elif current_price < ma5 < ma20:
                                technical_score += 2

                        # MACD金叉
                        if "macd_hist" in df_kline.columns:
                            macd_hist_current = df_kline["macd_hist"].iloc[-1]
                            macd_hist_prev = df_kline["macd_hist"].iloc[-2] if len(df_kline) > 1 else 0
                            if macd_hist_prev < 0 and macd_hist_current > 0:
                                technical_score += 10
                                signals.append("MACD金叉")

                        # 量价配合
                        if volume > df_kline["volume"].rolling(5).mean().iloc[-1] * 1.5:
                            technical_score += 10
                            signals.append("放量上涨")

                except Exception as e:
                    logger.warning(f"[{symbol}] 技术面分析失败: {e}")

                # 资金面分析(30分)
                try:
                    # 获取资金流向
                    df_flow = fetch_fund_flow(symbol=symbol, days=fund_flow_days)

                    if not df_flow.empty:
                        main_inflow = df_flow["main_inflow"].sum() if "main_inflow" in df_flow.columns else 0

                        if main_inflow > 0:
                            fund_score += 15
                            signals.append(f"主力净流入({main_inflow:.0f}万)")

                        # 龙虎榜检查
                        try:
                            df_lhb = ak.stock_lhb_detail_em(start_date=(datetime.now() - timedelta(days=fund_flow_days)).strftime("%Y%m%d"), end_date=datetime.now().strftime("%Y%m%d"))
                            if not df_lhb.empty and symbol in df_lhb["代码"].values:
                                fund_score += 15
                                signals.append("近期上榜龙虎榜")
                        except:
                            pass

                except Exception as e:
                    logger.warning(f"[{symbol}] 资金面分析失败: {e}")

                # 情绪面分析(20分)
                # 涨跌幅和换手率反映情绪
                if change_pct > 5:
                    sentiment_score += 10
                    signals.append("强势上涨")
                elif change_pct > 0:
                    sentiment_score += 5

                if turnover_rate > 10:
                    sentiment_score += 10
                    signals.append("高换手")
                elif turnover_rate > 5:
                    sentiment_score += 5

                # 消息面(10分) - 暂用业绩预告替代
                try:
                    df_yjyg = ak.stock_yjyg_em(date=datetime.now().strftime("%Y%m"))
                    if not df_yjyg.empty:
                        stock_yjyg = df_yjyg[df_yjyg["股票代码"] == symbol]
                        if not stock_yjyg.empty:
                            change_type = stock_yjyg.iloc[0].get("变动类型", "")
                            if "预增" in change_type or "预盈" in change_type:
                                news_score += 10
                                signals.append("业绩预增")
                except:
                    pass

                # 计算总分
                total_score = technical_score + fund_score + sentiment_score + news_score

                # 添加到候选列表
                candidates.append({
                    "symbol": symbol,
                    "name": name,
                    "price": price,
                    "change_pct": change_pct,
                    "volume": volume,
                    "turnover_rate": turnover_rate,
                    "technical_score": technical_score,
                    "fund_score": fund_score,
                    "sentiment_score": sentiment_score,
                    "news_score": news_score,
                    "total_score": total_score,
                    "signals": "; ".join(signals) if signals else ""
                })

            except Exception as e:
                logger.warning(f"[{symbol}] 处理失败: {e}")
                continue

        # 按总分排序
        candidates.sort(key=lambda x: x["total_score"], reverse=True)

        # 取前N个
        top_candidates = candidates[:top_n]

        # 转换为DataFrame
        df_result = pd.DataFrame(top_candidates)

        logger.info(f"[short_term_stock_selector] 选股完成，返回 {len(df_result)} 只股票")
        return df_result

    except Exception as e:
        logger.error(f"[short_term_stock_selector] 选股失败: {e}")
        raise DataSourceError(f"短期选股失败: {e}")


# 策略类定义
class TechnicalBreakthroughStrategy:
    """技术突破型策略"""

    def __init__(self):
        self.name = "技术突破型"
        self.description = "突破关键压力位、均线多头排列"

    def filter(self, df_spot: pd.DataFrame) -> pd.DataFrame:
        """筛选符合技术突破条件的股票"""
        # 涨幅在3%-8%之间（突破但不追高）
        df_filtered = df_spot[
            (df_spot["涨跌幅"] >= 3) &
            (df_spot["涨跌幅"] <= 8)
        ]
        return df_filtered


class CapitalDrivenStrategy:
    """资金驱动型策略"""

    def __init__(self):
        self.name = "资金驱动型"
        self.description = "主力资金持续流入、龙虎榜游资接力"

    def filter(self, df_spot: pd.DataFrame) -> pd.DataFrame:
        """筛选符合资金驱动条件的股票"""
        # 换手率在5%-20%之间（有资金关注但不过度）
        df_filtered = df_spot[
            (df_spot["换手率"] >= 5) &
            (df_spot["换手率"] <= 20)
        ]
        return df_filtered


class EventDrivenStrategy:
    """事件催化型策略"""

    def __init__(self):
        self.name = "事件催化型"
        self.description = "利好消息、业绩超预期、政策刺激"

    def filter(self, df_spot: pd.DataFrame) -> pd.DataFrame:
        """筛选符合事件催化条件的股票"""
        # 业绩预增或涨停
        df_filtered = df_spot[
            (df_spot["涨跌幅"] >= 9.5) |  # 涨停
            (df_spot["涨跌幅"] >= 5)     # 或者大涨
        ]
        return df_filtered


class SentimentResonanceStrategy:
    """情绪共振型策略"""

    def __init__(self):
        self.name = "情绪共振型"
        self.description = "板块联动、题材热点"

    def filter(self, df_spot: pd.DataFrame) -> pd.DataFrame:
        """筛选符合情绪共振条件的股票"""
        # 强势股，涨幅领先
        df_filtered = df_spot[
            df_spot["涨跌幅"] >= df_spot["涨跌幅"].quantile(0.8)
        ]
        return df_filtered


class ShortTermSelector:
    """
    短期选股器类

    提供短期选股的统一接口
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.strategies = [
            TechnicalBreakthroughStrategy(),
            CapitalDrivenStrategy(),
            EventDrivenStrategy(),
            SentimentResonanceStrategy()
        ]

    def select(self, **kwargs) -> pd.DataFrame:
        """执行选股"""
        return short_term_stock_selector(**kwargs)

    def get_strategies(self) -> List[Any]:
        """获取所有策略"""
        return self.strategies
