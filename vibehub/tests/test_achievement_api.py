"""成就系统 API 测试"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.achievement import (
    ACHIEVEMENT_CONFIG,
    AchievementCategory,
    AchievementRarity,
)
from src.main import app
from src.storage.database import Database
from src.storage.models import Achievement, Player


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
            level=15,
            gold=1000,
            experience=500,
        )
        session.add(player)
        session.commit()
        # 刷新以获取完整对象
        session.refresh(player)
        return player.player_id


@pytest.fixture
def player_with_achievements(test_db, test_player):
    """创建带有成就的玩家"""
    with test_db.get_session() as session:
        # 添加一个已解锁的成就
        unlocked_ach = Achievement(
            player_id=test_player,
            achievement_id="first_code",
            progress=1,
            target=1,
            is_unlocked=True,
        )
        # 添加一个进行中的成就
        in_progress_ach = Achievement(
            player_id=test_player,
            achievement_id="code_hour",
            progress=1800,
            target=3600,
            is_unlocked=False,
        )
        session.add(unlocked_ach)
        session.add(in_progress_ach)
        session.commit()
    return test_player


class TestAchievementConfig:
    """成就配置测试"""

    def test_achievement_config_has_required_fields(self):
        """测试成就配置包含必要字段"""
        required_fields = [
            "name",
            "description",
            "category",
            "rarity",
            "target",
            "reward_gold",
            "reward_exp",
            "icon",
        ]
        for ach_id, config in ACHIEVEMENT_CONFIG.items():
            for field in required_fields:
                assert field in config, f"成就 {ach_id} 缺少字段 {field}"

    def test_achievement_config_has_valid_categories(self):
        """测试成就配置的类别有效"""
        valid_categories = set(AchievementCategory)
        for ach_id, config in ACHIEVEMENT_CONFIG.items():
            assert (
                config["category"] in valid_categories
            ), f"成就 {ach_id} 的类别无效"

    def test_achievement_config_has_valid_rarities(self):
        """测试成就配置的稀有度有效"""
        valid_rarities = set(AchievementRarity)
        for ach_id, config in ACHIEVEMENT_CONFIG.items():
            assert (
                config["rarity"] in valid_rarities
            ), f"成就 {ach_id} 的稀有度无效"

    def test_achievement_config_has_positive_targets(self):
        """测试成就配置的目标值为正数"""
        for ach_id, config in ACHIEVEMENT_CONFIG.items():
            assert config["target"] > 0, f"成就 {ach_id} 的目标值必须为正数"

    def test_achievement_config_count(self):
        """测试成就配置数量"""
        assert len(ACHIEVEMENT_CONFIG) >= 10, "应该至少有 10 个成就配置"


@pytest.mark.asyncio
class TestGetAchievementConfigs:
    """获取成就配置列表测试"""

    async def test_get_all_configs(self):
        """测试获取所有成就配置"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/achievements/config")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(ACHIEVEMENT_CONFIG)

    async def test_get_configs_by_category(self):
        """测试按类别筛选成就配置"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements/config", params={"category": "coding"}
            )

        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["category"] == "coding"


@pytest.mark.asyncio
class TestGetAchievements:
    """获取成就列表测试"""

    async def test_get_achievements_player_not_found(self):
        """测试玩家不存在时返回 404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements", params={"player_id": "non-existent"}
            )

        assert response.status_code == 404

    async def test_get_achievements_success(self, test_db, test_player, monkeypatch):
        """测试成功获取成就列表"""
        # 替换数据库实例
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements", params={"player_id": test_player}
            )

        assert response.status_code == 200
        data = response.json()
        assert "achievements" in data
        assert "total" in data
        assert "unlocked_count" in data
        assert data["total"] == len(ACHIEVEMENT_CONFIG)

    async def test_get_achievements_with_category_filter(
        self, test_db, test_player, monkeypatch
    ):
        """测试按类别筛选成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements",
                params={"player_id": test_player, "category": "farming"},
            )

        assert response.status_code == 200
        data = response.json()
        for ach in data["achievements"]:
            assert ach["category"] == "farming"


@pytest.mark.asyncio
class TestGetUnlockedAchievements:
    """获取已解锁成就测试"""

    async def test_get_unlocked_achievements_empty(
        self, test_db, test_player, monkeypatch
    ):
        """测试没有解锁成就时返回空列表"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements/unlocked", params={"player_id": test_player}
            )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_get_unlocked_achievements_with_data(
        self, test_db, player_with_achievements, monkeypatch
    ):
        """测试获取已解锁成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements/unlocked",
                params={"player_id": player_with_achievements},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["achievement_id"] == "first_code"
        assert data[0]["is_unlocked"] is True


@pytest.mark.asyncio
class TestGetSingleAchievement:
    """获取单个成就详情测试"""

    async def test_get_achievement_not_found(self, test_db, test_player, monkeypatch):
        """测试成就不存在时返回 404"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements/non_existent",
                params={"player_id": test_player},
            )

        assert response.status_code == 404

    async def test_get_achievement_success(self, test_db, test_player, monkeypatch):
        """测试成功获取成就详情"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements/first_code",
                params={"player_id": test_player},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["achievement_id"] == "first_code"
        assert data["name"] == "初次编码"
        assert data["progress"] == 0
        assert data["is_unlocked"] is False

    async def test_get_achievement_with_progress(
        self, test_db, player_with_achievements, monkeypatch
    ):
        """测试获取有进度的成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/achievements/code_hour",
                params={"player_id": player_with_achievements},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["achievement_id"] == "code_hour"
        assert data["progress"] == 1800
        assert data["target"] == 3600
        assert data["is_unlocked"] is False


@pytest.mark.asyncio
class TestUpdateAchievementProgress:
    """更新成就进度测试"""

    async def test_update_progress_player_not_found(self):
        """测试玩家不存在时返回 404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievements/first_code/progress",
                params={"player_id": "non-existent"},
                json={"increment": 1},
            )

        assert response.status_code == 404

    async def test_update_progress_achievement_not_found(
        self, test_db, test_player, monkeypatch
    ):
        """测试成就不存在时返回 404"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievements/non_existent/progress",
                params={"player_id": test_player},
                json={"increment": 1},
            )

        assert response.status_code == 404

    async def test_update_progress_creates_new_record(
        self, test_db, test_player, monkeypatch
    ):
        """测试更新进度时创建新记录"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievements/first_harvest/progress",
                params={"player_id": test_player},
                json={"increment": 1},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["achievement_id"] == "first_harvest"
        assert data["previous_progress"] == 0
        assert data["current_progress"] == 1
        assert data["newly_unlocked"] is True

    async def test_update_progress_increments_existing(
        self, test_db, player_with_achievements, monkeypatch
    ):
        """测试增加现有进度"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievements/code_hour/progress",
                params={"player_id": player_with_achievements},
                json={"increment": 600},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["previous_progress"] == 1800
        assert data["current_progress"] == 2400
        assert data["newly_unlocked"] is False

    async def test_update_progress_unlocks_achievement(
        self, test_db, player_with_achievements, monkeypatch
    ):
        """测试进度达到目标时解锁成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievements/code_hour/progress",
                params={"player_id": player_with_achievements},
                json={"increment": 2000},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["current_progress"] == 3600
        assert data["is_unlocked"] is True
        assert data["newly_unlocked"] is True
        assert data["reward_gold"] == 200
        assert data["reward_exp"] == 100

    async def test_update_progress_already_unlocked(
        self, test_db, player_with_achievements, monkeypatch
    ):
        """测试已解锁成就不再更新进度"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievements/first_code/progress",
                params={"player_id": player_with_achievements},
                json={"increment": 10},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["is_unlocked"] is True
        assert data["newly_unlocked"] is False
        assert data["previous_progress"] == data["current_progress"]


@pytest.mark.asyncio
class TestCheckAchievements:
    """检查成就测试"""

    async def test_check_achievements_player_not_found(self):
        """测试玩家不存在时返回 404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievements/check",
                json={"player_id": "non-existent"},
            )

        assert response.status_code == 404

    async def test_check_achievements_unlocks_level_achievement(
        self, test_db, test_player, monkeypatch
    ):
        """测试检查成就时解锁等级成就"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/achievements/check",
                json={"player_id": test_player},
            )

        assert response.status_code == 200
        data = response.json()
        # 玩家等级 15，应该解锁 level_10 成就
        assert len(data["newly_unlocked"]) >= 1
        unlocked_ids = [a["achievement_id"] for a in data["newly_unlocked"]]
        assert "level_10" in unlocked_ids

    async def test_check_achievements_no_duplicates(
        self, test_db, test_player, monkeypatch
    ):
        """测试重复检查不会重复解锁"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 第一次检查
            response1 = await client.post(
                "/api/achievements/check",
                json={"player_id": test_player},
            )
            # 第二次检查
            response2 = await client.post(
                "/api/achievements/check",
                json={"player_id": test_player},
            )

        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        # 第二次检查不应该有新解锁
        assert len(data2["newly_unlocked"]) == 0
        assert data2["total_reward_gold"] == 0


@pytest.mark.asyncio
class TestAchievementRewards:
    """成就奖励测试"""

    async def test_rewards_added_to_player(
        self, test_db, test_player, monkeypatch
    ):
        """测试解锁成就时奖励正确添加到玩家"""
        monkeypatch.setattr("src.api.achievement.get_db", lambda: test_db)

        # 获取初始金币
        with test_db.get_session() as session:
            player = (
                session.query(Player)
                .filter(Player.player_id == test_player)
                .first()
            )
            initial_gold = player.gold
            initial_exp = player.experience

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 解锁 first_harvest 成就
            response = await client.post(
                "/api/achievements/first_harvest/progress",
                params={"player_id": test_player},
                json={"increment": 1},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["newly_unlocked"] is True

        # 验证奖励已添加
        with test_db.get_session() as session:
            player = (
                session.query(Player)
                .filter(Player.player_id == test_player)
                .first()
            )
            config = ACHIEVEMENT_CONFIG["first_harvest"]
            assert player.gold == initial_gold + config["reward_gold"]
            assert player.experience == initial_exp + config["reward_exp"]
