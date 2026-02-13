"""系统托盘图标模块."""

import asyncio
import threading
from enum import Enum
from io import BytesIO
from typing import Callable

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem


class TrayStatus(Enum):
    """托盘状态."""

    IDLE = "idle"  # 空闲
    TRACKING = "tracking"  # 追踪中
    FLOW = "flow"  # 心流状态
    DISCONNECTED = "disconnected"  # 未连接


class TrayIcon:
    """系统托盘图标管理器."""

    # 状态对应的颜色
    STATUS_COLORS = {
        TrayStatus.IDLE: "#808080",  # 灰色
        TrayStatus.TRACKING: "#4CAF50",  # 绿色
        TrayStatus.FLOW: "#2196F3",  # 蓝色
        TrayStatus.DISCONNECTED: "#F44336",  # 红色
    }

    def __init__(self) -> None:
        """初始化托盘图标."""
        self._icon: Icon | None = None
        self._status = TrayStatus.DISCONNECTED
        self._is_tracking = False
        self._thread: threading.Thread | None = None

        # 回调函数
        self._on_start_tracking: Callable[[], None] | None = None
        self._on_stop_tracking: Callable[[], None] | None = None
        self._on_open_game: Callable[[], None] | None = None
        self._on_open_settings: Callable[[], None] | None = None
        self._on_quit: Callable[[], None] | None = None

    def set_callbacks(
        self,
        on_start_tracking: Callable[[], None] | None = None,
        on_stop_tracking: Callable[[], None] | None = None,
        on_open_game: Callable[[], None] | None = None,
        on_open_settings: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
    ) -> None:
        """设置回调函数."""
        self._on_start_tracking = on_start_tracking
        self._on_stop_tracking = on_stop_tracking
        self._on_open_game = on_open_game
        self._on_open_settings = on_open_settings
        self._on_quit = on_quit

    def _create_icon_image(self, color: str, size: int = 64) -> Image.Image:
        """创建托盘图标图像.

        Args:
            color: 图标颜色
            size: 图标大小

        Returns:
            PIL Image 对象
        """
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # 绘制圆形背景
        margin = 4
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=color,
        )

        # 绘制 "V" 字母
        center = size // 2
        v_color = "#FFFFFF"
        points = [
            (center - 12, center - 8),
            (center, center + 10),
            (center + 12, center - 8),
        ]
        draw.line(points[:2], fill=v_color, width=4)
        draw.line(points[1:], fill=v_color, width=4)

        return image

    def _get_status_image(self) -> Image.Image:
        """获取当前状态对应的图标图像."""
        color = self.STATUS_COLORS.get(self._status, "#808080")
        return self._create_icon_image(color)

    def _get_menu(self) -> Menu:
        """创建托盘菜单."""
        return Menu(
            MenuItem(
                "开始追踪" if not self._is_tracking else "停止追踪",
                self._toggle_tracking,
            ),
            Menu.SEPARATOR,
            MenuItem("打开游戏", self._handle_open_game),
            MenuItem("设置", self._handle_open_settings),
            Menu.SEPARATOR,
            MenuItem("退出", self._handle_quit),
        )

    def _toggle_tracking(self, icon: Icon | None = None, item: MenuItem | None = None) -> None:
        """切换追踪状态."""
        if self._is_tracking:
            self._is_tracking = False
            if self._on_stop_tracking:
                self._on_stop_tracking()
        else:
            self._is_tracking = True
            if self._on_start_tracking:
                self._on_start_tracking()
        self._update_menu()

    def _handle_open_game(self, icon: Icon | None = None, item: MenuItem | None = None) -> None:
        """处理打开游戏."""
        if self._on_open_game:
            self._on_open_game()

    def _handle_open_settings(self, icon: Icon | None = None, item: MenuItem | None = None) -> None:
        """处理打开设置."""
        if self._on_open_settings:
            self._on_open_settings()

    def _handle_quit(self, icon: Icon | None = None, item: MenuItem | None = None) -> None:
        """处理退出."""
        if self._on_quit:
            self._on_quit()
        self.stop()

    def _update_menu(self) -> None:
        """更新菜单."""
        if self._icon:
            self._icon.menu = self._get_menu()

    def set_status(self, status: TrayStatus) -> None:
        """设置托盘状态.

        Args:
            status: 新状态
        """
        self._status = status
        if self._icon:
            self._icon.icon = self._get_status_image()

    def set_tracking(self, is_tracking: bool) -> None:
        """设置追踪状态.

        Args:
            is_tracking: 是否正在追踪
        """
        self._is_tracking = is_tracking
        self._update_menu()

    def _get_tooltip(self) -> str:
        """获取托盘提示文本."""
        status_text = {
            TrayStatus.IDLE: "空闲",
            TrayStatus.TRACKING: "追踪中",
            TrayStatus.FLOW: "心流状态",
            TrayStatus.DISCONNECTED: "未连接",
        }
        return f"Happy Vibe - {status_text.get(self._status, '未知')}"

    def run(self) -> None:
        """运行托盘图标（阻塞）."""
        self._icon = Icon(
            name="Happy Vibe",
            icon=self._get_status_image(),
            title=self._get_tooltip(),
            menu=self._get_menu(),
        )
        self._icon.run()

    def run_detached(self) -> None:
        """在后台线程运行托盘图标."""
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止托盘图标."""
        if self._icon:
            self._icon.stop()
            self._icon = None

    @property
    def is_running(self) -> bool:
        """检查托盘是否正在运行."""
        return self._icon is not None and self._icon.visible
