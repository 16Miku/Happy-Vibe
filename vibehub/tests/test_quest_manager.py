"""任务管理器单元测试"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.core.quest import QuestManager, QuestReward
from src.storage.database import get_db
from src.storage.models import Player, Quest, QuestProgress, QuestType


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
    unique_name = f"test_quest_player_{uuid.uuid4().hex[:8]}"
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


@pytest.fixture
def quest_manager(db_session):
    """创建任务管理器"""
    return QuestManager(db_session)


class TestQuestManager:
    """任务管理器测试"""

    def test_get_daily_quests(self, quest_manager, test_player):
        """测试获取每日任务"""
        quests = quest_manager.get_daily_quests(test_player.player_id)

        assert len(quests) == 5  # 默认5个每日任务
        for quest in quests:
            assert quest.is_daily is True
            assert quest.is_active is True

    def test_update_progress(self, quest_manager, test_player, db_session):
        """测试更新任务进度"""
        # 初始化任务
        quest_manager.initialize_daily_quests()

        # 更新编码时长任务进度
        completed = quest_manager.update_progress(
            test_player.player_id,
            QuestType.CODING_TIME.value,
            delta=600,  # 10分钟
        )

        assert completed is False  # 还没完成

        # 获取进度
        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.CODING_TIME.value
        ).first()
        progress = db_session.query(QuestProgress).filter(
            QuestProgress.player_id == test_player.player_id,
            QuestProgress.quest_id == quest.quest_id,
        ).first()

        assert progress.current_value == 600

    def test_complete_quest(self, quest_manager, test_player, db_session):
        """测试完成任务"""
        quest_manager.initialize_daily_quests()

        # 获取签到任务
        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.DAILY_CHECK_IN.value
        ).first()

        # 完成任务
        reward = quest_manager.complete_quest(test_player.player_id, quest.quest_id)

        assert isinstance(reward, QuestReward)

        # 验证进度已完成
        progress = db_session.query(QuestProgress).filter(
            QuestProgress.player_id == test_player.player_id,
            QuestProgress.quest_id == quest.quest_id,
        ).first()

        assert progress.is_completed is True

    def test_claim_reward(self, quest_manager, test_player, db_session):
        """测试领取奖励"""
        quest_manager.initialize_daily_quests()

        # 获取签到任务
        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.DAILY_CHECK_IN.value
        ).first()

        # 完成任务
        quest_manager.complete_quest(test_player.player_id, quest.quest_id)

        # 记录领取前的资源
        gold_before = test_player.gold
        exp_before = test_player.experience

        # 领取奖励
        result = quest_manager.claim_reward(test_player.player_id, quest.quest_id)

        assert "quest_id" in result
        assert "reward" in result
        assert "claimed_at" in result

        # 验证资源已增加
        db_session.refresh(test_player)
        assert test_player.gold > gold_before
        assert test_player.experience > exp_before

    def test_daily_refresh(self, quest_manager, test_player, db_session):
        """测试每日刷新"""
        quest_manager.initialize_daily_quests()

        # 获取任务并更新进度
        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.HARVEST_CROPS.value
        ).first()

        quest_manager.update_progress(
            test_player.player_id,
            QuestType.HARVEST_CROPS.value,
            delta=3,
        )

        # 验证进度已更新
        progress = db_session.query(QuestProgress).filter(
            QuestProgress.player_id == test_player.player_id,
            QuestProgress.quest_id == quest.quest_id,
        ).first()

        assert progress.current_value == 3

        # 模拟跨天 - 修改所有进度的 last_refresh 为2天前
        all_progress = db_session.query(QuestProgress).filter(
            QuestProgress.player_id == test_player.player_id,
        ).all()

        for p in all_progress:
            p.last_refresh = datetime.utcnow() - timedelta(days=2)
        db_session.commit()

        # 再次获取任务会触发刷新
        quest_manager.get_or_create_progress(test_player.player_id, quest.quest_id)

        # 验证进度已被重置
        db_session.refresh(progress)
        assert progress.current_value == 0

    def test_claim_reward_not_completed(self, quest_manager, test_player, db_session):
        """测试领取未完成任务的奖励"""
        quest_manager.initialize_daily_quests()

        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.CODING_TIME.value
        ).first()

        # 创建进度但不完成
        quest_manager.get_or_create_progress(test_player.player_id, quest.quest_id)

        with pytest.raises(ValueError, match="任务尚未完成"):
            quest_manager.claim_reward(test_player.player_id, quest.quest_id)

    def test_claim_reward_already_claimed(self, quest_manager, test_player, db_session):
        """测试重复领取奖励"""
        quest_manager.initialize_daily_quests()

        quest = db_session.query(Quest).filter(
            Quest.quest_type == QuestType.DAILY_CHECK_IN.value
        ).first()

        # 完成并领取
        quest_manager.complete_quest(test_player.player_id, quest.quest_id)
        quest_manager.claim_reward(test_player.player_id, quest.quest_id)

        # 再次领取
        with pytest.raises(ValueError, match="奖励已领取"):
            quest_manager.claim_reward(test_player.player_id, quest.quest_id)


class TestQuestReward:
    """任务奖励测试"""

    def test_from_json(self):
        """测试从JSON创建奖励"""
        json_str = '{"gold": 100, "exp": 50, "energy": 25}'
        reward = QuestReward.from_json(json_str)

        assert reward.gold == 100
        assert reward.exp == 50
        assert reward.energy == 25
        assert reward.diamonds == 0

    def test_from_json_empty(self):
        """测试空JSON"""
        reward = QuestReward.from_json("")
        assert reward.gold == 0
        assert reward.exp == 0

    def test_to_dict(self):
        """测试转换为字典"""
        reward = QuestReward(gold=100, exp=50, energy=25)
        result = reward.to_dict()

        assert result["gold"] == 100
        assert result["exp"] == 50
        assert result["energy"] == 25
