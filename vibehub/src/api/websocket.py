"""WebSocket 路由

处理实时通信的 WebSocket 端点。
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from src.multiplayer.connection_manager import connection_manager
from src.multiplayer.models import MessageType, OnlineStatus

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    player_id: str = Query(..., description="玩家 ID"),
    username: Optional[str] = Query(None, description="玩家用户名"),
    level: Optional[int] = Query(1, description="玩家等级"),
):
    """WebSocket 连接端点

    客户端通过此端点建立实时通信连接。

    消息格式:
    ```json
    {
        "action": "chat|status|ping|join_room|leave_room|...",
        "data": {...}
    }
    ```
    """
    player_info = {
        "username": username or f"Player_{player_id[:8]}",
        "level": level,
    }

    # 建立连接
    await connection_manager.connect(websocket, player_id, player_info)

    # 发送连接成功消息
    await websocket.send_json(
        {
            "type": "connected",
            "player_id": player_id,
            "online_count": connection_manager.online_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            action = data.get("action", "")
            payload = data.get("data", {})

            # 处理不同类型的消息
            response = await _handle_message(player_id, action, payload)

            if response:
                await websocket.send_json(response)

    except WebSocketDisconnect:
        await connection_manager.disconnect(player_id)
    except Exception as e:
        print(f"[WebSocket] Error for player {player_id}: {e}")
        await connection_manager.disconnect(player_id)


async def _handle_message(
    player_id: str, action: str, payload: dict
) -> Optional[dict]:
    """处理 WebSocket 消息

    Args:
        player_id: 发送者 ID
        action: 动作类型
        payload: 消息数据

    Returns:
        响应消息 (可选)
    """
    timestamp = datetime.utcnow().isoformat()

    # ==================== 心跳 ====================
    if action == "ping":
        return {"type": "pong", "timestamp": timestamp}

    # ==================== 状态更新 ====================
    elif action == "status":
        status_str = payload.get("status", "online")
        try:
            status = OnlineStatus(status_str)
            await connection_manager.update_status(player_id, status)
            return {"type": "status_updated", "status": status.value, "timestamp": timestamp}
        except ValueError:
            return {"type": "error", "message": f"Invalid status: {status_str}"}

    # ==================== 私聊消息 ====================
    elif action == "chat":
        target_id = payload.get("target_id")
        content = payload.get("content", "")
        message_type = payload.get("message_type", MessageType.CHAT.value)

        if not target_id or not content:
            return {"type": "error", "message": "Missing target_id or content"}

        message = {
            "type": "chat_message",
            "from_player_id": player_id,
            "message_type": message_type,
            "content": content,
            "timestamp": timestamp,
        }

        success = await connection_manager.send_personal(target_id, message)

        return {
            "type": "chat_sent",
            "success": success,
            "target_id": target_id,
            "timestamp": timestamp,
        }

    # ==================== 广播消息 (公会/房间) ====================
    elif action == "broadcast":
        room_id = payload.get("room_id")
        content = payload.get("content", "")

        if not room_id or not content:
            return {"type": "error", "message": "Missing room_id or content"}

        message = {
            "type": "broadcast_message",
            "from_player_id": player_id,
            "content": content,
        }

        count = await connection_manager.broadcast_to_room(
            room_id, message, exclude=[player_id]
        )

        return {
            "type": "broadcast_sent",
            "room_id": room_id,
            "recipients": count,
            "timestamp": timestamp,
        }

    # ==================== 加入房间 ====================
    elif action == "join_room":
        room_id = payload.get("room_id")
        if not room_id:
            return {"type": "error", "message": "Missing room_id"}

        success = await connection_manager.join_room(player_id, room_id)
        members = connection_manager.get_room_members(room_id)

        return {
            "type": "room_joined",
            "room_id": room_id,
            "success": success,
            "members": members,
            "timestamp": timestamp,
        }

    # ==================== 离开房间 ====================
    elif action == "leave_room":
        room_id = payload.get("room_id")
        if not room_id:
            return {"type": "error", "message": "Missing room_id"}

        success = await connection_manager.leave_room(player_id, room_id)

        return {
            "type": "room_left",
            "room_id": room_id,
            "success": success,
            "timestamp": timestamp,
        }

    # ==================== 获取在线好友 ====================
    elif action == "get_online_friends":
        friend_ids = payload.get("friend_ids", [])
        online_friends = connection_manager.get_online_friends(friend_ids)

        return {
            "type": "online_friends",
            "friends": online_friends,
            "timestamp": timestamp,
        }

    # ==================== 发送礼物通知 ====================
    elif action == "send_gift":
        target_id = payload.get("target_id")
        item_id = payload.get("item_id")
        item_name = payload.get("item_name", "礼物")

        if not target_id or not item_id:
            return {"type": "error", "message": "Missing target_id or item_id"}

        message = {
            "type": "gift_received",
            "from_player_id": player_id,
            "item_id": item_id,
            "item_name": item_name,
            "timestamp": timestamp,
        }

        success = await connection_manager.send_personal(target_id, message)

        return {
            "type": "gift_sent",
            "success": success,
            "target_id": target_id,
            "timestamp": timestamp,
        }

    # ==================== 帮忙通知 ====================
    elif action == "help_action":
        target_id = payload.get("target_id")
        help_type = payload.get("help_type", "water")  # water, harvest, fertilize

        if not target_id:
            return {"type": "error", "message": "Missing target_id"}

        message = {
            "type": "help_received",
            "from_player_id": player_id,
            "help_type": help_type,
            "timestamp": timestamp,
        }

        success = await connection_manager.send_personal(target_id, message)

        return {
            "type": "help_sent",
            "success": success,
            "target_id": target_id,
            "help_type": help_type,
            "timestamp": timestamp,
        }

    # ==================== 未知动作 ====================
    else:
        return {"type": "error", "message": f"Unknown action: {action}"}
