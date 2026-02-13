"""任务管理器

实现任务系统的核心逻辑，包括：
- 每日任务的获取和刷新
- 任务进度更新
- 奖励领取
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.models import (
    DEFAULT_DAILY_QUESTS,
    Player,
    Quest,
    QuestProgress,
    QuestType,
    generate_uuid,
)


@dataclass
class QuestReward:
    """任务奖励数据类"""

    energy: int = 0
    gold: int = 0
    exp: int = 0
    diamonds: int = 0
    item: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            "energy": self.energy,
            "gold": self.gold,
            "exp": self.exp,
            "diamonds": self.diamonds,
        }
        if self.item:
            result["item"] = self.item
        return result

    @classmethod
    def from_json(cls, json_str: str) -> "QuestReward":
        """从JSON字符串创建"""
        if not json_str:
            return cls()
        data = json.loads(json_str)
        return cls(
            energy=data.get("energy", 0),
            gold=data.get("gold", 0),
            exp=data.get("exp", 0),
            diamonds=data.get("diamonds", 0),
            item=data.get("item"),
        )


class QuestManager:
    """任务管理器

    负责任务的创建、进度更新、奖励发放等核心逻辑。
    """

    def __init__(self, db: Session):
        self.db = db

    def initialize_daily_quests(self) -> None:
        """初始化每日任务配置到数据库"""
        for quest_config in DEFAULT_DAILY_QUESTS:
            existing = self.db.execute(
                select(Quest).where(
                    Quest.quest_type == quest_config["quest_type"],
                    Quest.is_daily == True,  # noqa: E712
                )
            ).scalar_one_or_none()

            if not existing:
                quest = Quest(
                    quest_type=quest_config["quest_type"],
                    title=quest_config["title"],
                    description=quest_config["description"],
                    target_value=quest_config["target_value"],
                    reward_json=quest_config.get("reward_json"),
                    is_daily=True,
                    is_active=True,
                )
                self.db.add(quest)

        self.db.commit()

    def get_daily_quests(self, player_id: str) -> list[Quest]:
        """获取玩家的每日任务列表

        Args:
            player_id: 玩家ID

        Returns:
            每日任务列表
        """
        # 确保每日任务已初始化
        self.initialize_daily_quests()

        # 查询所有每日任务
        quests = self.db.execute(
            select(Quest).where(
                Quest.is_daily == True,  # noqa: E712
                Quest.is_active == True,  # noqa: E712
            )
        ).scalars().all()

        return list(quests)

    def get_or_create_progress(
        self, player_id: str, quest_id: str
    ) -> QuestProgress:
        """获取或创建任务进度

        Args:
            player_id: 玩家ID
            quest_id: 任务ID

        Returns:
            任务进度记录
        """
        # 检查是否需要刷新
        if self.should_refresh_daily(player_id):
            self._refresh_daily_progress(player_id)

        # 查找现有进度
        progress = self.db.execute(
            select(QuestProgress).where(
                QuestProgress.player_id == player_id,
                QuestProgress.quest_id == quest_id,
            )
        ).scalar_one_or_none()

        if not progress:
            # 创建新进度
            progress = QuestProgress(
                player_id=player_id,
                quest_id=quest_id,
                current_value=0,
                is_completed=False,
                is_claimed=False,
                last_refresh=datetime.utcnow(),
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)

        return progress

    def update_progress(
        self, player_id: str, quest_type: str, delta: int = 1
    ) -> bool:
        """更新任务进度

        Args:
            player_id: 玩家ID
            quest_type: 任务类型
            delta: 增加的进度值

        Returns:
            是否有任务完成
        """
        # 查找该类型的任务
        quest = self.db.execute(
            select(Quest).where(
                Quest.quest_type == quest_type,
                Quest.is_active == True,  # noqa: E712
            )
        ).scalar_one_or_none()

        if not quest:
            return False

        # 获取或创建进度
        progress = self.get_or_create_progress(player_id, quest.quest_id)

        # 如果已完成，不再更新
        if progress.is_completed:
            return False

        # 更新进度
        progress.current_value += delta

        # 检查是否完成
        completed = False
        if progress.current_value >= quest.target_value:
            progress.current_value = quest.target_value
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            completed = True

        self.db.commit()
        return completed

    def complete_quest(self, player_id: str, quest_id: str) -> QuestReward:
        """完成任务（手动标记完成）

        Args:
            player_id: 玩家ID
            quest_id: 任务ID

        Returns:
            任务奖励

        Raises:
            ValueError: 任务不存在或已完成
        """
        quest = self.db.execute(
            select(Quest).where(Quest.quest_id == quest_id)
        ).scalar_one_or_none()

        if not quest:
            raise ValueError(f"任务不存在: {quest_id}")

        progress = self.get_or_create_progress(player_id, quest_id)

        if progress.is_completed:
            raise ValueError("任务已完成")

        # 标记完成
        progress.current_value = quest.target_value
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()

        self.db.commit()

        return QuestReward.from_json(quest.reward_json or "{}")

    def claim_reward(self, player_id: str, quest_id: str) -> dict:
        """领取任务奖励

        Args:
            player_id: 玩家ID
            quest_id: 任务ID

        Returns:
            领取的奖励详情

        Raises:
            ValueError: 任务未完成或已领取
        """
        quest = self.db.execute(
            select(Quest).where(Quest.quest_id == quest_id)
        ).scalar_one_or_none()

        if not quest:
            raise ValueError(f"任务不存在: {quest_id}")

        progress = self.db.execute(
            select(QuestProgress).where(
                QuestProgress.player_id == player_id,
                QuestProgress.quest_id == quest_id,
            )
        ).scalar_one_or_none()

        if not progress:
            raise ValueError("任务进度不存在")

        if not progress.is_completed:
            raise ValueError("任务尚未完成")

        if progress.is_claimed:
            raise ValueError("奖励已领取")

        # 获取玩家
        player = self.db.execute(
            select(Player).where(Player.player_id == player_id)
        ).scalar_one_or_none()

        if not player:
            raise ValueError(f"玩家不存在: {player_id}")

        # 解析奖励
        reward = QuestReward.from_json(quest.reward_json or "{}")

        # 发放奖励
        player.vibe_energy = min(
            player.vibe_energy + reward.energy, player.max_vibe_energy
        )
        player.gold += reward.gold
        player.experience += reward.exp
        player.diamonds += reward.diamonds

        # 标记已领取
        progress.is_claimed = True
        progress.claimed_at = datetime.utcnow()

        self.db.commit()

        return {
            "quest_id": quest_id,
            "reward": reward.to_dict(),
            "claimed_at": progress.claimed_at.isoformat(),
        }

    def should_refresh_daily(self, player_id: str) -> bool:
        """检查是否需要刷新每日任务

        Args:
            player_id: 玩家ID

        Returns:
            是否需要刷新
        """
        # 获取任意一个每日任务的进度
        progress = self.db.execute(
            select(QuestProgress).where(
                QuestProgress.player_id == player_id,
            )
        ).scalars().first()

        if not progress or not progress.last_refresh:
            return True

        # 检查是否跨天（以凌晨4点为界）
        now = datetime.utcnow()
        last_refresh = progress.last_refresh

        # 计算上次刷新的"游戏日"
        last_game_day = self._get_game_day(last_refresh)
        current_game_day = self._get_game_day(now)

        return current_game_day > last_game_day

    def _refresh_daily_progress(self, player_id: str) -> None:
        """刷新每日任务进度

        Args:
            player_id: 玩家ID
        """
        # 获取所有每日任务
        daily_quests = self.db.execute(
            select(Quest).where(
                Quest.is_daily == True,  # noqa: E712
                Quest.is_active == True,  # noqa: E712
            )
        ).scalars().all()

        now = datetime.utcnow()

        for quest in daily_quests:
            # 查找现有进度
            progress = self.db.execute(
                select(QuestProgress).where(
                    QuestProgress.player_id == player_id,
                    QuestProgress.quest_id == quest.quest_id,
                )
            ).scalar_one_or_none()

            if progress:
                # 重置进度
                progress.current_value = 0
                progress.is_completed = False
                progress.is_claimed = False
                progress.completed_at = None
                progress.claimed_at = None
                progress.last_refresh = now
            else:
                # 创建新进度
                progress = QuestProgress(
                    player_id=player_id,
                    quest_id=quest.quest_id,
                    current_value=0,
                    is_completed=False,
                    is_claimed=False,
                    last_refresh=now,
                )
                self.db.add(progress)

        self.db.commit()

    def _get_game_day(self, dt: datetime) -> int:
        """获取游戏日（以凌晨4点为界）

        Args:
            dt: 日期时间

        Returns:
            游戏日编号
        """
        # 如果在凌晨4点之前，算作前一天
        if dt.hour < 4:
            dt = dt - timedelta(days=1)
        return dt.toordinal()

    def get_quest_progress(self, player_id: str, quest_id: str) -> dict:
        """获取任务进度详情

        Args:
            player_id: 玩家ID
            quest_id: 任务ID

        Returns:
            任务进度详情
        """
        quest = self.db.execute(
            select(Quest).where(Quest.quest_id == quest_id)
        ).scalar_one_or_none()

        if not quest:
            raise ValueError(f"任务不存在: {quest_id}")

        progress = self.get_or_create_progress(player_id, quest_id)

        return {
            "quest_id": quest_id,
            "title": quest.title,
            "description": quest.description,
            "quest_type": quest.quest_type,
            "target_value": quest.target_value,
            "current_value": progress.current_value,
            "is_completed": progress.is_completed,
            "is_claimed": progress.is_claimed,
            "reward": QuestReward.from_json(quest.reward_json or "{}").to_dict(),
        }

    def get_available_quests(self, player_id: str) -> list[dict]:
        """获取所有可接受的任务

        Args:
            player_id: 玩家ID

        Returns:
            可接受的任务列表
        """
        # 确保每日任务已初始化
        self.initialize_daily_quests()

        # 检查是否需要刷新
        if self.should_refresh_daily(player_id):
            self._refresh_daily_progress(player_id)

        # 获取所有活跃任务
        quests = self.db.execute(
            select(Quest).where(Quest.is_active == True)  # noqa: E712
        ).scalars().all()

        result = []
        for quest in quests:
            progress = self.get_or_create_progress(player_id, quest.quest_id)
            result.append({
                "quest_id": quest.quest_id,
                "title": quest.title,
                "description": quest.description,
                "quest_type": quest.quest_type,
                "target_value": quest.target_value,
                "current_value": progress.current_value,
                "is_completed": progress.is_completed,
                "is_claimed": progress.is_claimed,
                "is_daily": quest.is_daily,
                "reward": QuestReward.from_json(quest.reward_json or "{}").to_dict(),
            })

        return result
