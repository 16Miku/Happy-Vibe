"""适配器基类定义。

提供所有数据适配器的公共接口和数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator


@dataclass
class ToolUsage:
    """工具使用统计。"""

    read: int = 0  # 文件读取次数
    write: int = 0  # 文件写入次数
    bash: int = 0  # 命令执行次数
    search: int = 0  # 搜索次数


@dataclass
class ActivityData:
    """编码活动数据。

    Attributes:
        session_id: 会话ID
        timestamp: 时间戳
        duration: 持续时长（秒）
        activity_type: 活动类型 (prompt/edit/read/execute)
        tool_usage: 工具使用统计
        lines_changed: 改动代码行数
        files_affected: 影响文件数
        languages: 使用的编程语言
        success_rate: 成功执行率
        iteration_count: 迭代次数
        response_time: 平均响应时间（秒）
    """

    session_id: str
    timestamp: datetime
    duration: float = 0.0
    activity_type: str = "prompt"
    tool_usage: ToolUsage = field(default_factory=ToolUsage)
    lines_changed: int = 0
    files_affected: int = 0
    languages: list[str] = field(default_factory=list)
    success_rate: float = 1.0
    iteration_count: int = 1
    response_time: float = 0.0


class BaseAdapter(ABC):
    """数据适配器基类。

    所有编码工具适配器都应继承此类并实现抽象方法。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """适配器名称。"""
        ...

    @abstractmethod
    def get_log_path(self) -> Path:
        """获取日志文件路径。

        Returns:
            日志目录路径
        """
        ...

    @abstractmethod
    def get_latest_session_file(self) -> Path | None:
        """获取最新的会话日志文件。

        Returns:
            最新日志文件路径，如果不存在则返回 None
        """
        ...

    @abstractmethod
    async def read_activities(
        self, since: datetime | None = None
    ) -> AsyncIterator[ActivityData]:
        """读取编码活动数据。

        Args:
            since: 只读取此时间之后的活动，None 表示读取所有

        Yields:
            ActivityData 对象
        """
        ...

    def is_available(self) -> bool:
        """检查适配器是否可用（日志路径存在）。

        Returns:
            True 如果日志路径存在
        """
        return self.get_log_path().exists()
