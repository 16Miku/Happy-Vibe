"""多人联机系统测试

测试 WebSocket 连接管理、好友系统、公会系统、排行榜系统。
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import WebSocket

# 导入被测试模块
from src.main import app
from src.multiplayer.connection_manager import ConnectionManager, connection_manager
from src.multiplayer.models import (
    OnlineStatus,
    MessageType,
    AFFINITY_LEVELS,
    GUILD_LEVEL_CONFIG,
)
from src.storage.models import FriendRequestStatus, GuildRole
from src.api import friends as friends_module
from src.api import leaderboards as leaderboards_module


# ==================== Fixtures ====================


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def conn_manager():
    """创建新的连接管理器实例"""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """创建模拟的 WebSocket"""
    ws = AsyncMock(spec=WebSocket)
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture(autouse=True)
def reset_state():
    """每个测试前重置状态"""
    friends_module._friendships.clear()
    friends_module._friend_requests.clear()
    friends_module._player_cache.clear()
    leaderboards_module._player_stats.clear()
    leaderboards_module._leaderboard_cache.clear()
    leaderboards_module._cache_timestamps.clear()
    yield
    friends_module._friendships.clear()
    friends_module._friend_requests.clear()
    friends_module._player_cache.clear()
    leaderboards_module._player_stats.clear()
    leaderboards_module._leaderboard_cache.clear()
    leaderboards_module._cache_timestamps.clear()


# ==================== ConnectionManager 测试 ====================


class TestConnectionManager:
    """连接管理器测试"""

    @pytest.mark.asyncio
    async def test_connect(self, conn_manager, mock_websocket):
        """测试建立连接"""
        player_id = "player_001"
        player_info = {"username": "TestPlayer", "level": 10}

        result = await conn_manager.connect(mock_websocket, player_id, player_info)

        assert result is True
        assert conn_manager.is_online(player_id)
        assert conn_manager.online_count == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, conn_manager, mock_websocket):
        """测试断开连接"""
        player_id = "player_001"
        await conn_manager.connect(mock_websocket, player_id)

        await conn_manager.disconnect(player_id)

        assert not conn_manager.is_online(player_id)
        assert conn_manager.online_count == 0

    @pytest.mark.asyncio
    async def test_update_status(self, conn_manager, mock_websocket):
        """测试更新状态"""
        player_id = "player_001"
        await conn_manager.connect(mock_websocket, player_id)

        await conn_manager.update_status(player_id, OnlineStatus.CODING)

        assert conn_manager.get_status(player_id) == OnlineStatus.CODING

    @pytest.mark.asyncio
    async def test_send_personal(self, conn_manager, mock_websocket):
        """测试发送私人消息"""
        player_id = "player_001"
        await conn_manager.connect(mock_websocket, player_id)

        message = {"type": "test", "content": "Hello"}
        result = await conn_manager.send_personal(player_id, message)

        assert result is True
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast(self, conn_manager):
        """测试广播消息"""
        # 创建多个模拟连接
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws3 = AsyncMock(spec=WebSocket)

        await conn_manager.connect(ws1, "player_001")
        await conn_manager.connect(ws2, "player_002")
        await conn_manager.connect(ws3, "player_003")

        # 重置 send_json 调用计数（因为 connect 会触发状态广播）
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()
        ws3.send_json.reset_mock()

        message = {"type": "broadcast", "content": "Hello everyone"}
        count = await conn_manager.broadcast(message, exclude=["player_001"])

        assert count == 2
        ws1.send_json.assert_not_called()  # 被排除
        ws2.send_json.assert_called()
        ws3.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_room_management(self, conn_manager, mock_websocket):
        """测试房间管理"""
        player_id = "player_001"
        room_id = "room_test"
        await conn_manager.connect(mock_websocket, player_id)

        # 加入房间
        result = await conn_manager.join_room(player_id, room_id)
        assert result is True
        assert player_id in conn_manager.get_room_members(room_id)

        # 离开房间
        result = await conn_manager.leave_room(player_id, room_id)
        assert result is True
        assert player_id not in conn_manager.get_room_members(room_id)

    @pytest.mark.asyncio
    async def test_get_online_friends(self, conn_manager):
        """测试获取在线好友"""
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await conn_manager.connect(ws1, "player_001", {"username": "Player1"})
        await conn_manager.connect(ws2, "player_002", {"username": "Player2"})

        friend_ids = ["player_001", "player_003"]  # player_003 不在线
        online_friends = conn_manager.get_online_friends(friend_ids)

        assert len(online_friends) == 1
        assert online_friends[0]["player_id"] == "player_001"


# ==================== 好友系统 API 测试 ====================


class TestFriendsAPI:
    """好友系统 API 测试"""

    def test_get_friends_list_empty(self, client):
        """测试获取空好友列表"""
        response = client.get("/api/friends/list/player_001")
        assert response.status_code == 200
        data = response.json()
        assert data["total_friends"] == 0
        assert data["friends"] == []

    def test_send_friend_request(self, client):
        """测试发送好友请求"""
        response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002",
                "message": "Let's be friends!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "request_id" in data

    def test_send_duplicate_friend_request(self, client):
        """测试发送重复好友请求"""
        # 第一次请求
        client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_dup_001",
                "to_player_id": "player_dup_002",
            },
        )

        # 第二次请求应该失败
        response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_dup_001",
                "to_player_id": "player_dup_002",
            },
        )
        assert response.status_code == 400

    def test_get_friend_requests(self, client):
        """测试获取好友请求列表"""
        # 先发送请求
        client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_req_001",
                "to_player_id": "player_req_002",
            },
        )

        # 获取接收者的请求列表
        response = client.get("/api/friends/requests/player_req_002")
        assert response.status_code == 200
        data = response.json()
        assert len(data["received"]) >= 1

    def test_respond_to_friend_request_accept(self, client):
        """测试接受好友请求"""
        # 发送请求
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_acc_001",
                "to_player_id": "player_acc_002",
            },
        )
        request_id = send_response.json()["request_id"]

        # 接受请求
        response = client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证好友关系已建立
        friends_response = client.get("/api/friends/list/player_acc_001")
        friends = friends_response.json()["friends"]
        friend_ids = [f["player_id"] for f in friends]
        assert "player_acc_002" in friend_ids

    def test_get_online_friends(self, client):
        """测试获取在线好友"""
        response = client.get("/api/friends/online/player_001")
        assert response.status_code == 200
        data = response.json()
        assert "online_friends" in data
        assert "count" in data


# ==================== 公会系统 API 测试 ====================


class TestGuildsAPI:
    """公会系统 API 测试"""

    def test_create_guild(self, client):
        """测试创建公会"""
        response = client.post(
            "/api/guilds/create",
            json={
                "name": "Test Guild",
                "description": "A test guild",
                "founder_id": "player_guild_001",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "guild_id" in data

    def test_create_duplicate_guild_name(self, client):
        """测试创建重复名称的公会"""
        # 第一个公会
        client.post(
            "/api/guilds/create",
            json={
                "name": "Unique Guild Name",
                "founder_id": "player_dup_guild_001",
            },
        )

        # 第二个同名公会应该失败
        response = client.post(
            "/api/guilds/create",
            json={
                "name": "Unique Guild Name",
                "founder_id": "player_dup_guild_002",
            },
        )
        assert response.status_code == 400

    def test_get_guilds_list(self, client):
        """测试获取公会列表"""
        response = client.get("/api/guilds/list")
        assert response.status_code == 200
        data = response.json()
        assert "guilds" in data
        assert "total" in data

    def test_get_guild_details(self, client):
        """测试获取公会详情"""
        # 先创建公会
        create_response = client.post(
            "/api/guilds/create",
            json={
                "name": "Detail Test Guild",
                "founder_id": "player_detail_001",
            },
        )
        guild_id = create_response.json()["guild_id"]

        # 获取详情
        response = client.get(f"/api/guilds/{guild_id}")
        assert response.status_code == 200
        data = response.json()
        assert "guild" in data
        assert "members" in data
        assert data["guild"]["name"] == "Detail Test Guild"

    def test_request_join_guild(self, client):
        """测试申请加入公会"""
        # 创建公会
        create_response = client.post(
            "/api/guilds/create",
            json={
                "name": "Join Test Guild",
                "founder_id": "player_join_founder",
            },
        )
        guild_id = create_response.json()["guild_id"]

        # 申请加入
        response = client.post(
            "/api/guilds/join",
            json={
                "player_id": "player_join_applicant",
                "guild_id": guild_id,
                "message": "I want to join!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_contribute_to_guild(self, client):
        """测试向公会贡献能量"""
        # 创建公会
        create_response = client.post(
            "/api/guilds/create",
            json={
                "name": "Contribute Test Guild",
                "founder_id": "player_contrib_001",
            },
        )
        guild_id = create_response.json()["guild_id"]

        # 贡献能量
        response = client.post(
            f"/api/guilds/{guild_id}/contribute",
            json={
                "player_id": "player_contrib_001",
                "guild_id": guild_id,
                "energy_amount": 1000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["energy_contributed"] == 1000
        assert data["exp_gained"] == 10  # 1000 / 100

    def test_get_player_guild(self, client):
        """测试获取玩家所属公会"""
        # 创建公会
        client.post(
            "/api/guilds/create",
            json={
                "name": "Player Guild Test",
                "founder_id": "player_pg_001",
            },
        )

        # 获取玩家公会
        response = client.get("/api/guilds/player/player_pg_001")
        assert response.status_code == 200
        data = response.json()
        assert data["has_guild"] is True
        assert data["membership"]["role"] == "leader"


# ==================== 排行榜系统 API 测试 ====================


class TestLeaderboardsAPI:
    """排行榜系统 API 测试"""

    def test_get_leaderboard_types(self, client):
        """测试获取排行榜类型"""
        response = client.get("/api/leaderboard/types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) > 0

        # 验证类型结构
        for lb_type in data["types"]:
            assert "type" in lb_type
            assert "name" in lb_type
            assert "periods" in lb_type

    def test_get_leaderboard(self, client):
        """测试获取排行榜数据"""
        response = client.get("/api/leaderboard/level?period=weekly")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "level"
        assert data["period"] == "weekly"
        assert "entries" in data
        assert "total" in data

    def test_get_leaderboard_invalid_type(self, client):
        """测试获取无效类型的排行榜"""
        response = client.get("/api/leaderboard/invalid_type")
        assert response.status_code == 400

    def test_get_player_rank(self, client):
        """测试获取玩家排名"""
        response = client.get("/api/leaderboard/level/player/player_rank_001?period=weekly")
        assert response.status_code == 200
        data = response.json()
        assert "rank" in data
        assert "percentile" in data

    def test_get_leaderboard_rewards(self, client):
        """测试获取排行榜奖励"""
        response = client.get("/api/leaderboard/level/rewards")
        assert response.status_code == 200
        data = response.json()
        assert "rewards" in data


# ==================== 模型测试 ====================


class TestModels:
    """数据模型测试"""

    def test_online_status_enum(self):
        """测试在线状态枚举"""
        assert OnlineStatus.ONLINE.value == "online"
        assert OnlineStatus.CODING.value == "coding"
        assert OnlineStatus.AWAY.value == "away"
        assert OnlineStatus.OFFLINE.value == "offline"

    def test_friend_request_status_enum(self):
        """测试好友请求状态枚举"""
        assert FriendRequestStatus.PENDING.value == "pending"
        assert FriendRequestStatus.ACCEPTED.value == "accepted"
        assert FriendRequestStatus.REJECTED.value == "rejected"

    def test_guild_role_enum(self):
        """测试公会角色枚举"""
        assert GuildRole.LEADER.value == "leader"
        assert GuildRole.OFFICER.value == "officer"
        assert GuildRole.MEMBER.value == "member"

    def test_affinity_levels_config(self):
        """测试好友度等级配置"""
        assert "stranger" in AFFINITY_LEVELS
        assert "best_friend" in AFFINITY_LEVELS
        assert AFFINITY_LEVELS["stranger"]["min"] == 0
        assert AFFINITY_LEVELS["best_friend"]["min"] == 201

    def test_guild_level_config(self):
        """测试公会等级配置"""
        assert 1 in GUILD_LEVEL_CONFIG
        assert GUILD_LEVEL_CONFIG[1]["max_members"] == 10
        assert GUILD_LEVEL_CONFIG[5]["max_members"] == 30


# ==================== 集成测试 ====================


class TestIntegration:
    """集成测试"""

    def test_full_friend_flow(self, client):
        """测试完整的好友流程"""
        # 1. 发送好友请求
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "integration_001",
                "to_player_id": "integration_002",
            },
        )
        assert send_response.status_code == 200
        request_id = send_response.json()["request_id"]

        # 2. 接受好友请求
        accept_response = client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": True},
        )
        assert accept_response.status_code == 200

        # 3. 验证好友列表
        list_response = client.get("/api/friends/list/integration_001")
        friends = list_response.json()["friends"]
        assert any(f["player_id"] == "integration_002" for f in friends)

        # 4. 访问好友农场
        visit_response = client.post("/api/friends/visit/integration_001/integration_002")
        assert visit_response.status_code == 200
        assert visit_response.json()["affinity_gained"] > 0

    def test_full_guild_flow(self, client):
        """测试完整的公会流程"""
        # 1. 创建公会
        create_response = client.post(
            "/api/guilds/create",
            json={
                "name": "Integration Test Guild",
                "description": "For integration testing",
                "founder_id": "guild_founder_001",
            },
        )
        assert create_response.status_code == 200
        guild_id = create_response.json()["guild_id"]

        # 2. 申请加入
        join_response = client.post(
            "/api/guilds/join",
            json={
                "player_id": "guild_member_001",
                "guild_id": guild_id,
            },
        )
        assert join_response.status_code == 200
        request_id = join_response.json()["request_id"]

        # 3. 会长批准申请
        approve_response = client.post(
            f"/api/guilds/join/{request_id}/respond?accept=true&operator_id=guild_founder_001"
        )
        assert approve_response.status_code == 200

        # 4. 验证成员列表
        details_response = client.get(f"/api/guilds/{guild_id}")
        members = details_response.json()["members"]
        assert len(members) == 2

        # 5. 贡献能量
        contrib_response = client.post(
            f"/api/guilds/{guild_id}/contribute",
            json={
                "player_id": "guild_member_001",
                "guild_id": guild_id,
                "energy_amount": 500,
            },
        )
        assert contrib_response.status_code == 200
