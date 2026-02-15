"""成就系统 API 测试

测试成就系统 API 的 REST 端点。
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.storage.database import Database
from src.storage.models import AchievementDefinition, AchievementProgress, Player


@pytest.fixture
def test_db(tmp_path):
    """创建测试数据库"""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.create_tables()

    # 初始化成就定义
    with db.get_session() as session:
        from src.core.achievement_manager import AchievementManager
        manager = AchievementManager(session)
        manager.initialize_achievements()

    return db


@pytest.fixture
def test_player(test_db):
    """创建测试玩家"""
    with test_db.get_session() as session:
        player = Player(
            player_id="test-player-001",
            username="test_user",
            level=15,
            gold=1000,
            experience=500,
        )
        session.add(player)
        session.commit()
        session.refresh(player)
        return player.player_id


class TestAchievementInitialization:
    """成就初始化测试"""

    async def test_initialize_achievements(self):
        """测试初始化成就端点"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/achievement/initialize")

        assert response.status_code == 200
        data = response.json()
        assert "initialized_count" in data
        assert data["initialized_count"] >= 50


class TestGetAchievements:
    """获取成就列表测试"""

    async def test_get_achievements_player_not_found(self):
        """测试玩家不存在时返回错误"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement",
                params={"player_id": "non-existent"},
            )

        # 应该返回空列表而不是 404，因为 API 设计是获取成就列表
        assert response.status_code == 200
        data = response.json()
        assert "achievements" in data

    async def test_get_achievements_success(self, test_db, test_player, monkeypatch):
        """测试成功获取成就列表"""
        # 替换数据库实例
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement",
                params={"player_id": test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert "achievements" in data
        assert "total" in data
        assert len(data["achievements"]) >= 50

    async def test_get_achievements_with_category_filter(
        self, test_db, test_player, monkeypatch
    ):
        """测试按类别筛选成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement",
                params={
                    "player_id": test_player,
                    "category": "coding",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["achievements"]) > 0
        for ach in data["achievements"]:
            assert ach["category"] == "coding"

    async def test_get_achievements_with_tier_filter(
        self, test_db, test_player, monkeypatch
    ):
        """测试按稀有度筛选成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement",
                params={
                    "player_id": test_player,
                    "tier": "legendary",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["achievements"]) > 0
        for ach in data["achievements"]:
            assert ach["tier"] == "legendary"

    async def test_get_achievements_with_hidden(
        self, test_db, test_player, monkeypatch
    ):
        """测试包含隐藏成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 不包含隐藏成就
            response1 = await client.get(
                "/api/achievement",
                params={
                    "player_id": test_player,
                    "include_hidden": False,
                },
            )

            # 包含隐藏成就
            response2 = await client.get(
                "/api/achievement",
                params={
                    "player_id": test_player,
                    "include_hidden": True,
                },
            )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # 包含隐藏成就时应该有更多或相同数量
        assert len(data2["achievements"]) >= len(data1["achievements"])


class TestAchievementStats:
    """成就统计测试"""

    async def test_get_achievement_stats(
        self, test_db, test_player, monkeypatch
    ):
        """测试获取成就统计"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement/stats",
                params={"player_id": test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert "total_achievements" in data
        assert "unlocked_count" in data
        assert "completed_count" in data
        assert "claimed_count" in data
        assert "unlocked_percent" in data
        assert data["total_achievements"] >= 50

    async def test_get_achievement_stats_not_found(self):
        """测试不存在玩家的统计"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement/stats",
                params={"player_id": "non-existent"},
            )

        assert response.status_code == 404


class TestGetSingleAchievement:
    """获取单个成就详情测试"""

    async def test_get_achievement_not_found(
        self, test_db, test_player, monkeypatch
    ):
        """测试成就不存在时返回 404"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement/non_existent",
                params={"player_id": test_player},
            )

        assert response.status_code == 404

    async def test_get_achievement_success(
        self, test_db, test_player, monkeypatch
    ):
        """测试成功获取成就详情"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement/coding_first",
                params={"player_id": test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["achievement_id"] == "coding_first"
        assert data["title_zh"] == "初次编码"
        assert data["current_value"] == 0
        assert data["is_completed"] is False


class TestUpdateProgress:
    """更新进度测试"""

    async def test_update_progress_creates_record(
        self, test_db, test_player, monkeypatch
    ):
        """测试更新进度时创建记录"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievement/coding_first/progress",
                params={"player_id": test_player},
                json={"increment": 1},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["achievement_id"] == "coding_first"
        assert data["current_value"] == 1
        assert data["is_completed"] is True
        assert data["newly_completed"] is True

    async def test_update_progress_increment(
        self, test_db, test_player, monkeypatch
    ):
        """测试增量更新进度"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 更新到 5
            response1 = await client.post(
                "/api/achievement/coding_10/progress",
                params={"player_id": test_player},
                json={"increment": 5},
            )

            # 再更新 3
            response2 = await client.post(
                "/api/achievement/coding_10/progress",
                params={"player_id": test_player},
                json={"increment": 3},
            )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1["current_value"] == 5
        assert data2["current_value"] == 8

    async def test_update_progress_cap_at_target(
        self, test_db, test_player, monkeypatch
    ):
        """测试进度不超过目标"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievement/coding_first/progress",
                params={"player_id": test_player},
                json={"increment": 100},
            )

        assert response.status_code == 200
        data = response.json()
        # 目标是 1，应该被限制在 1
        assert data["current_value"] == 1
        assert data["progress_percent"] == 100.0


class TestEventUpdate:
    """事件更新测试"""

    async def test_update_by_event(
        self, test_db, test_player, monkeypatch
    ):
        """测试通过事件更新进度"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievement/update",
                params={"player_id": test_player},
                json={
                    "event_type": "coding_count",
                    "event_data": {"increment": 1},
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated_achievements" in data
        assert "count" in data

    async def test_update_by_event_multiple_achievements(
        self, test_db, test_player, monkeypatch
    ):
        """测试一次事件更新多个成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 编程活动会更新多个编程类成就
            response = await client.post(
                "/api/achievement/update",
                params={"player_id": test_player},
                json={
                    "event_type": "coding_count",
                    "event_data": {"increment": 50},
                },
            )

        assert response.status_code == 200
        data = response.json()
        # 应该更新了多个成就（至少 coding_first）
        assert data["count"] >= 1


class TestClaimReward:
    """领取奖励测试"""

    async def test_claim_reward_not_completed(
        self, test_db, test_player, monkeypatch
    ):
        """测试领取未完成成就的奖励"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievement/coding_first/claim",
                params={"player_id": test_player},
            )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_claim_reward_success(
        self, test_db, test_player, monkeypatch
    ):
        """测试成功领取奖励"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先完成成就
            await client.post(
                "/api/achievement/coding_first/progress",
                params={"player_id": test_player},
                json={"increment": 1},
            )

            # 领取奖励
            response = await client.post(
                "/api/achievement/coding_first/claim",
                params={"player_id": test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["achievement_id"] == "coding_first"
        assert data["gold_rewarded"] == 100
        assert data["exp_rewarded"] == 50

    async def test_claim_reward_already_claimed(
        self, test_db, test_player, monkeypatch
    ):
        """测试重复领取奖励"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 完成并领取
            await client.post(
                "/api/achievement/coding_10/progress",
                params={"player_id": test_player},
                json={"increment": 10},
            )
            await client.post(
                "/api/achievement/coding_10/claim",
                params={"player_id": test_player},
            )

            # 再次领取
            response = await client.post(
                "/api/achievement/coding_10/claim",
                params={"player_id": test_player},
            )

        assert response.status_code == 400
        data = response.json()
        assert "已领取" in data["detail"]


class TestEnsureProgress:
    """确保进度记录测试"""

    async def test_ensure_player_progress(
        self, test_db, test_player, monkeypatch
    ):
        """测试确保玩家进度记录"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievement/ensure-progress",
                params={"player_id": test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert "player_id" in data
        assert "message" in data


class TestCategoryCombinations:
    """类别组合测试"""

    @pytest.mark.parametrize(
        "category",
        ["coding", "farming", "social", "economy", "special"],
    )
    async def test_all_categories_have_achievements(
        self, test_db, test_player, monkeypatch, category
    ):
        """测试所有类别都有成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement",
                params={
                    "player_id": test_player,
                    "category": category,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["achievements"]) > 0


class TestTierCombinations:
    """稀有度组合测试"""

    @pytest.mark.parametrize(
        "tier",
        ["common", "rare", "epic", "legendary"],
    )
    async def test_all_tiers_have_achievements(
        self, test_db, test_player, monkeypatch, tier
    ):
        """测试所有稀有度都有成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievement",
                params={
                    "player_id": test_player,
                    "tier": tier,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["achievements"]) > 0
        for ach in data["achievements"]:
            assert ach["tier"] == tier
