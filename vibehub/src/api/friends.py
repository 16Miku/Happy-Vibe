"""好友系统 API

提供好友相关的 REST API 端点。
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.multiplayer.connection_manager import connection_manager
from src.multiplayer.models import (
    AFFINITY_ACTIONS,
    AFFINITY_LEVELS,
    FriendRequestStatus,
)

router = APIRouter(prefix="/api/friends", tags=["friends"])


# ==================== 请求/响应模型 ====================


class FriendRequestCreate(BaseModel):
    """发送好友请求"""

    from_player_id: str = Field(..., description="发送者 ID")
    to_player_id: str = Field(..., description="接收者 ID")
    message: Optional[str] = Field(None, max_length=200, description="附加消息")


class FriendRequestResponse(BaseModel):
    """好友请求响应"""

    request_id: str
    accept: bool = Field(..., description="是否接受")


class SendGiftRequest(BaseModel):
    """发送礼物请求"""

    from_player_id: str
    to_player_id: str
    item_id: str
    item_name: str
    quantity: int = 1


class HelpActionRequest(BaseModel):
    """帮忙操作请求"""

    from_player_id: str
    to_player_id: str
    action_type: str = Field(..., description="操作类型: water, harvest, fertilize")


class FriendInfo(BaseModel):
    """好友信息"""

    player_id: str
    username: str
    level: int
    affinity_score: int
    affinity_title: str
    is_online: bool
    status: str
    last_online: Optional[str] = None


# ==================== 内存存储 (临时，后续迁移到数据库) ====================

# 好友关系: player_id -> {friend_id: affinity_score}
_friendships: dict[str, dict[str, int]] = {}

# 好友请求: request_id -> request_data
_friend_requests: dict[str, dict] = {}

# 玩家信息缓存: player_id -> player_info
_player_cache: dict[str, dict] = {}


def _get_affinity_title(score: int) -> str:
    """根据好友度获取称号"""
    for level_name, config in AFFINITY_LEVELS.items():
        if config["min"] <= score <= config["max"]:
            return config["title"]
    return "初识者"


# ==================== API 端点 ====================


@router.get("/list/{player_id}")
async def get_friends_list(
    player_id: str,
    include_offline: bool = Query(True, description="是否包含离线好友"),
) -> dict:
    """获取好友列表

    Args:
        player_id: 玩家 ID
        include_offline: 是否包含离线好友

    Returns:
        好友列表
    """
    friends = _friendships.get(player_id, {})
    friend_list = []

    for friend_id, affinity_score in friends.items():
        is_online = connection_manager.is_online(friend_id)

        if not include_offline and not is_online:
            continue

        # 获取好友信息
        friend_info = _player_cache.get(friend_id, {})
        status = connection_manager.get_status(friend_id).value

        friend_list.append(
            FriendInfo(
                player_id=friend_id,
                username=friend_info.get("username", f"Player_{friend_id[:8]}"),
                level=friend_info.get("level", 1),
                affinity_score=affinity_score,
                affinity_title=_get_affinity_title(affinity_score),
                is_online=is_online,
                status=status,
                last_online=friend_info.get("last_online"),
            ).model_dump()
        )

    # 按在线状态和好友度排序
    friend_list.sort(key=lambda x: (-x["is_online"], -x["affinity_score"]))

    return {
        "player_id": player_id,
        "total_friends": len(friends),
        "online_count": sum(1 for f in friend_list if f["is_online"]),
        "friends": friend_list,
    }


@router.post("/request")
async def send_friend_request(request: FriendRequestCreate) -> dict:
    """发送好友请求

    Args:
        request: 好友请求数据

    Returns:
        请求结果
    """
    from_id = request.from_player_id
    to_id = request.to_player_id

    # 检查是否已经是好友
    if to_id in _friendships.get(from_id, {}):
        raise HTTPException(status_code=400, detail="Already friends")

    # 检查是否已有待处理的请求
    for req_id, req_data in _friend_requests.items():
        if (
            req_data["from_player_id"] == from_id
            and req_data["to_player_id"] == to_id
            and req_data["status"] == FriendRequestStatus.PENDING.value
        ):
            raise HTTPException(status_code=400, detail="Request already pending")

    # 创建请求
    import uuid

    request_id = str(uuid.uuid4())
    _friend_requests[request_id] = {
        "request_id": request_id,
        "from_player_id": from_id,
        "to_player_id": to_id,
        "message": request.message,
        "status": FriendRequestStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat(),
    }

    # 如果目标在线，发送实时通知
    if connection_manager.is_online(to_id):
        from_info = _player_cache.get(from_id, {})
        await connection_manager.send_personal(
            to_id,
            {
                "type": "friend_request",
                "request_id": request_id,
                "from_player_id": from_id,
                "from_username": from_info.get("username", f"Player_{from_id[:8]}"),
                "message": request.message,
            },
        )

    return {
        "success": True,
        "request_id": request_id,
        "message": "Friend request sent",
    }


@router.get("/requests/{player_id}")
async def get_friend_requests(
    player_id: str,
    status: Optional[str] = Query(None, description="筛选状态"),
) -> dict:
    """获取好友请求列表

    Args:
        player_id: 玩家 ID
        status: 筛选状态 (pending, accepted, rejected)

    Returns:
        请求列表
    """
    received = []
    sent = []

    for req_id, req_data in _friend_requests.items():
        if status and req_data["status"] != status:
            continue

        if req_data["to_player_id"] == player_id:
            from_info = _player_cache.get(req_data["from_player_id"], {})
            received.append(
                {
                    **req_data,
                    "from_username": from_info.get(
                        "username", f"Player_{req_data['from_player_id'][:8]}"
                    ),
                }
            )
        elif req_data["from_player_id"] == player_id:
            to_info = _player_cache.get(req_data["to_player_id"], {})
            sent.append(
                {
                    **req_data,
                    "to_username": to_info.get(
                        "username", f"Player_{req_data['to_player_id'][:8]}"
                    ),
                }
            )

    return {
        "player_id": player_id,
        "received": received,
        "sent": sent,
    }


@router.post("/request/respond")
async def respond_to_friend_request(response: FriendRequestResponse) -> dict:
    """响应好友请求

    Args:
        response: 响应数据

    Returns:
        处理结果
    """
    request_id = response.request_id

    if request_id not in _friend_requests:
        raise HTTPException(status_code=404, detail="Request not found")

    req_data = _friend_requests[request_id]

    if req_data["status"] != FriendRequestStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Request already processed")

    from_id = req_data["from_player_id"]
    to_id = req_data["to_player_id"]

    if response.accept:
        # 接受请求，建立好友关系
        req_data["status"] = FriendRequestStatus.ACCEPTED.value

        # 双向添加好友
        if from_id not in _friendships:
            _friendships[from_id] = {}
        if to_id not in _friendships:
            _friendships[to_id] = {}

        _friendships[from_id][to_id] = 0
        _friendships[to_id][from_id] = 0

        # 通知发送者
        if connection_manager.is_online(from_id):
            to_info = _player_cache.get(to_id, {})
            await connection_manager.send_personal(
                from_id,
                {
                    "type": "friend_request_accepted",
                    "request_id": request_id,
                    "friend_id": to_id,
                    "friend_username": to_info.get("username", f"Player_{to_id[:8]}"),
                },
            )

        return {
            "success": True,
            "message": "Friend request accepted",
            "friend_id": from_id,
        }
    else:
        # 拒绝请求
        req_data["status"] = FriendRequestStatus.REJECTED.value

        return {
            "success": True,
            "message": "Friend request rejected",
        }


@router.delete("/{player_id}/{friend_id}")
async def remove_friend(player_id: str, friend_id: str) -> dict:
    """删除好友

    Args:
        player_id: 玩家 ID
        friend_id: 好友 ID

    Returns:
        删除结果
    """
    if player_id not in _friendships or friend_id not in _friendships[player_id]:
        raise HTTPException(status_code=404, detail="Friend not found")

    # 双向删除
    del _friendships[player_id][friend_id]
    if friend_id in _friendships and player_id in _friendships[friend_id]:
        del _friendships[friend_id][player_id]

    return {
        "success": True,
        "message": "Friend removed",
    }


@router.post("/gift")
async def send_gift(request: SendGiftRequest) -> dict:
    """发送礼物给好友

    Args:
        request: 礼物请求数据

    Returns:
        发送结果
    """
    from_id = request.from_player_id
    to_id = request.to_player_id

    # 检查是否是好友
    if to_id not in _friendships.get(from_id, {}):
        raise HTTPException(status_code=400, detail="Not friends")

    # 增加好友度
    affinity_gain = AFFINITY_ACTIONS["send_gift"]
    _friendships[from_id][to_id] += affinity_gain
    _friendships[to_id][from_id] += affinity_gain

    # 发送实时通知
    if connection_manager.is_online(to_id):
        from_info = _player_cache.get(from_id, {})
        await connection_manager.send_personal(
            to_id,
            {
                "type": "gift_received",
                "from_player_id": from_id,
                "from_username": from_info.get("username", f"Player_{from_id[:8]}"),
                "item_id": request.item_id,
                "item_name": request.item_name,
                "quantity": request.quantity,
            },
        )

    return {
        "success": True,
        "message": f"Gift sent to friend",
        "affinity_gained": affinity_gain,
        "new_affinity": _friendships[from_id][to_id],
    }


@router.post("/help")
async def help_friend(request: HelpActionRequest) -> dict:
    """帮助好友 (浇水/收获/施肥)

    Args:
        request: 帮忙请求数据

    Returns:
        帮忙结果
    """
    from_id = request.from_player_id
    to_id = request.to_player_id
    action_type = request.action_type

    # 检查是否是好友
    if to_id not in _friendships.get(from_id, {}):
        raise HTTPException(status_code=400, detail="Not friends")

    # 检查好友度是否足够
    current_affinity = _friendships[from_id][to_id]
    if current_affinity < 51:  # 需要"好友"级别
        raise HTTPException(
            status_code=400, detail="Affinity too low (need 51+ to help)"
        )

    # 增加好友度
    affinity_gain = AFFINITY_ACTIONS.get(f"help_{action_type}", 2)
    _friendships[from_id][to_id] += affinity_gain
    _friendships[to_id][from_id] += affinity_gain

    # 发送实时通知
    if connection_manager.is_online(to_id):
        from_info = _player_cache.get(from_id, {})
        await connection_manager.send_personal(
            to_id,
            {
                "type": "help_received",
                "from_player_id": from_id,
                "from_username": from_info.get("username", f"Player_{from_id[:8]}"),
                "action_type": action_type,
            },
        )

    return {
        "success": True,
        "message": f"Helped friend with {action_type}",
        "affinity_gained": affinity_gain,
        "new_affinity": _friendships[from_id][to_id],
    }


@router.get("/online/{player_id}")
async def get_online_friends(player_id: str) -> dict:
    """获取在线好友列表

    Args:
        player_id: 玩家 ID

    Returns:
        在线好友列表
    """
    friends = _friendships.get(player_id, {})
    friend_ids = list(friends.keys())

    online_friends = connection_manager.get_online_friends(friend_ids)

    # 添加好友度信息
    for friend in online_friends:
        friend_id = friend["player_id"]
        friend["affinity_score"] = friends.get(friend_id, 0)
        friend["affinity_title"] = _get_affinity_title(friend["affinity_score"])

    return {
        "player_id": player_id,
        "online_friends": online_friends,
        "count": len(online_friends),
    }


@router.post("/visit/{player_id}/{friend_id}")
async def visit_friend_farm(player_id: str, friend_id: str) -> dict:
    """访问好友农场

    Args:
        player_id: 访问者 ID
        friend_id: 被访问者 ID

    Returns:
        访问结果
    """
    # 检查是否是好友
    if friend_id not in _friendships.get(player_id, {}):
        raise HTTPException(status_code=400, detail="Not friends")

    # 增加好友度
    affinity_gain = AFFINITY_ACTIONS["visit_farm"]
    _friendships[player_id][friend_id] += affinity_gain
    _friendships[friend_id][player_id] += affinity_gain

    # 通知被访问者
    if connection_manager.is_online(friend_id):
        visitor_info = _player_cache.get(player_id, {})
        await connection_manager.send_personal(
            friend_id,
            {
                "type": "farm_visited",
                "visitor_id": player_id,
                "visitor_username": visitor_info.get(
                    "username", f"Player_{player_id[:8]}"
                ),
            },
        )

    return {
        "success": True,
        "message": "Visiting friend's farm",
        "affinity_gained": affinity_gain,
        "new_affinity": _friendships[player_id][friend_id],
    }


# ==================== 内部函数 (供其他模块调用) ====================


def update_player_cache(player_id: str, info: dict) -> None:
    """更新玩家信息缓存"""
    _player_cache[player_id] = {**_player_cache.get(player_id, {}), **info}


def get_friend_ids(player_id: str) -> list[str]:
    """获取好友 ID 列表"""
    return list(_friendships.get(player_id, {}).keys())


def are_friends(player_id: str, other_id: str) -> bool:
    """检查两个玩家是否是好友"""
    return other_id in _friendships.get(player_id, {})
