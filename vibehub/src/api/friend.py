"""好友系统 API 路由

提供好友相关的 REST API 端点，包括：
- 发送/接受/拒绝好友请求
- 好友列表管理
- 访问好友农场
- 好友度系统
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.storage.database import get_db
from src.storage.models import (
    FriendRequest,
    FriendRequestStatus,
    Player,
    Relationship,
    RelationshipType,
)


router = APIRouter(prefix="/api/friend", tags=["friend"])


# ============== Pydantic 模型定义 ==============


class FriendRequestCreate(BaseModel):
    """发送好友请求模型"""

    target_username: str = Field(..., min_length=2, max_length=50, description="目标玩家用户名")
    message: Optional[str] = Field(None, max_length=200, description="附言")


class FriendRequestResponse(BaseModel):
    """好友请求响应模型"""

    request_id: str
    sender_id: str
    sender_username: str
    receiver_id: str
    receiver_username: str
    status: str
    message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class FriendInfo(BaseModel):
    """好友信息模型"""

    player_id: str
    username: str
    level: int
    affinity_score: int  # 好友度
    created_at: datetime  # 成为好友的时间

    model_config = {"from_attributes": True}


class FriendListResponse(BaseModel):
    """好友列表响应模型"""

    total: int
    friends: list[FriendInfo]


class FriendFarmResponse(BaseModel):
    """好友农场响应模型"""

    player_id: str
    username: str
    farm_name: str
    plot_count: int
    decoration_score: int
    crops_count: int


class AffinityUpdateRequest(BaseModel):
    """更新好友度请求模型"""

    amount: int = Field(..., ge=-100, le=100, description="好友度变化量")
    reason: str = Field(default="interaction", description="变化原因")


class AffinityUpdateResponse(BaseModel):
    """更新好友度响应模型"""

    friend_id: str
    previous_affinity: int
    change: int
    current_affinity: int


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


def get_player_by_id(session: Session, player_id: str) -> Player:
    """根据 ID 获取玩家"""
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家 {player_id} 不存在"
        )
    return player


def get_player_by_username(session: Session, username: str) -> Player:
    """根据用户名获取玩家"""
    player = session.query(Player).filter(Player.username == username).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 '{username}' 不存在"
        )
    return player


def check_existing_friendship(session: Session, player_id: str, target_id: str) -> bool:
    """检查是否已经是好友"""
    relationship = session.query(Relationship).filter(
        Relationship.player_id == player_id,
        Relationship.target_id == target_id,
        Relationship.relationship_type == RelationshipType.FRIEND.value
    ).first()
    return relationship is not None


def check_pending_request(session: Session, sender_id: str, receiver_id: str) -> Optional[FriendRequest]:
    """检查是否存在待处理的好友请求"""
    return session.query(FriendRequest).filter(
        FriendRequest.sender_id == sender_id,
        FriendRequest.receiver_id == receiver_id,
        FriendRequest.status == FriendRequestStatus.PENDING.value
    ).first()


# ============== API 端点 ==============


@router.post("/request", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    data: FriendRequestCreate,
    session: Session = Depends(get_db_session)
) -> FriendRequestResponse:
    """发送好友请求

    Args:
        data: 好友请求数据

    Returns:
        创建的好友请求信息
    """
    current_player = get_current_player(session)
    target_player = get_player_by_username(session, data.target_username)

    # 不能添加自己为好友
    if current_player.player_id == target_player.player_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能添加自己为好友"
        )

    # 检查是否已经是好友
    if check_existing_friendship(session, current_player.player_id, target_player.player_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"你和 '{data.target_username}' 已经是好友了"
        )

    # 检查是否已有待处理的请求
    existing_request = check_pending_request(
        session, current_player.player_id, target_player.player_id
    )
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="已存在待处理的好友请求"
        )

    # 检查对方是否已向我发送请求（如果是，直接接受）
    reverse_request = check_pending_request(
        session, target_player.player_id, current_player.player_id
    )
    if reverse_request:
        # 自动接受对方的请求
        reverse_request.status = FriendRequestStatus.ACCEPTED.value

        # 创建双向好友关系
        relationship1 = Relationship(
            player_id=current_player.player_id,
            target_id=target_player.player_id,
            relationship_type=RelationshipType.FRIEND.value
        )
        relationship2 = Relationship(
            player_id=target_player.player_id,
            target_id=current_player.player_id,
            relationship_type=RelationshipType.FRIEND.value
        )
        session.add_all([relationship1, relationship2])
        session.commit()

        return FriendRequestResponse(
            request_id=reverse_request.request_id,
            sender_id=reverse_request.sender_id,
            sender_username=target_player.username,
            receiver_id=reverse_request.receiver_id,
            receiver_username=current_player.username,
            status=FriendRequestStatus.ACCEPTED.value,
            message=reverse_request.message,
            created_at=reverse_request.created_at
        )

    # 创建新的好友请求
    friend_request = FriendRequest(
        sender_id=current_player.player_id,
        receiver_id=target_player.player_id,
        message=data.message
    )
    session.add(friend_request)
    session.commit()
    session.refresh(friend_request)

    return FriendRequestResponse(
        request_id=friend_request.request_id,
        sender_id=friend_request.sender_id,
        sender_username=current_player.username,
        receiver_id=friend_request.receiver_id,
        receiver_username=target_player.username,
        status=friend_request.status,
        message=friend_request.message,
        created_at=friend_request.created_at
    )


@router.get("/requests", response_model=list[FriendRequestResponse])
async def get_friend_requests(
    session: Session = Depends(get_db_session)
) -> list[FriendRequestResponse]:
    """获取收到的好友请求列表

    Returns:
        待处理的好友请求列表
    """
    current_player = get_current_player(session)

    requests = session.query(FriendRequest).filter(
        FriendRequest.receiver_id == current_player.player_id,
        FriendRequest.status == FriendRequestStatus.PENDING.value
    ).order_by(FriendRequest.created_at.desc()).all()

    result = []
    for req in requests:
        sender = get_player_by_id(session, req.sender_id)
        result.append(FriendRequestResponse(
            request_id=req.request_id,
            sender_id=req.sender_id,
            sender_username=sender.username,
            receiver_id=req.receiver_id,
            receiver_username=current_player.username,
            status=req.status,
            message=req.message,
            created_at=req.created_at
        ))

    return result


@router.get("/requests/sent", response_model=list[FriendRequestResponse])
async def get_sent_requests(
    session: Session = Depends(get_db_session)
) -> list[FriendRequestResponse]:
    """获取已发送的好友请求列表

    Returns:
        已发送的好友请求列表
    """
    current_player = get_current_player(session)

    requests = session.query(FriendRequest).filter(
        FriendRequest.sender_id == current_player.player_id,
        FriendRequest.status == FriendRequestStatus.PENDING.value
    ).order_by(FriendRequest.created_at.desc()).all()

    result = []
    for req in requests:
        receiver = get_player_by_id(session, req.receiver_id)
        result.append(FriendRequestResponse(
            request_id=req.request_id,
            sender_id=req.sender_id,
            sender_username=current_player.username,
            receiver_id=req.receiver_id,
            receiver_username=receiver.username,
            status=req.status,
            message=req.message,
            created_at=req.created_at
        ))

    return result


@router.post("/accept/{request_id}", response_model=FriendRequestResponse)
async def accept_friend_request(
    request_id: str,
    session: Session = Depends(get_db_session)
) -> FriendRequestResponse:
    """接受好友请求

    Args:
        request_id: 好友请求 ID

    Returns:
        更新后的好友请求信息
    """
    current_player = get_current_player(session)

    # 查找好友请求
    friend_request = session.query(FriendRequest).filter(
        FriendRequest.request_id == request_id
    ).first()

    if not friend_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="好友请求不存在"
        )

    # 验证是否是接收者
    if friend_request.receiver_id != current_player.player_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此好友请求"
        )

    # 检查请求状态
    if friend_request.status != FriendRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"好友请求已被处理，当前状态: {friend_request.status}"
        )

    # 更新请求状态
    friend_request.status = FriendRequestStatus.ACCEPTED.value

    # 创建双向好友关系
    sender = get_player_by_id(session, friend_request.sender_id)

    relationship1 = Relationship(
        player_id=current_player.player_id,
        target_id=friend_request.sender_id,
        relationship_type=RelationshipType.FRIEND.value
    )
    relationship2 = Relationship(
        player_id=friend_request.sender_id,
        target_id=current_player.player_id,
        relationship_type=RelationshipType.FRIEND.value
    )
    session.add_all([relationship1, relationship2])
    session.commit()

    return FriendRequestResponse(
        request_id=friend_request.request_id,
        sender_id=friend_request.sender_id,
        sender_username=sender.username,
        receiver_id=friend_request.receiver_id,
        receiver_username=current_player.username,
        status=friend_request.status,
        message=friend_request.message,
        created_at=friend_request.created_at
    )


@router.post("/reject/{request_id}", response_model=FriendRequestResponse)
async def reject_friend_request(
    request_id: str,
    session: Session = Depends(get_db_session)
) -> FriendRequestResponse:
    """拒绝好友请求

    Args:
        request_id: 好友请求 ID

    Returns:
        更新后的好友请求信息
    """
    current_player = get_current_player(session)

    # 查找好友请求
    friend_request = session.query(FriendRequest).filter(
        FriendRequest.request_id == request_id
    ).first()

    if not friend_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="好友请求不存在"
        )

    # 验证是否是接收者
    if friend_request.receiver_id != current_player.player_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此好友请求"
        )

    # 检查请求状态
    if friend_request.status != FriendRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"好友请求已被处理，当前状态: {friend_request.status}"
        )

    # 更新请求状态
    friend_request.status = FriendRequestStatus.REJECTED.value
    session.commit()

    sender = get_player_by_id(session, friend_request.sender_id)

    return FriendRequestResponse(
        request_id=friend_request.request_id,
        sender_id=friend_request.sender_id,
        sender_username=sender.username,
        receiver_id=friend_request.receiver_id,
        receiver_username=current_player.username,
        status=friend_request.status,
        message=friend_request.message,
        created_at=friend_request.created_at
    )


@router.get("/list", response_model=FriendListResponse)
async def get_friend_list(
    session: Session = Depends(get_db_session)
) -> FriendListResponse:
    """获取好友列表

    Returns:
        好友列表
    """
    current_player = get_current_player(session)

    # 查询好友关系
    relationships = session.query(Relationship).filter(
        Relationship.player_id == current_player.player_id,
        Relationship.relationship_type == RelationshipType.FRIEND.value
    ).all()

    friends = []
    for rel in relationships:
        friend = session.query(Player).filter(
            Player.player_id == rel.target_id
        ).first()
        if friend:
            friends.append(FriendInfo(
                player_id=friend.player_id,
                username=friend.username,
                level=friend.level,
                affinity_score=rel.affinity_score,
                created_at=rel.created_at
            ))

    return FriendListResponse(
        total=len(friends),
        friends=friends
    )


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    friend_id: str,
    session: Session = Depends(get_db_session)
) -> None:
    """删除好友

    Args:
        friend_id: 好友玩家 ID
    """
    current_player = get_current_player(session)

    # 检查是否是好友
    if not check_existing_friendship(session, current_player.player_id, friend_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该玩家不是你的好友"
        )

    # 删除双向好友关系
    session.query(Relationship).filter(
        Relationship.player_id == current_player.player_id,
        Relationship.target_id == friend_id,
        Relationship.relationship_type == RelationshipType.FRIEND.value
    ).delete()

    session.query(Relationship).filter(
        Relationship.player_id == friend_id,
        Relationship.target_id == current_player.player_id,
        Relationship.relationship_type == RelationshipType.FRIEND.value
    ).delete()

    session.commit()


@router.get("/{friend_id}/farm", response_model=FriendFarmResponse)
async def visit_friend_farm(
    friend_id: str,
    session: Session = Depends(get_db_session)
) -> FriendFarmResponse:
    """访问好友农场

    Args:
        friend_id: 好友玩家 ID

    Returns:
        好友农场信息
    """
    current_player = get_current_player(session)

    # 检查是否是好友
    if not check_existing_friendship(session, current_player.player_id, friend_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能访问好友的农场"
        )

    friend = get_player_by_id(session, friend_id)

    if not friend.farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="好友还没有创建农场"
        )

    crops_count = len(friend.farm.crops) if friend.farm.crops else 0

    return FriendFarmResponse(
        player_id=friend.player_id,
        username=friend.username,
        farm_name=friend.farm.name,
        plot_count=friend.farm.plot_count,
        decoration_score=friend.farm.decoration_score,
        crops_count=crops_count
    )


@router.put("/{friend_id}/affinity", response_model=AffinityUpdateResponse)
async def update_affinity(
    friend_id: str,
    data: AffinityUpdateRequest,
    session: Session = Depends(get_db_session)
) -> AffinityUpdateResponse:
    """更新好友度

    Args:
        friend_id: 好友玩家 ID
        data: 好友度更新数据

    Returns:
        更新后的好友度信息
    """
    current_player = get_current_player(session)

    # 查找好友关系
    relationship = session.query(Relationship).filter(
        Relationship.player_id == current_player.player_id,
        Relationship.target_id == friend_id,
        Relationship.relationship_type == RelationshipType.FRIEND.value
    ).first()

    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该玩家不是你的好友"
        )

    previous_affinity = relationship.affinity_score
    new_affinity = max(0, previous_affinity + data.amount)  # 好友度不能为负
    relationship.affinity_score = new_affinity
    session.commit()

    return AffinityUpdateResponse(
        friend_id=friend_id,
        previous_affinity=previous_affinity,
        change=data.amount,
        current_affinity=new_affinity
    )
