"""排行榜管理器单元测试"""

import pytest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.leaderboard_manager import LeaderboardManager
from src.storage.models import (
    Base,
    Guild,
    Leaderboard,
    Player,
    Season,
    LeaderboardType,
    SeasonType,
)


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
def leaderboard_manager(db_session):
    """创建排行榜管理器"""
    return LeaderboardManager(db_session)


@pytest.fixture
def active_season(db_session):
    """创建激活的赛季"""
    now = datetime.utcnow()
    season = Season(
        season_id="test-season-id",
        season_name="Test Season",
        season_number=1,
        season_type=SeasonType.REGULAR.value,
        start_time=now - timedelta(days=1),
        end_time=now + timedelta(days=30),
        is_active=True,
    )
    db_session.add(season)
    db_session.commit()
    db_session.refresh(season)
    return season


@pytest.fixture
def test_players(db_session):
    """创建测试玩家"""
    players = []
    for i in range(5):
        player = Player(
            username=f"player{i}",
            level=10 + i,
            experience=1000 * (i + 1),
            gold=500 * (i + 1),
        )
        db_session.add(player)
        db_session.flush()
        players.append(player)
    db_session.commit()
    return players


class TestLeaderboardManager:
    """排行榜管理器测试"""

    @pytest.mark.asyncio
    async def test_get_leaderboard_when_none_exists(
        self, leaderboard_manager: LeaderboardManager, active_season: Season
    ):
        """测试获取不存在的排行榜时自动创建"""
        result = await leaderboard_manager.get_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
            limit=10,
        )

        assert "leaderboard_id" in result
        assert result["season_id"] == active_season.season_id
        assert result["leaderboard_type"] == LeaderboardType.INDIVIDUAL.value
        assert result["total"] == 0
        assert result["rankings"] == []

    @pytest.mark.asyncio
    async def test_update_leaderboard(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试更新排行榜"""
        result = await leaderboard_manager.update_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        assert result["leaderboard_type"] == LeaderboardType.INDIVIDUAL.value
        assert result["total"] == len(test_players)
        assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_update_and_get_leaderboard(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试更新后获取排行榜"""
        # 先更新
        await leaderboard_manager.update_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        # 再获取
        result = await leaderboard_manager.get_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
            limit=10,
        )

        assert result["total"] == len(test_players)
        assert len(result["rankings"]) == len(test_players)

        # 检查排名
        rankings = result["rankings"]
        assert rankings[0]["rank"] == 1
        assert rankings[0]["entity_id"] == test_players[-1].player_id  # 等级最高的玩家

    @pytest.mark.asyncio
    async def test_get_player_rank(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试获取玩家排名"""
        # 先更新排行榜
        await leaderboard_manager.update_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        # 获取玩家排名
        result = await leaderboard_manager.get_player_rank(
            player_id=test_players[0].player_id,
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        assert result["player_id"] == test_players[0].player_id
        assert "rank" in result
        assert result["total"] == len(test_players)
        assert result["on_leaderboard"] is True

    @pytest.mark.asyncio
    async def test_get_player_rank_without_leaderboard(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试在排行榜不存在时获取玩家排名"""
        result = await leaderboard_manager.get_player_rank(
            player_id=test_players[0].player_id,
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        assert result["player_id"] == test_players[0].player_id
        assert "rank" in result
        assert result["total"] > 0

    @pytest.mark.asyncio
    async def test_create_snapshot(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试创建排行榜快照"""
        # 先更新排行榜
        await leaderboard_manager.update_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        # 创建快照
        snapshot = await leaderboard_manager.create_snapshot(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        assert "snapshot_id" in snapshot
        assert snapshot["season_id"] == active_season.season_id
        assert "snapshot_time" in snapshot

    @pytest.mark.asyncio
    async def test_get_snapshots(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试获取快照列表"""
        # 先更新排行榜并创建快照
        await leaderboard_manager.update_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )
        await leaderboard_manager.create_snapshot(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        # 获取快照列表
        snapshots = await leaderboard_manager.get_snapshots(
            season_id=active_season.season_id,
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            limit=10,
        )

        assert len(snapshots) == 1
        assert snapshots[0]["leaderboard_type"] == LeaderboardType.INDIVIDUAL.value
        assert "snapshot_time" in snapshots[0]

    @pytest.mark.asyncio
    async def test_calculate_individual_rankings(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试计算个人排名"""
        rankings = await leaderboard_manager._calculate_individual_rankings(
            active_season.season_id
        )

        assert len(rankings) == len(test_players)

        # 检查排名顺序
        assert rankings[0]["rank"] == 1
        assert rankings[-1]["rank"] == len(test_players)

        # 检查分数计算公式: level * 100 + exp / 10 + gold / 1000
        # player4: level=14, exp=5000, gold=2500
        # score = 14*100 + 5000/10 + 2500/1000 = 1400 + 500 + 2.5 = 1902.5
        expected_score = 14 * 100 + 5000 / 10 + 2500 / 1000
        top_player = next(
            (p for p in rankings if p["entity_id"] == test_players[4].player_id), None
        )
        assert top_player is not None
        assert top_player["score"] == round(expected_score, 2)

    @pytest.mark.asyncio
    async def test_calculate_guild_rankings(
        self, leaderboard_manager: LeaderboardManager, active_season: Season
    ):
        """测试计算公会排名"""
        # 创建测试公会
        for i in range(3):
            guild = Guild(
                guild_id=f"guild{i}",
                guild_name=f"Guild {i}",
                leader_id=f"leader{i}",
                level=5 + i,
                member_count=10 + i * 5,
                contribution_points=100 * (i + 1),
            )
            leaderboard_manager.session.add(guild)
        leaderboard_manager.session.commit()

        rankings = await leaderboard_manager._calculate_guild_rankings(
            active_season.season_id
        )

        assert len(rankings) == 3

        # 检查排名
        assert rankings[0]["rank"] == 1
        # 分数公式: level * 500 + member_count * 50 + contribution_points
        # Guild 2: level=7, member_count=20, contribution=300
        # score = 7*500 + 20*50 + 300 = 3500 + 1000 + 300 = 4800
        assert rankings[0]["score"] == 7 * 500 + 20 * 50 + 300

    @pytest.mark.asyncio
    async def test_calculate_achievement_rankings(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试计算成就排名"""
        # 由于没有实际成就数据，这应该返回所有玩家，分数为0
        rankings = await leaderboard_manager._calculate_achievement_rankings(
            active_season.season_id
        )

        assert len(rankings) == len(test_players)
        # 所有玩家成就数都为0
        for ranking in rankings:
            assert ranking["achievement_count"] == 0
            assert ranking["score"] == 0

    @pytest.mark.asyncio
    async def test_get_top_players(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试获取前N名玩家"""
        # 先更新排行榜
        await leaderboard_manager.update_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        # 获取前3名
        top_players = await leaderboard_manager.get_top_players(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
            limit=3,
        )

        assert len(top_players) == 3
        assert top_players[0]["rank"] == 1
        assert top_players[2]["rank"] == 3

    @pytest.mark.asyncio
    async def test_generate_leaderboard(
        self, leaderboard_manager: LeaderboardManager, active_season: Season
    ):
        """测试生成排行榜"""
        leaderboard = await leaderboard_manager.generate_leaderboard(
            season_id=active_season.season_id,
            leaderboard_type=LeaderboardType.GUILD.value,
        )

        assert leaderboard.season_id == active_season.season_id
        assert leaderboard.leaderboard_type == LeaderboardType.GUILD.value
        assert leaderboard.update_frequency == "hourly"

    @pytest.mark.asyncio
    async def test_get_leaderboard_with_offset_and_limit(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试排行榜分页"""
        # 先更新排行榜
        await leaderboard_manager.update_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
        )

        # 获取第2-3名 (offset=1, limit=2)
        result = await leaderboard_manager.get_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id=active_season.season_id,
            limit=2,
            offset=1,
        )

        assert result["total"] == len(test_players)
        assert result["offset"] == 1
        assert result["limit"] == 2
        assert len(result["rankings"]) == 2
        assert result["rankings"][0]["rank"] == 2

    @pytest.mark.asyncio
    async def test_get_leaderboard_invalid_season(
        self, leaderboard_manager: LeaderboardManager
    ):
        """测试获取无效赛季的排行榜"""
        result = await leaderboard_manager.get_leaderboard(
            leaderboard_type=LeaderboardType.INDIVIDUAL.value,
            season_id="nonexistent-season-id",
            limit=10,
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_calculate_individual_player_rank(
        self,
        leaderboard_manager: LeaderboardManager,
        active_season: Season,
        test_players: list[Player],
    ):
        """测试计算单个玩家的个人排名"""
        result = await leaderboard_manager._calculate_individual_player_rank(
            player_id=test_players[0].player_id,
            season_id=active_season.season_id,
        )

        assert result["player_id"] == test_players[0].player_id
        assert "rank" in result
        assert result["total"] == len(test_players)
        assert "score" in result

    @pytest.mark.asyncio
    async def test_invalid_leaderboard_type(
        self, leaderboard_manager: LeaderboardManager, active_season: Season
    ):
        """测试无效的排行榜类型"""
        result = await leaderboard_manager.get_player_rank(
            player_id="some-player-id",
            leaderboard_type="invalid_type",
            season_id=active_season.season_id,
        )

        assert "error" in result
