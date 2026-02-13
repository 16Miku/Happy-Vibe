"""任务系统 API 路由

提供每日任务、任务进度查询、完成任务并领取奖励等功能的 REST API 端点。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.quest import QuestManager, QuestReward
from src.storage.database import get_db
from src.storage.models import Player


# ============ Pydantic 模型 ============


class QuestRewardResponse(BaseModel):
    """任务奖励响应模型"""

    energy: int = 0
    gold: int = 0
    exp: int = 0
    diamonds: int = 0
    item: str | None = None


class QuestProgressResponse(BaseModel):
    """任务进度响应模型"""

    quest_id: str
    title: str
    description: str
    quest_type: str
    target_value: int
    current_value: int
    is_completed: bool
    is_claimed: bool
    reward: QuestRewardResponse


class QuestListResponse(BaseModel):
    """任务列表响应模型"""

    quests: list[QuestProgressResponse]
    total: int


class ClaimRewardResponse(BaseModel):
    """领取奖励响应模型"""

    quest_id: str
    reward: QuestRewardResponse
    claimed_at: str


# ============ 依赖注入 ============


def get_db_session():
    """获取数据库会话"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


def get_quest_manager(session: Session = Depends(get_db_session)) -> QuestManager:
    """获取任务管理器"""
    return QuestManager(session)


# ============ 路由定义 ============

router = APIRouter(prefix="/api/quest", tags=["quest"])


@router.get("/daily", response_model=QuestListResponse)
async def get_daily_quests(
    player_id: str,
    manager: QuestManager = Depends(get_quest_manager),
    session: Session = Depends(get_db_session),
) -> QuestListResponse:
    """获取日常任务列表

    Args:
        player_id: 玩家 ID

    Returns:
        日常任务列表
    """
    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    # 获取每日任务
    quests = manager.get_daily_quests(player_id)

    quest_responses = []
    for quest in quests:
        progress = manager.get_or_create_progress(player_id, quest.quest_id)
        reward = QuestReward.from_json(quest.reward_json or "{}")

        quest_responses.append(
            QuestProgressResponse(
                quest_id=quest.quest_id,
                title=quest.title,
                description=quest.description,
                quest_type=quest.quest_type,
                target_value=quest.target_value,
                current_value=progress.current_value,
                is_completed=progress.is_completed,
                is_claimed=progress.is_claimed,
                reward=QuestRewardResponse(
                    energy=reward.energy,
                    gold=reward.gold,
                    exp=reward.exp,
                    diamonds=reward.diamonds,
                    item=reward.item,
                ),
            )
        )

    return QuestListResponse(
        quests=quest_responses,
        total=len(quest_responses),
    )


@router.get("/{quest_id}/progress", response_model=QuestProgressResponse)
async def get_quest_progress(
    quest_id: str,
    player_id: str,
    manager: QuestManager = Depends(get_quest_manager),
    session: Session = Depends(get_db_session),
) -> QuestProgressResponse:
    """查询任务进度

    Args:
        quest_id: 任务 ID
        player_id: 玩家 ID

    Returns:
        任务进度详情
    """
    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    try:
        progress_data = manager.get_quest_progress(player_id, quest_id)
        return QuestProgressResponse(
            quest_id=progress_data["quest_id"],
            title=progress_data["title"],
            description=progress_data["description"],
            quest_type=progress_data["quest_type"],
            target_value=progress_data["target_value"],
            current_value=progress_data["current_value"],
            is_completed=progress_data["is_completed"],
            is_claimed=progress_data["is_claimed"],
            reward=QuestRewardResponse(**progress_data["reward"]),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{quest_id}/complete", response_model=ClaimRewardResponse)
async def complete_quest(
    quest_id: str,
    player_id: str,
    manager: QuestManager = Depends(get_quest_manager),
    session: Session = Depends(get_db_session),
) -> ClaimRewardResponse:
    """完成任务并领取奖励

    Args:
        quest_id: 任务 ID
        player_id: 玩家 ID

    Returns:
        领取的奖励信息
    """
    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    try:
        # 先完成任务
        manager.complete_quest(player_id, quest_id)
        # 然后领取奖励
        result = manager.claim_reward(player_id, quest_id)

        return ClaimRewardResponse(
            quest_id=result["quest_id"],
            reward=QuestRewardResponse(**result["reward"]),
            claimed_at=result["claimed_at"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/available", response_model=QuestListResponse)
async def get_available_quests(
    player_id: str,
    manager: QuestManager = Depends(get_quest_manager),
    session: Session = Depends(get_db_session),
) -> QuestListResponse:
    """获取所有可接受的任务

    Args:
        player_id: 玩家 ID

    Returns:
        可接受的任务列表
    """
    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    quests_data = manager.get_available_quests(player_id)

    quest_responses = [
        QuestProgressResponse(
            quest_id=q["quest_id"],
            title=q["title"],
            description=q["description"],
            quest_type=q["quest_type"],
            target_value=q["target_value"],
            current_value=q["current_value"],
            is_completed=q["is_completed"],
            is_claimed=q["is_claimed"],
            reward=QuestRewardResponse(**q["reward"]),
        )
        for q in quests_data
    ]

    return QuestListResponse(
        quests=quest_responses,
        total=len(quest_responses),
    )
