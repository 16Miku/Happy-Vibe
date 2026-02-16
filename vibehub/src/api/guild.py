"""公会系统 API

提供公会相关的 REST API 端点。
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.guild_manager import GuildError, GuildManager
from src.storage.database import get_db

router = APIRouter(prefix="/api/guilds", tags=["guilds"])


# ==================== 依赖注入 ====================


def get_guild_manager(session: Session = Depends(get_db)) -> GuildManager:
    """获取公会管理器实例"""
    return GuildManager(session)


# ==================== 请求/响应模型 ====================


class GuildCreateRequest(BaseModel):
    """创建公会请求"""

    leader_id: str = Field(..., description="会长玩家ID")
    guild_name: str = Field(..., min_length=2, max_length=50, description="公会名称")
    guild_name_zh: str | None = Field(None, max_length=50, description="公会中文名称")
    description: str | None = Field(None, max_length=500, description="公会描述")
    icon: str | None = Field(None, description="公会图标")
    join_type: str = Field("open", description="加入方式: open/closed/invite_only")
    min_level: int = Field(1, ge=1, le=100, description="最低加入等级")


class GuildUpdateRequest(BaseModel):
    """更新公会设置请求"""

    operator_id: str = Field(..., description="操作者玩家ID")
    description: str | None = Field(None, max_length=500, description="公会描述")
    guild_name_zh: str | None = Field(None, max_length=50, description="公会中文名称")
    icon: str | None = Field(None, description="公会图标")
    join_type: str | None = Field(None, description="加入方式: open/closed/invite_only")
    min_level: int | None = Field(None, ge=1, le=100, description="最低加入等级")


class MemberRoleUpdateRequest(BaseModel):
    """更新成员角色请求"""

    operator_id: str = Field(..., description="操作者玩家ID")
    target_id: str = Field(..., description="目标成员玩家ID")
    new_role: str = Field(..., description="新角色: leader/officer/member")


class ContributeRequest(BaseModel):
    """贡献请求"""

    player_id: str = Field(..., description="玩家ID")
    amount: int = Field(..., ge=1, description="贡献数量")


class JoinRequest(BaseModel):
    """加入公会请求"""

    player_id: str = Field(..., description="玩家ID")


# ==================== API 端点 ====================


@router.post(
    "/create",
    summary="创建公会",
    description="创建一个新的公会，创建者自动成为会长。",
    responses={
        200: {"description": "公会创建成功"},
        400: {"description": "已在公会中或公会名已存在"},
        404: {"description": "玩家不存在"},
    },
)
async def create_guild(
    request: GuildCreateRequest,
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """创建公会

    Args:
        request: 创建请求
        manager: 公会管理器

    Returns:
        创建结果

    Raises:
        HTTPException: 创建失败时抛出
    """
    try:
        result = manager.create_guild(
            leader_id=request.leader_id,
            guild_name=request.guild_name,
            description=request.description,
            guild_name_zh=request.guild_name_zh,
            icon=request.icon,
            join_type=request.join_type,
            min_level=request.min_level,
        )
        return result
    except GuildError as e:
        status_code = 400
        if e.code in ["PLAYER_NOT_FOUND"]:
            status_code = 404
        elif e.code in ["ALREADY_IN_GUILD", "NAME_EXISTS"]:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=e.message)


@router.get(
    "/list",
    summary="获取公会列表",
    description="获取公会列表，支持分页、搜索和筛选。",
    responses={
        200: {"description": "成功返回公会列表"},
    },
)
async def list_guilds(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str | None = Query(None, description="搜索关键词"),
    join_type: str | None = Query(None, description="加入方式筛选"),
    min_level: int | None = Query(None, ge=1, description="最低等级筛选"),
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """获取公会列表

    Args:
        page: 页码
        page_size: 每页数量
        search: 搜索关键词
        join_type: 加入方式筛选
        min_level: 最低等级筛选
        manager: 公会管理器

    Returns:
        公会列表
    """
    return manager.get_guild_list(
        page=page,
        page_size=page_size,
        search=search,
        join_type=join_type,
        min_level=min_level,
    )


@router.get(
    "/{guild_id}",
    summary="获取公会详情",
    description="获取指定公会的详细信息。",
    responses={
        200: {"description": "成功返回公会详情"},
        404: {"description": "公会不存在"},
    },
)
async def get_guild(
    guild_id: str,
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """获取公会详情

    Args:
        guild_id: 公会ID
        manager: 公会管理器

    Returns:
        公会详情

    Raises:
        HTTPException: 公会不存在时抛出
    """
    try:
        return manager.get_guild_info(guild_id)
    except GuildError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.put(
    "/{guild_id}/settings",
    summary="更新公会设置",
    description="更新公会的基本设置，需要管理员权限。",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "更新失败"},
        403: {"description": "无权限"},
    },
)
async def update_guild_settings(
    guild_id: str,
    request: GuildUpdateRequest,
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """更新公会设置

    Args:
        guild_id: 公会ID
        request: 更新请求
        manager: 公会管理器

    Returns:
        更新结果

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        return manager.update_guild_settings(
            operator_id=request.operator_id,
            guild_id=guild_id,
            description=request.description,
            guild_name_zh=request.guild_name_zh,
            icon=request.icon,
            join_type=request.join_type,
            min_level=request.min_level,
        )
    except GuildError as e:
        status_code = 400
        if e.code == "NOT_MEMBER":
            status_code = 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.post(
    "/{guild_id}/join",
    summary="加入公会",
    description="申请加入指定公会，需要满足公会的加入条件。",
    responses={
        200: {"description": "加入成功"},
        400: {"description": "已在公会中"},
        403: {"description": "等级不足"},
        404: {"description": "公会或玩家不存在"},
    },
)
async def join_guild(
    guild_id: str,
    request: JoinRequest,
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """加入公会

    Args:
        guild_id: 公会ID
        request: 加入请求
        manager: 公会管理器

    Returns:
        加入结果

    Raises:
        HTTPException: 加入失败时抛出
    """
    try:
        return manager.join_guild(
            player_id=request.player_id,
            guild_id=guild_id,
        )
    except GuildError as e:
        status_code = 400
        if e.code in ["GUILD_NOT_FOUND", "PLAYER_NOT_FOUND"]:
            status_code = 404
        elif e.code == "ALREADY_IN_GUILD":
            status_code = 400
        elif e.code == "LEVEL_TOO_LOW":
            status_code = 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.post(
    "/leave",
    summary="离开公会",
    description="离开当前所在的公会。会长不能直接离开，需要先转让会长。",
    responses={
        200: {"description": "离开成功"},
        400: {"description": "离开失败"},
        404: {"description": "不在任何公会中"},
    },
)
async def leave_guild(
    player_id: str = Query(..., description="玩家ID"),
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """离开公会

    Args:
        player_id: 玩家ID
        manager: 公会管理器

    Returns:
        离开结果

    Raises:
        HTTPException: 离开失败时抛出
    """
    try:
        return manager.leave_guild(player_id)
    except GuildError as e:
        status_code = 400
        if e.code == "NOT_IN_GUILD":
            status_code = 404
        raise HTTPException(status_code=status_code, detail=e.message)


@router.delete(
    "/{guild_id}/members/{player_id}",
    summary="踢出成员",
    description="将指定成员踢出公会，需要管理员权限。",
    responses={
        200: {"description": "踢出成功"},
        400: {"description": "操作失败"},
        403: {"description": "无权限"},
        404: {"description": "成员不存在"},
    },
)
async def kick_member(
    guild_id: str,
    player_id: str,
    operator_id: str = Query(..., description="操作者玩家ID"),
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """踢出成员

    Args:
        guild_id: 公会ID
        player_id: 要踢出的成员ID
        operator_id: 操作者ID
        manager: 公会管理器

    Returns:
        操作结果

    Raises:
        HTTPException: 操作失败时抛出
    """
    try:
        return manager.kick_member(
            operator_id=operator_id,
            member_player_id=player_id,
        )
    except GuildError as e:
        status_code = 400
        if e.code in ["OPERATOR_NOT_IN_GUILD", "MEMBER_NOT_FOUND"]:
            status_code = 404
        elif e.code in ["NO_PERMISSION", "NOT_SAME_GUILD"]:
            status_code = 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.put(
    "/{guild_id}/members/{player_id}/role",
    summary="更新成员角色",
    description="更新公会成员的角色，需要会长权限。",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "更新失败"},
        403: {"description": "无权限"},
        404: {"description": "成员不存在"},
    },
)
async def update_member_role(
    guild_id: str,
    player_id: str,
    request: MemberRoleUpdateRequest,
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """更新成员角色

    Args:
        guild_id: 公会ID
        player_id: 目标成员ID
        request: 角色更新请求
        manager: 公会管理器

    Returns:
        更新结果

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        return manager.update_member_role(
            operator_id=request.operator_id,
            target_player_id=player_id,
            new_role=request.new_role,
        )
    except GuildError as e:
        status_code = 400
        if e.code in ["OPERATOR_NOT_IN_GUILD", "MEMBER_NOT_FOUND"]:
            status_code = 404
        elif e.code in ["NO_PERMISSION", "NOT_SAME_GUILD"]:
            status_code = 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.get(
    "/{guild_id}/members",
    summary="获取公会成员列表",
    description="获取指定公会的成员列表，支持分页。",
    responses={
        200: {"description": "成功返回成员列表"},
        404: {"description": "公会不存在"},
    },
)
async def get_guild_members(
    guild_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """获取公会成员列表

    Args:
        guild_id: 公会ID
        page: 页码
        page_size: 每页数量
        manager: 公会管理器

    Returns:
        成员列表

    Raises:
        HTTPException: 获取失败时抛出
    """
    try:
        return manager.get_guild_members(
            guild_id=guild_id,
            page=page,
            page_size=page_size,
        )
    except GuildError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/contribute",
    summary="向公会贡献",
    description="向所在公会贡献资源，增加公会经验和个人贡献值。",
    responses={
        200: {"description": "贡献成功"},
        400: {"description": "贡献失败"},
        403: {"description": "不在任何公会中"},
    },
)
async def contribute_to_guild(
    request: ContributeRequest,
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """向公会贡献

    Args:
        request: 贡献请求
        manager: 公会管理器

    Returns:
        贡献结果

    Raises:
        HTTPException: 贡献失败时抛出
    """
    try:
        return manager.contribute(
            player_id=request.player_id,
            amount=request.amount,
        )
    except GuildError as e:
        status_code = 400
        if e.code == "NOT_IN_GUILD":
            status_code = 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.get(
    "/player/{player_id}",
    summary="获取玩家所属公会",
    description="获取指定玩家所属的公会信息。",
    responses={
        200: {"description": "成功返回公会信息或空"},
    },
)
async def get_player_guild(
    player_id: str,
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """获取玩家所属公会

    Args:
        player_id: 玩家ID
        manager: 公会管理器

    Returns:
        公会信息
    """
    return manager.get_player_guild(player_id)


@router.post(
    "/{guild_id}/weekly-reset",
    summary="重置本周贡献",
    description="重置公会所有成员的本周贡献值（管理员接口）。",
    responses={
        200: {"description": "重置成功"},
        404: {"description": "公会不存在"},
    },
)
async def reset_weekly_contributions(
    guild_id: str,
    manager: GuildManager = Depends(get_guild_manager),
) -> dict:
    """重置本周贡献（管理员接口）

    Args:
        guild_id: 公会ID
        manager: 公会管理器

    Returns:
        重置结果
    """
    try:
        return manager.reset_weekly_contributions(guild_id)
    except GuildError as e:
        raise HTTPException(status_code=404, detail=e.message)
