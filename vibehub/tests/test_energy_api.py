"""Energy API 测试"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.energy import DAILY_ENERGY_CAP
from src.main import app
from src.storage.models import CodingActivity, Player


@pytest.fixture(autouse=True)
def clear_sessions():
    """每个测试前清理活动会话"""
    from src.api.activity import _active_sessions
    _active_sessions.clear()
    yield
    _active_sessions.clear()


@pytest.fixture
def energy_test_player(test_db):
    """创建能量测试专用玩家"""
    player_id = f"test-player-energy-{uuid.uuid4()}"
    with test_db.get_session() as session:
        player = Player(
            player_id=player_id,
            username="energy_test_user",
            vibe_energy=100,
            max_vibe_energy=1000,
            consecutive_days=5,
        )
        session.add(player)
    return player_id


@pytest.mark.asyncio
class TestCalculateEnergy:
    """能量计算 API 测试"""

    async def test_calculate_energy_basic(self, test_db):
        """测试基础能量计算"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/energy/calculate",
                json={
                    "duration_minutes": 30,
                    "consecutive_days": 0,
                    "is_flow_state": False,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "vibe_energy" in data
        assert "experience" in data
        assert "code_essence" in data
        assert "breakdown" in data
        assert data["vibe_energy"] > 0

    async def test_calculate_energy_with_flow_state(self, test_db):
        """测试心流状态加成"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 无心流状态
            response_normal = await client.post(
                "/api/energy/calculate",
                json={
                    "duration_minutes": 30,
                    "is_flow_state": False,
                },
            )
            # 有心流状态
            response_flow = await client.post(
                "/api/energy/calculate",
                json={
                    "duration_minutes": 30,
                    "is_flow_state": True,
                },
            )

        normal_energy = response_normal.json()["vibe_energy"]
        flow_energy = response_flow.json()["vibe_energy"]
        assert flow_energy > normal_energy
        assert response_flow.json()["breakdown"]["flow_bonus"] == 1.5

    async def test_calculate_energy_with_streak(self, test_db):
        """测试连续签到加成"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 无连续签到
            response_no_streak = await client.post(
                "/api/energy/calculate",
                json={
                    "duration_minutes": 30,
                    "consecutive_days": 0,
                },
            )
            # 有连续签到
            response_streak = await client.post(
                "/api/energy/calculate",
                json={
                    "duration_minutes": 30,
                    "consecutive_days": 10,
                },
            )

        no_streak_energy = response_no_streak.json()["vibe_energy"]
        streak_energy = response_streak.json()["vibe_energy"]
        assert streak_energy > no_streak_energy

    async def test_calculate_energy_with_quality(self, test_db):
        """测试质量指标加成"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/energy/calculate",
                json={
                    "duration_minutes": 30,
                    "quality": {
                        "success_rate": 0.9,
                        "iteration_count": 2,
                        "lines_changed": 200,
                        "files_affected": 5,
                        "languages": ["python", "typescript"],
                        "tool_usage": {
                            "read": 10,
                            "write": 5,
                            "bash": 3,
                            "search": 2,
                        },
                    },
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["breakdown"]["quality_bonus"] > 0.5

    async def test_calculate_energy_invalid_duration(self, test_db):
        """测试无效时长参数"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/energy/calculate",
                json={
                    "duration_minutes": 0,
                },
            )

        assert response.status_code == 422


@pytest.mark.asyncio
class TestAwardEnergy:
    """能量发放 API 测试"""

    async def test_award_energy_success(self, test_db, energy_test_player):
        """测试成功发放能量"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/energy/award",
                json={
                    "player_id": energy_test_player,
                    "duration_minutes": 30,
                    "consecutive_days": 5,
                    "is_flow_state": False,
                    "source": "claude_code",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["player_id"] == energy_test_player
        assert data["awarded_energy"] > 0
        assert data["awarded_experience"] >= 0
        assert data["current_energy"] > 100  # 初始100 + 发放的能量
        assert data["daily_cap"] == DAILY_ENERGY_CAP
        assert data["capped"] is False
        assert "能量发放成功" in data["message"]

    async def test_award_energy_player_not_found(self, test_db):
        """测试玩家不存在时返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/energy/award",
                json={
                    "player_id": "non-existent-player",
                    "duration_minutes": 30,
                },
            )

        assert response.status_code == 404
        assert "玩家不存在" in response.json()["detail"]

    async def test_award_energy_updates_player(self, test_db, energy_test_player):
        """测试发放能量后玩家数据更新"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 发放能量
            response = await client.post(
                "/api/energy/award",
                json={
                    "player_id": energy_test_player,
                    "duration_minutes": 30,
                },
            )

        data = response.json()
        # 验证玩家能量已更新
        assert data["current_energy"] == 100 + data["awarded_energy"]

    async def test_award_energy_creates_activity_record(self, test_db, energy_test_player):
        """测试发放能量后创建活动记录"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 发放能量
            await client.post(
                "/api/energy/award",
                json={
                    "player_id": energy_test_player,
                    "duration_minutes": 30,
                    "source": "test_source",
                },
            )

            # 查询历史记录
            history_response = await client.get(
                "/api/energy/history",
                params={"player_id": energy_test_player},
            )

        assert history_response.status_code == 200
        data = history_response.json()
        assert data["total"] >= 1
        assert data["items"][0]["source"] == "test_source"

    async def test_award_energy_respects_max_energy(self, test_db):
        """测试发放能量不超过玩家能量上限"""
        # 创建一个接近能量上限的玩家
        player_id = f"test-player-max-{uuid.uuid4()}"
        with test_db.get_session() as session:
            player = Player(
                player_id=player_id,
                username="max_energy_user",
                vibe_energy=990,
                max_vibe_energy=1000,
            )
            session.add(player)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/energy/award",
                json={
                    "player_id": player_id,
                    "duration_minutes": 60,  # 会产生较多能量
                },
            )

        assert response.status_code == 200
        data = response.json()
        # 当前能量不应超过上限
        assert data["current_energy"] <= data["max_energy"]


@pytest.mark.asyncio
class TestEnergyDailyCap:
    """每日能量上限测试"""

    async def test_daily_cap_triggers(self, test_db):
        """测试每日能量上限触发"""
        from datetime import datetime

        # 创建玩家
        player_id = f"test-player-cap-{uuid.uuid4()}"
        with test_db.get_session() as session:
            player = Player(
                player_id=player_id,
                username="cap_test_user",
                vibe_energy=100,
                max_vibe_energy=10000,
            )
            session.add(player)

        # 预先添加接近上限的活动记录
        with test_db.get_session() as session:
            activity = CodingActivity(
                player_id=player_id,
                started_at=datetime.utcnow(),
                ended_at=datetime.utcnow(),
                duration_seconds=3600,
                source="test",
                energy_earned=DAILY_ENERGY_CAP - 100,  # 距离上限还剩100
            )
            session.add(activity)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 尝试发放超过剩余上限的能量
            response = await client.post(
                "/api/energy/award",
                json={
                    "player_id": player_id,
                    "duration_minutes": 60,  # 会产生超过100的能量
                },
            )

        assert response.status_code == 200
        data = response.json()
        # 应该触发上限
        assert data["capped"] is True
        assert data["awarded_energy"] <= 100
        assert "已触发每日上限" in data["message"]

    async def test_daily_cap_not_triggered(self, test_db, energy_test_player):
        """测试未触发每日能量上限"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/energy/award",
                json={
                    "player_id": energy_test_player,
                    "duration_minutes": 10,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["capped"] is False


@pytest.mark.asyncio
class TestEnergyHistory:
    """能量历史 API 测试"""

    async def test_get_history_empty(self, test_db, energy_test_player):
        """测试空历史记录"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/energy/history",
                params={"player_id": energy_test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["player_id"] == energy_test_player
        assert data["total"] == 0
        assert data["items"] == []
        assert data["daily_cap"] == DAILY_ENERGY_CAP

    async def test_get_history_with_records(self, test_db, energy_test_player):
        """测试有历史记录"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先发放一些能量
            await client.post(
                "/api/energy/award",
                json={
                    "player_id": energy_test_player,
                    "duration_minutes": 30,
                },
            )
            await client.post(
                "/api/energy/award",
                json={
                    "player_id": energy_test_player,
                    "duration_minutes": 20,
                },
            )

            # 查询历史
            response = await client.get(
                "/api/energy/history",
                params={"player_id": energy_test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_get_history_pagination(self, test_db, energy_test_player):
        """测试历史记录分页"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 创建多条记录
            for _ in range(5):
                await client.post(
                    "/api/energy/award",
                    json={
                        "player_id": energy_test_player,
                        "duration_minutes": 10,
                    },
                )

            # 测试分页
            response = await client.get(
                "/api/energy/history",
                params={"player_id": energy_test_player, "limit": 2, "offset": 0},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    async def test_get_history_player_not_found(self, test_db):
        """测试玩家不存在时返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/energy/history",
                params={"player_id": "non-existent-player"},
            )

        assert response.status_code == 404
        assert "玩家不存在" in response.json()["detail"]


@pytest.mark.asyncio
class TestEnergyStatus:
    """能量状态 API 测试"""

    async def test_get_status_success(self, test_db, energy_test_player):
        """测试获取能量状态"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/energy/status",
                params={"player_id": energy_test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["player_id"] == energy_test_player
        assert data["current_energy"] == 100
        assert data["max_energy"] == 1000
        assert data["daily_earned"] == 0
        assert data["daily_cap"] == DAILY_ENERGY_CAP
        assert data["daily_remaining"] == DAILY_ENERGY_CAP

    async def test_get_status_after_award(self, test_db, energy_test_player):
        """测试发放能量后的状态"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 发放能量
            award_response = await client.post(
                "/api/energy/award",
                json={
                    "player_id": energy_test_player,
                    "duration_minutes": 30,
                },
            )
            awarded = award_response.json()["awarded_energy"]

            # 获取状态
            response = await client.get(
                "/api/energy/status",
                params={"player_id": energy_test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["current_energy"] == 100 + awarded
        assert data["daily_earned"] == awarded
        assert data["daily_remaining"] == DAILY_ENERGY_CAP - awarded

    async def test_get_status_player_not_found(self, test_db):
        """测试玩家不存在时返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/energy/status",
                params={"player_id": "non-existent-player"},
            )

        assert response.status_code == 404
        assert "玩家不存在" in response.json()["detail"]


@pytest.mark.asyncio
class TestEnergyIntegration:
    """能量 API 集成测试"""

    async def test_full_energy_workflow(self, test_db, energy_test_player):
        """测试完整的能量工作流"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 先计算能量（预览）
            calc_response = await client.post(
                "/api/energy/calculate",
                json={
                    "duration_minutes": 45,
                    "consecutive_days": 5,
                    "is_flow_state": True,
                    "quality": {
                        "success_rate": 0.9,
                        "lines_changed": 200,
                    },
                },
            )
            assert calc_response.status_code == 200
            preview_energy = calc_response.json()["vibe_energy"]

            # 2. 检查初始状态
            status_before = await client.get(
                "/api/energy/status",
                params={"player_id": energy_test_player},
            )
            assert status_before.json()["daily_earned"] == 0

            # 3. 发放能量
            award_response = await client.post(
                "/api/energy/award",
                json={
                    "player_id": energy_test_player,
                    "duration_minutes": 45,
                    "consecutive_days": 5,
                    "is_flow_state": True,
                    "quality": {
                        "success_rate": 0.9,
                        "lines_changed": 200,
                    },
                },
            )
            assert award_response.status_code == 200
            awarded_energy = award_response.json()["awarded_energy"]

            # 4. 验证发放的能量与预览一致（或因上限而减少）
            assert awarded_energy <= preview_energy

            # 5. 检查状态更新
            status_after = await client.get(
                "/api/energy/status",
                params={"player_id": energy_test_player},
            )
            assert status_after.json()["daily_earned"] == awarded_energy
            # 能量可能被上限限制，所以检查不超过 max_energy
            assert status_after.json()["current_energy"] <= status_after.json()["max_energy"]

            # 6. 检查历史记录
            history_response = await client.get(
                "/api/energy/history",
                params={"player_id": energy_test_player},
            )
            assert history_response.json()["total"] == 1
            assert history_response.json()["items"][0]["energy_earned"] == awarded_energy
