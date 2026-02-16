"""自动启动管理器."""

import os
import platform
import sys
from pathlib import Path


class AutoStartManager:
    """自动启动管理器，支持 Windows 和 macOS."""

    APP_NAME = "HappyVibeMonitor"

    def __init__(self) -> None:
        """初始化管理器."""
        self._system = platform.system()

    @property
    def is_supported(self) -> bool:
        """检查当前系统是否支持自动启动."""
        return self._system in ("Windows", "Darwin")

    @property
    def is_enabled(self) -> bool:
        """检查自动启动是否已启用."""
        if self._system == "Windows":
            return self._check_windows_autostart()
        elif self._system == "Darwin":
            return self._check_macos_autostart()
        return False

    def enable(self) -> bool:
        """启用自动启动.

        Returns:
            是否成功启用
        """
        if self._system == "Windows":
            return self._enable_windows_autostart()
        elif self._system == "Darwin":
            return self._enable_macos_autostart()
        return False

    def disable(self) -> bool:
        """禁用自动启动.

        Returns:
            是否成功禁用
        """
        if self._system == "Windows":
            return self._disable_windows_autostart()
        elif self._system == "Darwin":
            return self._disable_macos_autostart()
        return False

    def _get_executable_path(self) -> str:
        """获取可执行文件路径."""
        if getattr(sys, "frozen", False):
            return sys.executable
        return sys.executable

    def _get_script_path(self) -> str:
        """获取启动脚本路径."""
        if getattr(sys, "frozen", False):
            return sys.executable
        return f'"{sys.executable}" -m src.main'

    # Windows 实现
    def _get_windows_startup_path(self) -> Path:
        """获取 Windows 启动文件夹路径."""
        startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup / f"{self.APP_NAME}.bat"

    def _check_windows_autostart(self) -> bool:
        """检查 Windows 自动启动状态."""
        return self._get_windows_startup_path().exists()

    def _enable_windows_autostart(self) -> bool:
        """启用 Windows 自动启动."""
        try:
            startup_path = self._get_windows_startup_path()
            startup_path.parent.mkdir(parents=True, exist_ok=True)

            script = self._get_script_path()
            batch_content = f'@echo off\nstart "" {script}\n'

            startup_path.write_text(batch_content, encoding="utf-8")
            return True
        except OSError:
            return False

    def _disable_windows_autostart(self) -> bool:
        """禁用 Windows 自动启动."""
        try:
            startup_path = self._get_windows_startup_path()
            if startup_path.exists():
                startup_path.unlink()
            return True
        except OSError:
            return False

    # macOS 实现
    def _get_macos_plist_path(self) -> Path:
        """获取 macOS LaunchAgent plist 路径."""
        return Path.home() / "Library" / "LaunchAgents" / "com.happyvibe.monitor.plist"

    def _check_macos_autostart(self) -> bool:
        """检查 macOS 自动启动状态."""
        return self._get_macos_plist_path().exists()

    def _enable_macos_autostart(self) -> bool:
        """启用 macOS 自动启动."""
        try:
            plist_path = self._get_macos_plist_path()
            plist_path.parent.mkdir(parents=True, exist_ok=True)

            executable = self._get_executable_path()

            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.happyvibe.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>{executable}</string>
        <string>-m</string>
        <string>src.main</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""
            plist_path.write_text(plist_content, encoding="utf-8")
            return True
        except OSError:
            return False

    def _disable_macos_autostart(self) -> bool:
        """禁用 macOS 自动启动."""
        try:
            plist_path = self._get_macos_plist_path()
            if plist_path.exists():
                plist_path.unlink()
            return True
        except OSError:
            return False
