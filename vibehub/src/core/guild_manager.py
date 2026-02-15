"""公会管理器

提供公会创建、成员管理、贡献等功能。
"""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.storage.models import (
    Guild,
    GuildJoinType,
    GuildMember,
    GuildRole,
    Player,
    generate_uuid,
)

# 公会等级配置
GUILD_LEVEL_CONFIG = {
    1: {"exp_required": 0, "max_members": 20, "features": ["basic", "chat"]},
    2: {"exp_required": 5000, "max_members": 25, "features": ["territory"]},
    3: {"exp_required": 15000, "max_members": 30, "features": ["warehouse"]},
    4: {"exp_required": 30000, "max_members": 35, "features": ["shop_discount"]},
    5: {"exp_required": 50000, "max_members": 40, "features": ["guild_quests"]},
    7: {"exp_required": 100000, "max_members": 50, "features": ["skills"]},
    10: {"exp_required": 200000, "max_members": 60, "features": ["guild_war"]},
    15: {"exp_required": 500000, "max_members": 100, "features": ["elite_war"]},
}


class GuildError(Exception):
    """公会操作错误"""

    def __init__(self, message: str, code: str = "GUILD_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class GuildManager:
    """公会管理器

    负责公会的创建、成员管理、贡献等功能。
    """

    def __init__(self, session: Session):
        """初始化公会管理器

        Args:
            session: 数据库会话
        """
        self.session = session

    # ==================== 公会创建和查询 ====================

    def create_guild(
        self,
        leader_id: str,
        guild_name: str,
        description: str | None = None,
        guild_name_zh: str | None = None,
        icon: str | None = None,
        join_type: str = GuildJoinType.OPEN.value,
        min_level: int = 1,
    ) -> dict[str, Any]:
        """创建公会

        Args:
            leader_id: 会长玩家ID
            guild_name: 公会名称（英文）
            description: 公会描述
            guild_name_zh: 公会中文名称
            icon: 公会图标
            join_type: 加入方式 (open/closed/invite_only)
            min_level: 最低加入等级

        Returns:
            创建结果，包含公会ID

        Raises:
            GuildError: 创建失败时抛出
        """
        # 验证玩家存在
        player = self.session.get(Player, leader_id)
        if not player:
            raise GuildError("Player not found", "PLAYER_NOT_FOUND")

        # 检查玩家是否已在公会中
        existing_member = self.session.scalar(
            select(GuildMember).where(GuildMember.player_id == leader_id)
        )
        if existing_member:
            raise GuildError("Player already in a guild", "ALREADY_IN_GUILD")

        # 检查公会名是否已存在
        existing_guild = self.session.scalar(
            select(Guild).where(Guild.guild_name == guild_name)
        )
        if existing_guild:
            raise GuildError("Guild name already exists", "NAME_EXISTS")

        # 验证加入方式
        if join_type not in [GuildJoinType.OPEN.value, GuildJoinType.CLOSED.value, GuildJoinType.INVITE_ONLY.value]:
            raise GuildError("Invalid join type", "INVALID_JOIN_TYPE")

        # 创建公会
        guild_id = generate_uuid()
        now = datetime.utcnow()

        guild = Guild(
            guild_id=guild_id,
            guild_name=guild_name,
            guild_name_zh=guild_name_zh,
            leader_id=leader_id,
            description=description,
            icon=icon,
            level=1,
            exp=0,
            member_count=1,
            max_members=GUILD_LEVEL_CONFIG[1]["max_members"],
            contribution_points=0,
            guild_funds=0,
            join_type=join_type,
            min_level=min_level,
            created_at=now,
        )

        # 创建会长成员记录
        leader_member = GuildMember(
            membership_id=generate_uuid(),
            guild_id=guild_id,
            player_id=leader_id,
            role=GuildRole.LEADER.value,
            title="会长",
            contribution_points=0,
            weekly_contribution=0,
            is_active=True,
            joined_at=now,
        )

        try:
            self.session.add(guild)
            self.session.add(leader_member)
            self.session.flush()
        except IntegrityError as e:
            self.session.rollback()
            raise GuildError(f"Database error: {e}", "DATABASE_ERROR")

        return {
            "guild_id": guild_id,
            "guild_name": guild_name,
            "message": "Guild created successfully",
        }

    def get_guild_info(self, guild_id: str) -> dict[str, Any]:
        """获取公会详情

        Args:
            guild_id: 公会ID

        Returns:
            公会详情

        Raises:
            GuildError: 公会不存在时抛出
        """
        guild = self.session.get(Guild, guild_id)
        if not guild:
            raise GuildError("Guild not found", "GUILD_NOT_FOUND")

        # 获取公会成员列表
        members = self.session.scalars(
            select(GuildMember)
            .where(GuildMember.guild_id == guild_id)
            .where(GuildMember.is_active)
        ).all()

        # 构建成员信息
        member_list = []
        for member in members:
            player = self.session.get(Player, member.player_id)
            member_list.append({
                "player_id": member.player_id,
                "username": player.username if player else f"Player_{member.player_id[:8]}",
                "level": player.level if player else 1,
                "role": member.role,
                "title": member.title,
                "contribution_points": member.contribution_points,
                "weekly_contribution": member.weekly_contribution,
                "is_active": member.is_active,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            })

        # 按角色排序
        role_order = {GuildRole.LEADER.value: 0, GuildRole.OFFICER.value: 1, GuildRole.MEMBER.value: 2}
        member_list.sort(key=lambda x: (role_order.get(x["role"], 99), -x["contribution_points"]))

        # 获取等级配置
        level_config = self._get_level_config(guild.level)

        return {
            "guild_id": guild.guild_id,
            "guild_name": guild.guild_name,
            "guild_name_zh": guild.guild_name_zh,
            "description": guild.description,
            "icon": guild.icon,
            "level": guild.level,
            "exp": guild.exp,
            "exp_to_next_level": self._calculate_exp_to_next(guild),
            "member_count": guild.member_count,
            "max_members": guild.max_members,
            "contribution_points": guild.contribution_points,
            "guild_funds": guild.guild_funds,
            "join_type": guild.join_type,
            "min_level": guild.min_level,
            "features": level_config["features"],
            "created_at": guild.created_at.isoformat() if guild.created_at else None,
            "members": member_list,
        }

    def get_guild_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        join_type: str | None = None,
        min_level: int | None = None,
    ) -> dict[str, Any]:
        """获取公会列表

        Args:
            page: 页码
            page_size: 每页数量
            search: 搜索关键词
            join_type: 筛选加入方式
            min_level: 筛选最低等级

        Returns:
            公会列表
        """
        query = select(Guild)

        # 搜索过滤
        if search:
            query = query.where(Guild.guild_name.contains(search))

        # 加入方式过滤
        if join_type:
            query = query.where(Guild.join_type == join_type)

        # 最低等级过滤
        if min_level is not None:
            query = query.where(Guild.level >= min_level)

        # 排序：按等级和成员数
        query = query.order_by(Guild.level.desc(), Guild.member_count.desc())

        # 获取总数
        total_query = select(func.count(Guild.guild_id))
        if search:
            total_query = total_query.where(Guild.guild_name.contains(search))
        if join_type:
            total_query = total_query.where(Guild.join_type == join_type)
        if min_level is not None:
            total_query = total_query.where(Guild.level >= min_level)

        total_result = self.session.execute(total_query).scalar()
        total = total_result or 0

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        guilds = self.session.scalars(query).all()

        # 构建结果
        result = []
        for guild in guilds:
            level_config = self._get_level_config(guild.level)
            result.append({
                "guild_id": guild.guild_id,
                "guild_name": guild.guild_name,
                "guild_name_zh": guild.guild_name_zh,
                "description": guild.description,
                "icon": guild.icon,
                "level": guild.level,
                "member_count": guild.member_count,
                "max_members": guild.max_members,
                "join_type": guild.join_type,
                "min_level": guild.min_level,
                "features": level_config["features"],
                "created_at": guild.created_at.isoformat() if guild.created_at else None,
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "guilds": result,
        }

    def get_player_guild(self, player_id: str) -> dict[str, Any]:
        """获取玩家所属公会

        Args:
            player_id: 玩家ID

        Returns:
            公会信息，如果不在公会中则返回空信息
        """
        member = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == player_id)
            .where(GuildMember.is_active)
        )

        if not member:
            return {
                "has_guild": False,
                "guild": None,
                "membership": None,
            }

        guild = self.session.get(Guild, member.guild_id)
        if not guild:
            return {
                "has_guild": False,
                "guild": None,
                "membership": None,
            }

        return {
            "has_guild": True,
            "guild": {
                "guild_id": guild.guild_id,
                "guild_name": guild.guild_name,
                "guild_name_zh": guild.guild_name_zh,
                "level": guild.level,
                "member_count": guild.member_count,
                "max_members": guild.max_members,
            },
            "membership": {
                "role": member.role,
                "title": member.title,
                "contribution_points": member.contribution_points,
                "weekly_contribution": member.weekly_contribution,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            },
        }

    # ==================== 成员管理 ====================

    def join_guild(
        self,
        player_id: str,
        guild_id: str,
    ) -> dict[str, Any]:
        """加入公会（直接加入或接受邀请后调用）

        Args:
            player_id: 玩家ID
            guild_id: 公会ID

        Returns:
            加入结果

        Raises:
            GuildError: 加入失败时抛出
        """
        # 验证玩家存在
        player = self.session.get(Player, player_id)
        if not player:
            raise GuildError("Player not found", "PLAYER_NOT_FOUND")

        # 检查玩家等级要求
        guild = self.session.get(Guild, guild_id)
        if not guild:
            raise GuildError("Guild not found", "GUILD_NOT_FOUND")

        if player.level < guild.min_level:
            raise GuildError(
                f"Player level {player.level} below required {guild.min_level}",
                "LEVEL_TOO_LOW"
            )

        # 检查玩家是否已在公会中
        existing_member = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == player_id)
            .where(GuildMember.is_active)
        )
        if existing_member:
            raise GuildError("Player already in a guild", "ALREADY_IN_GUILD")

        # 检查公会是否已满
        active_members = self.session.scalars(
            select(GuildMember)
            .where(GuildMember.guild_id == guild_id)
            .where(GuildMember.is_active)
        ).all()

        if len(active_members) >= guild.max_members:
            raise GuildError("Guild is full", "GUILD_FULL")

        # 创建成员记录
        now = datetime.utcnow()
        new_member = GuildMember(
            membership_id=generate_uuid(),
            guild_id=guild_id,
            player_id=player_id,
            role=GuildRole.MEMBER.value,
            title=None,
            contribution_points=0,
            weekly_contribution=0,
            is_active=True,
            joined_at=now,
        )

        # 更新公会成员数
        guild.member_count += 1

        self.session.add(new_member)

        return {
            "success": True,
            "guild_id": guild_id,
            "guild_name": guild.guild_name,
            "message": "Joined guild successfully",
        }

    def leave_guild(self, player_id: str) -> dict[str, Any]:
        """离开公会

        Args:
            player_id: 玩家ID

        Returns:
            离开结果

        Raises:
            GuildError: 离开失败时抛出
        """
        member = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == player_id)
            .where(GuildMember.is_active)
        )

        if not member:
            raise GuildError("Player not in a guild", "NOT_IN_GUILD")

        guild = self.session.get(Guild, member.guild_id)
        if not guild:
            raise GuildError("Guild not found", "GUILD_NOT_FOUND")

        # 会长不能直接离开
        if member.role == GuildRole.LEADER.value:
            # 检查是否有其他成员可以转让
            other_members = self.session.scalars(
                select(GuildMember)
                .where(GuildMember.guild_id == member.guild_id)
                .where(GuildMember.player_id != player_id)
                .where(GuildMember.is_active)
            ).all()

            if not other_members:
                # 最后一个成员，直接解散公会
                return self._disband_guild(guild.guild_id)

            raise GuildError("Leader must transfer leadership first", "LEADER_CANNOT_LEAVE")

        # 标记为非活跃
        member.is_active = False
        member.left_at = datetime.utcnow()

        # 更新公会成员数
        guild.member_count -= 1

        return {
            "success": True,
            "message": "Left guild successfully",
        }

    def kick_member(
        self,
        operator_id: str,
        member_player_id: str,
    ) -> dict[str, Any]:
        """踢出成员

        Args:
            operator_id: 操作者ID
            member_player_id: 要踢出的成员ID

        Returns:
            操作结果

        Raises:
            GuildError: 操作失败时抛出
        """
        # 获取操作者成员信息
        operator = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == operator_id)
            .where(GuildMember.is_active)
        )

        if not operator:
            raise GuildError("Operator not in a guild", "OPERATOR_NOT_IN_GUILD")

        # 获取目标成员信息
        target = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == member_player_id)
            .where(GuildMember.is_active)
        )

        if not target:
            raise GuildError("Target member not found", "MEMBER_NOT_FOUND")

        # 检查是否在同一公会
        if operator.guild_id != target.guild_id:
            raise GuildError("Not in the same guild", "NOT_SAME_GUILD")

        # 权限检查
        if operator.role == GuildRole.MEMBER.value:
            raise GuildError("No permission to kick", "NO_PERMISSION")

        if operator.role == GuildRole.OFFICER.value:
            # 干部只能踢普通成员
            if target.role != GuildRole.MEMBER.value:
                raise GuildError("Cannot kick officer or leader", "NO_PERMISSION")

        # 不能踢自己
        if operator_id == member_player_id:
            raise GuildError("Cannot kick yourself", "INVALID_OPERATION")

        # 标记为非活跃
        target.is_active = False
        target.left_at = datetime.utcnow()

        # 更新公会成员数
        guild = self.session.get(Guild, operator.guild_id)
        if guild:
            guild.member_count -= 1

        return {
            "success": True,
            "message": "Member kicked successfully",
        }

    def update_member_role(
        self,
        operator_id: str,
        target_player_id: str,
        new_role: str,
    ) -> dict[str, Any]:
        """更新成员角色

        Args:
            operator_id: 操作者ID
            target_player_id: 目标成员ID
            new_role: 新角色 (leader/officer/member)

        Returns:
            操作结果

        Raises:
            GuildError: 操作失败时抛出
        """
        # 验证角色
        if new_role not in [GuildRole.LEADER.value, GuildRole.OFFICER.value, GuildRole.MEMBER.value]:
            raise GuildError("Invalid role", "INVALID_ROLE")

        # 获取操作者成员信息
        operator = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == operator_id)
            .where(GuildMember.is_active)
        )

        if not operator:
            raise GuildError("Operator not in a guild", "OPERATOR_NOT_IN_GUILD")

        # 只有会长可以更改角色
        if operator.role != GuildRole.LEADER.value:
            raise GuildError("Only leader can change roles", "NO_PERMISSION")

        # 获取目标成员信息
        target = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == target_player_id)
            .where(GuildMember.is_active)
        )

        if not target:
            raise GuildError("Target member not found", "MEMBER_NOT_FOUND")

        # 检查是否在同一公会
        if operator.guild_id != target.guild_id:
            raise GuildError("Not in the same guild", "NOT_SAME_GUILD")

        # 转让会长
        if new_role == GuildRole.LEADER.value:
            if operator_id == target_player_id:
                raise GuildError("Cannot transfer to yourself", "INVALID_OPERATION")

            # 原会长转为干部
            operator.role = GuildRole.OFFICER.value
            target.role = GuildRole.LEADER.value

            # 更新公会的leader_id
            guild = self.session.get(Guild, operator.guild_id)
            if guild:
                guild.leader_id = target_player_id

            return {
                "success": True,
                "message": "Leadership transferred successfully",
            }

        # 普通角色更改
        target.role = new_role

        return {
            "success": True,
            "message": "Role updated successfully",
        }

    def get_guild_members(
        self,
        guild_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """获取公会成员列表

        Args:
            guild_id: 公会ID
            page: 页码
            page_size: 每页数量

        Returns:
            成员列表
        """
        guild = self.session.get(Guild, guild_id)
        if not guild:
            raise GuildError("Guild not found", "GUILD_NOT_FOUND")

        # 获取活跃成员
        query = select(GuildMember).where(
            GuildMember.guild_id == guild_id,
            GuildMember.is_active,
        )

        # 获取总数
        total_query = select(func.count(GuildMember.membership_id)).where(
            GuildMember.guild_id == guild_id,
            GuildMember.is_active,
        )
        total_result = self.session.execute(total_query).scalar()
        total = total_result or 0

        # 排序和分页
        role_order = {GuildRole.LEADER.value: 0, GuildRole.OFFICER.value: 1, GuildRole.MEMBER.value: 2}
        query = query.order_by(GuildMember.role)
        query = query.offset((page - 1) * page_size).limit(page_size)

        members = self.session.scalars(query).all()

        # 构建结果
        result = []
        for member in members:
            player = self.session.get(Player, member.player_id)
            result.append({
                "player_id": member.player_id,
                "username": player.username if player else f"Player_{member.player_id[:8]}",
                "level": player.level if player else 1,
                "role": member.role,
                "title": member.title,
                "contribution_points": member.contribution_points,
                "weekly_contribution": member.weekly_contribution,
                "is_active": member.is_active,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            })

        # 按角色排序
        result.sort(key=lambda x: (role_order.get(x["role"], 99), -x["contribution_points"]))

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "members": result,
        }

    # ==================== 公会设置 ====================

    def update_guild_settings(
        self,
        operator_id: str,
        guild_id: str,
        description: str | None = None,
        guild_name_zh: str | None = None,
        icon: str | None = None,
        join_type: str | None = None,
        min_level: int | None = None,
    ) -> dict[str, Any]:
        """更新公会设置

        Args:
            operator_id: 操作者ID
            guild_id: 公会ID
            description: 公会描述
            guild_name_zh: 中文名称
            icon: 公会图标
            join_type: 加入方式
            min_level: 最低加入等级

        Returns:
            更新结果

        Raises:
            GuildError: 更新失败时抛出
        """
        # 获取操作者成员信息
        operator = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == operator_id)
            .where(GuildMember.guild_id == guild_id)
            .where(GuildMember.is_active)
        )

        if not operator:
            raise GuildError("Not a guild member", "NOT_MEMBER")

        # 权限检查（会长和干部可以修改）
        if operator.role not in [GuildRole.LEADER.value, GuildRole.OFFICER.value]:
            raise GuildError("No permission", "NO_PERMISSION")

        # 获取公会
        guild = self.session.get(Guild, guild_id)
        if not guild:
            raise GuildError("Guild not found", "GUILD_NOT_FOUND")

        # 更新字段
        if description is not None:
            guild.description = description

        if guild_name_zh is not None:
            guild.guild_name_zh = guild_name_zh

        if icon is not None:
            guild.icon = icon

        if join_type is not None:
            if join_type not in [GuildJoinType.OPEN.value, GuildJoinType.CLOSED.value, GuildJoinType.INVITE_ONLY.value]:
                raise GuildError("Invalid join type", "INVALID_JOIN_TYPE")
            guild.join_type = join_type

        if min_level is not None:
            if min_level < 1 or min_level > 100:
                raise GuildError("Invalid min level", "INVALID_LEVEL")
            guild.min_level = min_level

        return {
            "success": True,
            "message": "Guild settings updated",
        }

    # ==================== 贡献系统 ====================

    def contribute(
        self,
        player_id: str,
        amount: int,
    ) -> dict[str, Any]:
        """向公会贡献

        Args:
            player_id: 玩家ID
            amount: 贡献数量（能量值）

        Returns:
            贡献结果

        Raises:
            GuildError: 贡献失败时抛出
        """
        if amount <= 0:
            raise GuildError("Invalid contribution amount", "INVALID_AMOUNT")

        # 获取成员信息
        member = self.session.scalar(
            select(GuildMember)
            .where(GuildMember.player_id == player_id)
            .where(GuildMember.is_active)
        )

        if not member:
            raise GuildError("Player not in a guild", "NOT_IN_GUILD")

        # 获取公会信息
        guild = self.session.get(Guild, member.guild_id)
        if not guild:
            raise GuildError("Guild not found", "GUILD_NOT_FOUND")

        # 计算公会经验（100能量 = 1经验）
        exp_gained = amount // 100

        # 更新公会数据
        guild.contribution_points += amount
        guild.exp += exp_gained

        # 更新成员数据
        member.contribution_points += amount
        member.weekly_contribution += amount

        # 检查升级
        level_up = False
        old_level = guild.level

        for lvl in sorted(GUILD_LEVEL_CONFIG.keys()):
            if lvl > old_level and guild.exp >= GUILD_LEVEL_CONFIG[lvl]["exp_required"]:
                guild.level = lvl
                guild.max_members = GUILD_LEVEL_CONFIG[lvl]["max_members"]
                level_up = True

        return {
            "success": True,
            "energy_contributed": amount,
            "exp_gained": exp_gained,
            "total_contribution": member.contribution_points,
            "guild_level": guild.level,
            "level_up": level_up,
            "new_features": GUILD_LEVEL_CONFIG[guild.level]["features"] if level_up else [],
        }

    def reset_weekly_contributions(self, guild_id: str) -> dict[str, Any]:
        """重置本周贡献（每周任务调用）

        Args:
            guild_id: 公会ID

        Returns:
            重置结果
        """
        guild = self.session.get(Guild, guild_id)
        if not guild:
            raise GuildError("Guild not found", "GUILD_NOT_FOUND")

        # 重置所有活跃成员的周贡献
        self.session.execute(
            update(GuildMember)
            .where(GuildMember.guild_id == guild_id)
            .where(GuildMember.is_active)
            .values(weekly_contribution=0)
        )

        return {
            "success": True,
            "message": "Weekly contributions reset",
        }

    # ==================== 私有方法 ====================

    def _get_level_config(self, level: int) -> dict[str, Any]:
        """获取等级配置"""
        for lvl in sorted(GUILD_LEVEL_CONFIG.keys(), reverse=True):
            if level >= lvl:
                return GUILD_LEVEL_CONFIG[lvl]
        return GUILD_LEVEL_CONFIG[1]

    def _calculate_exp_to_next(self, guild: Guild) -> int:
        """计算升级所需经验"""
        current_exp = guild.exp
        for lvl in sorted(GUILD_LEVEL_CONFIG.keys()):
            if lvl > guild.level:
                required = GUILD_LEVEL_CONFIG[lvl]["exp_required"]
                return max(0, required - current_exp)
        return 0  # 已满级

    def _disband_guild(self, guild_id: str) -> dict[str, Any]:
        """解散公会"""
        guild = self.session.get(Guild, guild_id)
        if not guild:
            raise GuildError("Guild not found", "GUILD_NOT_FOUND")

        # 标记为已解散
        guild.disbanded_at = datetime.utcnow()

        # 标记所有成员为非活跃
        self.session.execute(
            update(GuildMember)
            .where(GuildMember.guild_id == guild_id)
            .values(is_active=False, left_at=datetime.utcnow())
        )

        return {
            "success": True,
            "message": "Guild disbanded",
        }


# 便捷函数
def get_guild_level_config(level: int) -> dict[str, Any]:
    """获取公会等级配置（外部调用）"""
    for lvl in sorted(GUILD_LEVEL_CONFIG.keys(), reverse=True):
        if level >= lvl:
            return GUILD_LEVEL_CONFIG[lvl]
    return GUILD_LEVEL_CONFIG[1]


def calculate_exp_to_next_level(level: int, current_exp: int) -> int:
    """计算升级所需经验（外部调用）"""
    for lvl in sorted(GUILD_LEVEL_CONFIG.keys()):
        if lvl > level:
            return max(0, GUILD_LEVEL_CONFIG[lvl]["exp_required"] - current_exp)
    return 0
