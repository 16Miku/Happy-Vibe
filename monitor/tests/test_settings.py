"""配置管理测试."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config.settings import Settings


class TestSettings:
    """Settings 测试类."""

    @pytest.fixture
    def settings(self):
        """创建测试配置."""
        return Settings()

    def test_default_values(self, settings):
        """测试默认值."""
        assert settings.vibehub_host == "127.0.0.1"
        assert settings.vibehub_port == 8765
        assert settings.notifications_enabled is True
        assert settings.auto_track is True
        assert settings.language == "zh"

    def test_vibehub_url(self, settings):
        """测试 VibeHub URL 属性."""
        assert settings.vibehub_url == "http://127.0.0.1:8765"

    def test_vibehub_url_custom(self):
        """测试自定义 VibeHub URL."""
        settings = Settings(vibehub_host="192.168.1.100", vibehub_port=9000)
        assert settings.vibehub_url == "http://192.168.1.100:9000"

    def test_notification_settings(self, settings):
        """测试通知设置."""
        assert settings.notification_sound is True
        assert settings.notify_on_flow_enter is True
        assert settings.notify_on_flow_exit is True
        assert settings.notify_on_achievement is True
        assert settings.notify_on_energy_gain is False

    def test_tracking_settings(self, settings):
        """测试追踪设置."""
        assert settings.track_interval_seconds == 30
        assert settings.idle_timeout_minutes == 5

    def test_ui_settings(self, settings):
        """测试界面设置."""
        assert settings.start_minimized is True
        assert settings.auto_start is False

    def test_config_dir(self, settings):
        """测试配置目录."""
        config_dir = settings.config_dir
        assert config_dir.exists()
        assert config_dir.name == ".happy-vibe"

    def test_save_and_load(self):
        """测试保存和加载配置."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建临时配置目录
            config_dir = Path(tmpdir) / ".happy-vibe"
            config_dir.mkdir()

            with patch.object(Settings, "config_dir", config_dir):
                # 创建并保存配置
                settings = Settings(
                    vibehub_host="192.168.1.50",
                    vibehub_port=9999,
                    notifications_enabled=False,
                    auto_track=False,
                )
                settings.save()

                # 验证配置文件已创建
                config_file = config_dir / "monitor.env"
                assert config_file.exists()

                # 读取配置文件内容
                content = config_file.read_text(encoding="utf-8")
                assert "HAPPY_VIBE_VIBEHUB_HOST=192.168.1.50" in content
                assert "HAPPY_VIBE_VIBEHUB_PORT=9999" in content

    def test_load_default_when_no_file(self):
        """测试无配置文件时加载默认值."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                settings = Settings.load()
                assert settings.vibehub_host == "127.0.0.1"

    def test_custom_settings(self):
        """测试自定义设置."""
        settings = Settings(
            vibehub_host="localhost",
            vibehub_port=8000,
            notifications_enabled=False,
            notification_sound=False,
            notify_on_flow_enter=False,
            notify_on_flow_exit=False,
            notify_on_achievement=False,
            notify_on_energy_gain=True,
            auto_track=False,
            track_interval_seconds=60,
            idle_timeout_minutes=10,
            language="en",
            start_minimized=False,
            auto_start=True,
        )

        assert settings.vibehub_host == "localhost"
        assert settings.vibehub_port == 8000
        assert settings.notifications_enabled is False
        assert settings.notification_sound is False
        assert settings.notify_on_energy_gain is True
        assert settings.track_interval_seconds == 60
        assert settings.language == "en"
        assert settings.auto_start is True

    def test_language_literal(self):
        """测试语言字面量类型."""
        settings_zh = Settings(language="zh")
        assert settings_zh.language == "zh"

        settings_en = Settings(language="en")
        assert settings_en.language == "en"
