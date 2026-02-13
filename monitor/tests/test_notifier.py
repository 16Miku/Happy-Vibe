"""通知系统测试."""

from unittest.mock import MagicMock, patch

import pytest

from src.notify.notifier import Notifier, NotificationType


class TestNotificationType:
    """NotificationType 枚举测试."""

    def test_notification_types(self):
        """测试通知类型值."""
        assert NotificationType.INFO.value == "info"
        assert NotificationType.SUCCESS.value == "success"
        assert NotificationType.WARNING.value == "warning"
        assert NotificationType.ACHIEVEMENT.value == "achievement"
        assert NotificationType.FLOW_ENTER.value == "flow_enter"
        assert NotificationType.FLOW_EXIT.value == "flow_exit"
        assert NotificationType.ENERGY.value == "energy"


class TestNotifier:
    """Notifier 测试类."""

    @pytest.fixture
    def notifier(self):
        """创建测试通知器."""
        return Notifier(enabled=True)

    @pytest.fixture
    def disabled_notifier(self):
        """创建禁用的通知器."""
        return Notifier(enabled=False)

    def test_init_enabled(self, notifier):
        """测试初始化（启用）."""
        assert notifier.enabled is True

    def test_init_disabled(self, disabled_notifier):
        """测试初始化（禁用）."""
        assert disabled_notifier.enabled is False

    def test_titles_mapping(self, notifier):
        """测试标题映射."""
        assert NotificationType.INFO in notifier.TITLES
        assert NotificationType.SUCCESS in notifier.TITLES
        assert NotificationType.ACHIEVEMENT in notifier.TITLES

    def test_add_callback(self, notifier):
        """测试添加回调."""
        callback = MagicMock()
        notifier.add_callback(callback)
        assert callback in notifier._callbacks

    def test_remove_callback(self, notifier):
        """测试移除回调."""
        callback = MagicMock()
        notifier.add_callback(callback)
        notifier.remove_callback(callback)
        assert callback not in notifier._callbacks

    def test_remove_nonexistent_callback(self, notifier):
        """测试移除不存在的回调."""
        callback = MagicMock()
        notifier.remove_callback(callback)  # 不应抛出异常

    @patch("src.notify.notifier.notification")
    def test_notify_when_enabled(self, mock_notification, notifier):
        """测试启用时发送通知."""
        notifier.notify("测试消息", NotificationType.INFO)
        mock_notification.notify.assert_called_once()

    @patch("src.notify.notifier.notification")
    def test_notify_when_disabled(self, mock_notification, disabled_notifier):
        """测试禁用时不发送通知."""
        disabled_notifier.notify("测试消息", NotificationType.INFO)
        mock_notification.notify.assert_not_called()

    @patch("src.notify.notifier.notification")
    def test_notify_with_custom_title(self, mock_notification, notifier):
        """测试自定义标题."""
        notifier.notify("测试消息", NotificationType.INFO, title="自定义标题")
        call_args = mock_notification.notify.call_args
        assert call_args.kwargs["title"] == "自定义标题"

    @patch("src.notify.notifier.notification")
    def test_notify_calls_callbacks(self, mock_notification, notifier):
        """测试通知调用回调."""
        callback = MagicMock()
        notifier.add_callback(callback)
        notifier.notify("测试消息", NotificationType.INFO)
        callback.assert_called_once()

    @patch("src.notify.notifier.notification")
    def test_notify_flow_enter(self, mock_notification, notifier):
        """测试心流进入通知."""
        notifier.notify_flow_enter(flow_level=1)
        mock_notification.notify.assert_called_once()
        call_args = mock_notification.notify.call_args
        assert "心流" in call_args.kwargs["message"]

    @patch("src.notify.notifier.notification")
    def test_notify_flow_enter_level_2(self, mock_notification, notifier):
        """测试心流进入通知（等级2）."""
        notifier.notify_flow_enter(flow_level=2)
        call_args = mock_notification.notify.call_args
        assert "加深" in call_args.kwargs["message"]

    @patch("src.notify.notifier.notification")
    def test_notify_flow_exit(self, mock_notification, notifier):
        """测试心流退出通知."""
        notifier.notify_flow_exit(duration_minutes=30, energy_earned=100.5)
        mock_notification.notify.assert_called_once()
        call_args = mock_notification.notify.call_args
        assert "30" in call_args.kwargs["message"]
        assert "100.5" in call_args.kwargs["message"]

    @patch("src.notify.notifier.notification")
    def test_notify_achievement(self, mock_notification, notifier):
        """测试成就解锁通知."""
        notifier.notify_achievement("首次编码", "完成第一次编码活动")
        mock_notification.notify.assert_called_once()
        call_args = mock_notification.notify.call_args
        assert "首次编码" in call_args.kwargs["message"]

    @patch("src.notify.notifier.notification")
    def test_notify_energy_gain(self, mock_notification, notifier):
        """测试能量获取通知."""
        notifier.notify_energy_gain(50.0, source="编码")
        mock_notification.notify.assert_called_once()
        call_args = mock_notification.notify.call_args
        assert "50.0" in call_args.kwargs["message"]

    @patch("src.notify.notifier.notification")
    def test_notify_activity_start(self, mock_notification, notifier):
        """测试活动开始通知."""
        notifier.notify_activity_start()
        mock_notification.notify.assert_called_once()

    @patch("src.notify.notifier.notification")
    def test_notify_activity_end(self, mock_notification, notifier):
        """测试活动结束通知."""
        notifier.notify_activity_end(duration_minutes=60, energy_earned=200.0)
        mock_notification.notify.assert_called_once()
        call_args = mock_notification.notify.call_args
        assert "60" in call_args.kwargs["message"]
        assert "200.0" in call_args.kwargs["message"]

    @patch("src.notify.notifier.notification")
    def test_notify_service_connected(self, mock_notification, notifier):
        """测试服务连接通知."""
        notifier.notify_service_status(connected=True)
        mock_notification.notify.assert_called_once()
        call_args = mock_notification.notify.call_args
        assert "连接" in call_args.kwargs["message"]

    @patch("src.notify.notifier.notification")
    def test_notify_service_disconnected(self, mock_notification, notifier):
        """测试服务断开通知."""
        notifier.notify_service_status(connected=False)
        mock_notification.notify.assert_called_once()
        call_args = mock_notification.notify.call_args
        assert "无法连接" in call_args.kwargs["message"]

    @patch("src.notify.notifier.notification")
    def test_notify_handles_exception(self, mock_notification, notifier):
        """测试通知异常处理."""
        mock_notification.notify.side_effect = Exception("通知失败")
        # 不应抛出异常
        notifier.notify("测试消息", NotificationType.INFO)

    def test_callback_exception_handled(self, notifier):
        """测试回调异常处理."""
        bad_callback = MagicMock(side_effect=Exception("回调错误"))
        notifier.add_callback(bad_callback)

        with patch("src.notify.notifier.notification"):
            # 不应抛出异常
            notifier.notify("测试消息", NotificationType.INFO)
