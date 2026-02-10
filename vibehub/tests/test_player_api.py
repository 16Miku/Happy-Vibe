"""Player API 测试

测试玩家相关的 REST API 端点，包括：
- 玩家创建、查询、更新
- 能量添加
- 经验值添加和升级
- 统计数据查询
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.storage.database import Database
from src.api.player import calculate_exp_for_level, calculate_level_from_exp


@pytest.fixture
def test_db(tmp_path):
    """创建测试数据库"""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.create_tables()
    return db


@pytest.fixture
def mock_db(test_db, monkeypatch):
    """Mock 全局数据库实例"""
    monkeypatch.setattr("src.api.player.get_db", lambda: test_db)
    return test_db


class TestExpCalculation:
    """经验值计算测试"""

    def test_calculate_exp_for_level_1(self):
        """测试1级所需经验"""
        exp = calculate_exp_for_level(1)
        assert exp == 100

    def test_calculate_exp_for_level_10(self):
        """测试10级所需经验"""
        exp = calculate_exp_for_level(10)
        assert exp == int(100 * (10 ** 1.5))

    def test_calculate_level_from_exp_zero(self):
        """测试0经验对应1级"""
        level = calculate_level_from_exp(0)
        assert level == 1

    def test_calculate_level_from_exp_100(self):
        """测试100经验对应1级"""
        level = calculate_level_from_exp(100)
        assert level == 1

    def test_calculate_level_from_exp_300(self):
        """测试300经验对应2级"""
        # 2级需要 100 * 2^1.5 ≈ 282
        level = calculate_level_from_exp(300)
        assert level == 2

    def test_calculate_level_from_exp_high(self):
        """测试高经验值"""
        # 10级需要 100 * 10^1.5 ≈ 3162
        level = calculate_level_from_exp(5000)
        assert level >= 10


@pytest.mark.asyncio
class TestPlayerAPI:
    """Player API 测试"""

    async def test_get_player_not_found(self, mock_db):
        """测试获取不存在的玩家返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/player")

        assert response.status_code == 404
        assert "玩家不存在" in response.json()["detail"]

    async def test_create_player_success(self, mock_db):
        """测试成功创建玩家"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/player",
                json={"username": "测试玩家"}
            )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "测试玩家"
        assert data["level"] == 1
        assert data["experience"] == 0
        assert data["vibe_energy"] == 100
        assert data["gold"] == 500
        assert "player_id" in data

    async def test_create_player_duplicate(self, mock_db):
        """测试重复创建玩家返回409"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 第一次创建
            await client.post("/api/player", json={"username": "玩家1"})
            # 第二次创建
            response = await client.post("/api/player", json={"username": "玩家2"})

        assert response.status_code == 409
        assert "玩家已存在" in response.json()["detail"]

    async def test_create_player_invalid_username(self, mock_db):
        """测试无效用户名返回422"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/player",
                json={"username": "a"}  # 太短
            )

        assert response.status_code == 422

    async def test_get_player_success(self, mock_db):
        """测试成功获取玩家"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建玩家
            await client.post("/api/player", json={"username": "测试玩家"})
            # 获取玩家
            response = await client.get("/api/player")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "测试玩家"

    async def test_update_player_success(self, mock_db):
        """测试成功更新玩家"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建玩家
            await client.post("/api/player", json={"username": "原名"})
            # 更新玩家
            response = await client.put(
                "/api/player",
                json={
                    "username": "新名字",
                    "focus": 150,
                    "efficiency": 120
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "新名字"
        assert data["focus"] == 150
        assert data["efficiency"] == 120

    async def test_update_player_not_found(self, mock_db):
        """测试更新不存在的玩家返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/player",
                json={"username": "新名字"}
            )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestPlayerStatsAPI:
    """Player Stats API 测试"""

    async def test_get_stats_success(self, mock_db):
        """测试成功获取玩家统计"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建玩家
            await client.post("/api/player", json={"username": "统计测试"})
            # 获取统计
            response = await client.get("/api/player/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "统计测试"
        assert data["level"] == 1
        assert data["total_coding_sessions"] == 0
        assert data["achievements_unlocked"] == 0
        assert "exp_to_next_level" in data

    async def test_get_stats_not_found(self, mock_db):
        """测试获取不存在玩家的统计返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/player/stats")

        assert response.status_code == 404


@pytest.mark.asyncio
class TestAddEnergyAPI:
    """Add Energy API 测试"""

    async def test_add_energy_success(self, mock_db):
        """测试成功添加能量"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建玩家
            await client.post("/api/player", json={"username": "能量测试"})
            # 添加能量
            response = await client.post(
                "/api/player/energy",
                json={"amount": 50, "source": "coding"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["previous_energy"] == 100
        assert data["added_energy"] == 50
        assert data["current_energy"] == 150
        assert data["is_capped"] is False

    async def test_add_energy_capped(self, mock_db):
        """测试能量超过上限被截断"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建玩家
            await client.post("/api/player", json={"username": "能量上限测试"})
            # 添加大量能量（超过上限1000）
            response = await client.post(
                "/api/player/energy",
                json={"amount": 5000}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["current_energy"] == 1000  # max_vibe_energy
        assert data["is_capped"] is True

    async def test_add_energy_invalid_amount(self, mock_db):
        """测试无效能量数量返回422"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post("/api/player", json={"username": "测试"})
            response = await client.post(
                "/api/player/energy",
                json={"amount": -10}  # 负数
            )

        assert response.status_code == 422

    async def test_add_energy_not_found(self, mock_db):
        """测试给不存在的玩家添加能量返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/player/energy",
                json={"amount": 50}
            )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestAddExpAPI:
    """Add Exp API 测试"""

    async def test_add_exp_success(self, mock_db):
        """测试成功添加经验"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建玩家
            await client.post("/api/player", json={"username": "经验测试"})
            # 添加经验
            response = await client.post(
                "/api/player/exp",
                json={"amount": 100, "source": "coding"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["previous_exp"] == 0
        assert data["added_exp"] == 100
        assert data["current_exp"] == 100
        assert data["previous_level"] == 1
        assert data["current_level"] == 1
        assert data["leveled_up"] is False

    async def test_add_exp_level_up(self, mock_db):
        """测试添加经验触发升级"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建玩家
            await client.post("/api/player", json={"username": "升级测试"})
            # 添加大量经验触发升级
            # 2级需要约282经验，3级需要约519经验
            response = await client.post(
                "/api/player/exp",
                json={"amount": 600}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["leveled_up"] is True
        assert data["current_level"] > 1
        assert data["levels_gained"] >= 1

    async def test_add_exp_multiple_levels(self, mock_db):
        """测试一次添加经验升多级"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先创建玩家
            await client.post("/api/player", json={"username": "多级测试"})
            # 添加大量经验
            response = await client.post(
                "/api/player/exp",
                json={"amount": 5000}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["leveled_up"] is True
        assert data["levels_gained"] >= 5

    async def test_add_exp_invalid_amount(self, mock_db):
        """测试无效经验数量返回422"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post("/api/player", json={"username": "测试"})
            response = await client.post(
                "/api/player/exp",
                json={"amount": 0}  # 必须大于0
            )

        assert response.status_code == 422

    async def test_add_exp_not_found(self, mock_db):
        """测试给不存在的玩家添加经验返回404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/player/exp",
                json={"amount": 100}
            )

        assert response.status_code == 404
