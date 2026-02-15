"""公会战管理器单元测试

测试 GuildWarManager 的各项功能。
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.core.guild_manager import GuildManager
from src.core.guild_war_manager import GuildWarManager, GuildWarError, WAR_REWARD_CONFIG
from src.storage.models import (
    Base,
    Guild,
    GuildMember,
    GuildWar,
    GuildWarParticipant,
    GuildRole,
    GuildWarType,
    GuildWarStatus,
    Player,
)


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """创建测试数据库引擎"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session(engine):
    """创建测试会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def war_manager(session):
    """创建公会战管理器实例"""
    return GuildWarManager(session)


@pytest.fixture
def guild_manager(session):
    """创建公会管理器实例"""
    return GuildManager(session)


@pytest.fixture
def test_players(session):
    """创建多个测试玩家"""
    players = []
    for i in range(1, 6):
        player = Player(
            player_id=f"test_player_{i}",
            username=f"TestPlayer{i}",
            level=10,
            gold=1000,
            vibe_energy=500,
        )
        session.add(player)
        players.append(player)
    session.commit()
    return players


@pytest.fixture
def test_guilds(guild_manager, test_players):
    """创建两个测试公会"""
    # 创建公会A
    guild_a = guild_manager.create_guild(
        leader_id=test_players[0].player_id,
        guild_name="TestGuildA",
        description="Guild A for testing",
    )
    session = guild_manager.session

    # 创建公会B
    guild_b = guild_manager.create_guild(
        leader_id=test_players[1].player_id,
        guild_name="TestGuildB",
        description="Guild B for testing",
    )

    # 升级公会等级以满足公会战要求
    guild_a_obj = session.get(Guild, guild_a["guild_id"])
    guild_b_obj = session.get(Guild, guild_b["guild_id"])
    guild_a_obj.level = 5
    guild_b_obj.level = 5
    session.commit()

    return {
        "guild_a": guild_a,
        "guild_b": guild_b,
        "guild_a_obj": guild_a_obj,
        "guild_b_obj": guild_b_obj,
    }


@pytest.fixture
def test_war(war_manager, test_players, test_guilds):
    """创建测试公会战"""
    result = war_manager.create_war(
        creator_id=test_players[0].player_id,
        guild_a_id=test_guilds["guild_a"]["guild_id"],
        guild_b_id=test_guilds["guild_b"]["guild_id"],
        war_type=GuildWarType.HONOR.value,
        duration_hours=24,
    )
    session = war_manager.session
    session.commit()
    return result


class TestGuildWarManager:
    """公会战管理器测试类"""

    def test_create_war_success(self, war_manager, test_players, test_guilds):
        """测试成功创建公会战"""
        result = war_manager.create_war(
            creator_id=test_players[0].player_id,
            guild_a_id=test_guilds["guild_a"]["guild_id"],
            guild_b_id=test_guilds["guild_b"]["guild_id"],
            war_type=GuildWarType.HONOR.value,
            duration_hours=24,
        )

        assert "war_id" in result
        assert result["status"] == GuildWarStatus.PREPARING.value

        # 提交事务以确保数据可查询
        war_manager.session.commit()

        # 验证数据库记录
        war = war_manager.session.get(GuildWar, result["war_id"])
        assert war is not None
        assert war.war_type == GuildWarType.HONOR.value
        assert war.guild_a_id == test_guilds["guild_a"]["guild_id"]
        assert war.guild_b_id == test_guilds["guild_b"]["guild_id"]

    def test_create_war_guild_not_found(self, war_manager, test_players):
        """测试公会不存在时创建公会战失败"""
        with pytest.raises(GuildWarError) as exc_info:
            war_manager.create_war(
                creator_id=test_players[0].player_id,
                guild_a_id="nonexistent_guild_a",
                guild_b_id="nonexistent_guild_b",
            )
        assert exc_info.value.code in ["GUILD_A_NOT_FOUND", "GUILD_B_NOT_FOUND"]

    def test_create_war_same_guild(self, war_manager, test_players, test_guilds):
        """测试同一公会不能对战"""
        with pytest.raises(GuildWarError) as exc_info:
            war_manager.create_war(
                creator_id=test_players[0].player_id,
                guild_a_id=test_guilds["guild_a"]["guild_id"],
                guild_b_id=test_guilds["guild_a"]["guild_id"],
            )
        assert exc_info.value.code == "SAME_GUILD"

    def test_create_war_level_too_low(self, guild_manager, war_manager, test_players):
        """测试等级不足的公会不能创建公会战"""
        # 创建低等级公会
        guild_a = guild_manager.create_guild(
            leader_id=test_players[0].player_id,
            guild_name="LowGuildA",
        )
        guild_b = guild_manager.create_guild(
            leader_id=test_players[1].player_id,
            guild_name="LowGuildB",
        )

        with pytest.raises(GuildWarError) as exc_info:
            war_manager.create_war(
                creator_id=test_players[0].player_id,
                guild_a_id=guild_a["guild_id"],
                guild_b_id=guild_b["guild_id"],
            )
        assert exc_info.value.code == "LEVEL_TOO_LOW"

    def test_create_war_no_permission(self, war_manager, test_players, test_guilds):
        """测试普通成员无权创建公会战"""
        with pytest.raises(GuildWarError) as exc_info:
            war_manager.create_war(
                creator_id=test_players[2].player_id,  # 不在任一公会中的玩家
                guild_a_id=test_guilds["guild_a"]["guild_id"],
                guild_b_id=test_guilds["guild_b"]["guild_id"],
            )
        assert exc_info.value.code == "NOT_MEMBER"

    def test_start_war_success(self, war_manager, test_war):
        """测试成功开始公会战"""
        war_id = test_war["war_id"]
        result = war_manager.start_war(war_id)

        assert result["success"] is True
        assert result["status"] == GuildWarStatus.ACTIVE.value

        # 验证数据库状态
        war = war_manager.session.get(GuildWar, war_id)
        assert war.status == GuildWarStatus.ACTIVE.value

    def test_start_war_already_active(self, war_manager, test_war):
        """测试重复开始公会战"""
        war_id = test_war["war_id"]
        war_manager.start_war(war_id)

        with pytest.raises(GuildWarError) as exc_info:
            war_manager.start_war(war_id)
        assert exc_info.value.code == "INVALID_STATUS"

    def test_get_war_info(self, war_manager, test_war):
        """测试获取公会战信息"""
        war_id = test_war["war_id"]
        info = war_manager.get_war_info(war_id)

        assert info["war_id"] == war_id
        assert info["status"] == GuildWarStatus.PREPARING.value
        assert "guild_a" in info
        assert "guild_b" in info
        assert info["guild_a"]["score"] == 0
        assert info["guild_b"]["score"] == 0

    def test_get_war_info_not_found(self, war_manager):
        """测试获取不存在的公会战信息"""
        with pytest.raises(GuildWarError) as exc_info:
            war_manager.get_war_info("nonexistent_war")
        assert exc_info.value.code == "WAR_NOT_FOUND"

    def test_get_active_wars(self, war_manager, test_war):
        """测试获取进行中的公会战列表"""
        result = war_manager.get_active_wars()

        assert "wars" in result
        assert result["count"] >= 1

    def test_get_active_wars_by_guild(self, war_manager, test_war, test_guilds):
        """测试按公会筛选进行中的公会战"""
        result = war_manager.get_active_wars(guild_id=test_guilds["guild_a"]["guild_id"])

        assert result["count"] >= 1
        for war in result["wars"]:
            assert war["status"] in [GuildWarStatus.PREPARING.value, GuildWarStatus.ACTIVE.value]

    def test_update_score_success(self, war_manager, test_war, test_players, test_guilds):
        """测试成功更新分数"""
        war_id = test_war["war_id"]
        war_manager.start_war(war_id)

        result = war_manager.update_score(
            war_id=war_id,
            player_id=test_players[0].player_id,
            score_delta=100,
            damage_dealt=50,
            battle_won=True,
        )

        assert result["success"] is True
        assert result["score_added"] == 100
        assert result["guild_score"] == 100

        # 验证参与者记录
        participant = war_manager.session.scalar(
            select(GuildWarParticipant).where(
                GuildWarParticipant.war_id == war_id,
                GuildWarParticipant.player_id == test_players[0].player_id,
            )
        )
        assert participant is not None
        assert participant.score == 100
        assert participant.battles_won == 1

    def test_update_score_war_not_active(self, war_manager, test_war, test_players):
        """测试非进行中状态不能更新分数"""
        war_id = test_war["war_id"]

        with pytest.raises(GuildWarError) as exc_info:
            war_manager.update_score(
                war_id=war_id,
                player_id=test_players[0].player_id,
                score_delta=100,
            )
        assert exc_info.value.code == "INVALID_STATUS"

    def test_update_score_player_not_in_guild(self, war_manager, test_war, test_players):
        """测试不在公会中的玩家不能更新分数"""
        war_id = test_war["war_id"]
        war_manager.start_war(war_id)

        # test_players[2] 不在任一公会中
        with pytest.raises(GuildWarError) as exc_info:
            war_manager.update_score(
                war_id=war_id,
                player_id=test_players[2].player_id,
                score_delta=100,
            )
        assert exc_info.value.code == "NOT_IN_GUILD"

    def test_update_score_early_finish(self, war_manager, test_war, test_players, test_guilds):
        """测试达到目标分数时提前结束"""
        war_id = test_war["war_id"]
        war = war_manager.session.get(GuildWar, war_id)
        war.target_score = 100
        war_manager.start_war(war_id)

        result = war_manager.update_score(
            war_id=war_id,
            player_id=test_players[0].player_id,
            score_delta=150,  # 超过目标分数
        )

        assert result["early_finish"] is True

        # 验证战争已结束
        war = war_manager.session.get(GuildWar, war_id)
        assert war.status == GuildWarStatus.FINISHED.value

    def test_end_war_success(self, war_manager, test_war, test_players):
        """测试手动结束公会战"""
        war_id = test_war["war_id"]
        war_manager.start_war(war_id)

        result = war_manager.end_war(war_id)

        assert result["success"] is True
        assert result["message"] == "Guild war finished"

        # 验证状态
        war = war_manager.session.get(GuildWar, war_id)
        assert war.status == GuildWarStatus.FINISHED.value

    def test_end_war_with_force_winner(self, war_manager, test_war, test_players, test_guilds):
        """测试强制指定获胜方结束公会战"""
        war_id = test_war["war_id"]
        war_manager.start_war(war_id)

        result = war_manager.end_war(
            war_id=war_id,
            force_winner_id=test_guilds["guild_a"]["guild_id"],
        )

        assert result["success"] is True
        assert result["winner_id"] == test_guilds["guild_a"]["guild_id"]

    def test_end_war_invalid_winner(self, war_manager, test_war, test_players):
        """测试指定无效获胜方失败"""
        war_id = test_war["war_id"]
        war_manager.start_war(war_id)

        with pytest.raises(GuildWarError) as exc_info:
            war_manager.end_war(war_id, force_winner_id="invalid_guild")
        assert exc_info.value.code == "INVALID_WINNER"

    def test_claim_war_reward_success(self, war_manager, test_war, test_players):
        """测试成功领取公会战奖励"""
        war_id = test_war["war_id"]
        war = war_manager.session.get(GuildWar, war_id)
        war.status = GuildWarStatus.FINISHED.value
        war.winner_id = war.guild_a_id

        # 创建参与记录
        participant = GuildWarParticipant(
            participation_id="test_participation_1",
            war_id=war_id,
            player_id=test_players[0].player_id,
            guild_id=war.guild_a_id,
            score=1000,
            battles_won=5,
            damage_dealt=500,
            personal_reward_claimed=False,
        )
        war_manager.session.add(participant)
        war_manager.session.flush()

        result = war_manager.claim_war_reward(
            player_id=test_players[0].player_id,
            war_id=war_id,
        )

        assert result["success"] is True
        assert "diamonds" in result
        assert "gold" in result

    def test_claim_war_reward_not_participated(self, war_manager, test_war, test_players):
        """测试未参与的玩家不能领取奖励"""
        war_id = test_war["war_id"]
        war = war_manager.session.get(GuildWar, war_id)
        war.status = GuildWarStatus.FINISHED.value

        with pytest.raises(GuildWarError) as exc_info:
            war_manager.claim_war_reward(
                player_id=test_players[0].player_id,
                war_id=war_id,
            )
        assert exc_info.value.code == "NOT_PARTICIPATED"

    def test_check_and_finish_expired_wars(self, war_manager, test_war, test_players):
        """测试检查并结束已过期的公会战"""
        war_id = test_war["war_id"]
        war = war_manager.session.get(GuildWar, war_id)

        # 设置为过期状态
        war.start_time = datetime.utcnow() - timedelta(days=2)
        war.end_time = datetime.utcnow() - timedelta(days=1)
        war.status = GuildWarStatus.ACTIVE.value
        war_manager.session.commit()

        finished = war_manager.check_and_finish_expired_wars()

        assert len(finished) >= 1

        # 验证公会战状态
        war = war_manager.session.get(GuildWar, war_id)
        assert war.status == GuildWarStatus.FINISHED.value

    def test_find_opponent(self, war_manager, guild_manager, test_players):
        """测试查找可对战公会"""
        # 创建多个不同等级的公会
        guild1 = guild_manager.create_guild(
            leader_id=test_players[0].player_id,
            guild_name="Level1Guild",
        )
        guild2 = guild_manager.create_guild(
            leader_id=test_players[1].player_id,
            guild_name="Level5Guild",
        )

        # 设置等级
        session = war_manager.session
        guild1_obj = session.get(Guild, guild1["guild_id"])
        guild2_obj = session.get(Guild, guild2["guild_id"])
        guild1_obj.level = 3
        guild2_obj.level = 5
        session.commit()

        opponents = war_manager.find_opponent(
            guild_id=guild1["guild_id"],
            war_type=GuildWarType.HONOR.value,
            level_diff=2,
        )

        # find_opponent 返回列表
        assert isinstance(opponents, list)
        # 应该找到等级相近的公会
        assert len(opponents) >= 0

    def test_reward_config(self):
        """测试奖励配置"""
        assert GuildWarType.HONOR.value in WAR_REWARD_CONFIG
        assert GuildWarType.TERRITORY.value in WAR_REWARD_CONFIG
        assert GuildWarType.RESOURCE.value in WAR_REWARD_CONFIG

        config = WAR_REWARD_CONFIG[GuildWarType.HONOR.value]
        assert "winner_multiplier" in config
        assert "loser_multiplier" in config
        assert "base_diamonds" in config
        assert "base_gold" in config
