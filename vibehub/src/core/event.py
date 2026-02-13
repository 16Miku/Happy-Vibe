"""活动管理器

实现游戏活动系统的核心逻辑，包括：
- 获取当前活跃的活动
- 获取活动效果
- 应用活动效果到奖励
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.storage.models import EventType, GameEvent


@dataclass
class VibeReward:
    """Vibe奖励数据类"""

    energy: int = 0
    gold: int = 0
    exp: int = 0
    diamonds: int = 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "energy": self.energy,
            "gold": self.gold,
            "exp": self.exp,
            "diamonds": self.diamonds,
        }


class EventManager:
    """活动管理器

    负责活动的查询、效果计算等核心逻辑。
    """

    def __init__(self, db: Session):
        self.db = db

    def get_active_events(self) -> list[GameEvent]:
        """获取当前活跃的活动列表

        Returns:
            活跃的活动列表
        """
        now = datetime.utcnow()

        events = self.db.execute(
            select(GameEvent).where(
                GameEvent.is_active == True,  # noqa: E712
                GameEvent.start_time <= now,
                GameEvent.end_time > now,
            )
        ).scalars().all()

        return list(events)

    def get_event_by_id(self, event_id: str) -> Optional[GameEvent]:
        """根据ID获取活动

        Args:
            event_id: 活动ID

        Returns:
            活动对象，不存在则返回None
        """
        return self.db.execute(
            select(GameEvent).where(GameEvent.event_id == event_id)
        ).scalar_one_or_none()

    def get_event_effects(self, event_type: str) -> dict:
        """获取指定类型活动的效果

        Args:
            event_type: 活动类型

        Returns:
            活动效果字典
        """
        now = datetime.utcnow()

        # 查找该类型的活跃活动
        event = self.db.execute(
            select(GameEvent).where(
                GameEvent.event_type == event_type,
                GameEvent.is_active == True,  # noqa: E712
                GameEvent.start_time <= now,
                GameEvent.end_time > now,
            )
        ).scalar_one_or_none()

        if not event or not event.effects_json:
            return {}

        return json.loads(event.effects_json)

    def apply_event_effects(self, base_reward: VibeReward) -> VibeReward:
        """应用活动效果到基础奖励

        Args:
            base_reward: 基础奖励

        Returns:
            应用效果后的奖励
        """
        active_events = self.get_active_events()

        result = VibeReward(
            energy=base_reward.energy,
            gold=base_reward.gold,
            exp=base_reward.exp,
            diamonds=base_reward.diamonds,
        )

        for event in active_events:
            if not event.effects_json:
                continue

            effects = json.loads(event.effects_json)

            # 双倍经验活动
            if event.event_type == EventType.DOUBLE_EXP.value:
                exp_multiplier = effects.get("exp_multiplier", 1.0)
                result.exp = int(result.exp * exp_multiplier)

            # 特殊作物活动 - 可能增加金币
            elif event.event_type == EventType.SPECIAL_CROP.value:
                gold_bonus = effects.get("gold_bonus", 0)
                result.gold += gold_bonus

            # 节日活动 - 可能有多种加成
            elif event.event_type == EventType.FESTIVAL.value:
                energy_multiplier = effects.get("energy_multiplier", 1.0)
                gold_multiplier = effects.get("gold_multiplier", 1.0)
                exp_multiplier = effects.get("exp_multiplier", 1.0)

                result.energy = int(result.energy * energy_multiplier)
                result.gold = int(result.gold * gold_multiplier)
                result.exp = int(result.exp * exp_multiplier)

        return result

    def create_event(
        self,
        event_type: str,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        effects: Optional[dict] = None,
    ) -> GameEvent:
        """创建新活动

        Args:
            event_type: 活动类型
            title: 活动标题
            description: 活动描述
            start_time: 开始时间
            end_time: 结束时间
            effects: 活动效果

        Returns:
            创建的活动对象
        """
        event = GameEvent(
            event_type=event_type,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            effects_json=json.dumps(effects) if effects else None,
            is_active=True,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def deactivate_event(self, event_id: str) -> bool:
        """停用活动

        Args:
            event_id: 活动ID

        Returns:
            是否成功停用
        """
        event = self.get_event_by_id(event_id)

        if not event:
            return False

        event.is_active = False
        self.db.commit()

        return True

    def get_event_detail(self, event_id: str) -> Optional[dict]:
        """获取活动详情

        Args:
            event_id: 活动ID

        Returns:
            活动详情字典
        """
        event = self.get_event_by_id(event_id)

        if not event:
            return None

        now = datetime.utcnow()
        is_ongoing = event.start_time <= now < event.end_time

        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "title": event.title,
            "description": event.description,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "effects": json.loads(event.effects_json) if event.effects_json else {},
            "is_active": event.is_active,
            "is_ongoing": is_ongoing,
        }

    def get_active_events_summary(self) -> list[dict]:
        """获取活跃活动摘要列表

        Returns:
            活动摘要列表
        """
        events = self.get_active_events()

        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "title": event.title,
                "description": event.description,
                "start_time": event.start_time.isoformat(),
                "end_time": event.end_time.isoformat(),
            }
            for event in events
        ]
