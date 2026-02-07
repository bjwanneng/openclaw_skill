"""
web_quote_validator.py - Web行情验证器

通过爬取东方财富/腾讯/新浪等网页接口获取实时价格，
用于验证AkShare数据的准确性和时效性。

当Web抓取价格与AkShare数据误差超过0.5%时，
将在返回结果中标记[DATA_MISMATCH_WARNING]。
"""

import requests
import json
import time
from typing import Dict, Any, Optional, Literal
from datetime import datetime
from urllib.parse import urlencode

from ..core.config import get_config
from ..core.exceptions import ValidationError, NetworkError, PriceMismatchError
from ..utils.decorators import tool, require_env, log_execution, retry
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WebQuoteValidator:
    """
    Web行情验证器类

    支持的数据源：
    - eastmoney: 东方财富（默认，数据最全）
    - tencent: 腾讯财经（速度快）
    - sina: 新浪财经（稳定性好）
    """

    # 数据源配置
    DATA_SOURCES = {
        "eastmoney": {
            "name": "东方财富",
            "base_url": "https://push2.eastmoney.com/api",
            "realtime_endpoint": "/qt/stock/get",
            "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f170,f171,f169,f170",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://quote.eastmoney.com/",
                "Accept": "application/json",
            }
        },
        "tencent": {
            "name": "腾讯财经",
            "base_url": "https://qt.gtimg.cn",
            "realtime_endpoint": "/q",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.qq.com/",
            }
        },
        "sina": {
            "name": "新浪财经",
            "base_url": "https://hq.sinajs.cn",
            "realtime_endpoint": "/list",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://finance.sina.com.cn",
            }
        }
    }

    def __init__(
        self,
        source: Literal["eastmoney", "tencent", "sina"] = "eastmoney",
        proxy: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化Web行情验证器

        Args:
            source: 数据源（eastmoney/tencent/sina）
            proxy: 代理服务器地址
            timeout: 请求超时时间（秒）
        """
        self.source = source
        self.config = self.DATA_SOURCES[source]
        self.timeout = timeout
        self.session = requests.Session()

        # 设置默认headers
        self.session.headers.update(self.config["headers"])

        # 设置代理
        self.proxy = proxy or get_config().get_proxy_url()
        if self.proxy:
            self.session.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }
            logger.info(f"[WebQuoteValidator] 已配置代理: {self.proxy}")

        logger.info(f"[WebQuoteValidator] 初始化完成，数据源: {self.config['name']}")

    def _format_symbol(
        self,
        symbol: str,
        market: Literal["sh", "sz", "hk"]
    ) -> str:
        """
        格式化股票代码为各数据源所需格式

        Args:
            symbol: 原始股票代码（如 "000001"）
            market: 市场类型（sh/sz/hk）

        Returns:
            格式化后的代码（根据数据源不同）
        """
        # 移除可能的前缀后缀，统一大写
        symbol = symbol.strip().upper()

        if self.source == "eastmoney":
            # 东方财富格式：市场代码 + 股票代码
            # 1-上海, 0-深圳, 116-港股
            market_map = {"sh": "1", "sz": "0", "hk": "116"}
            return f"{market_map[market]}.{symbol}"

        elif self.source == "tencent":
            # 腾讯格式：市场前缀 + 股票代码
            # sh-上海, sz-深圳, hk-港股
            return f"{market}{symbol}"

        elif self.source == "sina":
            # 新浪格式：市场前缀 + 股票代码
            market_map = {"sh": "sh", "sz": "sz", "hk": "hk"}
            return f"{market_map[market]}{symbol}"

        return symbol

    @retry(max_attempts=3, delay=1.0)
    def get_realtime_quote(
        self,
        symbol: str,
        market: Literal["sh", "sz", "hk"] = "sh"
    ) -> Dict[str, Any]:
        """
        获取实时行情数据

        Args:
            symbol: 股票代码（如 "000001"）
            market: 市场类型（sh-上证, sz-深证, hk-港股）

        Returns:
            包含实时行情数据的字典
        """
        formatted_symbol = self._format_symbol(symbol, market)
        logger.info(
            f"[WebQuoteValidator] 正在从{self.config['name']}获取 "
            f"{market}:{symbol} 的实时行情..."
        )

        try:
            if self.source == "eastmoney":
                return self._fetch_eastmoney_realtime(formatted_symbol, symbol, market)
            elif self.source == "tencent":
                return self._fetch_tencent_realtime(formatted_symbol, symbol, market)
            elif self.source == "sina":
                return self._fetch_sina_realtime(formatted_symbol, symbol, market)
            else:
                raise ValueError(f"不支持的数据源: {self.source}")

        except requests.exceptions.RequestException as e:
            logger.error(f"[WebQuoteValidator] 网络请求失败: {str(e)}")
            raise NetworkError(f"获取{symbol}行情失败: {str(e)}")
        except Exception as e:
            logger.error(f"[WebQuoteValidator] 数据处理错误: {str(e)}")
            raise ValidationError(f"解析{symbol}行情数据失败: {str(e)}")

    def _fetch_eastmoney_realtime(
        self,
        formatted_symbol: str,
        original_symbol: str,
        market: str
    ) -> Dict[str, Any]:
        """从东方财富获取实时行情"""
        url = f"{self.config['base_url']}{self.config['realtime_endpoint']}"
        params = {
            "secid": formatted_symbol,
            "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f170",
            "_": int(time.time() * 1000)
        }

        response = self.session.get(
            url,
            params=params,
            headers=self.config["headers"],
            timeout=self.timeout
        )
        response.raise_for_status()

        data = response.json()
        if data.get("rc") != 0:
            raise ValidationError(f"东方财富API错误: {data.get('rt')}")

        fields = data.get("data", {})

        # 解析字段（东方财富字段编码）
        # f43: 最新价, f44: 最高价, f45: 最低价, f46: 开盘价
        # f47: 成交量, f48: 成交额, f57: 代码, f58: 名称
        # f60: 昨收, f170: 涨跌幅
        result = {
            "source": "eastmoney",
            "symbol": original_symbol,
            "market": market,
            "name": fields.get("f58", ""),
            "price": round(fields.get("f43", 0) / 100, 2) if fields.get("f43") else 0,
            "open": round(fields.get("f46", 0) / 100, 2) if fields.get("f46") else 0,
            "high": round(fields.get("f44", 0) / 100, 2) if fields.get("f44") else 0,
            "low": round(fields.get("f45", 0) / 100, 2) if fields.get("f45") else 0,
            "pre_close": round(fields.get("f60", 0) / 100, 2) if fields.get("f60") else 0,
            "volume": fields.get("f47", 0),
            "amount": fields.get("f48", 0),
            "change_pct": round(fields.get("f170", 0) / 100, 2) if fields.get("f170") else 0,
            "timestamp": datetime.now().isoformat()
        }

        # 计算涨跌额
        result["change"] = round(result["price"] - result["pre_close"], 2)

        logger.info(
            f"[WebQuoteValidator] 从东方财富成功获取 {result['name']}({original_symbol}) "
            f"实时行情，价格: {result['price']}"
        )

        return result

    def _fetch_tencent_realtime(
        self,
        formatted_symbol: str,
        original_symbol: str,
        market: str
    ) -> Dict[str, Any]:
        """从腾讯财经获取实时行情"""
        url = f"{self.config['base_url']}{self.config['realtime_endpoint']}"

        response = self.session.get(
            url,
            params={"q": formatted_symbol},
            headers=self.config["headers"],
            timeout=self.timeout
        )
        response.raise_for_status()

        # 腾讯返回格式为: v_sh600519="1~贵州茅台~600519~...";
        text = response.text
        try:
            # 提取引号内的数据
            start = text.find('"') + 1
            end = text.rfind('"')
            data_str = text[start:end]
            fields = data_str.split("~")

            if len(fields) < 45:
                raise ValueError(f"腾讯返回数据字段不足: {len(fields)}")

            # 解析字段
            result = {
                "source": "tencent",
                "symbol": original_symbol,
                "market": market,
                "name": fields[1],
                "price": float(fields[3]) if fields[3] else 0,
                "pre_close": float(fields[4]) if fields[4] else 0,
                "open": float(fields[5]) if fields[5] else 0,
                "high": float(fields[33]) if fields[33] else 0,
                "low": float(fields[34]) if fields[34] else 0,
                "volume": int(float(fields[36])) if fields[36] else 0,
                "amount": float(fields[37]) if fields[37] else 0,
                "change_pct": float(fields[32]) if fields[32] else 0,
                "timestamp": datetime.now().isoformat()
            }

            # 计算涨跌额
            result["change"] = round(result["price"] - result["pre_close"], 2)

            logger.info(
                f"[WebQuoteValidator] 从腾讯财经成功获取 {result['name']}({original_symbol}) "
                f"实时行情，价格: {result['price']}"
            )

            return result

        except Exception as e:
            logger.error(f"[WebQuoteValidator] 解析腾讯数据失败: {str(e)}")
            raise ValidationError(f"解析腾讯行情数据失败: {str(e)}")

    def _fetch_sina_realtime(
        self,
        formatted_symbol: str,
        original_symbol: str,
        market: str
    ) -> Dict[str, Any]:
        """从新浪财经获取实时行情"""
        url = f"{self.config['base_url']}{self.config['realtime_endpoint']}"

        response = self.session.get(
            url,
            params={"list": formatted_symbol},
            headers=self.config["headers"],
            timeout=self.timeout
        )
        response.raise_for_status()

        # 新浪返回格式为: var hq_str_sh600519="贵州茅台,1740.00,...";
        text = response.text
        try:
            # 提取引号内的数据
            start = text.find('"') + 1
            end = text.rfind('"')

            if start <= 0 or end <= 0 or end <= start:
                raise ValueError("无法找到有效的数据字段")

            data_str = text[start:end]
            fields = data_str.split(",")

            if len(fields) < 33:
                raise ValueError(f"新浪返回数据字段不足: {len(fields)}")

            # 解析字段（新浪格式）
            # 字段顺序: 股票名称,今日开盘价,昨日收盘价,当前价格,今日最高价,今日最低价,
            # 竞买价,竞卖价,成交股票数,成交金额,...
            result = {
                "source": "sina",
                "symbol": original_symbol,
                "market": market,
                "name": fields[0],
                "open": float(fields[1]) if fields[1] else 0,
                "pre_close": float(fields[2]) if fields[2] else 0,
                "price": float(fields[3]) if fields[3] else 0,
                "high": float(fields[4]) if fields[4] else 0,
                "low": float(fields[5]) if fields[5] else 0,
                "volume": int(float(fields[8])) if fields[8] else 0,
                "amount": float(fields[9]) if fields[9] else 0,
                "timestamp": datetime.now().isoformat()
            }

            # 计算涨跌幅和涨跌额
            if result["pre_close"] > 0:
                result["change_pct"] = round(
                    (result["price"] - result["pre_close"]) / result["pre_close"] * 100, 2
                )
            else:
                result["change_pct"] = 0

            result["change"] = round(result["price"] - result["pre_close"], 2)

            logger.info(
                f"[WebQuoteValidator] 从新浪财经成功获取 {result['name']}({original_symbol}) "
                f"实时行情，价格: {result['price']}"
            )

            return result

        except Exception as e:
            logger.error(f"[WebQuoteValidator] 解析新浪数据失败: {str(e)}")
            raise ValidationError(f"解析新浪行情数据失败: {str(e)}")

    def validate_against_reference(
        self,
        web_price: float,
        reference_price: float,
        symbol: str,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        验证Web价格与参考价格的差异

        当价格偏差超过指定阈值时，在返回结果中标记警告。

        Args:
            web_price: Web抓取的价格
            reference_price: 参考价格（如AkShare获取的价格）
            symbol: 股票代码
            threshold: 价格差异阈值（百分比，默认0.5%）

        Returns:
            包含验证结果的字典：
            - is_valid: 验证是否通过
            - web_price: Web抓取价格
            - reference_price: 参考价格
            - diff: 价格差异绝对值
            - diff_pct: 价格差异百分比
            - threshold: 验证阈值
            - warning: 警告信息（如果验证失败）
        """
        if reference_price == 0:
            return {
                "is_valid": False,
                "warning": "[DATA_MISMATCH_WARNING] 参考价格为0，无法验证",
                "web_price": web_price,
                "reference_price": reference_price,
                "diff_pct": None,
                "threshold": threshold
            }

        # 计算差异百分比（绝对值）
        diff_pct = abs(web_price - reference_price) / reference_price * 100
        is_valid = diff_pct <= threshold

        result = {
            "is_valid": is_valid,
            "web_price": web_price,
            "reference_price": reference_price,
            "diff": round(abs(web_price - reference_price), 2),
            "diff_pct": round(diff_pct, 4),
            "threshold": threshold
        }

        if not is_valid:
            result["warning"] = (
                f"[DATA_MISMATCH_WARNING] 价格偏差超过{threshold}%！"
                f"Web价格({web_price})与参考价格({reference_price})差异为{diff_pct:.4f}%"
            )
            logger.warning(result["warning"])

        return result


# ============================================================================
# OpenClaw Tool 封装
# ============================================================================

@tool(
    name="web_quote_validator",
    description="Web行情验证器 - 通过东方财富/腾讯/新浪获取实时价格，用于验证AkShare数据"
)
@log_execution
def web_quote_validator_tool(
    symbol: str = "",
    market: Literal["sh", "sz", "hk"] = "sh",
    source: Literal["eastmoney", "tencent", "sina"] = "eastmoney",
    headers: Optional[Dict[str, str]] = None,
    proxies: Optional[Dict[str, str]] = None,
    reference_price: Optional[float] = None,
    threshold: float = 0.5,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Web行情验证器 - 实时价格双重验证工具

    本工具作为ak_market_tool的Double Check，通过爬取东方财富、腾讯财经或新浪
    财经的网页接口获取实时价格，用于验证主数据源的准确性。

    当提供reference_price参数时，如果Web抓取价格与参考价格误差超过0.5%，
    将在返回结果中标记[DATA_MISMATCH_WARNING]。

    代理配置优先级：
    1. 显式传入的proxies参数
    2. 环境变量PROXY_URL
    3. 无代理（直接连接）

    Args:
        symbol: 股票代码（如"000001"表示平安银行）
        market: 市场类型（"sh"-上证, "sz"-深证, "hk"-港股）
        source: 数据源选择（"eastmoney"/"tencent"/"sina"）
        headers: 自定义HTTP请求头（可选）
        proxies: 代理配置（可选，默认从环境变量PROXY_URL读取）
        reference_price: 参考价格用于验证（可选）
        threshold: 价格差异阈值（百分比，默认0.5%）
        timeout: 请求超时时间（秒）

    Returns:
        包含实时行情数据的字典，字段包括：
        - source: 数据来源
        - symbol: 股票代码
        - market: 市场类型
        - name: 股票名称
        - price: 当前价格
        - change: 涨跌额
        - change_pct: 涨跌幅(%)
        - volume: 成交量
        - amount: 成交额
        - open: 开盘价
        - high: 最高价
        - low: 最低价
        - pre_close: 昨收价
        - timestamp: 数据时间戳
        - validation: 验证结果（如果提供了reference_price）

    Raises:
        NetworkError: 网络请求失败
        ValidationError: 数据验证失败
        PriceMismatchError: 价格偏差超过阈值（当开启严格模式时）

    Examples:
        >>> # 仅获取Web价格
        >>> result = web_quote_validator_tool(
        ...     symbol="000001",
        ...     market="sz",
        ...     source="eastmoney"
        ... )

        >>> # 获取Web价格并与参考价格验证
        >>> result = web_quote_validator_tool(
        ...     symbol="000001",
        ...     market="sz",
        ...     source="eastmoney",
        ...     reference_price=10.26,
        ...     threshold=0.5
        ... )
    """
    if not symbol:
        raise ValueError("必须提供股票代码(symbol)")

    # 初始化验证器
    validator = WebQuoteValidator(
        source=source,
        proxy=None,  # 代理在内部从环境变量读取
        timeout=timeout
    )

    # 使用自定义headers（如果提供）
    if headers:
        validator.session.headers.update(headers)

    # 使用自定义proxies（如果提供，覆盖环境变量）
    if proxies:
        validator.session.proxies = proxies

    # 获取实时行情
    logger.info(f"[WebQuoteValidator] 开始从{source}获取 {market}:{symbol} 的实时行情...")
    quote_data = validator.get_realtime_quote(symbol, market)

    # 如果提供了参考价格，执行验证
    if reference_price is not None and reference_price > 0:
        logger.info(f"[WebQuoteValidator] 正在验证价格，参考价格: {reference_price}")
        validation_result = validator.validate_against_reference(
            web_price=quote_data["price"],
            reference_price=reference_price,
            symbol=symbol,
            threshold=threshold
        )

        # 将验证结果添加到返回数据
        quote_data["validation"] = validation_result

        # 如果验证失败，记录警告
        if not validation_result["is_valid"]:
            logger.warning(
                f"[WebQuoteValidator] 价格验证失败: {validation_result.get('warning')}"
            )

    logger.info(
        f"[WebQuoteValidator] 成功获取 {quote_data.get('name', symbol)} 行情，"
        f"当前价格: {quote_data['price']}"
    )

    return quote_data
