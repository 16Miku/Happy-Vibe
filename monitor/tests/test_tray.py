"""系统托盘模块测试."""

from unittest.mock import MagicMock, patch

import pytest

from src.tray.tray_icon import TrayIcon, TrayStatus


class TestTrayStatus:
    """TrayStatus 枚举测试."""

    def test_status_values(self):
        """测试状态值."""
        assert TrayStatus.IDLE.value == "idle"
        assert TrayStatus.TRACKING.value == "tracking"
        assert TrayStatus.FLOW.value == "flow"
        assert TrayStatus.DISCONNECTED.value == "disconnected"


class TestTrayIcon:
    """TrayIcon 测试类."""

    @pytest.fixture
    def tray(self):
        """创建测试托盘."""
        return TrayIcon()

    def test_init(self, tray):
        """测试初始化."""
        assert tray._status == TrayStatus.DISCONNECTED
        assert tray._is_tracking is False
        assert tray._icon is None

    def test_status_colors(self, tray):
        """测试状态颜色映射."""
        assert TrayStatus.IDLE in tray.STATUS_COLORS
        assert TrayStatus.TRACKING in tray.STATUS_COLORS
        assert TrayStatus.FLOW in tray.STATUS_COLORS
        assert TrayStatus.DISCONNECTED in tray.STATUS_COLORS

    def test_set_callbacks(self, tray):
        """测试设置回调."""
        start_cb = MagicMock()
        stop_cb = MagicMock()
        game_cb = MagicMock()
        settings_cb = MagicMock()
        quit_cb = MagicMock()

        tray.set_callbacks(
            on_start_tracking=start_cb,
            on_stop_tracking=stop_cb,
            on_open_game=game_cb,
            on_open_settings=settings_cb,
            on_quit=quit_cb,
        )

        assert tray._on_start_tracking is start_cb
        assert tray._on_stop_tracking is stop_cb
        assert tray._on_open_game is game_cb
        assert tray._on_open_settings is settings_cb
        assert tray._on_quit is quit_cb

    def test_create_icon_image(self, tray):
        """测试创建图标图像."""
        image = tray._create_icon_image("#FF0000", size=64)

        assert image is not None
        assert image.size == (64, 64)
        assert image.mode == "RGBA"

    def test_get_status_image(self, tray):
        """测试获取状态图像."""
        tray._status = TrayStatus.TRACKING
        image = tray._get_status_image()

        assert image is not None
        assert image.size == (64, 64)

    def test_set_status(self, tray):
        """测试设置状态."""
        tray._icon = MagicMock()

        tray.set_status(TrayStatus.FLOW)

        assert tray._status == TrayStatus.FLOW
        assert tray._icon.icon is not None

    def test_set_tracking(self, tray):
        """测试设置追踪状态."""
        tray._icon = MagicMock()

        tray.set_tracking(True)
        assert tray._is_tracking is True

        tray.set_tracking(False)
        assert tray._is_tracking is False

    def test_toggle_tracking_start(self, tray):
        """测试切换追踪（开始）."""
        start_cb = MagicMock()
        tray.set_callbacks(on_start_tracking=start_cb)
        tray._is_tracking = False

        tray._toggle_tracking()

        assert tray._is_tracking is True
        start_cb.assert_called_once()

    def test_toggle_tracking_stop(self, tray):
        """测试切换追踪（停止）."""
        stop_cb = MagicMock()
        tray.set_callbacks(on_stop_tracking=stop_cb)
        tray._is_tracking = True

        tray._toggle_tracking()

        assert tray._is_tracking is False
        stop_cb.assert_called_once()

    def test_handle_open_game(self, tray):
        """测试打开游戏处理."""
        game_cb = MagicMock()
        tray.set_callbacks(on_open_game=game_cb)

        tray._handle_open_game()

        game_cb.assert_called_once()

    def test_handle_open_settings(self, tray):
        """测试打开设置处理."""
        settings_cb = MagicMock()
        tray.set_callbacks(on_open_settings=settings_cb)

        tray._handle_open_settings()

        settings_cb.assert_called_once()

    def test_handle_quit(self, tray):
        """测试退出处理."""
        quit_cb = MagicMock()
        tray.set_callbacks(on_quit=quit_cb)
        tray._icon = MagicMock()

        tray._handle_quit()

        quit_cb.assert_called_once()

    def test_get_tooltip(self, tray):
        """测试获取提示文本."""
        tray._status = TrayStatus.TRACKING
        tooltip = tray._get_tooltip()

        assert "Happy Vibe" in tooltip
        assert "追踪中" in tooltip

    def test_get_menu(self, tray):
        """测试获取菜单."""
        menu = tray._get_menu()
        assert menu is not None

    def test_is_running_false(self, tray):
        """测试运行状态（未运行）."""
        assert tray.is_running is False

    def test_stop_when_not_running(self, tray):
        """测试停止（未运行时）."""
        tray.stop()  # 不应抛出异常

    def test_stop_when_running(self, tray):
        """测试停止（运行时）."""
        mock_icon = MagicMock()
        tray._icon = mock_icon

        tray.stop()

        mock_icon.stop.assert_called_once()
        assert tray._icon is None
