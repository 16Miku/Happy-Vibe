"""赛季系统 API

提供赛季相关的 REST API 端点。
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Any

from src.core.season_manager import SeasonManager
from src.storage.database import get_db
from src.storage.models import SeasonType

router = APIRouter(prefix="/api/season", tags=["season"])


# ==================== Pydantic 模型 ====================


class SeasonCreateRequest(BaseModel):
    """创建赛季请求"""

    season_name: str = Field(..., description="赛季名称")
    season_number: int = Field(..., ge=1, description="赛季编号")
    season_type: str = Field(
        default=SeasonType.REGULAR.value,
        description="赛季类型 (regular/special/championship)",
    )
    start_time: str = Field(..., description="开始时间 (ISO 8601)")
    end_time: str = Field(..., description="结束时间 (ISO 8601)")
    reward_tiers: dict[str, Any] | None = Field(None, description="奖励层级配置")


class SeasonResponse(BaseModel):
    """赛季响应"""

    season_id: str
    season_name: str
    season_number: int
    season_type: str
    start_time: str
    end_time: str
    reward_tiers: dict[str, Any] | None
    is_active: bool
    created_at: str


class SeasonStatusResponse(BaseModel):
    """赛季状态响应"""

    season_id: str
    season_name: str
    season_number: int
    is_active: bool
    status: str
    start_time: str
    end_time: str
    remaining_time: str
    leaderboard_count: int


# ==================== API 端点 ====================


@router.get("/current")
async def get_current_season() -> dict[str, Any]:
    """获取当前激活的赛季

    Returns:
        当前赛季信息，如果没有则返回 404
    """
    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        season = await manager.get_current_season()

    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active season found",
        )

    return season


@router.get("/list")
async def get_season_list(
    include_inactive: bool = Query(True, description="是否包含非激活赛季"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
) -> dict[str, Any]:
    """获取赛季列表

    Args:
        include_inactive: 是否包含非激活赛季
        limit: 返回数量限制

    Returns:
        赛季列表
    """
    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        seasons = await manager.get_season_list(include_inactive, limit)

    return {
        "total": len(seasons),
        "seasons": seasons,
    }


@router.get("/{season_id}")
async def get_season(season_id: str) -> dict[str, Any]:
    """获取指定赛季信息

    Args:
        season_id: 赛季 ID

    Returns:
        赛季信息
    """
    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        season = await manager.get_season(season_id)

    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Season not found: {season_id}",
        )

    return season


@router.get("/{season_id}/status")
async def get_season_status(season_id: str) -> dict[str, Any]:
    """获取赛季状态

    Args:
        season_id: 赛季 ID

    Returns:
        赛季状态信息
    """
    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        season_status = await manager.get_season_status(season_id)

    return season_status


@router.post("")
async def create_season(request: SeasonCreateRequest) -> dict[str, Any]:
    """创建新赛季

    Args:
        request: 创建赛季请求

    Returns:
        创建的赛季信息
    """
    # 解析时间
    try:
        start_time = datetime.fromisoformat(request.start_time.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(request.end_time.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid datetime format: {e}",
        )

    # 验证时间
    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    # 验证赛季类型
    valid_types = [t.value for t in SeasonType]
    if request.season_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season type: {request.season_type}. Must be one of: {valid_types}",
        )

    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        season = await manager.create_season(
            season_name=request.season_name,
            season_number=request.season_number,
            season_type=request.season_type,
            start_time=start_time,
            end_time=end_time,
            reward_tiers=request.reward_tiers,
        )

    return season


@router.post("/{season_id}/activate")
async def activate_season(season_id: str) -> dict[str, Any]:
    """激活赛季

    先关闭其他激活的赛季，再激活指定赛季。

    Args:
        season_id: 赛季 ID

    Returns:
        更新后的赛季信息
    """
    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        try:
            season = await manager.activate_season(season_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    return season


@router.post("/{season_id}/end")
async def end_season(season_id: str) -> dict[str, Any]:
    """结束赛季

    创建最终快照并关闭赛季。

    Args:
        season_id: 赛季 ID

    Returns:
        结赛季信息
    """
    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        try:
            season = await manager.end_season(season_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    return season


@router.post("/{season_id}/rewards/distribute")
async def distribute_season_rewards(season_id: str) -> dict[str, Any]:
    """发放赛季奖励

    根据最终排名发放奖励。

    Args:
        season_id: 赛季 ID

    Returns:
        奖励发放结果
    """
    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        try:
            result = await manager.distribute_season_rewards(season_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    return result


@router.get("/{season_id}/rankings")
async def calculate_season_rankings(season_id: str) -> dict[str, Any]:
    """计算赛季最终排名

    Args:
        season_id: 赛季 ID

    Returns:
        排名计算结果
    """
    db = get_db()
    with db.get_session() as session:
        manager = SeasonManager(session)
        try:
            result = await manager.calculate_season_rankings(season_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )

    return result


@router.get("/types/available")
async def get_season_types() -> dict[str, Any]:
    """获取所有可用的赛季类型

    Returns:
        赛季类型列表
    """
    return {
        "types": [
            {
                "type": SeasonType.REGULAR.value,
                "name": "常规赛季",
                "description": "标准的赛季，按月或季度进行",
                "duration": "通常为 1-3 个月",
            },
            {
                "type": SeasonType.SPECIAL.value,
                "name": "特殊赛季",
                "description": "限定主题的特别赛季",
                "duration": "通常为 2-4 周",
            },
            {
                "type": SeasonType.CHAMPIONSHIP.value,
                "name": "锦标赛",
                "description": "高强度的锦标赛赛季",
                "duration": "通常为 1-2 周",
            },
        ]
    }
