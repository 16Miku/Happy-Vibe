"""Claude Code 日志适配器测试。"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from src.adapters.base import ActivityData, ToolUsage
from src.adapters.claude_code import ClaudeCodeAdapter


class TestClaudeCodeAdapter:
    """ClaudeCodeAdapter 测试类。"""

    @pytest.fixture
    def adapter(self) -> ClaudeCodeAdapter:
        """创建适配器实例。"""
        return ClaudeCodeAdapter()

    @pytest.fixture
    def temp_log_dir(self, tmp_path: Path) -> Path:
        """创建临时日志目录。"""
        log_dir = tmp_path / ".claude" / "logs"
        log_dir.mkdir(parents=True)
        return log_dir

    @pytest.fixture
    def sample_log_data(self) -> list[dict]:
        """示例日志数据。"""
        return [
            {
                "timestamp": "2024-01-15T10:00:00.000Z",
                "type": "user",
                "message": "请帮我创建一个函数",
            },
            {
                "timestamp": "2024-01-15T10:00:05.000Z",
                "tool": "Read",
                "parameters": {"file_path": "/project/src/main.py"},
                "result": {"content": "# main.py"},
            },
            {
                "timestamp": "2024-01-15T10:00:10.000Z",
                "tool": "Edit",
                "parameters": {"file_path": "/project/src/utils.py"},
                "result": {"success": True},
            },
            {
                "timestamp": "2024-01-15T10:00:15.000Z",
                "tool": "Bash",
                "parameters": {"command": "pytest"},
                "result": {"exit_code": 0},
            },
            {
                "timestamp": "2024-01-15T10:00:20.000Z",
                "tool": "Grep",
                "parameters": {"pattern": "def test_"},
                "result": {"files": ["/project/tests/test_main.py"]},
            },
        ]

    def test_name(self, adapter: ClaudeCodeAdapter) -> None:
        """测试适配器名称。"""
        assert adapter.name == "Claude Code"

    def test_get_log_path_windows(self, adapter: ClaudeCodeAdapter) -> None:
        """测试 Windows 日志路径。"""
        with patch("platform.system", return_value="Windows"):
            path = adapter.get_log_path()
            assert path == Path.home() / ".claude" / "logs"

    def test_get_log_path_macos(self, adapter: ClaudeCodeAdapter) -> None:
        """测试 macOS 日志路径。"""
        with patch("platform.system", return_value="Darwin"):
            path = adapter.get_log_path()
            assert path == Path.home() / "Library" / "Application Support" / "Claude" / "logs"

    def test_get_log_path_linux(self, adapter: ClaudeCodeAdapter) -> None:
        """测试 Linux 日志路径。"""
        with patch("platform.system", return_value="Linux"):
            path = adapter.get_log_path()
            assert path == Path.home() / ".claude" / "logs"

    def test_get_latest_session_file_no_dir(self, adapter: ClaudeCodeAdapter) -> None:
        """测试日志目录不存在时返回 None。"""
        with patch.object(adapter, "get_log_path", return_value=Path("/nonexistent")):
            assert adapter.get_latest_session_file() is None

    def test_get_latest_session_file_empty_dir(
        self, adapter: ClaudeCodeAdapter, temp_log_dir: Path
    ) -> None:
        """测试空目录返回 None。"""
        with patch.object(adapter, "get_log_path", return_value=temp_log_dir):
            assert adapter.get_latest_session_file() is None

    def test_get_latest_session_file(
        self, adapter: ClaudeCodeAdapter, temp_log_dir: Path
    ) -> None:
        """测试获取最新会话文件。"""
        import time
        # 创建多个日志文件，确保修改时间不同
        (temp_log_dir / "session-2024-01-14.jsonl").write_text("{}")
        time.sleep(0.01)  # 确保文件修改时间不同
        (temp_log_dir / "session-2024-01-15.jsonl").write_text("{}")

        with patch.object(adapter, "get_log_path", return_value=temp_log_dir):
            latest = adapter.get_latest_session_file()
            assert latest is not None
            assert latest.name == "session-2024-01-15.jsonl"

    def test_is_available_true(
        self, adapter: ClaudeCodeAdapter, temp_log_dir: Path
    ) -> None:
        """测试适配器可用。"""
        with patch.object(adapter, "get_log_path", return_value=temp_log_dir):
            assert adapter.is_available() is True

    def test_is_available_false(self, adapter: ClaudeCodeAdapter) -> None:
        """测试适配器不可用。"""
        with patch.object(adapter, "get_log_path", return_value=Path("/nonexistent")):
            assert adapter.is_available() is False

    def test_extract_session_id(self, adapter: ClaudeCodeAdapter) -> None:
        """测试提取会话ID。"""
        path = Path("/logs/session-2024-01-15.jsonl")
        assert adapter._extract_session_id(path) == "2024-01-15"

    def test_extract_session_id_complex(self, adapter: ClaudeCodeAdapter) -> None:
        """测试复杂会话ID提取。"""
        path = Path("/logs/session-2024-01-15T10-30-00.jsonl")
        assert adapter._extract_session_id(path) == "2024-01-15T10-30-00"

    def test_parse_timestamp_iso_format(self, adapter: ClaudeCodeAdapter) -> None:
        """测试 ISO 格式时间戳解析。"""
        data = {"timestamp": "2024-01-15T10:00:00.000Z"}
        ts = adapter._parse_timestamp(data)
        assert ts is not None
        assert ts.year == 2024
        assert ts.month == 1
        assert ts.day == 15

    def test_parse_timestamp_alternative_key(self, adapter: ClaudeCodeAdapter) -> None:
        """测试备用时间戳键。"""
        data = {"time": "2024-01-15T10:00:00Z"}
        ts = adapter._parse_timestamp(data)
        assert ts is not None

    def test_parse_timestamp_invalid(self, adapter: ClaudeCodeAdapter) -> None:
        """测试无效时间戳。"""
        data = {"timestamp": "invalid"}
        assert adapter._parse_timestamp(data) is None

    def test_parse_timestamp_missing(self, adapter: ClaudeCodeAdapter) -> None:
        """测试缺失时间戳。"""
        data = {}
        assert adapter._parse_timestamp(data) is None

    def test_detect_activity_type_edit(self, adapter: ClaudeCodeAdapter) -> None:
        """测试检测编辑活动。"""
        assert adapter._detect_activity_type({"tool": "Edit"}) == "edit"
        assert adapter._detect_activity_type({"tool": "Write"}) == "edit"
        assert adapter._detect_activity_type({"tool_name": "NotebookEdit"}) == "edit"

    def test_detect_activity_type_read(self, adapter: ClaudeCodeAdapter) -> None:
        """测试检测读取活动。"""
        assert adapter._detect_activity_type({"tool": "Read"}) == "read"
        assert adapter._detect_activity_type({"tool": "Glob"}) == "read"
        assert adapter._detect_activity_type({"tool": "Grep"}) == "read"

    def test_detect_activity_type_execute(self, adapter: ClaudeCodeAdapter) -> None:
        """测试检测执行活动。"""
        assert adapter._detect_activity_type({"tool": "Bash"}) == "execute"
        assert adapter._detect_activity_type({"tool": "Task"}) == "execute"

    def test_detect_activity_type_prompt(self, adapter: ClaudeCodeAdapter) -> None:
        """测试检测提示活动。"""
        assert adapter._detect_activity_type({"type": "user"}) == "prompt"
        assert adapter._detect_activity_type({}) == "prompt"

    def test_update_tool_usage(self, adapter: ClaudeCodeAdapter) -> None:
        """测试更新工具使用统计。"""
        tool_usage = ToolUsage()

        adapter._update_tool_usage({"tool": "Read"}, tool_usage)
        assert tool_usage.read == 1

        adapter._update_tool_usage({"tool": "Edit"}, tool_usage)
        assert tool_usage.write == 1

        adapter._update_tool_usage({"tool": "Bash"}, tool_usage)
        assert tool_usage.bash == 1

        adapter._update_tool_usage({"tool": "Grep"}, tool_usage)
        assert tool_usage.search == 1

    def test_extract_files_from_parameters(self, adapter: ClaudeCodeAdapter) -> None:
        """测试从参数提取文件。"""
        data = {"parameters": {"file_path": "/project/main.py"}}
        files = adapter._extract_files(data)
        assert "/project/main.py" in files

    def test_extract_files_from_result(self, adapter: ClaudeCodeAdapter) -> None:
        """测试从结果提取文件。"""
        data = {"result": {"files": ["/a.py", "/b.py"]}}
        files = adapter._extract_files(data)
        assert "/a.py" in files
        assert "/b.py" in files

    def test_detect_language(self, adapter: ClaudeCodeAdapter) -> None:
        """测试语言检测。"""
        assert adapter._detect_language("/project/main.py") == "Python"
        assert adapter._detect_language("/project/app.ts") == "TypeScript"
        assert adapter._detect_language("/project/index.js") == "JavaScript"
        assert adapter._detect_language("/project/main.go") == "Go"
        assert adapter._detect_language("/project/game.gd") == "GDScript"
        assert adapter._detect_language("/project/unknown.xyz") is None

    def test_is_tool_result(self, adapter: ClaudeCodeAdapter) -> None:
        """测试工具结果检测。"""
        assert adapter._is_tool_result({"tool": "Read"}) is True
        assert adapter._is_tool_result({"tool_name": "Edit"}) is True
        assert adapter._is_tool_result({"type": "tool_result"}) is True
        assert adapter._is_tool_result({"type": "user"}) is False

    def test_is_success(self, adapter: ClaudeCodeAdapter) -> None:
        """测试成功检测。"""
        assert adapter._is_success({}) is True
        assert adapter._is_success({"error": True}) is False
        assert adapter._is_success({"is_error": True}) is False
        assert adapter._is_success({"exit_code": 0}) is True
        assert adapter._is_success({"exit_code": 1}) is False

    def test_determine_primary_activity(self, adapter: ClaudeCodeAdapter) -> None:
        """测试主要活动类型判断。"""
        assert adapter._determine_primary_activity(ToolUsage(write=1)) == "edit"
        assert adapter._determine_primary_activity(ToolUsage(bash=1)) == "execute"
        assert adapter._determine_primary_activity(ToolUsage(read=1)) == "read"
        assert adapter._determine_primary_activity(ToolUsage(search=1)) == "read"
        assert adapter._determine_primary_activity(ToolUsage()) == "prompt"

    def test_estimate_lines_changed(self, adapter: ClaudeCodeAdapter) -> None:
        """测试代码行数估算。"""
        assert adapter._estimate_lines_changed(ToolUsage(write=0)) == 0
        assert adapter._estimate_lines_changed(ToolUsage(write=1)) == 20
        assert adapter._estimate_lines_changed(ToolUsage(write=5)) == 100

    @pytest.mark.asyncio
    async def test_read_activities(
        self,
        adapter: ClaudeCodeAdapter,
        temp_log_dir: Path,
        sample_log_data: list[dict],
    ) -> None:
        """测试读取活动数据。"""
        # 创建日志文件
        log_file = temp_log_dir / "session-2024-01-15.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            for entry in sample_log_data:
                f.write(json.dumps(entry) + "\n")

        with patch.object(adapter, "get_log_path", return_value=temp_log_dir):
            activities = []
            async for activity in adapter.read_activities():
                activities.append(activity)

            assert len(activities) == 1
            activity = activities[0]

            assert activity.session_id == "2024-01-15"
            assert activity.tool_usage.read == 1
            assert activity.tool_usage.write == 1
            assert activity.tool_usage.bash == 1
            assert activity.tool_usage.search == 1
            assert activity.files_affected >= 2
            assert "Python" in activity.languages
            assert activity.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_read_activities_with_since(
        self,
        adapter: ClaudeCodeAdapter,
        temp_log_dir: Path,
    ) -> None:
        """测试带时间过滤的活动读取。"""
        log_data = [
            {"timestamp": "2024-01-15T10:00:00.000Z", "tool": "Read"},
            {"timestamp": "2024-01-15T12:00:00.000Z", "tool": "Edit"},
        ]

        log_file = temp_log_dir / "session-2024-01-15.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            for entry in log_data:
                f.write(json.dumps(entry) + "\n")

        since = datetime(2024, 1, 15, 11, 0, 0)

        with patch.object(adapter, "get_log_path", return_value=temp_log_dir):
            activities = []
            async for activity in adapter.read_activities(since=since):
                activities.append(activity)

            # 应该只有一个活动（12:00 的）
            assert len(activities) == 1
            assert activities[0].tool_usage.write == 1
            assert activities[0].tool_usage.read == 0

    @pytest.mark.asyncio
    async def test_read_activities_empty_file(
        self,
        adapter: ClaudeCodeAdapter,
        temp_log_dir: Path,
    ) -> None:
        """测试空日志文件。"""
        log_file = temp_log_dir / "session-2024-01-15.jsonl"
        log_file.write_text("")

        with patch.object(adapter, "get_log_path", return_value=temp_log_dir):
            activities = []
            async for activity in adapter.read_activities():
                activities.append(activity)

            assert len(activities) == 0

    @pytest.mark.asyncio
    async def test_read_activities_invalid_json(
        self,
        adapter: ClaudeCodeAdapter,
        temp_log_dir: Path,
    ) -> None:
        """测试包含无效 JSON 的日志文件。"""
        log_file = temp_log_dir / "session-2024-01-15.jsonl"
        log_file.write_text("invalid json\n{\"timestamp\": \"2024-01-15T10:00:00Z\", \"tool\": \"Read\"}\n")

        with patch.object(adapter, "get_log_path", return_value=temp_log_dir):
            activities = []
            async for activity in adapter.read_activities():
                activities.append(activity)

            # 应该跳过无效行，解析有效行
            assert len(activities) == 1

    @pytest.mark.asyncio
    async def test_read_activities_with_errors(
        self,
        adapter: ClaudeCodeAdapter,
        temp_log_dir: Path,
    ) -> None:
        """测试包含错误的活动。"""
        log_data = [
            {"timestamp": "2024-01-15T10:00:00.000Z", "tool": "Bash", "error": True},
            {"timestamp": "2024-01-15T10:00:05.000Z", "tool": "Bash", "exit_code": 0},
            {"timestamp": "2024-01-15T10:00:10.000Z", "tool": "Bash", "exit_code": 1},
        ]

        log_file = temp_log_dir / "session-2024-01-15.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            for entry in log_data:
                f.write(json.dumps(entry) + "\n")

        with patch.object(adapter, "get_log_path", return_value=temp_log_dir):
            activities = []
            async for activity in adapter.read_activities():
                activities.append(activity)

            assert len(activities) == 1
            # 3 个工具调用，1 个成功
            assert activities[0].success_rate == pytest.approx(1 / 3, rel=0.01)
