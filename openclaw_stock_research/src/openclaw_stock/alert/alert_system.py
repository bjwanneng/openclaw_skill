"""
预警系统模块

实现设计文档4.5节的接口10: 实时预警
"""

from typing import Literal, Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import threading
import time
import pandas as pd

from ..core.exceptions import AlertError
from ..utils.logger import get_logger
from ..data.market_data import fetch_realtime_quote

try:
    import akshare as ak
except ImportError:
    ak = None

logger = get_logger(__name__)


class AlertType(Enum):
    """预警类型"""
    PRICE = "price"
    VOLUME = "volume"
    TECHNICAL = "technical"
    NEWS = "news"


class AlertStatus(Enum):
    """预警状态"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISABLED = "disabled"
    EXPIRED = "expired"


@dataclass
class AlertCondition:
    """预警条件"""
    operator: Literal["above", "below", "between", "equals", "cross_above", "cross_below"]
    value: float
    value2: Optional[float] = None  # 用于between
    duration: Optional[int] = None  # 持续分钟数


@dataclass
class Alert:
    """预警对象"""
    id: str
    symbol: str
    alert_type: AlertType
    condition: AlertCondition
    status: AlertStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    triggered_at: Optional[datetime] = None
    triggered_value: Optional[float] = None
    notification_methods: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PriceAlert:
    """价格预警"""

    def __init__(self, symbol: str, condition: Dict[str, Any]):
        self.symbol = symbol
        self.condition = condition
        self.alert_type = AlertType.PRICE

    def check(self, data: Dict[str, Any]) -> bool:
        """检查是否触发预警"""
        current_price = data.get("price", 0)
        operator = self.condition.get("operator", "above")
        value = self.condition.get("value", 0)

        if operator == "above":
            return current_price > value
        elif operator == "below":
            return current_price < value
        elif operator == "between":
            value2 = self.condition.get("value2", value)
            return value <= current_price <= value2
        elif operator == "equals":
            return abs(current_price - value) < 0.01

        return False


class VolumeAlert:
    """成交量预警"""

    def __init__(self, symbol: str, condition: Dict[str, Any]):
        self.symbol = symbol
        self.condition = condition
        self.alert_type = AlertType.VOLUME

    def check(self, data: Dict[str, Any]) -> bool:
        """检查是否触发预警"""
        current_volume = data.get("volume", 0)
        operator = self.condition.get("operator", "above")
        value = self.condition.get("value", 0)

        if operator == "above":
            return current_volume > value
        elif operator == "below":
            return current_volume < value
        elif operator == "sudden_increase":
            # 成交量突增(放量)
            avg_volume = data.get("avg_volume", current_volume)
            return current_volume > avg_volume * value  # value是倍数

        return False


class TechnicalAlert:
    """技术指标预警"""

    def __init__(self, symbol: str, condition: Dict[str, Any]):
        self.symbol = symbol
        self.condition = condition
        self.alert_type = AlertType.TECHNICAL

    def check(self, data: Dict[str, Any]) -> bool:
        """检查是否触发预警"""
        indicator = self.condition.get("indicator", "")
        operator = self.condition.get("operator", "cross_above")
        value = self.condition.get("value", 0)

        indicators = data.get("indicators", {})

        if indicator == "macd":
            macd_hist = indicators.get("macd_hist", 0)
            macd_hist_prev = data.get("macd_hist_prev", macd_hist)

            if operator == "golden_cross":  # 金叉
                return macd_hist_prev < 0 and macd_hist > 0
            elif operator == "dead_cross":  # 死叉
                return macd_hist_prev > 0 and macd_hist < 0

        elif indicator == "rsi":
            rsi = indicators.get("rsi6", 0)
            if operator == "above":
                return rsi > value
            elif operator == "below":
                return rsi < value
            elif operator == "overbought":  # 超买
                return rsi > 80
            elif operator == "oversold":  # 超卖
                return rsi < 20

        elif indicator == "ma":
            price = data.get("price", 0)
            ma_period = self.condition.get("ma_period", 20)
            ma_value = indicators.get(f"ma{ma_period}", 0)

            if operator == "cross_above":  # 价格上穿均线
                return price > ma_value
            elif operator == "cross_below":  # 价格下穿均线
                return price < ma_value

        elif indicator == "boll":
            price = data.get("price", 0)
            boll_upper = indicators.get("boll_upper", float('inf'))
            boll_lower = indicators.get("boll_lower", 0)

            if operator == "breakout_up":  # 突破上轨
                return price > boll_upper
            elif operator == "breakout_down":  # 突破下轨
                return price < boll_lower

        return False


class AlertSystem:
    """
    预警系统类

    管理所有预警的创建、监控和触发
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.alerts: Dict[str, Alert] = {}
        self.running = False
        self.monitor_thread = None
        self.check_interval = 60  # 检查间隔(秒)

    def setup_alert(
        self,
        symbol: str,
        alert_type: Literal["price", "volume", "technical", "news"],
        condition: Dict[str, Any],
        notification_method: Literal["email", "wechat", "dingtalk", "console"] = "console",
        expires_in_hours: Optional[int] = None
    ) -> str:
        """
        设置股票预警（接口10实现）

        参数:
            symbol: 股票代码
            alert_type: 预警类型(price/volume/technical/news)
            condition: 条件字典
            notification_method: 通知方式
            expires_in_hours: 过期时间(小时)

        返回:
            预警ID

        示例:
            setup_alert('000001', 'price', {'above': 15.0})
            setup_alert('600519', 'technical', {'macd': 'golden_cross'})
        """
        alert_id = f"{symbol}_{alert_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 解析条件
        alert_condition = AlertCondition(
            operator=condition.get("operator", "above"),
            value=condition.get("value", 0),
            value2=condition.get("value2"),
            duration=condition.get("duration")
        )

        # 计算过期时间
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        # 创建预警对象
        alert = Alert(
            id=alert_id,
            symbol=symbol,
            alert_type=AlertType(alert_type),
            condition=alert_condition,
            status=AlertStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=expires_at,
            notification_methods=[notification_method]
        )

        # 保存预警
        self.alerts[alert_id] = alert

        self.logger.info(f"[setup_alert] 创建预警成功: {alert_id}")

        return alert_id

    def remove_alert(self, alert_id: str) -> bool:
        """移除预警"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self.logger.info(f"[remove_alert] 移除预警: {alert_id}")
            return True
        return False

    def list_alerts(self, symbol: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有预警"""
        result = []
        for alert in self.alerts.values():
            if symbol and alert.symbol != symbol:
                continue
            if status and alert.status.value != status:
                continue

            result.append({
                "id": alert.id,
                "symbol": alert.symbol,
                "alert_type": alert.alert_type.value,
                "status": alert.status.value,
                "created_at": alert.created_at.isoformat(),
                "expires_at": alert.expires_at.isoformat() if alert.expires_at else None
            })
        return result

    def start_monitoring(self):
        """启动监控线程"""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        self.logger.info("[start_monitoring] 预警监控已启动")

    def stop_monitoring(self):
        """停止监控线程"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.logger.info("[stop_monitoring] 预警监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._check_all_alerts()
            except Exception as e:
                self.logger.error(f"[_monitor_loop] 检查预警失败: {e}")

            # 等待下一个检查周期
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _check_all_alerts(self):
        """检查所有预警"""
        for alert in list(self.alerts.values()):
            # 跳过已触发或已禁用的预警
            if alert.status in [AlertStatus.TRIGGERED, AlertStatus.DISABLED]:
                continue

            # 检查是否过期
            if alert.expires_at and datetime.now() > alert.expires_at:
                alert.status = AlertStatus.EXPIRED
                continue

            # 检查预警条件
            try:
                triggered = self._check_alert_condition(alert)
                if triggered:
                    alert.status = AlertStatus.TRIGGERED
                    alert.triggered_at = datetime.now()
                    self._send_notification(alert)
            except Exception as e:
                self.logger.error(f"[_check_all_alerts] 检查预警 {alert.id} 失败: {e}")

    def _check_alert_condition(self, alert: Alert) -> bool:
        """检查单个预警条件"""
        # 获取实时数据
        try:
            realtime_data = fetch_realtime_quote(symbol=alert.symbol, market="sh")
        except:
            try:
                realtime_data = fetch_realtime_quote(symbol=alert.symbol, market="sz")
            except:
                return False

        # 根据预警类型检查条件
        if alert.alert_type == AlertType.PRICE:
            return self._check_price_condition(alert, realtime_data)
        elif alert.alert_type == AlertType.VOLUME:
            return self._check_volume_condition(alert, realtime_data)
        elif alert.alert_type == AlertType.TECHNICAL:
            return self._check_technical_condition(alert, realtime_data)
        elif alert.alert_type == AlertType.NEWS:
            return self._check_news_condition(alert)

        return False

    def _check_price_condition(self, alert: Alert, data: Dict[str, Any]) -> bool:
        """检查价格条件"""
        current_price = data.get("price", 0)
        operator = alert.condition.operator
        value = alert.condition.value

        if operator == "above":
            return current_price > value
        elif operator == "below":
            return current_price < value
        elif operator == "between":
            return value <= current_price <= alert.condition.value2
        elif operator == "equals":
            return abs(current_price - value) < 0.01

        return False

    def _check_volume_condition(self, alert: Alert, data: Dict[str, Any]) -> bool:
        """检查成交量条件"""
        current_volume = data.get("volume", 0)
        operator = alert.condition.operator
        value = alert.condition.value

        if operator == "above":
            return current_volume > value
        elif operator == "below":
            return current_volume < value
        elif operator == "sudden_increase":
            # 需要获取历史平均成交量
            return False

        return False

    def _check_technical_condition(self, alert: Alert, data: Dict[str, Any]) -> bool:
        """检查技术指标条件"""
        indicator = alert.condition.get("indicator", "")
        operator = alert.condition.operator

        # 简化处理，实际应该获取历史K线计算指标
        if indicator == "macd":
            # 需要获取历史数据计算MACD
            return False
        elif indicator == "rsi":
            # 需要获取历史数据计算RSI
            return False

        return False

    def _check_news_condition(self, alert: Alert) -> bool:
        """检查新闻条件"""
        # 简化处理，实际应该监控新闻源
        return False

    def _send_notification(self, alert: Alert):
        """发送预警通知"""
        for method in alert.notification_methods:
            try:
                if method == "console":
                    self._console_notification(alert)
                elif method == "email":
                    self._email_notification(alert)
                elif method == "wechat":
                    self._wechat_notification(alert)
                elif method == "dingtalk":
                    self._dingtalk_notification(alert)
            except Exception as e:
                self.logger.error(f"[_send_notification] {method} 通知失败: {e}")

    def _console_notification(self, alert: Alert):
        """控制台通知"""
        message = f"""
=====================================
⚠️  预警触发提醒
=====================================
预警ID: {alert.id}
股票代码: {alert.symbol}
预警类型: {alert.alert_type.value}
触发时间: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}
触发值: {alert.triggered_value}
=====================================
"""
        print(message)
        self.logger.info(f"[console_notification] 预警 {alert.id} 已触发")

    def _email_notification(self, alert: Alert):
        """邮件通知"""
        # 实际实现需要配置邮件服务器
        self.logger.info(f"[email_notification] 预警 {alert.id} 邮件通知(待实现)")

    def _wechat_notification(self, alert: Alert):
        """微信通知"""
        # 实际实现需要配置微信API
        self.logger.info(f"[wechat_notification] 预警 {alert.id} 微信通知(待实现)")

    def _dingtalk_notification(self, alert: Alert):
        """钉钉通知"""
        # 实际实现需要配置钉钉API
        self.logger.info(f"[dingtalk_notification] 预警 {alert.id} 钉钉通知(待实现)")


# 便利函数
def setup_alert(
    symbol: str,
    alert_type: Literal["price", "volume", "technical", "news"],
    condition: Dict[str, Any],
    notification_method: str = "console",
    expires_in_hours: Optional[int] = None
) -> str:
    """
    设置股票预警（接口10实现）

    示例:
        setup_alert('000001', 'price', {'operator': 'above', 'value': 15.0})
        setup_alert('600519', 'technical', {'indicator': 'macd', 'operator': 'golden_cross'})
    """
    system = AlertSystem()
    return system.setup_alert(
        symbol=symbol,
        alert_type=alert_type,
        condition=condition,
        notification_method=notification_method,
        expires_in_hours=expires_in_hours
    )


def remove_alert(alert_id: str) -> bool:
    """移除预警"""
    system = AlertSystem()
    return system.remove_alert(alert_id)


def list_alerts(symbol: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出所有预警"""
    system = AlertSystem()
    return system.list_alerts(symbol, status)
