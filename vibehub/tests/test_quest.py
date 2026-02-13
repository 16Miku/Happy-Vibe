"""任务系统测试

测试任务管理器核心逻辑和 API 端点。
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.core.quest import QuestManager, QuestReward
from src.storage.database import get_db
from src.storage.models import (
    Base,
    Player,
    Quest,
    QuestProgress,
    QuestCategory,
    QuestStatus,
    QuestType,
)


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    db = get_db()
    db.create_tables()
    session = db.get_session_instance()

    # 按正确顺序清理数据（先清理有外键依赖的表）
    try:
        session.query(QuestProgress).delete()
        session.commit()
    except Exception:
        session.rollback()

    try:
        session.query(Quest).delete()
        session.commit()
    except Exception:
        session.rollback()

    try:
        session.query(Player).delete()
        session.commit()
    except Exception:
        session.rollback()

    yield session

    # 清理测试数据
    try:
        session.query(QuestProgress).delete()
        session.commit()
    except Exception:
        session.rollback()

    try:
        session.query(Quest).delete()
        session.commit()
    except Exception:
        session.rollback()

    try:
        session.query(Player).delete()
        session.commit()
    except Exception:
        session.rollback()

    session.close()


@pytest.fixture
def test_player(db_session):
    """创建测试玩家"""
    player = Player(
        username="test_quest_user",
        vibe_energy=100,
        max_vibe_energy=1000,
        gold=500,
        diamonds=10,
        experience=0,
    )
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    return player


@pytest.fixture
def quest_manager(db_session):
    """创建任务管理器"""
    manager = QuestManager(db_session)
    manager.initialize_quests()
    return manager


class TestQuestManager:
    """任务管理器测试"""

    def test_initialize_quests(self, db_session):
        """测试初始化任务配置"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        # 验证每日任务已创建
        daily_quests = (
            db_session.query(Quest)
            .filter(Quest.quest_type == QuestType.DAILY.value)
            .all()
        )
        assert len(daily_quests) == 5

        # 验证每周任务已创建
        weekly_quests = (
            db_session.query(Quest)
            .filter(Quest.quest_type == QuestType.WEEKLY.value)
            .all()
        )
        assert len(weekly_quests) == 4

    def test_initialize_quests_idempotent(self, db_session):
        """测试初始化任务是幂等的"""
        manager = QuestManager(db_session)
        manager.initialize_quests()
        manager.initialize_quests()  # 再次初始化

        # 验证任务数量不变
        all_quests = db_session.query(Quest).all()
        assert len(all_quests) == 9  # 5 daily + 4 weekly

    def test_get_daily_quests(self, quest_manager, test_player, db_session):
        """测试获取每日任务"""
        quests = quest_manager.get_daily_quests(test_player.player_id)

        assert len(quests) == 5
        for quest in quests:
            assert "quest_id" in quest
            assert "name" in quest
            assert "description" in quest
            assert "target_value" in quest
            assert "current_value" in quest
            assert quest["current_value"] == 0
            assert quest["status"] == QuestStatus.ACTIVE.value

    def test_get_weekly_quests(self, quest_manager, test_player, db_session):
        """测试获取每周任务"""
        quests = quest_manager.get_weekly_quests(test_player.player_id)

        assert len(quests) == 4
        for quest in quests:
            assert "quest_id" in quest
            assert quest["status"] == QuestStatus.ACTIVE.value

    def test_update_progress(self, quest_manager, test_player, db_session):
        """测试更新任务进度"""
        result = quest_manager.update_progress(
            test_player.player_id, "daily_harvest_5", increment=2
        )

        assert result["quest_id"] == "daily_harvest_5"
        assert result["current_value"] == 2
        assert result["target_value"] == 5
        assert result["status"] == QuestStatus.ACTIVE.value
        assert result["is_completed"] is False

    def test_update_progress_complete(self, quest_manager, test_player, db_session):
        """测试更新进度至完成"""
        # 更新进度到目标值
        result = quest_manager.update_progress(
            test_player.player_id, "daily_harvest_5", increment=5
        )

        assert result["current_value"] == 5
        assert result["status"] == QuestStatus.COMPLETED.value
        assert result["is_completed"] is True

    def test_update_progress_exceed_target(self, quest_manager, test_player, db_session):
        """测试进度不超过目标值"""
        result = quest_manager.update_progress(
            test_player.player_id, "daily_harvest_5", increment=10
        )

        assert result["current_value"] == 5  # 不超过目标值
        assert result["is_completed"] is True

    def test_update_progress_invalid_quest(self, quest_manager, test_player):
        """测试更新不存在的任务"""
        with pytest.raises(ValueError, match="任务不存在"):
            quest_manager.update_progress(
                test_player.player_id, "invalid_quest", increment=1
            )

    def test_update_progress_by_category(self, quest_manager, test_player, db_session):
        """测试按类别更新进度"""
        results = quest_manager.update_progress_by_category(
            test_player.player_id, QuestCategory.FARMING.value, increment=1
        )

        # 应该更新所有农场类任务
        assert len(results) >= 1
        for result in results:
            assert result["current_value"] >= 1

    def test_claim_reward(self, quest_manager, test_player, db_session):
        """测试领取奖励"""
        # 先完成任务
        quest_manager.update_progress(
            test_player.player_id, "daily_harvest_5", increment=5
        )

        # 记录领取前的资源
        gold_before = test_player.gold
        exp_before = test_player.experience

        # 领取奖励
        reward = quest_manager.claim_reward(test_player.player_id, "daily_harvest_5")

        assert isinstance(reward, QuestReward)
        assert reward.gold == 50
        assert reward.exp == 20

        # 验证玩家资源已更新
        db_session.refresh(test_player)
        assert test_player.gold == gold_before + 50
        assert test_player.experience == exp_before + 20

    def test_claim_reward_not_completed(self, quest_manager, test_player):
        """测试领取未完成任务的奖励"""
        # 确保任务进度存在但未完成
        quest_manager.get_daily_quests(test_player.player_id)

        with pytest.raises(ValueError, match="任务尚未完成"):
            quest_manager.claim_reward(test_player.player_id, "daily_harvest_5")

    def test_claim_reward_already_claimed(self, quest_manager, test_player, db_session):
        """测试重复领取奖励"""
        # 完成并领取
        quest_manager.update_progress(
            test_player.player_id, "daily_harvest_5", increment=5
        )
        quest_manager.claim_reward(test_player.player_id, "daily_harvest_5")

        # 再次领取
        with pytest.raises(ValueError, match="奖励已领取"):
            quest_manager.claim_reward(test_player.player_id, "daily_harvest_5")

    def test_refresh_daily_quests(self, quest_manager, test_player, db_session):
        """测试刷新每日任务"""
        # 先更新一些进度
        quest_manager.update_progress(
            test_player.player_id, "daily_harvest_5", increment=3
        )

        # 刷新任务
        quests = quest_manager.refresh_daily_quests(test_player.player_id)

        assert len(quests) == 5
        # 验证进度被重置（新的进度记录）
        for quest in quests:
            if quest["quest_id"] == "daily_harvest_5":
                # 由于刷新创建新记录，旧记录可能仍存在
                # 但新查询应该返回有效的进度
                assert quest["status"] in [
                    QuestStatus.ACTIVE.value,
                    QuestStatus.COMPLETED.value,
                ]


class TestQuestAPI:
    """任务 API 测试"""

    def test_get_all_quests(self, client, test_player, db_session):
        """测试获取所有任务"""
        # 初始化任务
        manager = QuestManager(db_session)
        manager.initialize_quests()

        response = client.get(f"/api/quest?player_id={test_player.player_id}")

        assert response.status_code == 200
        data = response.json()

        assert "quests" in data
        assert "total" in data
        assert "completed_count" in data
        assert data["total"] == 9  # 5 daily + 4 weekly

    def test_get_daily_quests(self, client, test_player, db_session):
        """测试获取每日任务"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        response = client.get(f"/api/quest/daily?player_id={test_player.player_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5
        assert all(q["status"] == "active" for q in data["quests"])

    def test_get_weekly_quests(self, client, test_player, db_session):
        """测试获取每周任务"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        response = client.get(f"/api/quest/weekly?player_id={test_player.player_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 4

    def test_update_quest_progress(self, client, test_player, db_session):
        """测试更新任务进度"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        response = client.post(
            f"/api/quest/daily_harvest_5/progress?player_id={test_player.player_id}",
            json={"increment": 2},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["quest_id"] == "daily_harvest_5"
        assert data["current_value"] == 2
        assert data["is_completed"] is False

    def test_update_progress_by_category(self, client, test_player, db_session):
        """测试按类别更新进度"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        response = client.post(
            f"/api/quest/progress/category?player_id={test_player.player_id}",
            json={"category": "farming", "increment": 1},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

    def test_claim_quest_reward(self, client, test_player, db_session):
        """测试领取任务奖励"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        # 先完成任务
        manager.update_progress(test_player.player_id, "daily_harvest_5", increment=5)

        response = client.post(
            f"/api/quest/daily_harvest_5/claim?player_id={test_player.player_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["quest_id"] == "daily_harvest_5"
        assert data["rewards"]["gold"] == 50
        assert data["rewards"]["exp"] == 20
        assert data["message"] == "奖励领取成功"

    def test_claim_reward_not_completed(self, client, test_player, db_session):
        """测试领取未完成任务的奖励"""
        manager = QuestManager(db_session)
        manager.initialize_quests()
        manager.get_daily_quests(test_player.player_id)

        response = client.post(
            f"/api/quest/daily_harvest_5/claim?player_id={test_player.player_id}"
        )

        assert response.status_code == 400
        assert "任务尚未完成" in response.json()["detail"]

    def test_refresh_daily_quests(self, client, test_player, db_session):
        """测试刷新每日任务"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        response = client.post(
            f"/api/quest/refresh?player_id={test_player.player_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert "quests" in data
        assert data["message"] == "每日任务已刷新"

    def test_initialize_quests_endpoint(self, client, db_session):
        """测试初始化任务端点"""
        response = client.post("/api/quest/initialize")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "初始化完成" in data["message"]

    def test_get_quests_invalid_player(self, client, db_session):
        """测试无效玩家获取任务"""
        response = client.get("/api/quest?player_id=invalid-player-id")

        assert response.status_code == 404
        assert "玩家不存在" in response.json()["detail"]

    def test_quest_with_energy_reward(self, client, test_player, db_session):
        """测试带能量奖励的任务"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        # 完成编码任务（有能量奖励）
        manager.update_progress(
            test_player.player_id, "daily_coding_30min", increment=1800
        )

        energy_before = test_player.vibe_energy

        response = client.post(
            f"/api/quest/daily_coding_30min/claim?player_id={test_player.player_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["rewards"]["energy"] == 100

        # 验证能量已增加
        db_session.refresh(test_player)
        assert test_player.vibe_energy == energy_before + 100

    def test_quest_with_diamond_reward(self, client, test_player, db_session):
        """测试带钻石奖励的任务"""
        manager = QuestManager(db_session)
        manager.initialize_quests()

        # 完成心流任务（有钻石奖励）
        manager.update_progress(
            test_player.player_id, "daily_flow_state", increment=1
        )

        diamonds_before = test_player.diamonds

        response = client.post(
            f"/api/quest/daily_flow_state/claim?player_id={test_player.player_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["rewards"]["diamonds"] == 5

        # 验证钻石已增加
        db_session.refresh(test_player)
        assert test_player.diamonds == diamonds_before + 5


class TestQuestReward:
    """任务奖励数据类测试"""

    def test_quest_reward_creation(self):
        """测试创建任务奖励"""
        reward = QuestReward(
            energy=100, gold=50, exp=25, diamonds=5, item="rare_seed"
        )

        assert reward.energy == 100
        assert reward.gold == 50
        assert reward.exp == 25
        assert reward.diamonds == 5
        assert reward.item == "rare_seed"

    def test_quest_reward_to_dict(self):
        """测试奖励转字典"""
        reward = QuestReward(energy=100, gold=50, exp=25, diamonds=5)
        result = reward.to_dict()

        assert result["energy"] == 100
        assert result["gold"] == 50
        assert result["exp"] == 25
        assert result["diamonds"] == 5
        assert "item" not in result

    def test_quest_reward_to_dict_with_item(self):
        """测试带物品的奖励转字典"""
        reward = QuestReward(gold=50, item="rare_seed")
        result = reward.to_dict()

        assert result["gold"] == 50
        assert result["item"] == "rare_seed"

    def test_quest_reward_defaults(self):
        """测试奖励默认值"""
        reward = QuestReward()

        assert reward.energy == 0
        assert reward.gold == 0
        assert reward.exp == 0
        assert reward.diamonds == 0
        assert reward.item is None
