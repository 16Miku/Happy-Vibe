"""任务 API 单元测试"""

import uuid

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.storage.database import get_db
from src.storage.models import Player, Quest, QuestProgress, QuestType


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

    yield session

    session.close()


@pytest.fixture
def test_player(db_session):
    """创建测试玩家"""
    unique_name = f"test_quest_api_player_{uuid.uuid4().hex[:8]}"
    player = Player(
        username=unique_name,
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


class TestQuestAPI:
    """任务 API 测试"""

    def test_get_daily_quests(self, client, test_player, db_session):
        """测试获取每日任务"""
        response = client.get(f"/api/quest/daily?player_id={test_player.player_id}")

        assert response.status_code == 200
        data = response.json()

        assert "quests" in data
        assert "total" in data
        assert data["total"] == 5  # 默认5个每日任务

    def test_get_daily_quests_invalid_player(self, client, db_session):
        """测试无效玩家获取每日任务"""
        response = client.get("/api/quest/daily?player_id=invalid-player-id")

        assert response.status_code == 404
        assert "玩家不存在" in response.json()["detail"]

    def test_get_progress(self, client, test_player, db_session):
        """测试获取任务进度"""
        # 先获取每日任务以初始化
        client.get(f"/api/quest/daily?player_id={test_player.player_id}")

        # 获取签到任务
        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.DAILY_CHECK_IN.value
        ).first()

        response = client.get(
            f"/api/quest/{quest.quest_id}/progress?player_id={test_player.player_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["quest_id"] == quest.quest_id
        assert data["current_value"] == 0
        assert data["is_completed"] is False

    def test_complete_quest(self, client, test_player, db_session):
        """测试完成任务"""
        # 先获取每日任务以初始化
        client.get(f"/api/quest/daily?player_id={test_player.player_id}")

        # 获取签到任务
        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.DAILY_CHECK_IN.value
        ).first()

        response = client.post(
            f"/api/quest/{quest.quest_id}/complete?player_id={test_player.player_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["quest_id"] == quest.quest_id
        assert "reward" in data
        assert "claimed_at" in data

    def test_complete_quest_already_completed(self, client, test_player, db_session):
        """测试重复完成任务"""
        # 先获取每日任务以初始化
        client.get(f"/api/quest/daily?player_id={test_player.player_id}")

        # 获取签到任务
        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.DAILY_CHECK_IN.value
        ).first()

        # 第一次完成
        client.post(
            f"/api/quest/{quest.quest_id}/complete?player_id={test_player.player_id}"
        )

        # 第二次完成
        response = client.post(
            f"/api/quest/{quest.quest_id}/complete?player_id={test_player.player_id}"
        )

        assert response.status_code == 400

    def test_claim_reward(self, client, test_player, db_session):
        """测试领取奖励"""
        # 先获取每日任务以初始化
        client.get(f"/api/quest/daily?player_id={test_player.player_id}")

        # 获取签到任务
        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.DAILY_CHECK_IN.value
        ).first()

        # 完成并领取
        response = client.post(
            f"/api/quest/{quest.quest_id}/complete?player_id={test_player.player_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["reward"]["gold"] == 50
        assert data["reward"]["exp"] == 20

    def test_get_available_quests(self, client, test_player, db_session):
        """测试获取所有可接受的任务"""
        response = client.get(
            f"/api/quest/available?player_id={test_player.player_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert "quests" in data
        assert data["total"] >= 5  # 至少有5个每日任务
