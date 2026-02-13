"""通知系统模块."""

from enum import Enum
from typing import Callable

from plyer import notification


class NotificationType(Enum):
    """通知类型."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ACHIEVEMENT = "achievement"
    FLOW_ENTER = "flow_enter"
    FLOW_EXIT = "flow_exit"
    ENERGY = "energy"


class Notifier:
    """桌面通知管理器."""

    APP_NAME = "Happy Vibe"
    ICON_PATH = None  # 可设置图标路径

    # 通知标题模板
    TITLES = {
        NotificationType.INFO: "Happy Vibe",
        NotificationType.SUCCESS: "✨ 完成",
        NotificationType.WARNING: "⚠️ 提醒",
        NotificationType.ACHIEVEMENT: "🏆 成就解锁",
        NotificationType.FLOW_ENTER: "🌊 进入心流",
        NotificationType.FLOW_EXIT: "💤 心流结束",
        NotificationType.ENERGY: "⚡ 能量获取",
    }

    def __init__(self, enabled: bool = True) -> None:
        """初始化通知器.

        Args:
            enabled: 是否启用通知
        """
        self.enabled = enabled
        self._callbacks: list[Callable[[NotificationType, str, str], None]] = []

    def add_callback(
        self, callback: Callable[[NotificationType, str, str], None]
    ) -> None:
        """添加通知回调.

        Args:
            callback: 回调函数，接收 (类型, 标题, 消息)
        """
        self._callbacks.append(callback)

    def remove_callback(
        self, callback: Callable[[NotificationType, str, str], None]
    ) -> None:
        """移除通知回调."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def notify(
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        title: str | None = None,
        timeout: int = 5,
    ) -> None:
        """发送桌面通知.

        Args:
            message: 通知消息
            notification_type: 通知类型
            title: 自定义标题，默认使用类型对应的标题
            timeout: 通知显示时间(秒)
        """
        if not self.enabled:
            return

        final_title = title or self.TITLES.get(notification_type, self.APP_NAME)

        # 调用回调
        for callback in self._callbacks:
            try:
                callback(notification_type, final_title, message)
            except Exception:
                pass

        # 发送系统通知
        try:
            notification.notify(
                title=final_title,
                message=message,
                app_name=self.APP_NAME,
                app_icon=self.ICON_PATH,
                timeout=timeout,
            )
        except Exception:
            # 通知失败时静默处理
            pass

    def notify_flow_enter(self, flow_level: int = 1) -> None:
        """通知进入心流状态.

        Args:
            flow_level: 心流等级
        """
        messages = {
            1: "你已进入心流状态！保持专注 🎯",
            2: "心流加深！效率提升中 🚀",
            3: "深度心流！能量加成最大化 ⚡",
        }
        message = messages.get(flow_level, messages[1])
        self.notify(message, NotificationType.FLOW_ENTER)

    def notify_flow_exit(self, duration_minutes: int, energy_earned: float) -> None:
        """通知心流状态结束.

        Args:
            duration_minutes: 心流持续时间(分钟)
            energy_earned: 获得的能量
        """
        message = f"心流持续 {duration_minutes} 分钟，获得 {energy_earned:.1f} 能量"
        self.notify(message, NotificationType.FLOW_EXIT)

    def notify_achievement(self, achievement_name: str, description: str) -> None:
        """通知成就解锁.

        Args:
            achievement_name: 成就名称
            description: 成就描述
        """
        message = f"{achievement_name}\n{description}"
        self.notify(message, NotificationType.ACHIEVEMENT, timeout=10)

    def notify_energy_gain(self, amount: float, source: str = "编码") -> None:
        """通知能量获取.

        Args:
            amount: 获得的能量
            source: 能量来源
        """
        message = f"通过{source}获得 {amount:.1f} 能量"
        self.notify(message, NotificationType.ENERGY)

    def notify_activity_start(self) -> None:
        """通知活动开始追踪."""
        self.notify("开始追踪编码活动", NotificationType.INFO)

    def notify_activity_end(self, duration_minutes: int, energy_earned: float) -> None:
        """通知活动结束.

        Args:
            duration_minutes: 活动持续时间(分钟)
            energy_earned: 获得的能量
        """
        message = f"编码 {duration_minutes} 分钟，获得 {energy_earned:.1f} 能量"
        self.notify(message, NotificationType.SUCCESS)

    def notify_service_status(self, connected: bool) -> None:
        """通知服务连接状态.

        Args:
            connected: 是否已连接
        """
        if connected:
            self.notify("已连接到 VibeHub 服务", NotificationType.SUCCESS)
        else:
            self.notify("无法连接到 VibeHub 服务", NotificationType.WARNING)
