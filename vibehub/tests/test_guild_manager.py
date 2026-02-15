"""公会管理器单元测试

测试 GuildManager 的各项功能。
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.core.guild_manager import GuildManager, GuildError, GUILD_LEVEL_CONFIG
from src.storage.models import Base, Guild, GuildMember, GuildRole, GuildJoinType, Player


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
def guild_manager(session):
    """创建公会管理器实例"""
    return GuildManager(session)


@pytest.fixture
def test_player(session):
    """创建测试玩家"""
    player = Player(
        player_id="test_player_1",
        username="TestPlayer1",
        level=10,
        gold=1000,
        vibe_energy=500,
    )
    session.add(player)
    session.flush()
    return player


@pytest.fixture
def test_player2(session):
    """创建第二个测试玩家"""
    player = Player(
        player_id="test_player_2",
        username="TestPlayer2",
        level=5,
        gold=500,
        vibe_energy=300,
    )
    session.add(player)
    session.flush()
    return player


@pytest.fixture
def test_guild(guild_manager, test_player):
    """创建测试公会"""
    result = guild_manager.create_guild(
        leader_id=test_player.player_id,
        guild_name="TestGuild",
        description="A test guild",
        join_type=GuildJoinType.OPEN.value,
    )
    session = guild_manager.session
    session.commit()
    return result


class TestGuildManager:
    """公会管理器测试类"""

    def test_create_guild_success(self, guild_manager, test_player):
        """测试成功创建公会"""
        result = guild_manager.create_guild(
            leader_id=test_player.player_id,
            guild_name="AwesomeGuild",
            description="An awesome guild",
            guild_name_zh="超棒公会",
            join_type=GuildJoinType.OPEN.value,
        )

        assert "guild_id" in result
        assert result["guild_name"] == "AwesomeGuild"
        assert result["message"] == "Guild created successfully"

        # 验证数据库中的记录
        guild = guild_manager.session.scalar(
            select(Guild).where(Guild.guild_name == "AwesomeGuild")
        )
        assert guild is not None
        assert guild.leader_id == test_player.player_id
        assert guild.level == 1

        # 验证会长成员记录
        member = guild_manager.session.scalar(
            select(GuildMember).where(
                GuildMember.player_id == test_player.player_id,
                GuildMember.is_active == True,
            )
        )
        assert member is not None
        assert member.role == GuildRole.LEADER.value

    def test_create_guild_player_not_found(self, guild_manager):
        """测试玩家不存在时创建公会失败"""
        with pytest.raises(GuildError) as exc_info:
            guild_manager.create_guild(
                leader_id="nonexistent_player",
                guild_name="GhostGuild",
            )
        assert exc_info.value.code == "PLAYER_NOT_FOUND"

    def test_create_guild_already_in_guild(self, guild_manager, test_player, test_guild):
        """测试已在公会中的玩家创建公会失败"""
        with pytest.raises(GuildError) as exc_info:
            guild_manager.create_guild(
                leader_id=test_player.player_id,
                guild_name="AnotherGuild",
            )
        assert exc_info.value.code == "ALREADY_IN_GUILD"

    def test_create_guild_name_exists(self, guild_manager, test_player2, test_guild):
        """测试公会名重复时创建失败"""
        with pytest.raises(GuildError) as exc_info:
            guild_manager.create_guild(
                leader_id=test_player2.player_id,
                guild_name="TestGuild",  # 已存在的名称
            )
        assert exc_info.value.code == "NAME_EXISTS"

    def test_get_guild_info(self, guild_manager, test_guild):
        """测试获取公会信息"""
        guild_id = test_guild["guild_id"]
        info = guild_manager.get_guild_info(guild_id)

        assert info["guild_id"] == guild_id
        assert info["guild_name"] == "TestGuild"
        assert info["level"] == 1
        assert info["member_count"] == 1
        assert len(info["members"]) == 1
        assert info["members"][0]["role"] == GuildRole.LEADER.value

    def test_get_guild_info_not_found(self, guild_manager):
        """测试获取不存在的公会信息"""
        with pytest.raises(GuildError) as exc_info:
            guild_manager.get_guild_info("nonexistent_guild")
        assert exc_info.value.code == "GUILD_NOT_FOUND"

    def test_get_guild_list(self, guild_manager, test_guild):
        """测试获取公会列表"""
        result = guild_manager.get_guild_list(page=1, page_size=20)

        assert "guilds" in result
        assert result["total"] >= 1
        assert len(result["guilds"]) >= 1

        # 检查返回的公会数据结构
        guild_data = result["guilds"][0]
        assert "guild_id" in guild_data
        assert "guild_name" in guild_data
        assert "level" in guild_data
        assert "member_count" in guild_data

    def test_get_guild_list_with_search(self, guild_manager, test_guild):
        """测试搜索公会列表"""
        result = guild_manager.get_guild_list(page=1, page_size=20, search="Test")

        assert result["total"] >= 1
        for guild in result["guilds"]:
            assert "Test" in guild["guild_name"]

    def test_join_guild_success(self, guild_manager, test_player2, test_guild):
        """测试成功加入公会"""
        result = guild_manager.join_guild(
            player_id=test_player2.player_id,
            guild_id=test_guild["guild_id"],
        )

        assert result["success"] is True
        assert result["guild_id"] == test_guild["guild_id"]

        # 提交事务以确保数据可查询
        guild_manager.session.commit()

        # 验证成员记录
        member = guild_manager.session.scalar(
            select(GuildMember).where(
                GuildMember.player_id == test_player2.player_id,
                GuildMember.is_active == True,
            )
        )
        assert member is not None
        assert member.role == GuildRole.MEMBER.value

    def test_join_guild_level_too_low(self, guild_manager, session, test_player2, test_guild):
        """测试等级不足时加入公会失败"""
        # 设置公会最低等级要求
        guild = guild_manager.session.get(Guild, test_guild["guild_id"])
        guild.min_level = 20

        with pytest.raises(GuildError) as exc_info:
            guild_manager.join_guild(
                player_id=test_player2.player_id,
                guild_id=test_guild["guild_id"],
            )
        assert exc_info.value.code == "LEVEL_TOO_LOW"

    def test_leave_guild_success(self, guild_manager, test_player2, test_guild):
        """测试成功离开公会"""
        # 先加入公会
        guild_manager.join_guild(
            player_id=test_player2.player_id,
            guild_id=test_guild["guild_id"],
        )
        guild_manager.session.commit()

        # 离开公会
        result = guild_manager.leave_guild(test_player2.player_id)

        assert result["success"] is True

        # 验证成员状态
        member = guild_manager.session.scalar(
            select(GuildMember).where(
                GuildMember.player_id == test_player2.player_id,
            )
        )
        assert member is not None
        assert member.is_active is False

    def test_leave_guild_leader_cannot_leave(self, guild_manager, session):
        """测试会长在有其他成员时不能直接离开公会"""
        import uuid
        # 创建两个新玩家
        player_id = f"leader_test_{uuid.uuid4().hex[:8]}"
        player = Player(
            player_id=player_id,
            username="LeaderPlayer",
            level=10,
            gold=1000,
            vibe_energy=500,
        )
        member_id = f"member_{uuid.uuid4().hex[:8]}"
        member_player = Player(
            player_id=member_id,
            username="MemberPlayer",
            level=5,
            gold=500,
            vibe_energy=300,
        )
        session.add(player)
        session.add(member_player)
        session.commit()

        # 创建公会
        guild_manager.create_guild(
            leader_id=player_id,
            guild_name=f"LeaderGuild_{uuid.uuid4().hex[:8]}",
        )
        guild_manager.session.commit()

        # 添加成员
        guild_id = guild_manager.get_player_guild(player_id)["guild"]["guild_id"]
        guild_manager.join_guild(
            player_id=member_id,
            guild_id=guild_id,
        )
        guild_manager.session.commit()

        # 会长不能离开公会（有其他成员）
        with pytest.raises(GuildError) as exc_info:
            guild_manager.leave_guild(player_id)
        assert exc_info.value.code == "LEADER_CANNOT_LEAVE"

    def test_kick_member_success(self, guild_manager, test_player, test_player2, test_guild):
        """测试成功踢出成员"""
        # test_player2 加入公会
        guild_manager.join_guild(
            player_id=test_player2.player_id,
            guild_id=test_guild["guild_id"],
        )
        guild_manager.session.commit()

        # 会长踢出成员
        result = guild_manager.kick_member(
            operator_id=test_player.player_id,
            member_player_id=test_player2.player_id,
        )

        assert result["success"] is True

    def test_kick_member_no_permission(self, guild_manager, session, test_guild):
        """测试普通成员无权踢人"""
        import uuid
        # 创建一个新玩家并加入公会
        new_player_id = f"member_test_{uuid.uuid4().hex[:8]}"
        new_player = Player(
            player_id=new_player_id,
            username=f"MemberPlayer_{uuid.uuid4().hex[:8]}",
            level=5,
            gold=500,
            vibe_energy=300,
        )
        session.add(new_player)
        session.commit()

        # 加入公会
        guild_manager.join_guild(
            player_id=new_player_id,
            guild_id=test_guild["guild_id"],
        )
        guild_manager.session.commit()

        # 将新玩家的角色改为普通成员
        member = guild_manager.session.scalar(
            select(GuildMember).where(
                GuildMember.player_id == new_player_id,
                GuildMember.guild_id == test_guild["guild_id"],
            )
        )
        if member:
            member.role = GuildRole.MEMBER.value
            guild_manager.session.commit()

            # 获取会长ID
            leader_member = guild_manager.session.scalar(
                select(GuildMember).where(
                    GuildMember.guild_id == test_guild["guild_id"],
                    GuildMember.role == GuildRole.LEADER.value,
                )
            )

            # 普通成员尝试踢人
            with pytest.raises(GuildError) as exc_info:
                guild_manager.kick_member(
                    operator_id=new_player_id,
                    member_player_id=leader_member.player_id,
                )
            assert exc_info.value.code == "NO_PERMISSION"

    def test_update_member_role_transfer_leadership(self, guild_manager, test_player, test_player2, test_guild):
        """测试转让会长"""
        # test_player2 加入公会
        guild_manager.join_guild(
            player_id=test_player2.player_id,
            guild_id=test_guild["guild_id"],
        )
        guild_manager.session.commit()

        # 转让会长
        result = guild_manager.update_member_role(
            operator_id=test_player.player_id,
            target_player_id=test_player2.player_id,
            new_role=GuildRole.LEADER.value,
        )

        assert result["success"] is True

        # 验证角色变更
        old_leader = guild_manager.session.scalar(
            select(GuildMember).where(GuildMember.player_id == test_player.player_id)
        )
        assert old_leader.role == GuildRole.OFFICER.value

        new_leader = guild_manager.session.scalar(
            select(GuildMember).where(GuildMember.player_id == test_player2.player_id)
        )
        assert new_leader.role == GuildRole.LEADER.value

        new_leader = guild_manager.session.scalar(
            select(GuildMember).where(GuildMember.player_id == test_player2.player_id)
        )
        assert new_leader.role == GuildRole.LEADER.value

    def test_contribute_success(self, guild_manager, test_player, test_guild):
        """测试成功贡献"""
        result = guild_manager.contribute(
            player_id=test_player.player_id,
            amount=500,
        )

        assert result["success"] is True
        assert result["energy_contributed"] == 500
        assert result["exp_gained"] == 5

    def test_contribute_level_up(self, guild_manager, test_player, test_guild):
        """测试贡献导致公会升级"""
        guild_id = test_guild["guild_id"]
        guild = guild_manager.session.get(Guild, guild_id)

        # 设置公会经验接近升级
        guild.exp = GUILD_LEVEL_CONFIG[2]["exp_required"] - 100

        # 贡献足够多的能量
        result = guild_manager.contribute(
            player_id=test_player.player_id,
            amount=10000,  # 100 经验
        )

        assert result["level_up"] is True
        assert result["guild_level"] == 2

    def test_get_guild_members(self, guild_manager, test_player, test_player2, test_guild):
        """测试获取公会成员列表"""
        # test_player2 加入公会
        guild_manager.join_guild(
            player_id=test_player2.player_id,
            guild_id=test_guild["guild_id"],
        )
        guild_manager.session.commit()

        result = guild_manager.get_guild_members(test_guild["guild_id"])

        assert result["total"] == 2
        assert len(result["members"]) == 2
        # 验证排序：会长在前
        assert result["members"][0]["role"] == GuildRole.LEADER.value
        assert result["members"][1]["role"] == GuildRole.MEMBER.value

    def test_update_guild_settings(self, guild_manager, test_player, test_guild):
        """测试更新公会设置"""
        result = guild_manager.update_guild_settings(
            operator_id=test_player.player_id,
            guild_id=test_guild["guild_id"],
            description="Updated description",
            join_type=GuildJoinType.INVITE_ONLY.value,
            min_level=10,
        )

        assert result["success"] is True

        # 验证更新
        guild = guild_manager.session.get(Guild, test_guild["guild_id"])
        assert guild.description == "Updated description"
        assert guild.join_type == GuildJoinType.INVITE_ONLY.value
        assert guild.min_level == 10

    def test_get_player_guild(self, guild_manager, test_player, test_guild):
        """测试获取玩家所属公会"""
        result = guild_manager.get_player_guild(test_player.player_id)

        assert result["has_guild"] is True
        assert result["guild"]["guild_id"] == test_guild["guild_id"]
        assert result["membership"]["role"] == GuildRole.LEADER.value

    def test_get_player_guild_no_guild(self, guild_manager, test_player2):
        """测试获取没有公会的玩家信息"""
        result = guild_manager.get_player_guild(test_player2.player_id)

        assert result["has_guild"] is False
        assert result["guild"] is None
