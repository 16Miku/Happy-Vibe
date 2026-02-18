"""任务 API 单元测试"""

import uuid

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.storage.models import Player, Quest, QuestProgress, QuestType


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def quest_test_player(test_db):
    """创建测试玩家"""
    unique_name = f"test_quest_api_player_{uuid.uuid4().hex[:8]}"
    player_id = f"quest-test-player-{uuid.uuid4().hex[:8]}"
    with test_db.get_session() as session:
        player = Player(
            player_id=player_id,
            username=unique_name,
            vibe_energy=100,
            max_vibe_energy=1000,
            gold=500,
            diamonds=10,
            experience=0,
        )
        session.add(player)
    return player_id


class TestQuestAPI:
    """任务 API 测试"""

    def test_get_daily_quests(self, client, quest_test_player, test_db):
        """测试获取每日任务"""
        response = client.get(f"/api/quest/daily?player_id={quest_test_player}")

        assert response.status_code == 200
        data = response.json()

        assert "quests" in data
        assert "total" in data
        assert data["total"] >= 1  # 至少有1个每日任务

    def test_get_daily_quests_invalid_player(self, client, test_db):
        """测试无效玩家获取每日任务"""
        response = client.get("/api/quest/daily?player_id=invalid-player-id")

        assert response.status_code == 404
        assert "玩家不存在" in response.json()["detail"]

    def test_get_progress(self, client, quest_test_player, test_db):
        """测试获取任务进度"""
        # 先获取每日任务以初始化
        daily_response = client.get(f"/api/quest/daily?player_id={quest_test_player}")
        assert daily_response.status_code == 200

        quests = daily_response.json().get("quests", [])
        if not quests:
            pytest.skip("没有可用的每日任务")

        quest_id = quests[0]["quest_id"]

        response = client.get(
            f"/api/quest/{quest_id}/progress?player_id={quest_test_player}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["quest_id"] == quest_id
        assert "current_value" in data
        assert "is_completed" in data

    def test_complete_quest(self, client, quest_test_player, test_db):
        """测试完成任务"""
        # 先获取每日任务以初始化
        daily_response = client.get(f"/api/quest/daily?player_id={quest_test_player}")
        assert daily_response.status_code == 200

        quests = daily_response.json().get("quests", [])
        if not quests:
            pytest.skip("没有可用的每日任务")

        quest_id = quests[0]["quest_id"]

        response = client.post(
            f"/api/quest/{quest_id}/complete?player_id={quest_test_player}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["quest_id"] == quest_id
        assert "reward" in data

    def test_complete_quest_already_completed(self, client, quest_test_player, test_db):
        """测试重复完成任务"""
        # 先获取每日任务以初始化
        daily_response = client.get(f"/api/quest/daily?player_id={quest_test_player}")
        assert daily_response.status_code == 200

        quests = daily_response.json().get("quests", [])
        if not quests:
            pytest.skip("没有可用的每日任务")

        quest_id = quests[0]["quest_id"]

        # 第一次完成
        client.post(
            f"/api/quest/{quest_id}/complete?player_id={quest_test_player}"
        )

        # 第二次完成
        response = client.post(
            f"/api/quest/{quest_id}/complete?player_id={quest_test_player}"
        )

        assert response.status_code == 400

    def test_claim_reward(self, client, quest_test_player, test_db):
        """测试领取奖励"""
        # 先获取每日任务以初始化
        daily_response = client.get(f"/api/quest/daily?player_id={quest_test_player}")
        assert daily_response.status_code == 200

        quests = daily_response.json().get("quests", [])
        if not quests:
            pytest.skip("没有可用的每日任务")

        quest_id = quests[0]["quest_id"]

        # 完成并领取
        response = client.post(
            f"/api/quest/{quest_id}/complete?player_id={quest_test_player}"
        )

        assert response.status_code == 200
        data = response.json()

        assert "reward" in data
        # 奖励可能包含 gold, exp 等
        assert data["reward"] is not None

    def test_get_available_quests(self, client, quest_test_player, test_db):
        """测试获取所有可接受的任务"""
        response = client.get(
            f"/api/quest/available?player_id={quest_test_player}"
        )

        assert response.status_code == 200
        data = response.json()

        assert "quests" in data
        assert data["total"] >= 1  # 至少有1个任务
