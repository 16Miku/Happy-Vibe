"""Claude Code 日志监听器."""

import contextlib
import json
import os
import platform
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class LogEventType(Enum):
    """日志事件类型."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    FILE_EDIT = "file_edit"
    FILE_CREATE = "file_create"
    COMMAND_RUN = "command_run"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class LogEvent:
    """日志事件."""

    event_type: LogEventType
    timestamp: datetime
    data: dict = field(default_factory=dict)
    raw_line: str = ""


class ClaudeLogHandler(FileSystemEventHandler):
    """Claude Code 日志文件事件处理器."""

    def __init__(
        self,
        callback: Callable[[LogEvent], None],
        log_dir: Path,
    ) -> None:
        """初始化处理器.

        Args:
            callback: 事件回调函数
            log_dir: 日志目录
        """
        super().__init__()
        self._callback = callback
        self._log_dir = log_dir
        self._file_positions: dict[str, int] = {}
        self._current_log_file: Path | None = None

    def on_created(self, event: FileSystemEvent) -> None:
        """处理文件创建事件."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if self._is_log_file(file_path):
            self._current_log_file = file_path
            self._file_positions[str(file_path)] = 0
            self._process_new_content(file_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """处理文件修改事件."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if self._is_log_file(file_path):
            self._process_new_content(file_path)

    def _is_log_file(self, file_path: Path) -> bool:
        """检查是否为日志文件."""
        return file_path.suffix in (".log", ".jsonl", ".json")

    def _process_new_content(self, file_path: Path) -> None:
        """处理文件新增内容."""
        try:
            file_key = str(file_path)
            last_pos = self._file_positions.get(file_key, 0)

            with open(file_path, encoding="utf-8", errors="ignore") as f:
                f.seek(last_pos)
                new_content = f.read()
                self._file_positions[file_key] = f.tell()

            if new_content:
                self._parse_content(new_content)
        except OSError:
            pass

    def _parse_content(self, content: str) -> None:
        """解析日志内容."""
        for line in content.strip().split("\n"):
            if not line.strip():
                continue

            event = self._parse_line(line)
            if event:
                self._callback(event)

    def _parse_line(self, line: str) -> LogEvent | None:
        """解析单行日志."""
        # 尝试 JSON 格式
        try:
            data = json.loads(line)
            return self._parse_json_event(data, line)
        except json.JSONDecodeError:
            pass

        # 尝试文本格式
        return self._parse_text_event(line)

    def _parse_json_event(self, data: dict, raw_line: str) -> LogEvent:
        """解析 JSON 格式事件."""
        timestamp = datetime.now()
        if "timestamp" in data:
            with contextlib.suppress(ValueError, AttributeError):
                timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

        event_type = self._detect_event_type(data)

        return LogEvent(
            event_type=event_type,
            timestamp=timestamp,
            data=data,
            raw_line=raw_line,
        )

    def _parse_text_event(self, line: str) -> LogEvent | None:
        """解析文本格式事件."""
        timestamp = datetime.now()

        # 尝试提取时间戳
        time_match = re.match(r"^\[?(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})", line)
        if time_match:
            with contextlib.suppress(ValueError):
                timestamp = datetime.fromisoformat(time_match.group(1))

        event_type = LogEventType.UNKNOWN
        data: dict = {}

        # 检测事件类型
        lower_line = line.lower()
        if "session" in lower_line and "start" in lower_line:
            event_type = LogEventType.SESSION_START
        elif "session" in lower_line and ("end" in lower_line or "close" in lower_line):
            event_type = LogEventType.SESSION_END
        elif "edit" in lower_line or "write" in lower_line:
            event_type = LogEventType.FILE_EDIT
            # 尝试提取文件路径
            path_match = re.search(r"['\"]([^'\"]+\.\w+)['\"]", line)
            if path_match:
                data["file_path"] = path_match.group(1)
        elif "create" in lower_line:
            event_type = LogEventType.FILE_CREATE
        elif "command" in lower_line or "bash" in lower_line or "run" in lower_line:
            event_type = LogEventType.COMMAND_RUN
        elif "error" in lower_line or "exception" in lower_line:
            event_type = LogEventType.ERROR

        return LogEvent(
            event_type=event_type,
            timestamp=timestamp,
            data=data,
            raw_line=line,
        )

    def _detect_event_type(self, data: dict) -> LogEventType:
        """从 JSON 数据检测事件类型."""
        # 检查常见字段
        event_field = data.get("event", data.get("type", data.get("action", "")))
        if isinstance(event_field, str):
            event_lower = event_field.lower()
            if "session" in event_lower and "start" in event_lower:
                return LogEventType.SESSION_START
            if "session" in event_lower and "end" in event_lower:
                return LogEventType.SESSION_END
            if "edit" in event_lower or "write" in event_lower:
                return LogEventType.FILE_EDIT
            if "create" in event_lower:
                return LogEventType.FILE_CREATE
            if "command" in event_lower or "bash" in event_lower:
                return LogEventType.COMMAND_RUN
            if "error" in event_lower:
                return LogEventType.ERROR

        # 检查工具调用
        if "tool" in data or "tool_name" in data:
            tool_name = data.get("tool", data.get("tool_name", "")).lower()
            if tool_name in ("edit", "write"):
                return LogEventType.FILE_EDIT
            if tool_name == "bash":
                return LogEventType.COMMAND_RUN

        return LogEventType.UNKNOWN


class ClaudeLogWatcher:
    """Claude Code 日志监听器."""

    def __init__(self, log_dir: Path | None = None) -> None:
        """初始化监听器.

        Args:
            log_dir: 日志目录，默认自动检测
        """
        self._log_dir = log_dir or self._get_default_log_dir()
        self._observer: Observer | None = None
        self._callbacks: list[Callable[[LogEvent], None]] = []
        self._running = False

        # 统计信息
        self._session_start_time: datetime | None = None
        self._event_counts: dict[LogEventType, int] = dict.fromkeys(LogEventType, 0)

    @staticmethod
    def _get_default_log_dir() -> Path:
        """获取默认日志目录."""
        system = platform.system()

        if system == "Windows":
            # Windows: %USERPROFILE%\.claude\logs
            base = Path(os.environ.get("USERPROFILE", Path.home()))
            return base / ".claude" / "logs"
        elif system == "Darwin":
            # macOS: ~/Library/Application Support/Claude/logs
            return Path.home() / "Library" / "Application Support" / "Claude" / "logs"
        else:
            # Linux: ~/.claude/logs
            return Path.home() / ".claude" / "logs"

    @property
    def log_dir(self) -> Path:
        """获取日志目录."""
        return self._log_dir

    @property
    def is_running(self) -> bool:
        """检查是否正在运行."""
        return self._running

    @property
    def event_counts(self) -> dict[LogEventType, int]:
        """获取事件计数."""
        return self._event_counts.copy()

    @property
    def session_duration_seconds(self) -> int:
        """获取当前会话持续时间(秒)."""
        if self._session_start_time is None:
            return 0
        return int((datetime.now() - self._session_start_time).total_seconds())

    def add_callback(self, callback: Callable[[LogEvent], None]) -> None:
        """添加事件回调.

        Args:
            callback: 回调函数
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[LogEvent], None]) -> None:
        """移除事件回调."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _handle_event(self, event: LogEvent) -> None:
        """处理日志事件."""
        # 更新统计
        self._event_counts[event.event_type] += 1

        # 处理会话事件
        if event.event_type == LogEventType.SESSION_START:
            self._session_start_time = event.timestamp
        elif event.event_type == LogEventType.SESSION_END:
            self._session_start_time = None

        # 调用回调
        for callback in self._callbacks:
            with contextlib.suppress(Exception):
                callback(event)

    def start(self) -> bool:
        """启动监听.

        Returns:
            是否成功启动
        """
        if self._running:
            return True

        # 确保日志目录存在
        if not self._log_dir.exists():
            try:
                self._log_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                return False

        # 创建观察者
        self._observer = Observer()
        handler = ClaudeLogHandler(self._handle_event, self._log_dir)

        try:
            self._observer.schedule(handler, str(self._log_dir), recursive=True)
            self._observer.start()
            self._running = True
            return True
        except Exception:
            self._observer = None
            return False

    def stop(self) -> None:
        """停止监听."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        self._running = False

    def reset_stats(self) -> None:
        """重置统计信息."""
        self._event_counts = dict.fromkeys(LogEventType, 0)
        self._session_start_time = None
