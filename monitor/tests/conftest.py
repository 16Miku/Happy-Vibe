"""测试配置."""

import pytest


@pytest.fixture
def settings():
    """创建测试用配置."""
    from src.config.settings import Settings

    return Settings(
        vibehub_host="127.0.0.1",
        vibehub_port=8765,
        notifications_enabled=False,
        auto_track=False,
    )
