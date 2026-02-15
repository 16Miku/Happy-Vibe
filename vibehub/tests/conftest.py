"""Pytest 配置和共享 fixtures

为所有测试提供统一的数据库和客户端配置。
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from src.main import app
from src.storage.database import Database


# ============ 自动 Monkey Patch Fixture ============


@pytest.fixture(autouse=True)
def auto_mock_database(test_db_path: str) -> None:
    """自动 mock 所有模块中的数据库依赖

    使用 autouse=True 使其自动应用于所有测试。
    """
    import src.api
    import src.api.activity
    import src.api.achievement
    import src.api.check_in
    import src.api.energy
    import src.api.event
    import src.api.farm
    import src.api.friends
    import src.api.guild
    import src.api.guild_war
    import src.api.leaderboard
    import src.api.player
    import src.api.pvp
    import src.api.quest
    import src.api.season

    # 为每个测试创建独立的数据库
    _test_db = Database(test_db_path)
    _test_db.create_tables()

    def _get_db() -> Database:
        return _test_db

    # Mock 所有模块中的 get_db 导入
    src.api.get_db = _get_db
    src.storage.database.get_db = _get_db

    src.api.activity.get_db = _get_db
    src.api.achievement.get_db = _get_db
    src.api.check_in.get_db = _get_db
    src.api.energy.get_db = _get_db
    src.api.event.get_db = _get_db
    src.api.farm.get_db = _get_db
    src.api.friends.get_db = _get_db
    src.api.guild.get_db = _get_db
    src.api.guild_war.get_db = _get_db
    src.api.leaderboard.get_db = _get_db
    src.api.player.get_db = _get_db
    src.api.pvp.get_db = _get_db
    src.api.quest.get_db = _get_db
    src.api.season.get_db = _get_db

    yield _test_db

    # 清理
    try:
        _test_db._engine.dispose()
        Path(test_db_path).unlink(missing_ok=True)
    except Exception:
        pass


# ============ 数据库 Fixtures ============


@pytest.fixture
def test_db_path(tmp_path: Path) -> str:
    """创建测试数据库文件路径"""
    return str(tmp_path / "test.db")


@pytest.fixture
def test_db(auto_mock_database: Database) -> Database:
    """获取自动创建的测试数据库实例"""
    return auto_mock_database


@pytest.fixture
def db_session(test_db: Database) -> Session:
    """创建数据库会话

    自动管理事务回滚，确保测试之间的隔离。
    """
    return test_db.get_session_instance()


# ============ 玩家 Fixtures ============


@pytest.fixture
def sample_player_id() -> str:
    """示例玩家 ID"""
    return "test-player-001"


@pytest.fixture
def sample_player_id_2() -> str:
    """示例玩家 ID 2"""
    return "test-player-002"


@pytest.fixture
def create_player(db_session: Session):
    """创建玩家工厂函数"""

    def _create_player(
        player_id: str = "test-player",
        username: str = "test_user",
        level: int = 1,
        gold: int = 100,
        experience: int = 0,
    ) -> str:
        from src.storage.models import Player

        player = Player(
            player_id=player_id,
            username=username,
            level=level,
            gold=gold,
            experience=experience,
        )
        db_session.add(player)
        db_session.commit()
        db_session.refresh(player)
        return player.player_id

    return _create_player


@pytest.fixture
def test_player(create_player) -> str:
    """创建测试玩家"""
    return create_player(
        player_id="test-player-001",
        username="test_user",
        level=15,
        gold=1000,
        experience=500,
    )


# ============ API 客户端 Fixtures ============


@pytest.fixture
async def test_client(test_db: Database) -> AsyncClient:
    """创建测试 API 客户端

    自动配置测试数据库依赖。
    """
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ============ 成就系统 Fixtures ============


@pytest.fixture
def init_achievements(test_db: Database) -> None:
    """初始化成就定义"""
    with test_db.get_session() as session:
        from src.core.achievement_manager import AchievementManager

        manager = AchievementManager(session)
        manager.initialize_achievements()


# ============ 经济系统 Fixtures ============


@pytest.fixture
def sample_item_data() -> dict:
    """示例物品数据"""
    return {
        "item_type": "carrot",
        "name": "胡萝卜",
        "quality": 1,
    }
