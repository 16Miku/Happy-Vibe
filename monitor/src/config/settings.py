"""配置管理模块."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Monitor 配置设置."""

    model_config = SettingsConfigDict(
        env_prefix="HAPPY_VIBE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # VibeHub 服务配置
    vibehub_host: str = Field(default="127.0.0.1", description="VibeHub 服务地址")
    vibehub_port: int = Field(default=8765, description="VibeHub 服务端口")

    # 通知配置
    notifications_enabled: bool = Field(default=True, description="是否启用通知")
    notification_sound: bool = Field(default=True, description="通知声音")
    notify_on_flow_enter: bool = Field(default=True, description="进入心流状态时通知")
    notify_on_flow_exit: bool = Field(default=True, description="退出心流状态时通知")
    notify_on_achievement: bool = Field(default=True, description="成就解锁时通知")
    notify_on_energy_gain: bool = Field(default=False, description="获得能量时通知")

    # 自动追踪配置
    auto_track: bool = Field(default=True, description="自动开始追踪")
    track_interval_seconds: int = Field(default=30, description="追踪更新间隔(秒)")
    idle_timeout_minutes: int = Field(default=5, description="空闲超时(分钟)")

    # 界面配置
    language: Literal["zh", "en"] = Field(default="zh", description="界面语言")
    start_minimized: bool = Field(default=True, description="启动时最小化到托盘")
    auto_start: bool = Field(default=False, description="开机自启动")

    @property
    def vibehub_url(self) -> str:
        """获取 VibeHub 服务 URL."""
        return f"http://{self.vibehub_host}:{self.vibehub_port}"

    @property
    def config_dir(self) -> Path:
        """获取配置目录."""
        config_path = Path.home() / ".happy-vibe"
        config_path.mkdir(parents=True, exist_ok=True)
        return config_path

    def save(self) -> None:
        """保存配置到文件."""
        config_file = self.config_dir / "monitor.env"
        lines = [
            f"HAPPY_VIBE_VIBEHUB_HOST={self.vibehub_host}",
            f"HAPPY_VIBE_VIBEHUB_PORT={self.vibehub_port}",
            f"HAPPY_VIBE_NOTIFICATIONS_ENABLED={self.notifications_enabled}",
            f"HAPPY_VIBE_NOTIFICATION_SOUND={self.notification_sound}",
            f"HAPPY_VIBE_NOTIFY_ON_FLOW_ENTER={self.notify_on_flow_enter}",
            f"HAPPY_VIBE_NOTIFY_ON_FLOW_EXIT={self.notify_on_flow_exit}",
            f"HAPPY_VIBE_NOTIFY_ON_ACHIEVEMENT={self.notify_on_achievement}",
            f"HAPPY_VIBE_NOTIFY_ON_ENERGY_GAIN={self.notify_on_energy_gain}",
            f"HAPPY_VIBE_AUTO_TRACK={self.auto_track}",
            f"HAPPY_VIBE_TRACK_INTERVAL_SECONDS={self.track_interval_seconds}",
            f"HAPPY_VIBE_IDLE_TIMEOUT_MINUTES={self.idle_timeout_minutes}",
            f"HAPPY_VIBE_LANGUAGE={self.language}",
            f"HAPPY_VIBE_START_MINIMIZED={self.start_minimized}",
            f"HAPPY_VIBE_AUTO_START={self.auto_start}",
        ]
        config_file.write_text("\n".join(lines), encoding="utf-8")

    @classmethod
    def load(cls) -> "Settings":
        """从配置文件加载设置."""
        config_file = Path.home() / ".happy-vibe" / "monitor.env"
        if config_file.exists():
            return cls(_env_file=str(config_file))
        return cls()
