"""日志监听模块测试."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.watcher.log_watcher import (
    ClaudeLogHandler,
    ClaudeLogWatcher,
    LogEvent,
    LogEventType,
)


class TestLogEventType:
    """LogEventType 枚举测试."""

    def test_event_type_values(self):
        """测试事件类型值."""
        assert LogEventType.SESSION_START.value == "session_start"
        assert LogEventType.SESSION_END.value == "session_end"
        assert LogEventType.FILE_EDIT.value == "file_edit"
        assert LogEventType.FILE_CREATE.value == "file_create"
        assert LogEventType.COMMAND_RUN.value == "command_run"
        assert LogEventType.ERROR.value == "error"
        assert LogEventType.UNKNOWN.value == "unknown"


class TestLogEvent:
    """LogEvent 数据类测试."""

    def test_log_event_creation(self):
        """测试日志事件创建."""
        event = LogEvent(
            event_type=LogEventType.FILE_EDIT,
            timestamp=datetime.now(),
            data={"file": "test.py"},
            raw_line="test line",
        )
        assert event.event_type == LogEventType.FILE_EDIT
        assert event.data == {"file": "test.py"}
        assert event.raw_line == "test line"

    def test_log_event_default_values(self):
        """测试日志事件默认值."""
        event = LogEvent(
            event_type=LogEventType.UNKNOWN,
            timestamp=datetime.now(),
        )
        assert event.data == {}
        assert event.raw_line == ""


class TestClaudeLogHandler:
    """ClaudeLogHandler 测试类."""

    @pytest.fixture
    def handler(self):
        """创建测试处理器."""
        callback = MagicMock()
        log_dir = Path(tempfile.gettempdir())
        return ClaudeLogHandler(callback, log_dir), callback

    def test_is_log_file(self, handler):
        """测试日志文件检测."""
        h, _ = handler
        assert h._is_log_file(Path("test.log")) is True
        assert h._is_log_file(Path("test.jsonl")) is True
        assert h._is_log_file(Path("test.json")) is True
        assert h._is_log_file(Path("test.txt")) is False
        assert h._is_log_file(Path("test.py")) is False

    def test_parse_json_event_session_start(self, handler):
        """测试解析 JSON 会话开始事件."""
        h, _ = handler
        data = {"event": "session_start", "timestamp": "2024-01-01T10:00:00Z"}
        event = h._parse_json_event(data, json.dumps(data))

        assert event.event_type == LogEventType.SESSION_START

    def test_parse_json_event_session_end(self, handler):
        """测试解析 JSON 会话结束事件."""
        h, _ = handler
        data = {"event": "session_end"}
        event = h._parse_json_event(data, json.dumps(data))

        assert event.event_type == LogEventType.SESSION_END

    def test_parse_json_event_file_edit(self, handler):
        """测试解析 JSON 文件编辑事件."""
        h, _ = handler
        data = {"action": "edit", "file": "test.py"}
        event = h._parse_json_event(data, json.dumps(data))

        assert event.event_type == LogEventType.FILE_EDIT

    def test_parse_json_event_command_run(self, handler):
        """测试解析 JSON 命令执行事件."""
        h, _ = handler
        data = {"tool": "bash", "command": "ls"}
        event = h._parse_json_event(data, json.dumps(data))

        assert event.event_type == LogEventType.COMMAND_RUN

    def test_parse_json_event_error(self, handler):
        """测试解析 JSON 错误事件."""
        h, _ = handler
        data = {"type": "error", "message": "Something went wrong"}
        event = h._parse_json_event(data, json.dumps(data))

        assert event.event_type == LogEventType.ERROR

    def test_parse_json_event_unknown(self, handler):
        """测试解析未知 JSON 事件."""
        h, _ = handler
        data = {"foo": "bar"}
        event = h._parse_json_event(data, json.dumps(data))

        assert event.event_type == LogEventType.UNKNOWN

    def test_parse_text_event_session_start(self, handler):
        """测试解析文本会话开始事件."""
        h, _ = handler
        event = h._parse_text_event("[2024-01-01 10:00:00] Session start")

        assert event is not None
        assert event.event_type == LogEventType.SESSION_START

    def test_parse_text_event_session_end(self, handler):
        """测试解析文本会话结束事件."""
        h, _ = handler
        event = h._parse_text_event("Session end at 10:30")

        assert event is not None
        assert event.event_type == LogEventType.SESSION_END

    def test_parse_text_event_file_edit(self, handler):
        """测试解析文本文件编辑事件."""
        h, _ = handler
        event = h._parse_text_event("Edit file 'test.py'")

        assert event is not None
        assert event.event_type == LogEventType.FILE_EDIT
        assert event.data.get("file_path") == "test.py"

    def test_parse_text_event_command(self, handler):
        """测试解析文本命令事件."""
        h, _ = handler
        event = h._parse_text_event("Run bash command: ls -la")

        assert event is not None
        assert event.event_type == LogEventType.COMMAND_RUN

    def test_parse_text_event_error(self, handler):
        """测试解析文本错误事件."""
        h, _ = handler
        event = h._parse_text_event("Error: Connection failed")

        assert event is not None
        assert event.event_type == LogEventType.ERROR

    def test_parse_line_json(self, handler):
        """测试解析 JSON 行."""
        h, _ = handler
        line = '{"event": "session_start"}'
        event = h._parse_line(line)

        assert event is not None
        assert event.event_type == LogEventType.SESSION_START

    def test_parse_line_text(self, handler):
        """测试解析文本行."""
        h, _ = handler
        line = "Session start at 10:00"
        event = h._parse_line(line)

        assert event is not None
        assert event.event_type == LogEventType.SESSION_START

    def test_parse_content_multiple_lines(self, handler):
        """测试解析多行内容."""
        h, callback = handler
        content = '{"event": "session_start"}\n{"action": "edit"}\n'
        h._parse_content(content)

        assert callback.call_count == 2

    def test_parse_content_empty_lines(self, handler):
        """测试解析包含空行的内容."""
        h, callback = handler
        content = '{"event": "session_start"}\n\n{"action": "edit"}\n'
        h._parse_content(content)

        assert callback.call_count == 2

    def test_detect_event_type_tool_edit(self, handler):
        """测试检测工具编辑事件类型."""
        h, _ = handler
        data = {"tool_name": "edit"}
        event_type = h._detect_event_type(data)

        assert event_type == LogEventType.FILE_EDIT

    def test_detect_event_type_tool_write(self, handler):
        """测试检测工具写入事件类型."""
        h, _ = handler
        data = {"tool": "write"}
        event_type = h._detect_event_type(data)

        assert event_type == LogEventType.FILE_EDIT


class TestClaudeLogWatcher:
    """ClaudeLogWatcher 测试类."""

    @pytest.fixture
    def watcher(self):
        """创建测试监听器."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ClaudeLogWatcher(Path(tmpdir))

    def test_init(self, watcher):
        """测试初始化."""
        assert watcher.is_running is False
        assert watcher.session_duration_seconds == 0

    def test_log_dir_property(self, watcher):
        """测试日志目录属性."""
        assert watcher.log_dir.exists()

    def test_event_counts_property(self, watcher):
        """测试事件计数属性."""
        counts = watcher.event_counts
        assert isinstance(counts, dict)
        assert all(t in counts for t in LogEventType)

    def test_add_callback(self, watcher):
        """测试添加回调."""
        callback = MagicMock()
        watcher.add_callback(callback)
        assert callback in watcher._callbacks

    def test_remove_callback(self, watcher):
        """测试移除回调."""
        callback = MagicMock()
        watcher.add_callback(callback)
        watcher.remove_callback(callback)
        assert callback not in watcher._callbacks

    def test_remove_nonexistent_callback(self, watcher):
        """测试移除不存在的回调."""
        callback = MagicMock()
        watcher.remove_callback(callback)  # 不应抛出异常

    def test_start_and_stop(self, watcher):
        """测试启动和停止."""
        result = watcher.start()
        assert result is True
        assert watcher.is_running is True

        watcher.stop()
        assert watcher.is_running is False

    def test_start_twice(self, watcher):
        """测试重复启动."""
        watcher.start()
        result = watcher.start()
        assert result is True
        watcher.stop()

    def test_stop_when_not_running(self, watcher):
        """测试未运行时停止."""
        watcher.stop()  # 不应抛出异常

    def test_reset_stats(self, watcher):
        """测试重置统计."""
        watcher._event_counts[LogEventType.FILE_EDIT] = 10
        watcher._session_start_time = datetime.now()

        watcher.reset_stats()

        assert watcher._event_counts[LogEventType.FILE_EDIT] == 0
        assert watcher._session_start_time is None

    def test_handle_event_updates_counts(self, watcher):
        """测试事件处理更新计数."""
        event = LogEvent(
            event_type=LogEventType.FILE_EDIT,
            timestamp=datetime.now(),
        )
        watcher._handle_event(event)

        assert watcher._event_counts[LogEventType.FILE_EDIT] == 1

    def test_handle_event_session_start(self, watcher):
        """测试处理会话开始事件."""
        event = LogEvent(
            event_type=LogEventType.SESSION_START,
            timestamp=datetime.now(),
        )
        watcher._handle_event(event)

        assert watcher._session_start_time is not None

    def test_handle_event_session_end(self, watcher):
        """测试处理会话结束事件."""
        watcher._session_start_time = datetime.now()

        event = LogEvent(
            event_type=LogEventType.SESSION_END,
            timestamp=datetime.now(),
        )
        watcher._handle_event(event)

        assert watcher._session_start_time is None

    def test_handle_event_calls_callbacks(self, watcher):
        """测试事件处理调用回调."""
        callback = MagicMock()
        watcher.add_callback(callback)

        event = LogEvent(
            event_type=LogEventType.FILE_EDIT,
            timestamp=datetime.now(),
        )
        watcher._handle_event(event)

        callback.assert_called_once_with(event)

    def test_handle_event_callback_exception(self, watcher):
        """测试回调异常处理."""
        bad_callback = MagicMock(side_effect=Exception("Callback error"))
        watcher.add_callback(bad_callback)

        event = LogEvent(
            event_type=LogEventType.FILE_EDIT,
            timestamp=datetime.now(),
        )
        # 不应抛出异常
        watcher._handle_event(event)

    def test_session_duration_when_active(self, watcher):
        """测试活跃会话持续时间."""
        watcher._session_start_time = datetime.now()
        duration = watcher.session_duration_seconds

        assert duration >= 0

    @patch("platform.system")
    def test_get_default_log_dir_windows(self, mock_system):
        """测试 Windows 默认日志目录."""
        mock_system.return_value = "Windows"
        with patch.dict("os.environ", {"USERPROFILE": "C:\\Users\\Test"}):
            log_dir = ClaudeLogWatcher._get_default_log_dir()
            assert "logs" in str(log_dir)

    @patch("platform.system")
    def test_get_default_log_dir_macos(self, mock_system):
        """测试 macOS 默认日志目录."""
        mock_system.return_value = "Darwin"
        log_dir = ClaudeLogWatcher._get_default_log_dir()
        assert "logs" in str(log_dir)

    @patch("platform.system")
    def test_get_default_log_dir_linux(self, mock_system):
        """测试 Linux 默认日志目录."""
        mock_system.return_value = "Linux"
        log_dir = ClaudeLogWatcher._get_default_log_dir()
        assert "logs" in str(log_dir)
