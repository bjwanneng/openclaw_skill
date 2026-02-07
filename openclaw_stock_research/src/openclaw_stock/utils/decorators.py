"""
OpenClaw工具装饰器定义

提供工具注册、环境变量检查、日志记录、重试等功能
"""

from functools import wraps
from typing import Callable, Any, List, TypeVar, Optional
import os
import time
import logging
from datetime import datetime

# 获取日志记录器
logger = logging.getLogger("openclaw_stock.decorators")

# 类型变量
F = TypeVar("F", bound=Callable[..., Any])


def tool(name: str, description: str) -> Callable[[F], F]:
    """
    OpenClaw工具装饰器

    标记函数为OpenClaw可调用的Tool，添加元数据信息

    参数:
        name: 工具名称
        description: 工具描述

    示例:
        @tool(name="ak_market_engine", description="AkShare市场数据引擎")
        def ak_market_engine_tool(...):
            ...
    """
    def decorator(func: F) -> F:
        # 添加工具元数据
        func._is_tool = True
        func._tool_name = name
        func._tool_description = description
        func._tool_timestamp = datetime.now().isoformat()

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"[Tool:{name}] 开始执行工具: {description}")
            start_time = time.time()

            try:
                # 执行被装饰的函数
                result = func(*args, **kwargs)

                elapsed = time.time() - start_time
                logger.info(f"[Tool:{name}] 执行成功，耗时 {elapsed:.2f}秒")

                # 在结果中添加元数据
                if isinstance(result, dict):
                    result["_tool_meta"] = {
                        "name": name,
                        "execution_time": elapsed,
                        "timestamp": datetime.now().isoformat()
                    }

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"[Tool:{name}] 执行失败，耗时 {elapsed:.2f}秒，错误: {str(e)}")
                raise

        return wrapper  # type: ignore

    return decorator


def require_env(env_vars: List[str]) -> Callable[[F], F]:
    """
    环境变量检查装饰器

    检查必需的环境变量是否存在，如不存在则抛出EnvironmentError

    参数:
        env_vars: 必需的环境变量名称列表

    示例:
        @require_env(["PROXY_URL", "STOCK_DATA_PATH"])
        def my_tool(...):
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            missing_vars = []

            for var in env_vars:
                value = os.environ.get(var)
                if value is None or value.strip() == "":
                    missing_vars.append(var)

            if missing_vars:
                error_msg = (
                    f"缺少必需的环境变量: {', '.join(missing_vars)}。"
                    f"请设置后重试。示例: export {missing_vars[0]}=your_value"
                )
                logger.error(f"[require_env] {error_msg}")
                raise EnvironmentError(error_msg)

            logger.debug(f"[require_env] 环境变量检查通过: {', '.join(env_vars)}")
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def log_execution(func: F) -> F:
    """
    执行日志装饰器

    记录函数执行的详细日志，包括参数和返回结果类型

    示例:
        @log_execution
        def my_function(x, y):
            return x + y
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__name__
        logger.debug(f"[log_execution] 调用 {func_name}，参数: args={len(args)}个, kwargs={list(kwargs.keys())}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"[log_execution] {func_name} 返回结果类型: {type(result).__name__}")
            return result
        except Exception as e:
            logger.error(f"[log_execution] {func_name} 执行异常: {str(e)}")
            raise

    return wrapper  # type: ignore


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable[[F], F]:
    """
    重试装饰器

    在函数执行失败时自动重试，支持指数退避

    参数:
        max_attempts: 最大尝试次数，默认为3
        delay: 初始延迟时间（秒），默认为1.0
        backoff: 退避系数，默认为2.0（每次延迟翻倍）
        exceptions: 需要捕获的异常类型元组，默认为(Exception,)

    示例:
        @retry(max_attempts=5, delay=2.0)
        def fetch_data():
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__name__
            current_delay = delay
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"[retry] {func_name} 第{attempt}次尝试...")
                    result = func(*args, **kwargs)

                    if attempt > 1:
                        logger.info(f"[retry] {func_name} 在第{attempt}次尝试后成功")

                    return result

                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        logger.warning(
                            f"[retry] {func_name} 第{attempt}次尝试失败: {str(e)}，"
                            f"{current_delay}秒后重试..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"[retry] {func_name} 所有{max_attempts}次尝试均失败，"
                            f"最后错误: {str(e)}"
                        )

            # 所有尝试失败，抛出最后的异常
            if last_exception:
                raise last_exception
            else:
                raise RuntimeError(f"{func_name} 重试机制异常")

        return wrapper  # type: ignore

    return decorator


def cache_result(
    cache_key_func: Optional[Callable[..., str]] = None,
    ttl: float = 300.0
) -> Callable[[F], F]:
    """
    结果缓存装饰器

    缓存函数的执行结果，在指定时间内直接返回缓存值

    参数:
        cache_key_func: 自定义缓存键生成函数，默认为函数名+参数哈希
        ttl: 缓存有效期（秒），默认为300秒（5分钟）

    示例:
        @cache_result(ttl=60.0)
        def get_stock_price(symbol: str):
            ...
    """
    _cache: Dict[str, tuple] = {}

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 生成缓存键
            if cache_key_func:
                key = cache_key_func(*args, **kwargs)
            else:
                # 默认缓存键: 函数名+参数哈希
                args_str = ",".join(str(a) for a in args)
                kwargs_str = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = f"{func.__name__}({args_str},{kwargs_str})"

            now = time.time()

            # 检查缓存
            if key in _cache:
                cached_value, cached_time = _cache[key]
                if now - cached_time < ttl:
                    logger.debug(f"[cache_result] 命中缓存: {key}")
                    return cached_value
                else:
                    logger.debug(f"[cache_result] 缓存过期: {key}")
                    del _cache[key]

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            _cache[key] = (result, now)
            logger.debug(f"[cache_result] 缓存结果: {key}")

            return result

        # 添加清除缓存的方法
        def clear_cache():
            """清除该函数的所有缓存"""
            keys_to_remove = [k for k in _cache if k.startswith(f"{func.__name__}(")]
            for key in keys_to_remove:
                del _cache[key]
            logger.debug(f"[cache_result] 清除 {len(keys_to_remove)} 个缓存项")

        wrapper.clear_cache = clear_cache  # type: ignore

        return wrapper  # type: ignore

    return decorator


# 导出所有装饰器
__all__ = [
    "tool",
    "require_env",
    "log_execution",
    "retry",
    "cache_result",
]
