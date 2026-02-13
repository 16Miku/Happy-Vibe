"""API 客户端测试."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.api.client import ActivityStatus, FlowStatus, PlayerInfo, VibeHubClient


class TestModels:
    """数据模型测试."""

    def test_activity_status_default(self):
        """测试 ActivityStatus 默认值."""
        status = ActivityStatus(is_active=False)
        assert status.is_active is False
        assert status.activity_type is None
        assert status.duration_seconds == 0
        assert status.energy_earned == 0.0

    def test_activity_status_with_values(self):
        """测试 ActivityStatus 带值."""
        status = ActivityStatus(
            is_active=True,
            activity_type="coding",
            duration_seconds=3600,
            energy_earned=100.5,
        )
        assert status.is_active is True
        assert status.activity_type == "coding"
        assert status.duration_seconds == 3600
        assert status.energy_earned == 100.5

    def test_flow_status_default(self):
        """测试 FlowStatus 默认值."""
        status = FlowStatus(in_flow=False)
        assert status.in_flow is False
        assert status.flow_level == 0
        assert status.multiplier == 1.0

    def test_flow_status_with_values(self):
        """测试 FlowStatus 带值."""
        status = FlowStatus(
            in_flow=True,
            flow_level=2,
            flow_duration_seconds=1800,
            multiplier=1.5,
        )
        assert status.in_flow is True
        assert status.flow_level == 2
        assert status.multiplier == 1.5

    def test_player_info(self):
        """测试 PlayerInfo."""
        player = PlayerInfo(
            player_id="test-123",
            name="测试玩家",
            level=5,
            total_energy=1000.0,
            today_energy=50.0,
        )
        assert player.player_id == "test-123"
        assert player.name == "测试玩家"
        assert player.level == 5


class TestVibeHubClient:
    """VibeHubClient 测试类."""

    @pytest.fixture
    def client(self):
        """创建测试客户端."""
        return VibeHubClient("http://127.0.0.1:8765")

    def test_init(self, client):
        """测试初始化."""
        assert client.base_url == "http://127.0.0.1:8765"
        assert client._client is None

    def test_init_strips_trailing_slash(self):
        """测试初始化去除尾部斜杠."""
        client = VibeHubClient("http://127.0.0.1:8765/")
        assert client.base_url == "http://127.0.0.1:8765"

    @pytest.mark.asyncio
    async def test_get_client_creates_new(self, client):
        """测试获取客户端创建新实例."""
        http_client = await client._get_client()
        assert http_client is not None
        assert isinstance(http_client, httpx.AsyncClient)
        await client.close()

    @pytest.mark.asyncio
    async def test_close(self, client):
        """测试关闭客户端."""
        await client._get_client()
        await client.close()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_when_not_open(self, client):
        """测试关闭未打开的客户端."""
        await client.close()  # 不应抛出异常

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """测试健康检查成功."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_http

            result = await client.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """测试健康检查失败."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(side_effect=httpx.RequestError("连接失败"))
            mock_get.return_value = mock_http

            result = await client.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_get_player_success(self, client):
        """测试获取玩家成功."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {
                "player_id": "test-123",
                "name": "测试玩家",
                "level": 1,
            }
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_http

            result = await client.get_player()
            assert result is not None
            assert result.player_id == "test-123"

    @pytest.mark.asyncio
    async def test_get_player_failure(self, client):
        """测试获取玩家失败."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(side_effect=httpx.RequestError("连接失败"))
            mock_get.return_value = mock_http

            result = await client.get_player()
            assert result is None

    @pytest.mark.asyncio
    async def test_start_activity_success(self, client):
        """测试开始活动成功."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {"activity_id": "act-123"}
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_http

            result = await client.start_activity("coding")
            assert result is not None
            assert result["activity_id"] == "act-123"

    @pytest.mark.asyncio
    async def test_start_activity_failure(self, client):
        """测试开始活动失败."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=httpx.RequestError("连接失败"))
            mock_get.return_value = mock_http

            result = await client.start_activity()
            assert result is None

    @pytest.mark.asyncio
    async def test_update_activity_success(self, client):
        """测试更新活动成功."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {"updated": True}
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_http

            result = await client.update_activity(lines_added=10)
            assert result is not None

    @pytest.mark.asyncio
    async def test_end_activity_success(self, client):
        """测试结束活动成功."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {
                "duration_seconds": 3600,
                "energy_earned": 100.0,
            }
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_http

            result = await client.end_activity()
            assert result is not None
            assert result["energy_earned"] == 100.0

    @pytest.mark.asyncio
    async def test_get_current_activity_success(self, client):
        """测试获取当前活动成功."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {
                "is_active": True,
                "activity_type": "coding",
            }
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_http

            result = await client.get_current_activity()
            assert result.is_active is True

    @pytest.mark.asyncio
    async def test_get_current_activity_failure(self, client):
        """测试获取当前活动失败返回默认值."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(side_effect=httpx.RequestError("连接失败"))
            mock_get.return_value = mock_http

            result = await client.get_current_activity()
            assert result.is_active is False

    @pytest.mark.asyncio
    async def test_get_flow_status_success(self, client):
        """测试获取心流状态成功."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {
                "in_flow": True,
                "flow_level": 2,
            }
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_http

            result = await client.get_flow_status()
            assert result.in_flow is True
            assert result.flow_level == 2

    @pytest.mark.asyncio
    async def test_get_flow_status_failure(self, client):
        """测试获取心流状态失败返回默认值."""
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(side_effect=httpx.RequestError("连接失败"))
            mock_get.return_value = mock_http

            result = await client.get_flow_status()
            assert result.in_flow is False
