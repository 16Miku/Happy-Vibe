"""成就系统 API 路由

提供成就列表、进度查询、奖励领取等功能的 REST API 端点。
使用新的 AchievementDefinition 和 AchievementProgress 数据模型。
"""

from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.achievement_manager import AchievementManager, get_achievement_manager
from src.storage.database import get_db
from src.storage.models import AchievementCategory, AchievementTier


# ============ 枚举类型 ============


class AchievementCategoryEnum(StrEnum):
    """成就类别枚举"""

    CODING = "coding"
    FARMING = "farming"
    SOCIAL = "social"
    ECONOMY = "economy"
    SPECIAL = "special"


class AchievementTierEnum(StrEnum):
    """成就稀有度枚举"""

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


# ============ Pydantic 模型 ============


class AchievementResponse(BaseModel):
    """成就响应模型"""

    achievement_id: str
    category: str
    tier: str
    title: str
    title_zh: str
    description: str
    icon: str
    is_hidden: bool
    is_secret: bool
    display_order: int
    current_value: int
    target_value: int
    progress_percent: float
    is_unlocked: bool
    is_completed: bool
    is_claimed: bool
    started_at: str | None
    completed_at: str | None
    claimed_at: str | None
    reward: dict[str, int]


class AchievementListResponse(BaseModel):
    """成就列表响应模型"""

    achievements: list[AchievementResponse]
    total: int


class AchievementStatsResponse(BaseModel):
    """成就统计响应模型"""

    total_achievements: int
    unlocked_count: int
    completed_count: int
    claimed_count: int
    unlocked_percent: float
    category_stats: dict[str, dict[str, int]]


class ProgressUpdateRequest(BaseModel):
    """进度更新请求模型"""

    increment: int = Field(default=1, ge=1, description="进度增量")


class ProgressUpdateResponse(BaseModel):
    """进度更新响应模型"""

    achievement_id: str
    previous_value: int
    current_value: int
    target_value: int
    progress_percent: float
    is_completed: bool
    is_unlocked: bool
    is_claimed: bool
    newly_completed: bool


class EventUpdateRequest(BaseModel):
    """事件更新请求模型"""

    event_type: str = Field(..., description="事件类型")
    event_data: dict = Field(default_factory=dict, description="事件数据")


class EventUpdateResponse(BaseModel):
    """事件更新响应模型"""

    updated_achievements: list[dict]
    count: int


class ClaimRewardResponse(BaseModel):
    """领取奖励响应模型"""

    success: bool
    achievement_id: str | None = None
    reward: dict[str, int] | None = None
    gold_rewarded: int = 0
    exp_rewarded: int = 0
    diamonds_rewarded: int = 0
    message: str | None = None


class InitializationResponse(BaseModel):
    """初始化响应模型"""

    initialized_count: int
    message: str


# ============ 依赖注入 ============


def get_db_session():
    """获取数据库会话"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


# ============ 路由定义 ============

router = APIRouter(prefix="/api/achievement", tags=["achievement"])


@router.get("", response_model=AchievementListResponse)
async def get_achievements(
    player_id: str = Query(..., description="玩家 ID"),
    category: AchievementCategoryEnum | None = Query(None, description="成就类别筛选"),
    tier: AchievementTierEnum | None = Query(None, description="稀有度筛选"),
    include_hidden: bool = Query(False, description="是否包含隐藏成就"),
    session: Session = Depends(get_db_session),
) -> AchievementListResponse:
    """获取玩家成就列表

    Args:
        player_id: 玩家 ID
        category: 可选的成就类别筛选
        tier: 可选的稀有度筛选
        include_hidden: 是否包含隐藏成就
        session: 数据库会话

    Returns:
        成就列表及统计信息
    """
    manager = AchievementManager(session)

    # 确保玩家有进度记录
    manager.ensure_player_progress(player_id)

    # 获取成就列表
    achievements = manager.get_player_achievements(
        player_id=player_id,
        category=category.value if category else None,
        tier=tier.value if tier else None,
        include_hidden=include_hidden,
    )

    return AchievementListResponse(
        achievements=[AchievementResponse(**ach) for ach in achievements],
        total=len(achievements),
    )


@router.get("/stats", response_model=AchievementStatsResponse)
async def get_achievement_stats(
    player_id: str = Query(..., description="玩家 ID"),
    session: Session = Depends(get_db_session),
) -> AchievementStatsResponse:
    """获取玩家成就统计信息

    Args:
        player_id: 玩家 ID
        session: 数据库会话

    Returns:
        成就统计信息
    """
    manager = AchievementManager(session)
    stats = manager.get_player_stats(player_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    return AchievementStatsResponse(**stats)


@router.get("/{achievement_id}", response_model=AchievementResponse)
async def get_achievement_detail(
    achievement_id: str,
    player_id: str = Query(..., description="玩家 ID"),
    session: Session = Depends(get_db_session),
) -> AchievementResponse:
    """获取单个成就详情

    Args:
        achievement_id: 成就 ID
        player_id: 玩家 ID
        session: 数据库会话

    Returns:
        成就详情
    """
    manager = AchievementManager(session)
    detail = manager.get_achievement_detail(player_id, achievement_id)

    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"成就不存在: {achievement_id}",
        )

    return AchievementResponse(**detail)


@router.post("/{achievement_id}/progress", response_model=ProgressUpdateResponse)
async def update_achievement_progress(
    achievement_id: str,
    player_id: str = Query(..., description="玩家 ID"),
    request: ProgressUpdateRequest | None = None,
    increment: int | None = None,
    session: Session = Depends(get_db_session),
) -> ProgressUpdateResponse:
    """直接更新成就进度

    Args:
        achievement_id: 成就 ID
        player_id: 玩家 ID
        request: 进度更新请求（可选）
        increment: 进度增量（可选，优先使用 request 中的值）
        session: 数据库会话

    Returns:
        更新后的进度信息
    """
    # 确定增量值
    inc = 1
    if request:
        inc = request.increment
    elif increment is not None:
        inc = increment

    manager = AchievementManager(session)
    result = manager.update_progress_direct(player_id, achievement_id, inc)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"成就或玩家不存在: {achievement_id}",
        )

    return ProgressUpdateResponse(**result)


@router.post("/update", response_model=EventUpdateResponse)
async def update_progress_by_event(
    request: EventUpdateRequest,
    player_id: str = Query(..., description="玩家 ID"),
    session: Session = Depends(get_db_session),
) -> EventUpdateResponse:
    """根据游戏事件更新相关成就进度

    Args:
        request: 事件更新请求
        player_id: 玩家 ID
        session: 数据库会话

    Returns:
        更新的成就列表
    """
    manager = AchievementManager(session)
    updated = manager.update_progress(
        player_id=player_id,
        event_type=request.event_type,
        event_data=request.event_data,
    )

    return EventUpdateResponse(
        updated_achievements=updated,
        count=len(updated),
    )


@router.post("/{achievement_id}/claim", response_model=ClaimRewardResponse)
async def claim_achievement_reward(
    achievement_id: str,
    player_id: str = Query(..., description="玩家 ID"),
    session: Session = Depends(get_db_session),
) -> ClaimRewardResponse:
    """领取成就奖励

    Args:
        achievement_id: 成就 ID
        player_id: 玩家 ID
        session: 数据库会话

    Returns:
        奖励信息
    """
    manager = AchievementManager(session)
    result = manager.claim_reward(player_id, achievement_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"成就或玩家不存在: {achievement_id}",
        )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "无法领取奖励"),
        )

    return ClaimRewardResponse(**result)


@router.post("/initialize", response_model=InitializationResponse)
async def initialize_achievements(
    session: Session = Depends(get_db_session),
) -> InitializationResponse:
    """初始化成就定义到数据库

    通常只在系统首次启动或更新成就配置时调用。

    Args:
        session: 数据库会话

    Returns:
        初始化结果
    """
    manager = AchievementManager(session)
    count = manager.initialize_achievements()

    return InitializationResponse(
        initialized_count=count,
        message=f"成功初始化 {count} 个成就定义",
    )


@router.post("/ensure-progress", response_model=dict[str, str])
async def ensure_player_progress(
    player_id: str = Query(..., description="玩家 ID"),
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    """确保玩家拥有所有成就的进度记录

    Args:
        player_id: 玩家 ID
        session: 数据库会话

    Returns:
        操作结果
    """
    manager = AchievementManager(session)
    new_records = manager.ensure_player_progress(player_id)

    return {
        "player_id": player_id,
        "message": f"为玩家创建了 {len(new_records)} 条新的进度记录",
    }
