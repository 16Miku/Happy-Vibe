"""Activity API 测试"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.activity import _active_sessions
from src.main import app
from src.storage.database import Database
from src.storage.models import Player


@pytest.fixture
def test_db(tmp_path):
    """创建测试数据库"""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.create_tables()
    return db


@pytest.fixture
def test_player(test_db):
    """创建测试玩家"""
    with test_db.get_session() as session:
        player = Player(
            player_id="test-player-001",
            username="test_user",
            consecutive_days=5,
        )
        session.add(player)
    return player


@pytest.fixture(autouse=True)
def clear_sessions():
    """每个测试前清理活动会话"""
    _active_sessions.clear()
    yield
    _active_sessions.clear()


@pytest.fixture
def mock_db(test_db, monkeypatch):
    """Mock 数据库依赖"""
    def mock_get_db():
        return test_db
    monkeypatch.setattr("src.api.activity.get_db", mock_get_db)
    return test_db


@pytest.mark.asyncio
class TestStartActivity:
    """开始活动 API 测试"""

    async def test_start_activity_success(self, mock_db, test_player):
        """测试成功开始活动"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001", "source": "claude_code"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "started_at" in data
        assert data["message"] == "活动追踪已开始"

    async def test_start_activity_player_not_found(self, mock_db):
        """测试玩家不存在时自动创建玩家"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/activity/start",
                json={"player_id": "non-existent-player"},
            )

        # API 设计为自动创建不存在的玩家
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    async def test_start_activity_duplicate_session(self, mock_db, test_player):
        """测试重复开始活动返回409"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 第一次开始
            await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001"},
            )
            # 第二次开始
            response = await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001"},
            )

        assert response.status_code == 409
        assert "已有活动会话" in response.json()["detail"]


@pytest.mark.asyncio
class TestUpdateActivity:
    """更新活动 API 测试"""

    async def test_update_activity_success(self, mock_db, test_player):
        """测试成功更新活动"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开始活动
            start_response = await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001"},
            )
            session_id = start_response.json()["session_id"]

            # 更新活动
            response = await client.post(
                "/api/activity/update",
                json={
                    "session_id": session_id,
                    "quality": {
                        "success_rate": 0.9,
                        "iteration_count": 3,
                        "lines_changed": 150,
                        "files_affected": 5,
                        "languages": ["python", "typescript"],
                        "tool_usage": {
                            "read": 10,
                            "write": 5,
                            "bash": 3,
                            "search": 2,
                        },
                    },
                    "last_interaction_gap": 30,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "duration_minutes" in data
        assert "flow_status" in data
        assert "estimated_energy" in data

    async def test_update_activity_session_not_found(self, mock_db):
        """测试会话不存在时返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/activity/update",
                json={"session_id": "non-existent-session"},
            )

        assert response.status_code == 404
        assert "会话不存在" in response.json()["detail"]


@pytest.mark.asyncio
class TestEndActivity:
    """结束活动 API 测试"""

    async def test_end_activity_success(self, mock_db, test_player):
        """测试成功结束活动"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开始活动
            start_response = await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001"},
            )
            session_id = start_response.json()["session_id"]

            # 结束活动
            response = await client.post(
                "/api/activity/end",
                json={
                    "session_id": session_id,
                    "quality": {
                        "success_rate": 0.85,
                        "iteration_count": 5,
                        "lines_changed": 200,
                        "files_affected": 8,
                        "languages": ["python"],
                        "tool_usage": {
                            "read": 15,
                            "write": 10,
                            "bash": 5,
                            "search": 3,
                        },
                    },
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "started_at" in data
        assert "ended_at" in data
        assert "duration_minutes" in data
        assert "was_in_flow" in data
        assert "reward" in data
        assert data["reward"]["vibe_energy"] >= 0
        assert data["reward"]["experience"] >= 0
        assert data["message"] == "活动已结束，奖励已发放"

    async def test_end_activity_session_not_found(self, mock_db):
        """测试会话不存在时返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/activity/end",
                json={"session_id": "non-existent-session"},
            )

        assert response.status_code == 404
        assert "会话不存在" in response.json()["detail"]

    async def test_end_activity_saves_to_database(self, mock_db, test_player):
        """测试结束活动后数据保存到数据库"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 开始并结束活动
            start_response = await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001"},
            )
            session_id = start_response.json()["session_id"]

            await client.post(
                "/api/activity/end",
                json={"session_id": session_id},
            )

            # 查询历史记录
            history_response = await client.get(
                "/api/activity/history",
                params={"player_id": "test-player-001"},
            )

        assert history_response.status_code == 200
        data = history_response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1


@pytest.mark.asyncio
class TestGetCurrentActivity:
    """获取当前活动 API 测试"""

    async def test_get_current_activity_with_session(self, mock_db, test_player):
        """测试有活动会话时返回正确状态"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开始活动
            start_response = await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001"},
            )
            session_id = start_response.json()["session_id"]

            # 获取当前活动
            response = await client.get(
                "/api/activity/current",
                params={"player_id": "test-player-001"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["has_active_session"] is True
        assert data["session_id"] == session_id
        assert "started_at" in data
        assert "duration_minutes" in data
        assert "flow_status" in data
        assert "estimated_energy" in data

    async def test_get_current_activity_without_session(self, mock_db):
        """测试没有活动会话时返回正确状态"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/activity/current",
                params={"player_id": "test-player-001"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["has_active_session"] is False
        assert data["session_id"] is None
        assert data["duration_minutes"] == 0
        assert data["estimated_energy"] == 0


@pytest.mark.asyncio
class TestGetActivityHistory:
    """获取活动历史 API 测试"""

    async def test_get_activity_history_empty(self, mock_db, test_player):
        """测试没有历史记录时返回空列表"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/activity/history",
                params={"player_id": "test-player-001"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_get_activity_history_with_pagination(self, mock_db, test_player):
        """测试分页参数"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 创建多个活动记录
            for _ in range(3):
                start_response = await client.post(
                    "/api/activity/start",
                    json={"player_id": "test-player-001"},
                )
                session_id = start_response.json()["session_id"]
                await client.post(
                    "/api/activity/end",
                    json={"session_id": session_id},
                )

            # 测试分页
            response = await client.get(
                "/api/activity/history",
                params={"player_id": "test-player-001", "limit": 2, "offset": 0},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2


@pytest.mark.asyncio
class TestGetFlowStatus:
    """获取心流状态 API 测试"""

    async def test_get_flow_status_with_session(self, mock_db, test_player):
        """测试有活动会话时返回心流状态"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先开始活动
            await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001"},
            )

            # 获取心流状态
            response = await client.get(
                "/api/activity/flow-status",
                params={"player_id": "test-player-001"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "is_active" in data
        assert "trigger_reason" in data
        assert "progress" in data

    async def test_get_flow_status_without_session(self, mock_db):
        """测试没有活动会话时返回默认状态"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/activity/flow-status",
                params={"player_id": "test-player-001"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["trigger_reason"] == "没有活动会话"
        assert data["progress"] == {}


@pytest.mark.asyncio
class TestActivityIntegration:
    """活动 API 集成测试"""

    async def test_full_activity_lifecycle(self, mock_db, test_player):
        """测试完整的活动生命周期"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 开始活动
            start_response = await client.post(
                "/api/activity/start",
                json={"player_id": "test-player-001", "source": "claude_code"},
            )
            assert start_response.status_code == 200
            session_id = start_response.json()["session_id"]

            # 2. 检查当前活动
            current_response = await client.get(
                "/api/activity/current",
                params={"player_id": "test-player-001"},
            )
            assert current_response.status_code == 200
            assert current_response.json()["has_active_session"] is True

            # 3. 更新活动
            update_response = await client.post(
                "/api/activity/update",
                json={
                    "session_id": session_id,
                    "quality": {
                        "success_rate": 0.9,
                        "lines_changed": 100,
                        "tool_usage": {"read": 5, "write": 3, "bash": 2, "search": 1},
                    },
                },
            )
            assert update_response.status_code == 200

            # 4. 检查心流状态
            flow_response = await client.get(
                "/api/activity/flow-status",
                params={"player_id": "test-player-001"},
            )
            assert flow_response.status_code == 200

            # 5. 结束活动
            end_response = await client.post(
                "/api/activity/end",
                json={"session_id": session_id},
            )
            assert end_response.status_code == 200
            assert end_response.json()["reward"]["vibe_energy"] >= 0

            # 6. 检查活动已结束
            current_after = await client.get(
                "/api/activity/current",
                params={"player_id": "test-player-001"},
            )
            assert current_after.json()["has_active_session"] is False

            # 7. 检查历史记录
            history_response = await client.get(
                "/api/activity/history",
                params={"player_id": "test-player-001"},
            )
            assert history_response.status_code == 200
            assert history_response.json()["total"] >= 1
