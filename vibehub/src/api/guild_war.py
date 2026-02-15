"""公会战 API

提供公会战相关的 REST API 端点。
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.guild_war_manager import GuildWarError, GuildWarManager
from src.storage.database import get_db

router = APIRouter(prefix="/api/guild-wars", tags=["guild-wars"])


# ==================== 依赖注入 ====================


def get_war_manager(session: Session = Depends(get_db)) -> GuildWarManager:
    """获取公会战管理器实例"""
    return GuildWarManager(session)


# ==================== 请求/响应模型 ====================


class CreateWarRequest(BaseModel):
    """创建公会战请求"""

    creator_id: str = Field(..., description="创建者玩家ID")
    guild_a_id: str = Field(..., description="公会A ID（发起方）")
    guild_b_id: str = Field(..., description="公会B ID（被挑战方）")
    war_type: str = Field("honor", description="战斗类型: territory/resource/honor")
    duration_hours: int = Field(24, ge=1, le=168, description="持续小时数")
    war_name: str | None = Field(None, description="战斗名称")
    target_score: int = Field(1000, ge=100, description="目标分数")


class UpdateScoreRequest(BaseModel):
    """更新分数请求"""

    player_id: str = Field(..., description="玩家ID")
    score_delta: int = Field(..., ge=1, description="分数增量")
    damage_dealt: int = Field(0, ge=0, description="造成伤害")
    battle_won: bool = Field(False, description="是否获胜本场")


class EndWarRequest(BaseModel):
    """结束公会战请求"""

    force_winner_id: str | None = Field(None, description="强制指定获胜公会ID")


# ==================== API 端点 ====================


@router.post("/create")
async def create_war(
    request: CreateWarRequest,
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """创建公会战

    Args:
        request: 创建请求
        manager: 公会战管理器

    Returns:
        创建结果

    Raises:
        HTTPException: 创建失败时抛出
    """
    try:
        return manager.create_war(
            creator_id=request.creator_id,
            guild_a_id=request.guild_a_id,
            guild_b_id=request.guild_b_id,
            war_type=request.war_type,
            duration_hours=request.duration_hours,
            war_name=request.war_name,
            target_score=request.target_score,
        )
    except GuildWarError as e:
        status_code = 400
        if e.code in ["GUILD_A_NOT_FOUND", "GUILD_B_NOT_FOUND"]:
            status_code = 404
        elif e.code in ["NOT_MEMBER", "LEVEL_TOO_LOW"]:
            status_code = 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.post("/{war_id}/start")
async def start_war(
    war_id: str,
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """开始公会战

    Args:
        war_id: 公会战ID
        manager: 公会战管理器

    Returns:
        开始结果

    Raises:
        HTTPException: 开始失败时抛出
    """
    try:
        return manager.start_war(war_id)
    except GuildWarError as e:
        status_code = 400
        if e.code == "WAR_NOT_FOUND":
            status_code = 404
        raise HTTPException(status_code=status_code, detail=e.message)


@router.get("/{war_id}")
async def get_war_info(
    war_id: str,
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """获取公会战详情

    Args:
        war_id: 公会战ID
        manager: 公会战管理器

    Returns:
        公会战详情

    Raises:
        HTTPException: 获取失败时抛出
    """
    try:
        return manager.get_war_info(war_id)
    except GuildWarError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/list/active")
async def get_active_wars(
    guild_id: str | None = Query(None, description="筛选特定公会的战斗"),
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """获取进行中的公会战列表

    Args:
        guild_id: 可选，筛选特定公会的战斗
        manager: 公会战管理器

    Returns:
        公会战列表
    """
    return manager.get_active_wars(guild_id=guild_id)


@router.get("/list/history")
async def get_war_history(
    guild_id: str | None = Query(None, description="筛选特定公会的战斗"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """获取公会战历史记录

    Args:
        guild_id: 可选，筛选特定公会的战斗
        page: 页码
        page_size: 每页数量
        manager: 公会战管理器

    Returns:
        公会战历史列表
    """
    return manager.get_war_history(
        guild_id=guild_id,
        page=page,
        page_size=page_size,
    )


@router.post("/{war_id}/score")
async def update_score(
    war_id: str,
    request: UpdateScoreRequest,
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """更新玩家在公会战中的分数

    Args:
        war_id: 公会战ID
        request: 分数更新请求
        manager: 公会战管理器

    Returns:
        更新结果

    Raises:
        HTTPException: 更新失败时抛出
    """
    try:
        return manager.update_score(
            war_id=war_id,
            player_id=request.player_id,
            score_delta=request.score_delta,
            damage_dealt=request.damage_dealt,
            battle_won=request.battle_won,
        )
    except GuildWarError as e:
        status_code = 400
        if e.code in ["WAR_NOT_FOUND", "NOT_PARTICIPATED"]:
            status_code = 404
        elif e.code in ["NOT_IN_GUILD"]:
            status_code = 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.post("/{war_id}/end")
async def end_war(
    war_id: str,
    request: EndWarRequest = None,
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """结束公会战

    Args:
        war_id: 公会战ID
        request: 结束请求
        manager: 公会战管理器

    Returns:
        结束结果

    Raises:
        HTTPException: 结束失败时抛出
    """
    force_winner_id = None
    if request:
        force_winner_id = request.force_winner_id

    try:
        return manager.end_war(war_id, force_winner_id=force_winner_id)
    except GuildWarError as e:
        status_code = 400
        if e.code == "WAR_NOT_FOUND":
            status_code = 404
        raise HTTPException(status_code=status_code, detail=e.message)


@router.post("/{war_id}/claim")
async def claim_war_reward(
    war_id: str,
    player_id: str = Query(..., description="玩家ID"),
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """领取公会战个人奖励

    Args:
        war_id: 公会战ID
        player_id: 玩家ID
        manager: 公会战管理器

    Returns:
        领取结果

    Raises:
        HTTPException: 领取失败时抛出
    """
    try:
        return manager.claim_war_reward(
            player_id=player_id,
            war_id=war_id,
        )
    except GuildWarError as e:
        status_code = 400
        if e.code in ["WAR_NOT_FOUND", "NOT_PARTICIPATED"]:
            status_code = 404
        raise HTTPException(status_code=status_code, detail=e.message)


@router.get("/guild/{guild_id}/opponents")
async def find_opponents(
    guild_id: str,
    war_type: str = Query("honor", description="战斗类型"),
    level_diff: int = Query(3, ge=1, le=10, description="等级差异限制"),
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """查找可对战公会

    Args:
        guild_id: 公会ID
        war_type: 战斗类型
        level_diff: 等级差异限制
        manager: 公会战管理器

    Returns:
        可对战公会列表

    Raises:
        HTTPException: 查找失败时抛出
    """
    try:
        opponents = manager.find_opponent(
            guild_id=guild_id,
            war_type=war_type,
            level_diff=level_diff,
        )
        return {
            "guild_id": guild_id,
            "war_type": war_type,
            "opponents": opponents,
        }
    except GuildWarError as e:
        status_code = 404
        if e.code == "GUILD_NOT_FOUND":
            status_code = 404
        raise HTTPException(status_code=status_code, detail=e.message)


@router.post("/check-expired")
async def check_expired_wars(
    manager: GuildWarManager = Depends(get_war_manager),
) -> dict:
    """检查并结束已过期的公会战（定时任务接口）

    Args:
        manager: 公会战管理器

    Returns:
        已结束的公会战列表
    """
    finished = manager.check_and_finish_expired_wars()
    return {
        "checked": True,
        "finished_count": len(finished),
        "finished": finished,
    }
