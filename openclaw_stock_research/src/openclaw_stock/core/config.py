"""
配置管理模块

从环境变量读取配置，确保零硬编码
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path


class Config:
    """配置管理类"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        if key not in self._cache:
            self._cache[key] = os.environ.get(key, default)
        return self._cache[key]

    def get_proxy_url(self) -> Optional[str]:
        """
        获取代理服务器地址

        从环境变量 PROXY_URL 读取
        格式: http://127.0.0.1:7890 或 https://proxy.example.com:8080

        Returns:
            代理URL字符串，如果未设置则返回None
        """
        proxy_url = self.get("PROXY_URL")
        if proxy_url:
            # 验证格式
            if not proxy_url.startswith(("http://", "https://", "socks5://")):
                raise ValueError(
                    f"PROXY_URL格式错误: {proxy_url}，应以http://、https://或socks5://开头"
                )
        return proxy_url

    def get_stock_data_path(self) -> str:
        """
        获取股票数据存储路径

        从环境变量 STOCK_DATA_PATH 读取，默认为 ./data

        Returns:
            数据存储路径字符串
        """
        path = self.get("STOCK_DATA_PATH", "./data")
        # 确保路径存在
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def get_log_path(self) -> Optional[str]:
        """
        获取日志存储路径

        从环境变量 LOG_PATH 读取，如果未设置则返回None（仅控制台输出）

        Returns:
            日志存储路径字符串，如果未设置则返回None
        """
        log_path = self.get("LOG_PATH")
        if log_path:
            Path(log_path).mkdir(parents=True, exist_ok=True)
        return log_path

    def get_timeout(self) -> int:
        """
        获取默认请求超时时间

        从环境变量 DEFAULT_TIMEOUT 读取，默认为30秒

        Returns:
            超时时间（秒）
        """
        return int(self.get("DEFAULT_TIMEOUT", 30))

    def get_max_retries(self) -> int:
        """
        获取最大重试次数

        从环境变量 MAX_RETRIES 读取，默认为3次

        Returns:
            最大重试次数
        """
        return int(self.get("MAX_RETRIES", 3))

    def get_price_diff_threshold(self) -> float:
        """
        获取价格差异验证阈值

        从环境变量 PRICE_DIFF_THRESHOLD 读取，默认为0.5%

        Returns:
            价格差异阈值（百分比）
        """
        return float(self.get("PRICE_DIFF_THRESHOLD", 0.5))

    def get_log_level(self) -> str:
        """
        获取日志级别

        从环境变量 LOG_LEVEL 读取，默认为INFO
        可选值: DEBUG, INFO, WARNING, ERROR, CRITICAL

        Returns:
            日志级别字符串
        """
        return self.get("LOG_LEVEL", "INFO").upper()

    def to_dict(self) -> Dict[str, Any]:
        """
        获取所有配置项为字典

        Returns:
            包含所有配置项的字典
        """
        return {
            "proxy_url": self.get_proxy_url(),
            "stock_data_path": self.get_stock_data_path(),
            "log_path": self.get_log_path(),
            "timeout": self.get_timeout(),
            "max_retries": self.get_max_retries(),
            "price_diff_threshold": self.get_price_diff_threshold(),
            "log_level": self.get_log_level(),
        }


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """
    获取全局配置实例

    使用单例模式确保配置只被初始化一次

    Returns:
        Config实例
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config():
    """
    重置配置实例

    主要用于测试场景，清除配置缓存
    """
    global _config
    _config = None
