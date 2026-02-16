"""自动启动模块测试."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.autostart.manager import AutoStartManager


class TestAutoStartManager:
    """AutoStartManager 测试类."""

    @pytest.fixture
    def manager(self):
        """创建测试管理器."""
        return AutoStartManager()

    def test_app_name(self, manager):
        """测试应用名称."""
        assert manager.APP_NAME == "HappyVibeMonitor"

    @patch("platform.system")
    def test_is_supported_windows(self, mock_system, manager):
        """测试 Windows 支持."""
        mock_system.return_value = "Windows"
        manager._system = "Windows"
        assert manager.is_supported is True

    @patch("platform.system")
    def test_is_supported_macos(self, mock_system, manager):
        """测试 macOS 支持."""
        mock_system.return_value = "Darwin"
        manager._system = "Darwin"
        assert manager.is_supported is True

    @patch("platform.system")
    def test_is_supported_linux(self, mock_system, manager):
        """测试 Linux 不支持."""
        mock_system.return_value = "Linux"
        manager._system = "Linux"
        assert manager.is_supported is False

    def test_is_enabled_unsupported_system(self, manager):
        """测试不支持系统的启用状态."""
        manager._system = "Linux"
        assert manager.is_enabled is False

    def test_enable_unsupported_system(self, manager):
        """测试不支持系统的启用操作."""
        manager._system = "Linux"
        assert manager.enable() is False

    def test_disable_unsupported_system(self, manager):
        """测试不支持系统的禁用操作."""
        manager._system = "Linux"
        assert manager.disable() is False


class TestAutoStartManagerWindows:
    """Windows 自动启动测试."""

    @pytest.fixture
    def manager(self):
        """创建 Windows 测试管理器."""
        m = AutoStartManager()
        m._system = "Windows"
        return m

    def test_get_windows_startup_path(self, manager):
        """测试获取 Windows 启动路径."""
        with patch.dict("os.environ", {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
            path = manager._get_windows_startup_path()
            assert "Startup" in str(path)
            assert manager.APP_NAME in str(path)

    def test_check_windows_autostart_not_exists(self, manager):
        """测试检查 Windows 自动启动（不存在）."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(manager, "_get_windows_startup_path", return_value=Path(tmpdir) / "test.bat"):
                assert manager._check_windows_autostart() is False

    def test_check_windows_autostart_exists(self, manager):
        """测试检查 Windows 自动启动（存在）."""
        with tempfile.TemporaryDirectory() as tmpdir:
            startup_path = Path(tmpdir) / "test.bat"
            startup_path.write_text("@echo off")
            with patch.object(manager, "_get_windows_startup_path", return_value=startup_path):
                assert manager._check_windows_autostart() is True

    def test_enable_windows_autostart(self, manager):
        """测试启用 Windows 自动启动."""
        with tempfile.TemporaryDirectory() as tmpdir:
            startup_path = Path(tmpdir) / "Startup" / "test.bat"
            with patch.object(manager, "_get_windows_startup_path", return_value=startup_path):
                result = manager._enable_windows_autostart()
                assert result is True
                assert startup_path.exists()

    def test_disable_windows_autostart(self, manager):
        """测试禁用 Windows 自动启动."""
        with tempfile.TemporaryDirectory() as tmpdir:
            startup_path = Path(tmpdir) / "test.bat"
            startup_path.write_text("@echo off")
            with patch.object(manager, "_get_windows_startup_path", return_value=startup_path):
                result = manager._disable_windows_autostart()
                assert result is True
                assert not startup_path.exists()

    def test_disable_windows_autostart_not_exists(self, manager):
        """测试禁用不存在的 Windows 自动启动."""
        with tempfile.TemporaryDirectory() as tmpdir:
            startup_path = Path(tmpdir) / "nonexistent.bat"
            with patch.object(manager, "_get_windows_startup_path", return_value=startup_path):
                result = manager._disable_windows_autostart()
                assert result is True

    def test_is_enabled_windows(self, manager):
        """测试 Windows 启用状态检查."""
        with tempfile.TemporaryDirectory() as tmpdir:
            startup_path = Path(tmpdir) / "test.bat"
            startup_path.write_text("@echo off")
            with patch.object(manager, "_get_windows_startup_path", return_value=startup_path):
                assert manager.is_enabled is True

    def test_enable_windows(self, manager):
        """测试 Windows 启用."""
        with tempfile.TemporaryDirectory() as tmpdir:
            startup_path = Path(tmpdir) / "test.bat"
            with patch.object(manager, "_get_windows_startup_path", return_value=startup_path):
                result = manager.enable()
                assert result is True

    def test_disable_windows(self, manager):
        """测试 Windows 禁用."""
        with tempfile.TemporaryDirectory() as tmpdir:
            startup_path = Path(tmpdir) / "test.bat"
            startup_path.write_text("@echo off")
            with patch.object(manager, "_get_windows_startup_path", return_value=startup_path):
                result = manager.disable()
                assert result is True


class TestAutoStartManagerMacOS:
    """macOS 自动启动测试."""

    @pytest.fixture
    def manager(self):
        """创建 macOS 测试管理器."""
        m = AutoStartManager()
        m._system = "Darwin"
        return m

    def test_get_macos_plist_path(self, manager):
        """测试获取 macOS plist 路径."""
        path = manager._get_macos_plist_path()
        assert "LaunchAgents" in str(path)
        assert "plist" in str(path)

    def test_check_macos_autostart_not_exists(self, manager):
        """测试检查 macOS 自动启动（不存在）."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(manager, "_get_macos_plist_path", return_value=Path(tmpdir) / "test.plist"):
                assert manager._check_macos_autostart() is False

    def test_check_macos_autostart_exists(self, manager):
        """测试检查 macOS 自动启动（存在）."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "test.plist"
            plist_path.write_text("<plist></plist>")
            with patch.object(manager, "_get_macos_plist_path", return_value=plist_path):
                assert manager._check_macos_autostart() is True

    def test_enable_macos_autostart(self, manager):
        """测试启用 macOS 自动启动."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "LaunchAgents" / "test.plist"
            with patch.object(manager, "_get_macos_plist_path", return_value=plist_path):
                result = manager._enable_macos_autostart()
                assert result is True
                assert plist_path.exists()
                content = plist_path.read_text()
                assert "com.happyvibe.monitor" in content

    def test_disable_macos_autostart(self, manager):
        """测试禁用 macOS 自动启动."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "test.plist"
            plist_path.write_text("<plist></plist>")
            with patch.object(manager, "_get_macos_plist_path", return_value=plist_path):
                result = manager._disable_macos_autostart()
                assert result is True
                assert not plist_path.exists()

    def test_disable_macos_autostart_not_exists(self, manager):
        """测试禁用不存在的 macOS 自动启动."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "nonexistent.plist"
            with patch.object(manager, "_get_macos_plist_path", return_value=plist_path):
                result = manager._disable_macos_autostart()
                assert result is True

    def test_is_enabled_macos(self, manager):
        """测试 macOS 启用状态检查."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "test.plist"
            plist_path.write_text("<plist></plist>")
            with patch.object(manager, "_get_macos_plist_path", return_value=plist_path):
                assert manager.is_enabled is True

    def test_enable_macos(self, manager):
        """测试 macOS 启用."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "test.plist"
            with patch.object(manager, "_get_macos_plist_path", return_value=plist_path):
                result = manager.enable()
                assert result is True

    def test_disable_macos(self, manager):
        """测试 macOS 禁用."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plist_path = Path(tmpdir) / "test.plist"
            plist_path.write_text("<plist></plist>")
            with patch.object(manager, "_get_macos_plist_path", return_value=plist_path):
                result = manager.disable()
                assert result is True
