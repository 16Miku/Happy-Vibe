"""WebSocket 连接管理器

管理多人联机的实时通信连接。
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import WebSocket

from .models import MessageType, OnlineStatus


class ConnectionManager:
    """WebSocket 连接管理器

    管理所有在线玩家的 WebSocket 连接，处理消息广播和点对点通信。
    """

    def __init__(self):
        # 活跃连接: player_id -> WebSocket
        self._connections: dict[str, WebSocket] = {}
        # 玩家状态: player_id -> OnlineStatus
        self._player_status: dict[str, OnlineStatus] = {}
        # 玩家信息缓存: player_id -> {username, level, ...}
        self._player_info: dict[str, dict] = {}
        # 房间/频道: room_id -> set[player_id]
        self._rooms: dict[str, set[str]] = {}
        # 锁，保证线程安全
        self._lock = asyncio.Lock()

    @property
    def online_count(self) -> int:
        """在线玩家数量"""
        return len(self._connections)

    async def connect(
        self, websocket: WebSocket, player_id: str, player_info: Optional[dict] = None
    ) -> bool:
        """建立连接

        Args:
            websocket: WebSocket 连接
            player_id: 玩家 ID
            player_info: 玩家信息 (username, level 等)

        Returns:
            是否连接成功
        """
        await websocket.accept()

        async with self._lock:
            # 如果已有连接，先断开旧连接
            if player_id in self._connections:
                old_ws = self._connections[player_id]
                try:
                    await old_ws.close(code=4000, reason="New connection established")
                except Exception:
                    pass

            self._connections[player_id] = websocket
            self._player_status[player_id] = OnlineStatus.ONLINE

            if player_info:
                self._player_info[player_id] = player_info

        # 广播上线通知
        await self._broadcast_status_change(player_id, OnlineStatus.ONLINE)

        return True

    async def disconnect(self, player_id: str) -> None:
        """断开连接

        Args:
            player_id: 玩家 ID
        """
        async with self._lock:
            if player_id in self._connections:
                del self._connections[player_id]

            if player_id in self._player_status:
                del self._player_status[player_id]

            # 从所有房间移除
            for room_id in list(self._rooms.keys()):
                self._rooms[room_id].discard(player_id)
                if not self._rooms[room_id]:
                    del self._rooms[room_id]

        # 广播下线通知
        await self._broadcast_status_change(player_id, OnlineStatus.OFFLINE)

    async def update_status(self, player_id: str, status: OnlineStatus) -> None:
        """更新玩家状态

        Args:
            player_id: 玩家 ID
            status: 新状态
        """
        if player_id not in self._connections:
            return

        old_status = self._player_status.get(player_id)
        if old_status == status:
            return

        self._player_status[player_id] = status
        await self._broadcast_status_change(player_id, status)

    async def _broadcast_status_change(
        self, player_id: str, status: OnlineStatus
    ) -> None:
        """广播状态变化

        Args:
            player_id: 玩家 ID
            status: 新状态
        """
        message = {
            "type": "status_change",
            "player_id": player_id,
            "status": status.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 获取该玩家的好友列表并通知
        # TODO: 从数据库获取好友列表，只通知好友
        # 暂时广播给所有在线玩家
        await self.broadcast(message, exclude=[player_id])

    async def send_personal(self, player_id: str, message: dict) -> bool:
        """发送私人消息

        Args:
            player_id: 目标玩家 ID
            message: 消息内容

        Returns:
            是否发送成功
        """
        if player_id not in self._connections:
            return False

        websocket = self._connections[player_id]
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            # 连接可能已断开
            await self.disconnect(player_id)
            return False

    async def send_to_friends(
        self, player_id: str, friend_ids: list[str], message: dict
    ) -> int:
        """发送消息给好友列表

        Args:
            player_id: 发送者 ID
            friend_ids: 好友 ID 列表
            message: 消息内容

        Returns:
            成功发送的数量
        """
        message["from_player_id"] = player_id
        message["timestamp"] = datetime.utcnow().isoformat()

        success_count = 0
        for friend_id in friend_ids:
            if await self.send_personal(friend_id, message):
                success_count += 1

        return success_count

    async def broadcast(
        self, message: dict, exclude: Optional[list[str]] = None
    ) -> int:
        """广播消息给所有在线玩家

        Args:
            message: 消息内容
            exclude: 排除的玩家 ID 列表

        Returns:
            成功发送的数量
        """
        exclude = exclude or []
        message["timestamp"] = datetime.utcnow().isoformat()

        success_count = 0
        disconnected = []

        for player_id, websocket in list(self._connections.items()):
            if player_id in exclude:
                continue

            try:
                await websocket.send_json(message)
                success_count += 1
            except Exception:
                disconnected.append(player_id)

        # 清理断开的连接
        for player_id in disconnected:
            await self.disconnect(player_id)

        return success_count

    # ==================== 房间/频道管理 ====================

    async def join_room(self, player_id: str, room_id: str) -> bool:
        """加入房间

        Args:
            player_id: 玩家 ID
            room_id: 房间 ID

        Returns:
            是否加入成功
        """
        if player_id not in self._connections:
            return False

        async with self._lock:
            if room_id not in self._rooms:
                self._rooms[room_id] = set()
            self._rooms[room_id].add(player_id)

        # 通知房间内其他玩家
        await self.broadcast_to_room(
            room_id,
            {
                "type": "room_join",
                "room_id": room_id,
                "player_id": player_id,
                "player_info": self._player_info.get(player_id, {}),
            },
            exclude=[player_id],
        )

        return True

    async def leave_room(self, player_id: str, room_id: str) -> bool:
        """离开房间

        Args:
            player_id: 玩家 ID
            room_id: 房间 ID

        Returns:
            是否离开成功
        """
        async with self._lock:
            if room_id not in self._rooms:
                return False

            self._rooms[room_id].discard(player_id)

            if not self._rooms[room_id]:
                del self._rooms[room_id]

        # 通知房间内其他玩家
        await self.broadcast_to_room(
            room_id,
            {
                "type": "room_leave",
                "room_id": room_id,
                "player_id": player_id,
            },
        )

        return True

    async def broadcast_to_room(
        self, room_id: str, message: dict, exclude: Optional[list[str]] = None
    ) -> int:
        """广播消息到房间

        Args:
            room_id: 房间 ID
            message: 消息内容
            exclude: 排除的玩家 ID 列表

        Returns:
            成功发送的数量
        """
        if room_id not in self._rooms:
            return 0

        exclude = exclude or []
        message["room_id"] = room_id
        message["timestamp"] = datetime.utcnow().isoformat()

        success_count = 0
        for player_id in self._rooms[room_id]:
            if player_id in exclude:
                continue
            if await self.send_personal(player_id, message):
                success_count += 1

        return success_count

    def get_room_members(self, room_id: str) -> list[str]:
        """获取房间成员列表

        Args:
            room_id: 房间 ID

        Returns:
            成员 ID 列表
        """
        return list(self._rooms.get(room_id, set()))

    # ==================== 查询方法 ====================

    def is_online(self, player_id: str) -> bool:
        """检查玩家是否在线

        Args:
            player_id: 玩家 ID

        Returns:
            是否在线
        """
        return player_id in self._connections

    def get_status(self, player_id: str) -> OnlineStatus:
        """获取玩家状态

        Args:
            player_id: 玩家 ID

        Returns:
            玩家状态
        """
        return self._player_status.get(player_id, OnlineStatus.OFFLINE)

    def get_online_players(self) -> list[dict]:
        """获取所有在线玩家信息

        Returns:
            在线玩家列表
        """
        result = []
        for player_id in self._connections:
            info = self._player_info.get(player_id, {})
            result.append(
                {
                    "player_id": player_id,
                    "status": self._player_status.get(
                        player_id, OnlineStatus.ONLINE
                    ).value,
                    **info,
                }
            )
        return result

    def get_online_friends(self, friend_ids: list[str]) -> list[dict]:
        """获取在线的好友列表

        Args:
            friend_ids: 好友 ID 列表

        Returns:
            在线好友列表
        """
        result = []
        for friend_id in friend_ids:
            if friend_id in self._connections:
                info = self._player_info.get(friend_id, {})
                result.append(
                    {
                        "player_id": friend_id,
                        "status": self._player_status.get(
                            friend_id, OnlineStatus.ONLINE
                        ).value,
                        **info,
                    }
                )
        return result


# 全局连接管理器实例
connection_manager = ConnectionManager()
