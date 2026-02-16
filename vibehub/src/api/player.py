"""玩家 API 路由

提供玩家数据相关的 REST API 端点，包括：
- 玩家信息查询和管理
- 资源管理（能量、金币等）
- 等级经验系统
- 玩家统计数据
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.storage.database import get_db
from src.storage.models import Player


router = APIRouter(prefix="/api/player", tags=["player"])


# ============== Pydantic 模型定义 ==============


class PlayerCreate(BaseModel):
    """创建玩家请求模型"""

    username: str = Field(..., min_length=2, max_length=50, description="玩家用户名")


class PlayerUpdate(BaseModel):
    """更新玩家请求模型"""

    username: Optional[str] = Field(None, min_length=2, max_length=50, description="用户名")
    focus: Optional[int] = Field(None, ge=0, le=1000, description="专注力")
    efficiency: Optional[int] = Field(None, ge=0, le=1000, description="效率值")
    creativity: Optional[int] = Field(None, ge=0, le=1000, description="创造力")
    settings_json: Optional[str] = Field(None, description="设置 JSON")


class PlayerResponse(BaseModel):
    """玩家信息响应模型"""

    player_id: str
    username: str
    created_at: datetime
    updated_at: datetime
    level: int
    experience: int
    vibe_energy: int
    max_vibe_energy: int
    gold: int
    diamonds: int
    focus: int
    efficiency: int
    creativity: int
    consecutive_days: int
    last_login_date: Optional[datetime]

    model_config = {"from_attributes": True}


class PlayerStats(BaseModel):
    """玩家统计数据响应模型"""

    player_id: str
    username: str
    level: int
    experience: int
    exp_to_next_level: int
    total_coding_sessions: int
    total_coding_duration: int
    total_energy_earned: int
    total_exp_earned: int
    flow_sessions: int
    achievements_unlocked: int
    inventory_items_count: int


class AddEnergyRequest(BaseModel):
    """添加能量请求模型"""

    amount: int = Field(..., gt=0, le=10000, description="能量数量")
    source: str = Field(default="manual", description="能量来源")


class AddEnergyResponse(BaseModel):
    """添加能量响应模型"""

    player_id: str
    previous_energy: int
    added_energy: int
    current_energy: int
    max_energy: int
    is_capped: bool


class AddExpRequest(BaseModel):
    """添加经验请求模型"""

    amount: int = Field(..., gt=0, le=100000, description="经验数量")
    source: str = Field(default="manual", description="经验来源")


class AddExpResponse(BaseModel):
    """添加经验响应模型"""

    player_id: str
    previous_exp: int
    added_exp: int
    current_exp: int
    previous_level: int
    current_level: int
    leveled_up: bool
    levels_gained: int


# ============== 辅助函数 ==============


def get_db_session():
    """获取数据库会话依赖"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


def calculate_exp_for_level(level: int) -> int:
    """计算升到指定等级所需的总经验值

    使用公式: exp = 100 * level^1.5

    Args:
        level: 目标等级

    Returns:
        所需总经验值
    """
    return int(100 * (level ** 1.5))


def calculate_level_from_exp(total_exp: int) -> int:
    """根据总经验值计算等级

    Args:
        total_exp: 总经验值

    Returns:
        当前等级
    """
    level = 1
    while calculate_exp_for_level(level + 1) <= total_exp:
        level += 1
    return level


def get_current_player(session: Session) -> Player:
    """获取当前玩家（假设单玩家模式，返回第一个玩家）

    Args:
        session: 数据库会话

    Returns:
        玩家对象

    Raises:
        HTTPException: 玩家不存在时抛出 404
    """
    player = session.query(Player).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家不存在，请先创建玩家"
        )
    return player


# ============== API 端点 ==============


@router.get(
    "",
    response_model=PlayerResponse,
    summary="获取当前玩家信息",
    description="获取当前登录玩家的完整信息，包括等级、经验、资源等。",
    responses={
        200: {"description": "成功返回玩家信息"},
        404: {"description": "玩家不存在，请先创建玩家"},
    },
)
async def get_player(session: Session = Depends(get_db_session)) -> Player:
    """获取当前玩家信息

    Returns:
        玩家信息
    """
    return get_current_player(session)


@router.post(
    "",
    response_model=PlayerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新玩家",
    description="创建一个新的玩家账户。本地模式只支持单玩家。",
    responses={
        201: {"description": "玩家创建成功"},
        409: {"description": "玩家已存在或用户名重复"},
    },
)
async def create_player(
    data: PlayerCreate,
    session: Session = Depends(get_db_session)
) -> Player:
    """创建新玩家

    Args:
        data: 创建玩家请求数据

    Returns:
        创建的玩家信息
    """
    # 检查是否已存在玩家
    existing = session.query(Player).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="玩家已存在，本地模式只支持单玩家"
        )

    # 检查用户名是否重复
    username_exists = session.query(Player).filter(
        Player.username == data.username
    ).first()
    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"用户名 '{data.username}' 已被使用"
        )

    # 创建新玩家
    player = Player(
        username=data.username,
        last_login_date=datetime.utcnow()
    )
    session.add(player)
    session.commit()
    session.refresh(player)

    return player


@router.put(
    "",
    response_model=PlayerResponse,
    summary="更新玩家信息",
    description="更新当前玩家的基本信息，如用户名、属性值等。",
    responses={
        200: {"description": "更新成功"},
        404: {"description": "玩家不存在"},
        409: {"description": "用户名已被使用"},
    },
)
async def update_player(
    data: PlayerUpdate,
    session: Session = Depends(get_db_session)
) -> Player:
    """更新玩家信息

    Args:
        data: 更新玩家请求数据

    Returns:
        更新后的玩家信息
    """
    player = get_current_player(session)

    # 如果要更新用户名，检查是否重复
    if data.username and data.username != player.username:
        username_exists = session.query(Player).filter(
            Player.username == data.username,
            Player.player_id != player.player_id
        ).first()
        if username_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"用户名 '{data.username}' 已被使用"
            )
        player.username = data.username

    # 更新其他字段
    if data.focus is not None:
        player.focus = data.focus
    if data.efficiency is not None:
        player.efficiency = data.efficiency
    if data.creativity is not None:
        player.creativity = data.creativity
    if data.settings_json is not None:
        player.settings_json = data.settings_json

    session.commit()
    session.refresh(player)

    return player


@router.get(
    "/stats",
    response_model=PlayerStats,
    summary="获取玩家统计数据",
    description="获取玩家的详细统计数据，包括编码活动、成就、库存等。",
    responses={
        200: {"description": "成功返回统计数据"},
        404: {"description": "玩家不存在"},
    },
)
async def get_player_stats(session: Session = Depends(get_db_session)) -> PlayerStats:
    """获取玩家统计数据

    Returns:
        玩家统计数据
    """
    player = get_current_player(session)

    # 计算编码活动统计
    coding_activities = player.coding_activities
    total_sessions = len(coding_activities)
    total_duration = sum(a.duration_seconds for a in coding_activities)
    total_energy = sum(a.energy_earned for a in coding_activities)
    total_exp = sum(a.exp_earned for a in coding_activities)
    flow_sessions = sum(1 for a in coding_activities if a.is_flow_state)

    # 计算成就统计
    achievements_unlocked = sum(1 for a in player.achievements if a.is_unlocked)

    # 计算库存物品数量
    inventory_count = len(player.inventory_items)

    # 计算下一级所需经验
    current_level_exp = calculate_exp_for_level(player.level)
    next_level_exp = calculate_exp_for_level(player.level + 1)
    exp_to_next = next_level_exp - player.experience

    return PlayerStats(
        player_id=player.player_id,
        username=player.username,
        level=player.level,
        experience=player.experience,
        exp_to_next_level=max(0, exp_to_next),
        total_coding_sessions=total_sessions,
        total_coding_duration=total_duration,
        total_energy_earned=total_energy,
        total_exp_earned=total_exp,
        flow_sessions=flow_sessions,
        achievements_unlocked=achievements_unlocked,
        inventory_items_count=inventory_count
    )


@router.post(
    "/energy",
    response_model=AddEnergyResponse,
    summary="添加能量",
    description="为当前玩家添加 Vibe 能量，能量不会超过上限。",
    responses={
        200: {"description": "能量添加成功"},
        404: {"description": "玩家不存在"},
    },
)
async def add_energy(
    data: AddEnergyRequest,
    session: Session = Depends(get_db_session)
) -> AddEnergyResponse:
    """添加能量

    Args:
        data: 添加能量请求数据

    Returns:
        能量添加结果
    """
    player = get_current_player(session)

    previous_energy = player.vibe_energy
    new_energy = previous_energy + data.amount

    # 检查是否超过上限
    is_capped = new_energy > player.max_vibe_energy
    if is_capped:
        new_energy = player.max_vibe_energy

    player.vibe_energy = new_energy
    session.commit()

    return AddEnergyResponse(
        player_id=player.player_id,
        previous_energy=previous_energy,
        added_energy=data.amount,
        current_energy=new_energy,
        max_energy=player.max_vibe_energy,
        is_capped=is_capped
    )


@router.post(
    "/exp",
    response_model=AddExpResponse,
    summary="添加经验值",
    description="为当前玩家添加经验值，可能触发升级。",
    responses={
        200: {"description": "经验添加成功，返回升级信息"},
        404: {"description": "玩家不存在"},
    },
)
async def add_exp(
    data: AddExpRequest,
    session: Session = Depends(get_db_session)
) -> AddExpResponse:
    """添加经验值

    Args:
        data: 添加经验请求数据

    Returns:
        经验添加结果，包含升级信息
    """
    player = get_current_player(session)

    previous_exp = player.experience
    previous_level = player.level

    # 添加经验
    new_exp = previous_exp + data.amount
    player.experience = new_exp

    # 计算新等级
    new_level = calculate_level_from_exp(new_exp)
    player.level = new_level

    session.commit()

    leveled_up = new_level > previous_level
    levels_gained = new_level - previous_level

    return AddExpResponse(
        player_id=player.player_id,
        previous_exp=previous_exp,
        added_exp=data.amount,
        current_exp=new_exp,
        previous_level=previous_level,
        current_level=new_level,
        leveled_up=leveled_up,
        levels_gained=levels_gained
    )
