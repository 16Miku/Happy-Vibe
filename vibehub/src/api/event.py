"""活动系统 API 路由

提供活动列表、活动详情等功能的 REST API 端点。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.event import EventManager
from src.storage.database import get_db


# ============ Pydantic 模型 ============


class EventEffectsResponse(BaseModel):
    """活动效果响应模型"""

    exp_multiplier: float | None = None
    gold_multiplier: float | None = None
    energy_multiplier: float | None = None
    gold_bonus: int | None = None


class EventSummaryResponse(BaseModel):
    """活动摘要响应模型"""

    event_id: str
    event_type: str
    title: str
    description: str
    start_time: str
    end_time: str


class EventDetailResponse(BaseModel):
    """活动详情响应模型"""

    event_id: str
    event_type: str
    title: str
    description: str
    start_time: str
    end_time: str
    effects: dict
    is_active: bool
    is_ongoing: bool


class EventListResponse(BaseModel):
    """活动列表响应模型"""

    events: list[EventSummaryResponse]
    total: int


# ============ 依赖注入 ============


def get_db_session():
    """获取数据库会话"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


def get_event_manager(session: Session = Depends(get_db_session)) -> EventManager:
    """获取活动管理器"""
    return EventManager(session)


# ============ 路由定义 ============

router = APIRouter(prefix="/api/event", tags=["event"])


@router.get("/active", response_model=EventListResponse)
async def get_active_events(
    manager: EventManager = Depends(get_event_manager),
) -> EventListResponse:
    """获取当前活跃的活动列表

    Returns:
        活跃的活动列表
    """
    events_data = manager.get_active_events_summary()

    event_responses = [
        EventSummaryResponse(
            event_id=e["event_id"],
            event_type=e["event_type"],
            title=e["title"],
            description=e["description"],
            start_time=e["start_time"],
            end_time=e["end_time"],
        )
        for e in events_data
    ]

    return EventListResponse(
        events=event_responses,
        total=len(event_responses),
    )


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event_detail(
    event_id: str,
    manager: EventManager = Depends(get_event_manager),
) -> EventDetailResponse:
    """获取活动详情

    Args:
        event_id: 活动 ID

    Returns:
        活动详情
    """
    event_data = manager.get_event_detail(event_id)

    if not event_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"活动不存在: {event_id}",
        )

    return EventDetailResponse(
        event_id=event_data["event_id"],
        event_type=event_data["event_type"],
        title=event_data["title"],
        description=event_data["description"],
        start_time=event_data["start_time"],
        end_time=event_data["end_time"],
        effects=event_data["effects"],
        is_active=event_data["is_active"],
        is_ongoing=event_data["is_ongoing"],
    )
