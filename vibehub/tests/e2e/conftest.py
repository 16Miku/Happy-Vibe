"""E2E 测试配置和共享 fixtures

提供端到端测试所需的服务器、客户端和模拟数据。
"""

import asyncio
import json
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.storage.database import Database


@pytest.fixture(scope="module")
def e2e_db_path(tmp_path_factory) -> str:
    """创建 E2E 测试数据库路径"""
    return str(tmp_path_factory.mktemp("e2e") / "e2e_test.db")


@pytest.fixture(scope="module")
def e2e_db(e2e_db_path: str) -> Generator[Database, None, None]:
    """创建 E2E 测试数据库"""
    import src.api
    import src.api.activity
    import src.api.energy
    import src.api.player
    import src.storage.database

    db = Database(e2e_db_path)
    db.create_tables()

    def _get_db() -> Database:
        return db

    # Mock 数据库依赖
    src.api.get_db = _get_db
    src.storage.database.get_db = _get_db
    src.api.activity.get_db = _get_db
    src.api.energy.get_db = _get_db
    src.api.player.get_db = _get_db

    yield db

    db.engine.dispose()
    Path(e2e_db_path).unlink(missing_ok=True)


@pytest_asyncio.fixture
async def e2e_client(e2e_db: Database) -> AsyncGenerator[AsyncClient, None]:
    """创建 E2E 测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_claude_log_dir(tmp_path: Path) -> Path:
    """创建模拟的 Claude Code 日志目录"""
    log_dir = tmp_path / ".claude" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


@pytest.fixture
def sample_claude_log_entries() -> list[dict]:
    """示例 Claude Code 日志条目"""
    base_time = datetime.utcnow()
    return [
        {
            "timestamp": base_time.isoformat(),
            "type": "session_start",
            "session_id": "test-session-001",
            "project": "/path/to/project",
        },
        {
            "timestamp": base_time.isoformat(),
            "type": "tool_use",
            "tool": "Read",
            "file": "src/main.py",
            "success": True,
        },
        {
            "timestamp": base_time.isoformat(),
            "type": "tool_use",
            "tool": "Edit",
            "file": "src/main.py",
            "lines_changed": 50,
            "success": True,
        },
        {
            "timestamp": base_time.isoformat(),
            "type": "tool_use",
            "tool": "Bash",
            "command": "pytest",
            "success": True,
        },
        {
            "timestamp": base_time.isoformat(),
            "type": "tool_use",
            "tool": "Write",
            "file": "src/new_file.py",
            "lines_changed": 100,
            "success": True,
        },
        {
            "timestamp": base_time.isoformat(),
            "type": "session_end",
            "session_id": "test-session-001",
            "duration_seconds": 3600,
        },
    ]


def write_mock_log_file(log_dir: Path, entries: list[dict], filename: str = "claude.jsonl") -> Path:
    """写入模拟日志文件"""
    log_file = log_dir / filename
    with open(log_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return log_file
