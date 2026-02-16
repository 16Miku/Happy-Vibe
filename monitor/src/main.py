"""Happy Vibe 桌面监控器主程序."""

import asyncio
import contextlib
import signal
from typing import Any

from src.api import VibeHubClient
from src.config import Settings
from src.notify import NotificationType, Notifier
from src.tray import TrayIcon
from src.tray.tray_icon import TrayStatus
from src.watcher import ClaudeLogWatcher, LogEvent, LogEventType


class Monitor:
    """桌面监控器主类."""

    def __init__(self, settings: Settings | None = None) -> None:
        """初始化监控器.

        Args:
            settings: 配置设置，默认从文件加载
        """
        self.settings = settings or Settings.load()
        self.client = VibeHubClient(self.settings.vibehub_url)
        self.notifier = Notifier(enabled=self.settings.notifications_enabled)
        self.tray = TrayIcon()
        self.log_watcher = ClaudeLogWatcher()

        self._running = False
        self._tracking = False
        self._last_flow_state = False
        self._track_task: asyncio.Task[None] | None = None
        self._pending_updates: dict[str, Any] = {
            "lines_added": 0,
            "lines_deleted": 0,
            "files_changed": 0,
        }

    def _setup_tray(self) -> None:
        """设置托盘回调."""
        self.tray.set_callbacks(
            on_start_tracking=self._on_start_tracking,
            on_stop_tracking=self._on_stop_tracking,
            on_open_game=self._on_open_game,
            on_open_settings=self._on_open_settings,
            on_quit=self._on_quit,
        )

    def _on_start_tracking(self) -> None:
        """开始追踪回调."""
        asyncio.create_task(self._start_tracking())

    def _on_stop_tracking(self) -> None:
        """停止追踪回调."""
        asyncio.create_task(self._stop_tracking())

    def _on_open_game(self) -> None:
        """打开游戏回调."""
        self.notifier.notify("游戏客户端尚未实现", NotificationType.WARNING)

    def _on_open_settings(self) -> None:
        """打开设置回调."""
        pass

    def _on_quit(self) -> None:
        """退出回调."""
        self._running = False

    def _on_log_event(self, event: LogEvent) -> None:
        """处理日志事件回调."""
        if event.event_type == LogEventType.SESSION_START:
            if not self._tracking:
                asyncio.create_task(self._start_tracking())
        elif event.event_type == LogEventType.SESSION_END:
            if self._tracking:
                asyncio.create_task(self._stop_tracking())
        elif event.event_type == LogEventType.FILE_EDIT or event.event_type == LogEventType.FILE_CREATE:
            self._pending_updates["files_changed"] += 1

    async def _start_tracking(self) -> None:
        """开始活动追踪."""
        if self._tracking:
            return

        result = await self.client.start_activity("coding")
        if result:
            self._tracking = True
            self.tray.set_status(TrayStatus.TRACKING)
            self.tray.set_tracking(True)
            self.notifier.notify_activity_start()

            # 启动追踪循环
            if self._track_task is None or self._track_task.done():
                self._track_task = asyncio.create_task(self._tracking_loop())

    async def _stop_tracking(self) -> None:
        """停止活动追踪."""
        if not self._tracking:
            return

        result = await self.client.end_activity()
        self._tracking = False
        self.tray.set_status(TrayStatus.IDLE)
        self.tray.set_tracking(False)

        if result:
            duration = result.get("duration_seconds", 0) // 60
            energy = result.get("energy_earned", 0)
            self.notifier.notify_activity_end(duration, energy)

        # 取消追踪任务
        if self._track_task and not self._track_task.done():
            self._track_task.cancel()

    async def _tracking_loop(self) -> None:
        """追踪循环，定期更新状态."""
        while self._tracking and self._running:
            try:
                # 更新活动
                await self.client.update_activity()

                # 检查心流状态
                flow_status = await self.client.get_flow_status()
                if flow_status.in_flow and not self._last_flow_state:
                    # 进入心流
                    self.tray.set_status(TrayStatus.FLOW)
                    if self.settings.notify_on_flow_enter:
                        self.notifier.notify_flow_enter(flow_status.flow_level)
                elif not flow_status.in_flow and self._last_flow_state:
                    # 退出心流
                    self.tray.set_status(TrayStatus.TRACKING)
                    if self.settings.notify_on_flow_exit:
                        self.notifier.notify_flow_exit(
                            flow_status.flow_duration_seconds // 60,
                            0,  # 能量在结束时计算
                        )
                self._last_flow_state = flow_status.in_flow

                await asyncio.sleep(self.settings.track_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception:
                # 连接错误时继续尝试
                await asyncio.sleep(self.settings.track_interval_seconds)

    async def _check_service(self) -> bool:
        """检查 VibeHub 服务状态."""
        connected = await self.client.health_check()
        if connected:
            self.tray.set_status(TrayStatus.IDLE)
        else:
            self.tray.set_status(TrayStatus.DISCONNECTED)
        return connected

    async def _service_monitor_loop(self) -> None:
        """服务监控循环."""
        last_connected = False
        while self._running:
            connected = await self._check_service()
            if connected != last_connected:
                self.notifier.notify_service_status(connected)
                last_connected = connected

                # 自动开始追踪
                if connected and self.settings.auto_track and not self._tracking:
                    await self._start_tracking()

            await asyncio.sleep(30)  # 每 30 秒检查一次

    async def run_async(self) -> None:
        """异步运行监控器."""
        self._running = True
        self._setup_tray()

        # 启动日志监听
        self.log_watcher.add_callback(self._on_log_event)
        self.log_watcher.start()

        # 启动托盘（在后台线程）
        self.tray.run_detached()

        # 初始检查服务
        connected = await self._check_service()
        if connected:
            self.notifier.notify_service_status(True)
            if self.settings.auto_track:
                await self._start_tracking()

        # 启动服务监控
        monitor_task = asyncio.create_task(self._service_monitor_loop())

        # 等待退出
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            # 清理
            monitor_task.cancel()
            if self._track_task:
                self._track_task.cancel()
            self.log_watcher.stop()
            await self.client.close()
            self.tray.stop()

    def run(self) -> None:
        """运行监控器."""
        with contextlib.suppress(KeyboardInterrupt):
            asyncio.run(self.run_async())


def main() -> None:
    """程序入口."""
    settings = Settings.load()
    monitor = Monitor(settings)

    # 设置信号处理
    def signal_handler(sig: int, frame: object) -> None:
        monitor._running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    monitor.run()


if __name__ == "__main__":
    main()
