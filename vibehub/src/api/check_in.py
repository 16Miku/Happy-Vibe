"""签到 API 路由

提供每日签到相关的 REST API 端点，包括：
- 执行签到
- 获取签到状态
- 查询签到历史
"""

from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.check_in import CheckInManager, CheckInStatus
from src.storage.database import get_db
from src.storage.models import Player, CheckInRecord


router = APIRouter(prefix="/api/check-in", tags=["check-in"])


# ============== Pydantic 模型定义 ==============


class CheckInRewardResponse(BaseModel):
    """签到奖励响应模型"""
    base_energy: int = Field(..., description="基础能量奖励")
    streak_bonus: int = Field(..., description="连续签到加成")
    total_energy: int = Field(..., description="总能量奖励")
    gold: int = Field(..., description="金币奖励")
    experience: int = Field(..., description="经验奖励")
    special_item: Optional[str] = Field(None, description="特殊物品奖励")


class CheckInResponse(BaseModel):
    """签到响应模型"""
    status: str = Field(..., description="签到状态")
    check_in_date: date = Field(..., description="签到日期")
    consecutive_days: int = Field(..., description="当前连续签到天数")
    previous_consecutive_days: int = Field(..., description="签到前连续天数")
    reward: CheckInRewardResponse = Field(..., description="签到奖励")
    message: str = Field(..., description="签到消息")
    is_success: bool = Field(..., description="是否签到成功")


class MilestoneInfo(BaseModel):
    """里程碑信息"""
    days: int = Field(..., description="里程碑天数")
    days_remaining: int = Field(..., description="距离里程碑剩余天数")
    reward_item: str = Field(..., description="奖励物品")
    reward_name: str = Field(..., description="奖励名称")
    gold_bonus: int = Field(..., description="金币加成")


class CheckInStatusResponse(BaseModel):
    """签到状态响应模型"""
    is_checked_today: bool = Field(..., description="今日是否已签到")
    current_consecutive_days: int = Field(..., description="当前连续签到天数")
    expected_streak_after_check_in: int = Field(..., description="签到后预计连续天数")
    will_break_streak: bool = Field(..., description="签到是否会中断连续")
    expected_reward: Optional[CheckInRewardResponse] = Field(None, description="预计奖励")
    next_milestone: Optional[MilestoneInfo] = Field(None, description="下一个里程碑")
    last_check_in_date: Optional[date] = Field(None, description="上次签到日期")


class CheckInHistoryItem(BaseModel):
    """签到历史记录项"""
    record_id: str
    check_in_date: date
    consecutive_days: int
    energy_reward: int
    gold_reward: int
    exp_reward: int
    special_item: Optional[str]

    model_config = {"from_attributes": True}


class CheckInHistoryResponse(BaseModel):
    """签到历史响应模型"""
    total_count: int = Field(..., description="总签到次数")
    records: list[CheckInHistoryItem] = Field(..., description="签到记录列表")


# ============== 辅助函数 ==============


def get_db_session():
    """获取数据库会话依赖"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


def get_current_player(session: Session) -> Player:
    """获取当前玩家"""
    player = session.query(Player).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家不存在，请先创建玩家"
        )
    return player


# ============== API 端点 ==============


@router.post("", response_model=CheckInResponse)
async def do_check_in(session: Session = Depends(get_db_session)) -> CheckInResponse:
    """执行每日签到

    Returns:
        签到结果，包含奖励信息
    """
    player = get_current_player(session)
    manager = CheckInManager()

    # 获取上次签到日期
    last_check_in_date = None
    if player.last_login_date:
        last_check_in_date = player.last_login_date.date()

    # 执行签到
    result = manager.check_in(
        last_check_in_date=last_check_in_date,
        current_consecutive_days=player.consecutive_days
    )

    # 如果签到成功，更新玩家数据并记录
    if result.is_success:
        # 更新玩家数据
        player.consecutive_days = result.consecutive_days
        player.last_login_date = datetime.combine(result.check_in_date, datetime.min.time())

        # 发放奖励
        player.vibe_energy = min(
            player.vibe_energy + result.reward.total_energy,
            player.max_vibe_energy
        )
        player.gold += result.reward.gold
        player.experience += result.reward.experience

        # 创建签到记录
        record = CheckInRecord(
            player_id=player.player_id,
            check_in_date=datetime.combine(result.check_in_date, datetime.min.time()),
            consecutive_days=result.consecutive_days,
            energy_reward=result.reward.total_energy,
            gold_reward=result.reward.gold,
            exp_reward=result.reward.experience,
            special_item=result.reward.special_item
        )
        session.add(record)
        session.commit()

    return CheckInResponse(
        status=result.status.value,
        check_in_date=result.check_in_date,
        consecutive_days=result.consecutive_days,
        previous_consecutive_days=result.previous_consecutive_days,
        reward=CheckInRewardResponse(
            base_energy=result.reward.base_energy,
            streak_bonus=result.reward.streak_bonus,
            total_energy=result.reward.total_energy,
            gold=result.reward.gold,
            experience=result.reward.experience,
            special_item=result.reward.special_item
        ),
        message=result.message,
        is_success=result.is_success
    )


@router.get("/status", response_model=CheckInStatusResponse)
async def get_check_in_status(
    session: Session = Depends(get_db_session)
) -> CheckInStatusResponse:
    """获取签到状态

    Returns:
        当前签到状态，包含是否已签到、连续天数、预计奖励等
    """
    player = get_current_player(session)
    manager = CheckInManager()

    # 获取上次签到日期
    last_check_in_date = None
    if player.last_login_date:
        last_check_in_date = player.last_login_date.date()

    # 获取签到状态
    status_info = manager.get_check_in_status(
        last_check_in_date=last_check_in_date,
        current_consecutive_days=player.consecutive_days
    )

    # 构建预计奖励响应
    expected_reward = None
    if status_info["expected_reward"]:
        reward = status_info["expected_reward"]
        expected_reward = CheckInRewardResponse(
            base_energy=reward.base_energy,
            streak_bonus=reward.streak_bonus,
            total_energy=reward.total_energy,
            gold=reward.gold,
            experience=reward.experience,
            special_item=reward.special_item
        )

    # 构建里程碑信息
    next_milestone = None
    if status_info["next_milestone"]:
        ms = status_info["next_milestone"]
        next_milestone = MilestoneInfo(
            days=ms["days"],
            days_remaining=ms["days_remaining"],
            reward_item=ms["reward"]["item"],
            reward_name=ms["reward"]["name"],
            gold_bonus=ms["reward"].get("gold_bonus", 0)
        )

    return CheckInStatusResponse(
        is_checked_today=status_info["is_checked_today"],
        current_consecutive_days=status_info["current_consecutive_days"],
        expected_streak_after_check_in=status_info["expected_streak_after_check_in"],
        will_break_streak=status_info["will_break_streak"],
        expected_reward=expected_reward,
        next_milestone=next_milestone,
        last_check_in_date=status_info["last_check_in_date"]
    )


@router.get("/history", response_model=CheckInHistoryResponse)
async def get_check_in_history(
    limit: int = 30,
    offset: int = 0,
    session: Session = Depends(get_db_session)
) -> CheckInHistoryResponse:
    """获取签到历史记录

    Args:
        limit: 返回记录数量限制，默认30
        offset: 偏移量，用于分页

    Returns:
        签到历史记录列表
    """
    player = get_current_player(session)

    # 查询总数
    total_count = session.query(CheckInRecord).filter(
        CheckInRecord.player_id == player.player_id
    ).count()

    # 查询记录
    records = session.query(CheckInRecord).filter(
        CheckInRecord.player_id == player.player_id
    ).order_by(
        CheckInRecord.check_in_date.desc()
    ).offset(offset).limit(limit).all()

    # 转换为响应模型
    history_items = [
        CheckInHistoryItem(
            record_id=r.record_id,
            check_in_date=r.check_in_date.date(),
            consecutive_days=r.consecutive_days,
            energy_reward=r.energy_reward,
            gold_reward=r.gold_reward,
            exp_reward=r.exp_reward,
            special_item=r.special_item
        )
        for r in records
    ]

    return CheckInHistoryResponse(
        total_count=total_count,
        records=history_items
    )
