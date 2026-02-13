"""VibeHub API 客户端."""

from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel


class ActivityStatus(BaseModel):
    """活动状态."""

    is_active: bool
    activity_type: str | None = None
    start_time: datetime | None = None
    duration_seconds: int = 0
    energy_earned: float = 0.0


class FlowStatus(BaseModel):
    """心流状态."""

    in_flow: bool
    flow_level: int = 0
    flow_duration_seconds: int = 0
    multiplier: float = 1.0


class PlayerInfo(BaseModel):
    """玩家信息."""

    player_id: str
    name: str
    level: int = 1
    total_energy: float = 0.0
    today_energy: float = 0.0


class VibeHubClient:
    """VibeHub API 客户端."""

    def __init__(self, base_url: str = "http://127.0.0.1:8765") -> None:
        """初始化客户端.

        Args:
            base_url: VibeHub 服务地址
        """
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=10.0,
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """检查服务健康状态."""
        try:
            client = await self._get_client()
            response = await client.get("/api/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def get_player(self) -> PlayerInfo | None:
        """获取玩家信息."""
        try:
            client = await self._get_client()
            response = await client.get("/api/player")
            if response.status_code == 200:
                data = response.json()
                return PlayerInfo(**data)
        except httpx.RequestError:
            pass
        return None

    async def start_activity(self, activity_type: str = "coding") -> dict[str, Any] | None:
        """开始活动追踪.

        Args:
            activity_type: 活动类型

        Returns:
            活动信息或 None
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/activity/start",
                json={"activity_type": activity_type},
            )
            if response.status_code == 200:
                return response.json()
        except httpx.RequestError:
            pass
        return None

    async def update_activity(
        self,
        lines_added: int = 0,
        lines_deleted: int = 0,
        files_changed: int = 0,
    ) -> dict[str, Any] | None:
        """更新活动进度.

        Args:
            lines_added: 新增行数
            lines_deleted: 删除行数
            files_changed: 修改文件数

        Returns:
            更新后的活动信息或 None
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/activity/update",
                json={
                    "lines_added": lines_added,
                    "lines_deleted": lines_deleted,
                    "files_changed": files_changed,
                },
            )
            if response.status_code == 200:
                return response.json()
        except httpx.RequestError:
            pass
        return None

    async def end_activity(self) -> dict[str, Any] | None:
        """结束活动并获取奖励.

        Returns:
            活动结算信息或 None
        """
        try:
            client = await self._get_client()
            response = await client.post("/api/activity/end")
            if response.status_code == 200:
                return response.json()
        except httpx.RequestError:
            pass
        return None

    async def get_current_activity(self) -> ActivityStatus:
        """获取当前活动状态.

        Returns:
            活动状态
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/activity/current")
            if response.status_code == 200:
                data = response.json()
                return ActivityStatus(**data)
        except httpx.RequestError:
            pass
        return ActivityStatus(is_active=False)

    async def get_flow_status(self) -> FlowStatus:
        """获取心流状态.

        Returns:
            心流状态
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/activity/flow-status")
            if response.status_code == 200:
                data = response.json()
                return FlowStatus(**data)
        except httpx.RequestError:
            pass
        return FlowStatus(in_flow=False)
