"""
自定义异常类模块

定义投研分析系统中使用的所有自定义异常
"""


class StockResearchError(Exception):
    """基础异常类 - 所有投研分析异常的基类"""

    def __init__(self, message: str = "投研分析系统错误"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"[StockResearchError] {self.message}"


class DataSourceError(StockResearchError):
    """数据源异常 - 从数据源获取数据时发生错误"""

    def __init__(self, message: str = "数据源访问失败"):
        super().__init__(message)

    def __str__(self):
        return f"[DataSourceError] {self.message}"


class ValidationError(StockResearchError):
    """数据验证异常 - 数据验证失败"""

    def __init__(self, message: str = "数据验证失败"):
        super().__init__(message)

    def __str__(self):
        return f"[ValidationError] {self.message}"


class NetworkError(StockResearchError):
    """网络异常 - 网络请求失败"""

    def __init__(self, message: str = "网络请求失败"):
        super().__init__(message)

    def __str__(self):
        return f"[NetworkError] {self.message}"


class SymbolNotFoundError(DataSourceError):
    """股票代码不存在异常 - 查询的股票代码不存在"""

    def __init__(self, symbol: str = "", market: str = ""):
        self.symbol = symbol
        self.market = market
        message = f"股票代码不存在: {market}:{symbol}"
        super().__init__(message)

    def __str__(self):
        return f"[SymbolNotFoundError] {self.message}"


class PriceMismatchError(ValidationError):
    """价格不匹配异常 - Web验证价格与参考价格差异过大"""

    def __init__(
        self,
        web_price: float = 0.0,
        reference_price: float = 0.0,
        diff_pct: float = 0.0,
        threshold: float = 0.5
    ):
        self.web_price = web_price
        self.reference_price = reference_price
        self.diff_pct = diff_pct
        self.threshold = threshold

        message = (
            f"价格偏差超过{threshold}%！"
            f"Web价格({web_price})与参考价格({reference_price})差异为{diff_pct:.4f}%"
        )
        super().__init__(message)

    def __str__(self):
        return f"[PriceMismatchError] {self.message}"


class CacheError(StockResearchError):
    """缓存异常 - 缓存操作失败"""

    def __init__(self, message: str = "缓存操作失败"):
        super().__init__(message)

    def __str__(self):
        return f"[CacheError] {self.message}"


class TimeoutError(NetworkError):
    """超时异常 - 请求超时"""

    def __init__(self, message: str = "请求超时", timeout: int = 30):
        self.timeout = timeout
        message = f"{message}（超时时间: {timeout}秒）"
        super().__init__(message)

    def __str__(self):
        return f"[TimeoutError] {self.message}"


class RateLimitError(NetworkError):
    """频率限制异常 - 请求频率过高被限制"""

    def __init__(self, message: str = "请求频率过高，请稍后重试"):
        super().__init__(message)

    def __str__(self):
        return f"[RateLimitError] {self.message}"


class CalculationError(StockResearchError):
    """计算异常 - 指标计算过程中发生错误"""

    def __init__(self, message: str = "计算失败"):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"[CalculationError] {self.message}"


class AlertError(StockResearchError):
    """预警异常 - 预警系统相关错误"""

    def __init__(self, message: str = "预警操作失败"):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"[AlertError] {self.message}"
