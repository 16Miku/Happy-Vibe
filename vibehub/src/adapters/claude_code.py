"""Claude Code 日志适配器。

监听和解析 Claude Code 日志文件，提取编码活动数据。
"""

import json
import platform
import re
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from src.adapters.base import ActivityData, BaseAdapter, ToolUsage


class ClaudeCodeAdapter(BaseAdapter):
    """Claude Code 日志适配器。

    解析 Claude Code 的 JSONL 格式日志文件，提取编码活动数据。

    日志路径:
        - Windows: %USERPROFILE%\\.claude\\logs\\
        - macOS: ~/Library/Application Support/Claude/logs/
        - Linux: ~/.claude/logs/

    日志格式: session-<date>.jsonl
    """

    # 工具名称到类别的映射
    TOOL_CATEGORIES = {
        "Read": "read",
        "Glob": "read",
        "Grep": "search",
        "Edit": "write",
        "Write": "write",
        "NotebookEdit": "write",
        "Bash": "bash",
        "Task": "bash",
        "WebFetch": "search",
        "WebSearch": "search",
    }

    # 文件扩展名到语言的映射
    EXTENSION_TO_LANGUAGE = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".jsx": "JavaScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".cs": "C#",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".gd": "GDScript",
        ".md": "Markdown",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".html": "HTML",
        ".css": "CSS",
        ".sql": "SQL",
        ".sh": "Shell",
        ".ps1": "PowerShell",
    }

    @property
    def name(self) -> str:
        """适配器名称。"""
        return "Claude Code"

    def get_log_path(self) -> Path:
        """获取 Claude Code 日志目录路径。

        Returns:
            日志目录路径
        """
        system = platform.system()

        if system == "Windows":
            return Path.home() / ".claude" / "logs"
        elif system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Claude" / "logs"
        else:  # Linux 和其他
            return Path.home() / ".claude" / "logs"

    def get_latest_session_file(self) -> Path | None:
        """获取最新的会话日志文件。

        Returns:
            最新日志文件路径，如果不存在则返回 None
        """
        log_path = self.get_log_path()

        if not log_path.exists():
            return None

        # 查找所有 session-*.jsonl 文件
        session_files = list(log_path.glob("session-*.jsonl"))

        if not session_files:
            return None

        # 按修改时间排序，返回最新的
        return max(session_files, key=lambda f: f.stat().st_mtime)

    def get_session_files(
        self, since: datetime | None = None
    ) -> list[Path]:
        """获取会话日志文件列表。

        Args:
            since: 只返回此时间之后修改的文件

        Returns:
            日志文件路径列表，按时间排序
        """
        log_path = self.get_log_path()

        if not log_path.exists():
            return []

        session_files = list(log_path.glob("session-*.jsonl"))

        if since:
            since_timestamp = since.timestamp()
            session_files = [
                f for f in session_files
                if f.stat().st_mtime >= since_timestamp
            ]

        return sorted(session_files, key=lambda f: f.stat().st_mtime)

    async def read_activities(
        self, since: datetime | None = None
    ) -> AsyncIterator[ActivityData]:
        """读取编码活动数据。

        Args:
            since: 只读取此时间之后的活动

        Yields:
            ActivityData 对象
        """
        session_files = self.get_session_files(since)

        for session_file in session_files:
            async for activity in self._parse_session_file(session_file, since):
                yield activity

    async def _parse_session_file(
        self, file_path: Path, since: datetime | None = None
    ) -> AsyncIterator[ActivityData]:
        """解析单个会话日志文件。

        Args:
            file_path: 日志文件路径
            since: 只返回此时间之后的活动

        Yields:
            ActivityData 对象
        """
        # 从文件名提取会话ID
        session_id = self._extract_session_id(file_path)

        # 用于聚合连续活动的状态
        current_activity: dict | None = None
        tool_usage = ToolUsage()
        files_affected: set[str] = set()
        languages: set[str] = set()
        success_count = 0
        total_count = 0
        start_time: datetime | None = None
        last_time: datetime | None = None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # 解析时间戳
                    timestamp = self._parse_timestamp(data)
                    if not timestamp:
                        continue

                    # 过滤时间
                    if since and timestamp < since:
                        continue

                    # 检测活动类型
                    activity_type = self._detect_activity_type(data)

                    # 更新工具使用统计
                    self._update_tool_usage(data, tool_usage)

                    # 提取文件信息
                    affected_files = self._extract_files(data)
                    files_affected.update(affected_files)

                    # 提取语言信息
                    for file_path_str in affected_files:
                        lang = self._detect_language(file_path_str)
                        if lang:
                            languages.add(lang)

                    # 统计成功率
                    if self._is_tool_result(data):
                        total_count += 1
                        if self._is_success(data):
                            success_count += 1

                    # 更新时间范围
                    if start_time is None:
                        start_time = timestamp
                    last_time = timestamp

                # 生成最终活动数据
                if start_time and last_time:
                    duration = (last_time - start_time).total_seconds()
                    success_rate = success_count / total_count if total_count > 0 else 1.0

                    yield ActivityData(
                        session_id=session_id,
                        timestamp=start_time,
                        duration=duration,
                        activity_type=self._determine_primary_activity(tool_usage),
                        tool_usage=tool_usage,
                        lines_changed=self._estimate_lines_changed(tool_usage),
                        files_affected=len(files_affected),
                        languages=list(languages),
                        success_rate=success_rate,
                        iteration_count=total_count,
                        response_time=duration / total_count if total_count > 0 else 0.0,
                    )

        except (OSError, IOError) as e:
            # 文件读取错误，跳过此文件
            pass

    def _extract_session_id(self, file_path: Path) -> str:
        """从文件名提取会话ID。

        Args:
            file_path: 日志文件路径

        Returns:
            会话ID
        """
        # session-2024-01-15.jsonl -> 2024-01-15
        match = re.search(r"session-(.+)\.jsonl$", file_path.name)
        if match:
            return match.group(1)
        return file_path.stem

    def _parse_timestamp(self, data: dict) -> datetime | None:
        """解析日志条目的时间戳。

        Args:
            data: 日志条目数据

        Returns:
            datetime 对象，解析失败返回 None
        """
        timestamp_str = data.get("timestamp") or data.get("time") or data.get("ts")

        if not timestamp_str:
            return None

        # 尝试多种时间格式
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # 尝试 ISO 格式
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _detect_activity_type(self, data: dict) -> str:
        """检测活动类型。

        Args:
            data: 日志条目数据

        Returns:
            活动类型: prompt/edit/read/execute
        """
        # 检查工具调用
        tool_name = data.get("tool") or data.get("tool_name") or ""

        if tool_name in ("Edit", "Write", "NotebookEdit"):
            return "edit"
        elif tool_name in ("Read", "Glob", "Grep"):
            return "read"
        elif tool_name in ("Bash", "Task"):
            return "execute"

        # 检查消息类型
        msg_type = data.get("type") or data.get("message_type") or ""

        if msg_type in ("user", "human"):
            return "prompt"
        elif msg_type in ("assistant", "ai"):
            return "prompt"

        return "prompt"

    def _update_tool_usage(self, data: dict, tool_usage: ToolUsage) -> None:
        """更新工具使用统计。

        Args:
            data: 日志条目数据
            tool_usage: 工具使用统计对象
        """
        tool_name = data.get("tool") or data.get("tool_name") or ""

        category = self.TOOL_CATEGORIES.get(tool_name)

        if category == "read":
            tool_usage.read += 1
        elif category == "write":
            tool_usage.write += 1
        elif category == "bash":
            tool_usage.bash += 1
        elif category == "search":
            tool_usage.search += 1

    def _extract_files(self, data: dict) -> set[str]:
        """提取涉及的文件路径。

        Args:
            data: 日志条目数据

        Returns:
            文件路径集合
        """
        files: set[str] = set()

        # 从工具参数中提取
        params = data.get("parameters") or data.get("params") or data.get("input") or {}

        if isinstance(params, dict):
            for key in ("file_path", "path", "file", "filename"):
                if key in params and params[key]:
                    files.add(str(params[key]))

        # 从结果中提取
        result = data.get("result") or data.get("output") or {}
        if isinstance(result, dict):
            for key in ("file_path", "path", "file", "files"):
                value = result.get(key)
                if value:
                    if isinstance(value, list):
                        files.update(str(f) for f in value)
                    else:
                        files.add(str(value))

        return files

    def _detect_language(self, file_path: str) -> str | None:
        """根据文件扩展名检测编程语言。

        Args:
            file_path: 文件路径

        Returns:
            语言名称，未知返回 None
        """
        ext = Path(file_path).suffix.lower()
        return self.EXTENSION_TO_LANGUAGE.get(ext)

    def _is_tool_result(self, data: dict) -> bool:
        """检查是否为工具执行结果。

        Args:
            data: 日志条目数据

        Returns:
            True 如果是工具结果
        """
        return bool(
            data.get("tool") or
            data.get("tool_name") or
            data.get("type") == "tool_result"
        )

    def _is_success(self, data: dict) -> bool:
        """检查工具执行是否成功。

        Args:
            data: 日志条目数据

        Returns:
            True 如果执行成功
        """
        # 检查错误标志
        if data.get("error") or data.get("is_error"):
            return False

        # 检查状态码
        status = data.get("status") or data.get("exit_code")
        if status is not None and status != 0:
            return False

        return True

    def _determine_primary_activity(self, tool_usage: ToolUsage) -> str:
        """根据工具使用情况确定主要活动类型。

        Args:
            tool_usage: 工具使用统计

        Returns:
            主要活动类型
        """
        if tool_usage.write > 0:
            return "edit"
        elif tool_usage.bash > 0:
            return "execute"
        elif tool_usage.read > 0 or tool_usage.search > 0:
            return "read"
        return "prompt"

    def _estimate_lines_changed(self, tool_usage: ToolUsage) -> int:
        """估算代码改动行数。

        基于写入操作次数进行估算。

        Args:
            tool_usage: 工具使用统计

        Returns:
            估算的改动行数
        """
        # 假设每次写入操作平均改动 20 行
        return tool_usage.write * 20
