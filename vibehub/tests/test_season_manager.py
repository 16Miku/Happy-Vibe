"""赛季管理器单元测试"""

import pytest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.season_manager import SeasonManager
from src.storage.models import Base, Season, SeasonType


@pytest.fixture
def in_memory_db():
    """创建内存数据库"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(in_memory_db):
    """创建数据库会话"""
    SessionLocal = sessionmaker(bind=in_memory_db, autocommit=False, autoflush=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def season_manager(db_session):
    """创建赛季管理器"""
    return SeasonManager(db_session)


class TestSeasonManager:
    """赛季管理器测试"""

    @pytest.mark.asyncio
    async def test_create_season(self, season_manager: SeasonManager):
        """测试创建赛季"""
        now = datetime.utcnow()
        end_time = now + timedelta(days=30)

        season = await season_manager.create_season(
            season_name="Test Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now,
            end_time=end_time,
            reward_tiers={
                "1": {"range": "1", "rewards": {"gold": 1000, "diamonds": 50}},
                "2-3": {"range": "2-3", "rewards": {"gold": 500, "diamonds": 25}},
            },
        )

        assert season["season_name"] == "Test Season"
        assert season["season_number"] == 1
        assert season["season_type"] == SeasonType.REGULAR.value
        assert season["is_active"] is False
        assert season["reward_tiers"] is not None
        assert "1" in season["reward_tiers"]
        assert "2-3" in season["reward_tiers"]

    @pytest.mark.asyncio
    async def test_get_season(self, season_manager: SeasonManager):
        """测试获取赛季"""
        now = datetime.utcnow()
        end_time = now + timedelta(days=30)

        created = await season_manager.create_season(
            season_name="Test Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now,
            end_time=end_time,
        )

        fetched = await season_manager.get_season(created["season_id"])

        assert fetched is not None
        assert fetched["season_id"] == created["season_id"]
        assert fetched["season_name"] == "Test Season"

    @pytest.mark.asyncio
    async def test_get_nonexistent_season(self, season_manager: SeasonManager):
        """测试获取不存在的赛季"""
        result = await season_manager.get_season("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_season_when_none(self, season_manager: SeasonManager):
        """测试当没有激活赛季时获取当前赛季"""
        result = await season_manager.get_current_season()
        assert result is None

    @pytest.mark.asyncio
    async def test_activate_season(self, season_manager: SeasonManager):
        """测试激活赛季"""
        now = datetime.utcnow()
        end_time = now + timedelta(days=30)

        season = await season_manager.create_season(
            season_name="Test Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now - timedelta(days=1),
            end_time=end_time,
        )

        activated = await season_manager.activate_season(season["season_id"])

        assert activated["is_active"] is True
        assert activated["season_id"] == season["season_id"]

    @pytest.mark.asyncio
    async def test_get_season_list(self, season_manager: SeasonManager):
        """测试获取赛季列表"""
        now = datetime.utcnow()

        # 创建多个赛季
        for i in range(3):
            await season_manager.create_season(
                season_name=f"Season {i+1}",
                season_number=i+1,
                season_type=SeasonType.REGULAR.value,
                start_time=now + timedelta(days=i*30),
                end_time=now + timedelta(days=(i+1)*30),
            )

        seasons = await season_manager.get_season_list(limit=10)

        assert len(seasons) == 3
        # 应该按赛季编号降序排列
        assert seasons[0]["season_number"] == 3

    @pytest.mark.asyncio
    async def test_end_season(self, season_manager: SeasonManager):
        """测试结束赛季"""
        now = datetime.utcnow()
        end_time = now + timedelta(days=30)

        season = await season_manager.create_season(
            season_name="Test Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now - timedelta(days=1),
            end_time=end_time,
        )

        # 先激活赛季
        await season_manager.activate_season(season["season_id"])

        # 结束赛季
        ended = await season_manager.end_season(season["season_id"])

        assert ended["is_active"] is False
        assert ended["season_id"] == season["season_id"]

    @pytest.mark.asyncio
    async def test_get_season_status(self, season_manager: SeasonManager):
        """测试获取赛季状态"""
        now = datetime.utcnow()
        end_time = now + timedelta(days=30)

        season = await season_manager.create_season(
            season_name="Test Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now - timedelta(days=1),
            end_time=end_time,
        )

        await season_manager.activate_season(season["season_id"])

        status = await season_manager.get_season_status(season["season_id"])

        assert status["season_id"] == season["season_id"]
        assert status["is_active"] is True
        assert status["status"] == "active"
        assert "remaining_time" in status

    @pytest.mark.asyncio
    async def test_activate_season_deactivates_others(self, season_manager: SeasonManager):
        """测试激活新赛季会关闭其他激活的赛季"""
        now = datetime.utcnow()
        end_time = now + timedelta(days=30)

        season1 = await season_manager.create_season(
            season_name="Season 1",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now - timedelta(days=1),
            end_time=end_time,
        )

        season2 = await season_manager.create_season(
            season_name="Season 2",
            season_number=2,
            season_type=SeasonType.REGULAR.value,
            start_time=now - timedelta(days=1),
            end_time=end_time,
        )

        # 激活第一个赛季
        await season_manager.activate_season(season1["season_id"])

        # 激活第二个赛季
        await season_manager.activate_season(season2["season_id"])

        # 检查第一个赛季已关闭
        season1_status = await season_manager.get_season_status(season1["season_id"])
        assert season1_status["is_active"] is False

        # 检查第二个赛季已激活
        season2_status = await season_manager.get_season_status(season2["season_id"])
        assert season2_status["is_active"] is True

    @pytest.mark.asyncio
    async def test_calculate_individual_rankings(self, season_manager: SeasonManager):
        """测试计算个人排名"""
        from src.storage.models import Player

        now = datetime.utcnow()

        # 创建测试玩家
        for i in range(3):
            player = Player(
                username=f"player{i}",
                level=10 + i,
                experience=1000 * (i + 1),
                gold=500 * (i + 1),
            )
            season_manager.session.add(player)
        season_manager.session.commit()

        season = await season_manager.create_season(
            season_name="Test Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now,
            end_time=now + timedelta(days=30),
        )

        rankings = await season_manager._calculate_individual_rankings(season["season_id"])

        assert len(rankings) == 3
        # 按分数排序
        assert rankings[0]["rank"] == 1
        assert rankings[0]["level"] == 12
        assert rankings[2]["rank"] == 3

    @pytest.mark.asyncio
    async def test_get_reward_for_rank(self, season_manager: SeasonManager):
        """测试根据排名获取奖励"""
        reward_tiers = {
            "1": {"range": "1", "rewards": {"gold": 1000}},
            "2-3": {"range": "2-3", "rewards": {"gold": 500}},
            "4-10": {"range": "4-10", "rewards": {"gold": 100}},
        }

        # 第1名
        reward = season_manager._get_reward_for_rank(1, reward_tiers)
        assert reward == {"gold": 1000}

        # 第2名
        reward = season_manager._get_reward_for_rank(2, reward_tiers)
        assert reward == {"gold": 500}

        # 第3名
        reward = season_manager._get_reward_for_rank(3, reward_tiers)
        assert reward == {"gold": 500}

        # 第5名
        reward = season_manager._get_reward_for_rank(5, reward_tiers)
        assert reward == {"gold": 100}

        # 第20名 (没有奖励)
        reward = season_manager._get_reward_for_rank(20, reward_tiers)
        assert reward is None

    @pytest.mark.asyncio
    async def test_season_to_dict(self, season_manager: SeasonManager):
        """测试赛季对象转字典"""
        now = datetime.utcnow()

        season = Season(
            season_id="test-id",
            season_name="Test Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now,
            end_time=now + timedelta(days=30),
            reward_tiers='{"1": {"rewards": {"gold": 1000}}}',
            is_active=True,
        )

        result = season_manager._season_to_dict(season)

        assert result["season_id"] == "test-id"
        assert result["season_name"] == "Test Season"
        assert result["is_active"] is True
        assert result["reward_tiers"] == {"1": {"rewards": {"gold": 1000}}}

    def test_get_season_status_upcoming(self, season_manager: SeasonManager):
        """测试获取即将开始的赛季状态"""
        now = datetime.utcnow()

        season = Season(
            season_id="test-id",
            season_name="Upcoming Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now + timedelta(days=7),
            end_time=now + timedelta(days=37),
            is_active=True,
        )

        status = season_manager._get_season_status(season, now)
        assert status == "upcoming"

    def test_get_season_status_ended(self, season_manager: SeasonManager):
        """测试获取已结束的赛季状态"""
        now = datetime.utcnow()

        season = Season(
            season_id="test-id",
            season_name="Ended Season",
            season_number=1,
            season_type=SeasonType.REGULAR.value,
            start_time=now - timedelta(days=60),
            end_time=now - timedelta(days=30),
            is_active=False,
        )

        status = season_manager._get_season_status(season, now)
        assert status == "ended"
