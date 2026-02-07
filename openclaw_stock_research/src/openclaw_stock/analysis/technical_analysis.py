"""
技术分析模块

实现设计文档4.2节的接口4: 技术指标计算
以及接口9: 支撑压力位计算
"""

from typing import Literal, Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np

from ..core.exceptions import DataSourceError, CalculationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TechnicalIndicators:
    """技术指标数据类"""
    # 移动平均线
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    ma120: Optional[float] = None
    ma250: Optional[float] = None

    # MACD指标
    macd_dif: Optional[float] = None
    macd_dea: Optional[float] = None
    macd_hist: Optional[float] = None
    macd_signal: Optional[str] = None  # golden_cross/dead_cross/none

    # KDJ指标
    kdj_k: Optional[float] = None
    kdj_d: Optional[float] = None
    kdj_j: Optional[float] = None
    kdj_signal: Optional[str] = None  # overbought/oversold/none

    # RSI指标
    rsi6: Optional[float] = None
    rsi12: Optional[float] = None
    rsi24: Optional[float] = None
    rsi_signal: Optional[str] = None  # overbought/oversold/none

    # 布林带
    boll_upper: Optional[float] = None
    boll_mid: Optional[float] = None
    boll_lower: Optional[float] = None
    boll_position: Optional[str] = None  # upper/mid/lower/breakout_up/breakout_down

    # 成交量指标
    volume_ma5: Optional[float] = None
    volume_ma10: Optional[float] = None
    volume_ratio: Optional[float] = None  # 量比


def calculate_ma(series: pd.Series, period: int) -> pd.Series:
    """计算简单移动平均线"""
    return series.rolling(window=period, min_periods=1).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """计算指数移动平均线"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算MACD指标

    返回:
        (dif, dea, hist) 三个Series
    """
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    dif = ema_fast - ema_slow
    dea = calculate_ema(dif, signal)
    hist = 2 * (dif - dea)
    return dif, dea, hist


def calculate_kdj(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    n: int = 9,
    m1: int = 3,
    m2: int = 3
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算KDJ指标

    返回:
        (k, d, j) 三个Series
    """
    lowest_low = low.rolling(window=n, min_periods=1).min()
    highest_high = high.rolling(window=n, min_periods=1).max()

    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    rsv = rsv.replace([np.inf, -np.inf], 50).fillna(50)

    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    j = 3 * k - 2 * d

    return k, d, j


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    计算RSI指标

    参数:
        series: 价格序列
        period: 计算周期

    返回:
        RSI值序列
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算布林带

    参数:
        series: 价格序列
        period: 计算周期
        std_dev: 标准差倍数

    返回:
        (upper, mid, lower) 三个Series
    """
    mid = series.rolling(window=period, min_periods=1).mean()
    std = series.rolling(window=period, min_periods=1).std()
    upper = mid + (std * std_dev)
    lower = mid - (std * std_dev)
    return upper, mid, lower


def calculate_technical_indicators(
    df: pd.DataFrame,
    indicators: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    计算技术指标（接口4实现）

    参数:
        df: K线数据，必须包含open/high/low/close/volume列
        indicators: 需要计算的指标列表，None表示计算所有

    返回:
        添加了技术指标列的DataFrame

    计算的技术指标:
    - 均线系统: MA5/10/20/60/120/250
    - MACD: DIF/DEA/HIST
    - KDJ: K/D/J
    - RSI: RSI6/12/24
    - 布林带: UPPER/MID/LOWER
    - 成交量指标: VOL_MA5/VOL_MA10/VOL_RATIO
    """
    logger.info("[calculate_technical_indicators] 开始计算技术指标")

    # 验证输入数据
    required_columns = ["open", "high", "low", "close", "volume"]
    for col in required_columns:
        if col not in df.columns:
            raise CalculationError(f"缺少必需的列: {col}")

    result = df.copy()

    # 默认计算所有指标
    if indicators is None:
        indicators = ["ma", "macd", "kdj", "rsi", "boll", "volume"]

    try:
        # 1. 均线系统
        if "ma" in indicators:
            result["ma5"] = calculate_ma(result["close"], 5)
            result["ma10"] = calculate_ma(result["close"], 10)
            result["ma20"] = calculate_ma(result["close"], 20)
            result["ma60"] = calculate_ma(result["close"], 60)
            result["ma120"] = calculate_ma(result["close"], 120)
            result["ma250"] = calculate_ma(result["close"], 250)

        # 2. MACD指标
        if "macd" in indicators:
            dif, dea, hist = calculate_macd(result["close"])
            result["macd_dif"] = dif
            result["macd_dea"] = dea
            result["macd_hist"] = hist

        # 3. KDJ指标
        if "kdj" in indicators:
            k, d, j = calculate_kdj(result["high"], result["low"], result["close"])
            result["kdj_k"] = k
            result["kdj_d"] = d
            result["kdj_j"] = j

        # 4. RSI指标
        if "rsi" in indicators:
            result["rsi6"] = calculate_rsi(result["close"], 6)
            result["rsi12"] = calculate_rsi(result["close"], 12)
            result["rsi24"] = calculate_rsi(result["close"], 24)

        # 5. 布林带
        if "boll" in indicators:
            upper, mid, lower = calculate_bollinger_bands(result["close"])
            result["boll_upper"] = upper
            result["boll_mid"] = mid
            result["boll_lower"] = lower

        # 6. 成交量指标
        if "volume" in indicators:
            result["volume_ma5"] = calculate_ma(result["volume"], 5)
            result["volume_ma10"] = calculate_ma(result["volume"], 10)
            # 量比 = 当前成交量 / 过去5日平均成交量
            result["volume_ratio"] = result["volume"] / result["volume"].rolling(window=5, min_periods=1).mean()

        logger.info("[calculate_technical_indicators] 技术指标计算完成")
        return result

    except Exception as e:
        logger.error(f"[calculate_technical_indicators] 计算失败: {e}")
        raise CalculationError(f"计算技术指标失败: {e}")


def calculate_support_resistance(
    symbol: str,
    df: pd.DataFrame,
    method: Literal["fibonacci", "pivot", "ma", "historical"] = "fibonacci",
    lookback: int = 60
) -> Dict[str, Any]:
    """
    计算支撑压力位（接口9实现）

    参数:
        symbol: 股票代码
        df: K线数据
        method: 计算方法(fibonacci/pivot/ma/historical)
        lookback: 回看周期数

    返回:
        {
            'symbol': 股票代码,
            'current_price': 当前价格,
            'method': 计算方法,
            'support_levels': [支撑位1, 支撑位2, ...],
            'resistance_levels': [压力位1, 压力位2, ...],
            'pivot_point': 枢轴点,
            'recommendation': 建议
        }
    """
    logger.info(f"[calculate_support_resistance] 计算 {symbol} 的支撑压力位")

    if len(df) < lookback:
        raise CalculationError(f"数据量不足，需要至少{lookback}条数据")

    try:
        # 获取当前价格和历史高低点
        current_price = df["close"].iloc[-1]
        recent_df = df.tail(lookback)

        high = recent_df["high"].max()
        low = recent_df["low"].min()
        pivot = (high + low + current_price) / 3

        support_levels = []
        resistance_levels = []

        if method == "fibonacci":
            # 斐波那契回调位
            diff = high - low
            # 支撑位
            support_levels = [
                round(high - 0.236 * diff, 2),
                round(high - 0.382 * diff, 2),
                round(high - 0.5 * diff, 2),
                round(high - 0.618 * diff, 2),
                round(high - 0.786 * diff, 2),
            ]
            # 压力位
            resistance_levels = [
                round(low + 1.0 * diff, 2),
                round(low + 1.236 * diff, 2),
                round(low + 1.382 * diff, 2),
                round(low + 1.5 * diff, 2),
                round(low + 1.618 * diff, 2),
            ]

        elif method == "pivot":
            # 枢轴点法
            r1 = 2 * pivot - low
            r2 = pivot + (high - low)
            r3 = high + 2 * (pivot - low)

            s1 = 2 * pivot - high
            s2 = pivot - (high - low)
            s3 = low - 2 * (high - pivot)

            support_levels = [round(s1, 2), round(s2, 2), round(s3, 2)]
            resistance_levels = [round(r1, 2), round(r2, 2), round(r3, 2)]

        elif method == "ma":
            # 移动平均线法
            ma5 = df["close"].rolling(5).mean().iloc[-1]
            ma10 = df["close"].rolling(10).mean().iloc[-1]
            ma20 = df["close"].rolling(20).mean().iloc[-1]
            ma60 = df["close"].rolling(60).mean().iloc[-1]

            # 均线作为支撑/压力
            if current_price > ma5:
                support_levels = [round(ma5, 2), round(ma10, 2), round(ma20, 2), round(ma60, 2)]
                resistance_levels = []
            else:
                support_levels = []
                resistance_levels = [round(ma5, 2), round(ma10, 2), round(ma20, 2), round(ma60, 2)]

        elif method == "historical":
            # 历史高低点法
            # 找出近期的高点和低点作为支撑/压力
            highs = recent_df["high"].nlargest(5).values
            lows = recent_df["low"].nsmallest(5).values

            support_levels = [round(x, 2) for x in sorted(lows, reverse=True)]
            resistance_levels = [round(x, 2) for x in sorted(highs)]

        else:
            raise ValueError(f"不支持的计算方法: {method}")

        # 生成建议
        recommendation = ""
        if current_price < support_levels[-1] if support_levels else False:
            recommendation = "价格跌破关键支撑位，建议观望或止损"
        elif current_price > resistance_levels[-1] if resistance_levels else False:
            recommendation = "价格突破关键压力位，可能开启上涨趋势"
        elif support_levels and current_price < support_levels[0]:
            recommendation = "价格接近支撑位，关注反弹机会"
        elif resistance_levels and current_price > resistance_levels[0]:
            recommendation = "价格接近压力位，注意回调风险"
        else:
            recommendation = "价格在支撑和压力之间震荡，建议观望"

        result = {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "method": method,
            "lookback": lookback,
            "pivot_point": round(pivot, 2) if 'pivot' in dir() else None,
            "support_levels": [s for s in support_levels if s > 0],
            "resistance_levels": [r for r in resistance_levels if r > 0],
            "recommendation": recommendation,
            "timestamp": pd.Timestamp.now().isoformat()
        }

        logger.info(f"[calculate_support_resistance] 计算完成: {symbol}")
        return result

    except Exception as e:
        logger.error(f"[calculate_support_resistance] 计算失败: {e}")
        raise CalculationError(f"计算支撑压力位失败: {e}")


class TechnicalAnalyzer:
    """
    技术分析器类

    提供技术分析的统一接口
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def calculate_indicators(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """计算技术指标"""
        return calculate_technical_indicators(df, **kwargs)

    def calculate_support_resistance(self, **kwargs) -> Dict[str, Any]:
        """计算支撑压力位"""
        return calculate_support_resistance(**kwargs)

    def detect_trend(self, df: pd.DataFrame) -> str:
        """
        检测趋势

        返回:
            "uptrend"/"downtrend"/"sideways"
        """
        if len(df) < 20:
            return "unknown"

        ma5 = df["close"].rolling(5).mean().iloc[-1]
        ma20 = df["close"].rolling(20).mean().iloc[-1]
        ma60 = df["close"].rolling(60).mean().iloc[-1] if len(df) >= 60 else ma20

        if ma5 > ma20 > ma60:
            return "uptrend"
        elif ma5 < ma20 < ma60:
            return "downtrend"
        else:
            return "sideways"

    def detect_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        检测交易信号

        返回:
            包含各种交易信号的字典
        """
        signals = {
            "macd_signal": None,
            "kdj_signal": None,
            "rsi_signal": None,
            "ma_signal": None,
            "boll_signal": None,
            "overall": None
        }

        if len(df) < 20:
            return signals

        # 计算指标
        df = calculate_technical_indicators(df)

        # MACD信号
        if len(df) >= 2:
            macd_hist_current = df["macd_hist"].iloc[-1]
            macd_hist_prev = df["macd_hist"].iloc[-2]
            if macd_hist_prev < 0 and macd_hist_current > 0:
                signals["macd_signal"] = "golden_cross"  # 金叉
            elif macd_hist_prev > 0 and macd_hist_current < 0:
                signals["macd_signal"] = "dead_cross"  # 死叉
            else:
                signals["macd_signal"] = "none"

        # KDJ信号
        if "kdj_k" in df.columns and "kdj_d" in df.columns:
            k = df["kdj_k"].iloc[-1]
            d = df["kdj_d"].iloc[-1]
            if k > 80 and d > 80:
                signals["kdj_signal"] = "overbought"
            elif k < 20 and d < 20:
                signals["kdj_signal"] = "oversold"
            else:
                signals["kdj_signal"] = "none"

        # RSI信号
        if "rsi6" in df.columns:
            rsi6 = df["rsi6"].iloc[-1]
            if rsi6 > 80:
                signals["rsi_signal"] = "overbought"
            elif rsi6 < 20:
                signals["rsi_signal"] = "oversold"
            else:
                signals["rsi_signal"] = "none"

        # 均线信号
        if "ma5" in df.columns and "ma20" in df.columns:
            ma5 = df["ma5"].iloc[-1]
            ma20 = df["ma20"].iloc[-1]
            close = df["close"].iloc[-1]
            if ma5 > ma20 and close > ma5:
                signals["ma_signal"] = "bullish"
            elif ma5 < ma20 and close < ma5:
                signals["ma_signal"] = "bearish"
            else:
                signals["ma_signal"] = "neutral"

        # 布林带信号
        if "boll_upper" in df.columns and "boll_lower" in df.columns:
            close = df["close"].iloc[-1]
            upper = df["boll_upper"].iloc[-1]
            lower = df["boll_lower"].iloc[-1]
            if close > upper:
                signals["boll_signal"] = "breakout_up"
            elif close < lower:
                signals["boll_signal"] = "breakout_down"
            else:
                signals["boll_signal"] = "within_band"

        # 综合信号
        bullish_count = sum([
            signals["macd_signal"] == "golden_cross",
            signals["kdj_signal"] != "overbought",
            signals["ma_signal"] == "bullish",
            signals["boll_signal"] == "breakout_up"
        ])
        bearish_count = sum([
            signals["macd_signal"] == "dead_cross",
            signals["kdj_signal"] == "overbought",
            signals["ma_signal"] == "bearish",
            signals["boll_signal"] == "breakout_down"
        ])

        if bullish_count >= 3:
            signals["overall"] = "strong_buy"
        elif bullish_count >= 2:
            signals["overall"] = "buy"
        elif bearish_count >= 3:
            signals["overall"] = "strong_sell"
        elif bearish_count >= 2:
            signals["overall"] = "sell"
        else:
            signals["overall"] = "neutral"

        return signals
