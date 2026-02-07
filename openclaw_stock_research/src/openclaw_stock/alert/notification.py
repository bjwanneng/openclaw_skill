"""
通知模块

提供邮件、微信、钉钉等通知方式
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..utils.logger import get_logger

logger = get_logger(__name__)


class BaseNotifier(ABC):
    """通知基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def send(self, message: str, title: Optional[str] = None) -> bool:
        """发送通知"""
        pass


class EmailNotifier(BaseNotifier):
    """邮件通知器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get("smtp_server", "")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.from_addr = config.get("from_addr", "")
        self.to_addrs = config.get("to_addrs", [])

    def send(self, message: str, title: Optional[str] = None) -> bool:
        """发送邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            msg['Subject'] = title or "股票预警通知"

            msg.attach(MIMEText(message, 'plain', 'utf-8'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            self.logger.info(f"邮件发送成功: {title}")
            return True

        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
            return False


class WeChatNotifier(BaseNotifier):
    """微信通知器(企业微信)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.corpid = config.get("corpid", "")
        self.corpsecret = config.get("corpsecret", "")
        self.agentid = config.get("agentid", "")
        self.access_token = None

    def _get_access_token(self) -> str:
        """获取access_token"""
        import requests

        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}"
        response = requests.get(url)
        data = response.json()
        return data.get("access_token", "")

    def send(self, message: str, title: Optional[str] = None) -> bool:
        """发送企业微信消息"""
        try:
            import requests

            if not self.access_token:
                self.access_token = self._get_access_token()

            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"

            data = {
                "touser": "@all",
                "msgtype": "text",
                "agentid": self.agentid,
                "text": {
                    "content": f"{title}\n{message}" if title else message
                }
            }

            response = requests.post(url, json=data)
            result = response.json()

            if result.get("errcode") == 0:
                self.logger.info(f"微信消息发送成功: {title}")
                return True
            else:
                self.logger.error(f"微信消息发送失败: {result}")
                return False

        except Exception as e:
            self.logger.error(f"微信消息发送失败: {e}")
            return False


class DingTalkNotifier(BaseNotifier):
    """钉钉通知器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook = config.get("webhook", "")
        self.secret = config.get("secret", "")

    def _generate_sign(self, timestamp: str) -> str:
        """生成钉钉签名"""
        import hashlib
        import hmac
        import base64

        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    def send(self, message: str, title: Optional[str] = None) -> bool:
        """发送钉钉消息"""
        try:
            import requests
            import time

            timestamp = str(round(time.time() * 1000))
            sign = self._generate_sign(timestamp)

            url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title or "股票预警",
                    "text": f"### {title}\n{message}" if title else message
                }
            }

            response = requests.post(url, json=data)
            result = response.json()

            if result.get("errcode") == 0:
                self.logger.info(f"钉钉消息发送成功: {title}")
                return True
            else:
                self.logger.error(f"钉钉消息发送失败: {result}")
                return False

        except Exception as e:
            self.logger.error(f"钉钉消息发送失败: {e}")
            return False


def send_notification(
    message: str,
    title: Optional[str] = None,
    notifier_type: str = "console",
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """
    发送通知的统一接口

    参数:
        message: 消息内容
        title: 标题
        notifier_type: 通知类型(email/wechat/dingtalk/console)
        config: 配置信息

    返回:
        是否发送成功
    """
    if notifier_type == "console":
        print(f"[{title}] {message}")
        return True

    if config is None:
        logger.error(f"缺少{notifier_type}的配置信息")
        return False

    if notifier_type == "email":
        notifier = EmailNotifier(config)
    elif notifier_type == "wechat":
        notifier = WeChatNotifier(config)
    elif notifier_type == "dingtalk":
        notifier = DingTalkNotifier(config)
    else:
        logger.error(f"不支持的通知类型: {notifier_type}")
        return False

    return notifier.send(message, title)
