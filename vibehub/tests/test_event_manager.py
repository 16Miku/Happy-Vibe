"""活动管理器单元测试"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.core.event import EventManager, VibeReward
from src.storage.database import get_db
from src.storage.models import EventType, GameEvent


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    db = get_db()
    db.create_tables()
    session = db.get_session_instance()

    # 清理数据
    try:
        session.query(GameEvent).delete()
        session.commit()
    except Exception:
        session.rollback()

    yield session

    # 清理
    try:
        session.query(GameEvent).delete()
        session.commit()
    except Exception:
        session.rollback()
    session.close()


@pytest.fixture
def event_manager(db_session):
    """创建活动管理器"""
    return EventManager(db_session)


@pytest.fixture
def active_event(db_session):
    """创建活跃活动"""
    now = datetime.utcnow()
    event = GameEvent(
        event_type=EventType.DOUBLE_EXP.value,
        title="双倍经验活动",
        description="所有经验获取翻倍",
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=23),
        effects_json='{"exp_multiplier": 2.0}',
        is_active=True,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def expired_event(db_session):
    """创建过期活动"""
    now = datetime.utcnow()
    event = GameEvent(
        event_type=EventType.SPECIAL_CROP.value,
        title="特殊作物活动",
        description="特殊作物产出增加",
        start_time=now - timedelta(days=2),
        end_time=now - timedelta(days=1),
        effects_json='{"gold_bonus": 100}',
        is_active=True,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


class TestEventManager:
    """活动管理器测试"""

    def test_get_active_events(self, event_manager, active_event):
        """测试获取活跃活动"""
        events = event_manager.get_active_events()

        assert len(events) == 1
        assert events[0].event_id == active_event.event_id

    def test_get_active_events_excludes_expired(self, event_manager, expired_event):
        """测试排除过期活动"""
        events = event_manager.get_active_events()

        assert len(events) == 0

    def test_apply_event_effects_double_exp(self, event_manager, active_event):
        """测试应用双倍经验效果"""
        base_reward = VibeReward(energy=100, gold=50, exp=25)

        result = event_manager.apply_event_effects(base_reward)

        assert result.exp == 50  # 25 * 2
        assert result.gold == 50  # 不变
        assert result.energy == 100  # 不变

    def test_apply_event_effects_no_active(self, event_manager):
        """测试无活跃活动时不改变奖励"""
        base_reward = VibeReward(energy=100, gold=50, exp=25)

        result = event_manager.apply_event_effects(base_reward)

        assert result.exp == 25
        assert result.gold == 50
        assert result.energy == 100

    def test_get_event_effects(self, event_manager, active_event):
        """测试获取活动效果"""
        effects = event_manager.get_event_effects(EventType.DOUBLE_EXP.value)

        assert effects["exp_multiplier"] == 2.0

    def test_get_event_effects_no_active(self, event_manager):
        """测试无活跃活动时返回空"""
        effects = event_manager.get_event_effects(EventType.FESTIVAL.value)

        assert effects == {}

    def test_create_event(self, event_manager, db_session):
        """测试创建活动"""
        now = datetime.utcnow()
        event = event_manager.create_event(
            event_type=EventType.FESTIVAL.value,
            title="春节活动",
            description="春节期间所有奖励增加",
            start_time=now,
            end_time=now + timedelta(days=7),
            effects={"gold_multiplier": 1.5, "exp_multiplier": 1.5},
        )

        assert event.event_id is not None
        assert event.title == "春节活动"
        assert event.is_active is True

    def test_deactivate_event(self, event_manager, active_event, db_session):
        """测试停用活动"""
        result = event_manager.deactivate_event(active_event.event_id)

        assert result is True

        db_session.refresh(active_event)
        assert active_event.is_active is False

    def test_deactivate_nonexistent_event(self, event_manager):
        """测试停用不存在的活动"""
        result = event_manager.deactivate_event("nonexistent-id")

        assert result is False

    def test_get_event_detail(self, event_manager, active_event):
        """测试获取活动详情"""
        detail = event_manager.get_event_detail(active_event.event_id)

        assert detail is not None
        assert detail["event_id"] == active_event.event_id
        assert detail["title"] == "双倍经验活动"
        assert detail["is_ongoing"] is True

    def test_get_event_detail_nonexistent(self, event_manager):
        """测试获取不存在的活动详情"""
        detail = event_manager.get_event_detail("nonexistent-id")

        assert detail is None

    def test_expired_events_not_ongoing(self, event_manager, expired_event):
        """测试过期活动不是进行中"""
        detail = event_manager.get_event_detail(expired_event.event_id)

        assert detail is not None
        assert detail["is_ongoing"] is False


class TestVibeReward:
    """Vibe奖励测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        reward = VibeReward(energy=100, gold=50, exp=25, diamonds=5)
        result = reward.to_dict()

        assert result["energy"] == 100
        assert result["gold"] == 50
        assert result["exp"] == 25
        assert result["diamonds"] == 5

    def test_default_values(self):
        """测试默认值"""
        reward = VibeReward()

        assert reward.energy == 0
        assert reward.gold == 0
        assert reward.exp == 0
        assert reward.diamonds == 0
