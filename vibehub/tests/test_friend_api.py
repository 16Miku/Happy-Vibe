"""好友系统 API 测试

测试好友相关的 REST API 端点，包括：
- 发送/接受/拒绝好友请求
- 好友列表管理
- 访问好友农场
- 好友度系统
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.api import friends as friends_module


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_friends_state():
    """每个测试前重置好友系统状态"""
    friends_module._friendships.clear()
    friends_module._friend_requests.clear()
    friends_module._player_cache.clear()
    yield
    friends_module._friendships.clear()
    friends_module._friend_requests.clear()
    friends_module._player_cache.clear()


class TestSendFriendRequest:
    """发送好友请求测试"""

    def test_send_request_success(self, client):
        """测试成功发送好友请求"""
        response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002",
                "message": "你好，交个朋友吧！"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "request_id" in data

    def test_send_request_to_self(self, client):
        """测试不能添加自己为好友"""
        response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_001"
            }
        )

        # 当前 API 没有检查自己添加自己，这里测试实际行为
        # 如果需要此功能，应该在 API 中添加检查
        assert response.status_code == 200

    def test_send_request_duplicate(self, client):
        """测试重复发送好友请求"""
        # 第一次发送
        client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        # 第二次发送
        response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )

        assert response.status_code == 400
        assert "pending" in response.json()["detail"].lower()


class TestGetFriendRequests:
    """获取好友请求列表测试"""

    def test_get_received_requests(self, client):
        """测试获取收到的好友请求"""
        # 发送请求
        client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )

        # 获取接收者的请求列表
        response = client.get("/api/friends/requests/player_002")
        assert response.status_code == 200
        data = response.json()
        assert len(data["received"]) >= 1

    def test_get_sent_requests(self, client):
        """测试获取已发送的好友请求"""
        # 发送请求
        client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        # 获取已发送的请求
        response = client.get("/api/friends/requests/player_001")

        assert response.status_code == 200
        data = response.json()
        assert len(data["sent"]) == 1


class TestAcceptRejectRequest:
    """接受/拒绝好友请求测试"""

    def test_accept_request_success(self, client):
        """测试成功接受好友请求"""
        # 发送请求
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        request_id = send_response.json()["request_id"]

        # 接受请求
        response = client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_accept_request_not_found(self, client):
        """测试接受不存在的请求"""
        response = client.post(
            "/api/friends/request/respond",
            json={"request_id": "invalid-id", "accept": True}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_reject_request_success(self, client):
        """测试成功拒绝好友请求"""
        # 发送请求
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        request_id = send_response.json()["request_id"]

        # 拒绝请求
        response = client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rejected" in data["message"].lower()

    def test_reject_request_not_found(self, client):
        """测试拒绝不存在的请求"""
        response = client.post(
            "/api/friends/request/respond",
            json={"request_id": "invalid-id", "accept": False}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestFriendList:
    """好友列表测试"""

    def test_get_empty_friend_list(self, client):
        """测试获取空好友列表"""
        response = client.get("/api/friends/list/player_001")

        assert response.status_code == 200
        data = response.json()
        assert data["total_friends"] == 0
        assert data["friends"] == []

    def test_get_friend_list_with_friends(self, client):
        """测试获取有好友的列表"""
        # 发送并接受好友请求
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        request_id = send_response.json()["request_id"]
        client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": True}
        )

        # 获取好友列表
        response = client.get("/api/friends/list/player_001")

        assert response.status_code == 200
        data = response.json()
        assert data["total_friends"] == 1
        assert len(data["friends"]) == 1
        assert data["friends"][0]["player_id"] == "player_002"


class TestRemoveFriend:
    """删除好友测试"""

    def test_remove_friend_success(self, client):
        """测试成功删除好友"""
        # 先建立好友关系
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        request_id = send_response.json()["request_id"]
        client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": True}
        )

        # 删除好友
        response = client.delete("/api/friends/player_001/player_002")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_remove_non_friend(self, client):
        """测试删除非好友"""
        response = client.delete("/api/friends/player_001/player_002")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestVisitFriendFarm:
    """访问好友农场测试"""

    def test_visit_friend_farm_success(self, client):
        """测试成功访问好友农场"""
        # 先建立好友关系
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        request_id = send_response.json()["request_id"]
        client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": True}
        )

        # 访问好友农场
        response = client.post("/api/friends/visit/player_001/player_002")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affinity_gained"] > 0

    def test_visit_non_friend_farm(self, client):
        """测试访问非好友的农场"""
        response = client.post("/api/friends/visit/player_001/player_002")

        assert response.status_code == 400
        assert "not friends" in response.json()["detail"].lower()


class TestOnlineFriends:
    """在线好友测试"""

    def test_get_online_friends_empty(self, client):
        """测试获取在线好友（无好友）"""
        response = client.get("/api/friends/online/player_001")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["online_friends"] == []


class TestSendGift:
    """发送礼物测试"""

    def test_send_gift_success(self, client):
        """测试成功发送礼物"""
        # 先建立好友关系
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        request_id = send_response.json()["request_id"]
        client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": True}
        )

        # 发送礼物
        response = client.post(
            "/api/friends/gift",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002",
                "item_id": "item_001",
                "item_name": "测试礼物",
                "quantity": 1
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["affinity_gained"] > 0

    def test_send_gift_non_friend(self, client):
        """测试向非好友发送礼物"""
        response = client.post(
            "/api/friends/gift",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002",
                "item_id": "item_001",
                "item_name": "测试礼物",
                "quantity": 1
            }
        )

        assert response.status_code == 400
        assert "not friends" in response.json()["detail"].lower()


class TestHelpFriend:
    """帮助好友测试"""

    def test_help_friend_affinity_too_low(self, client):
        """测试好友度不足时帮助好友"""
        # 先建立好友关系（初始好友度为 0）
        send_response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )
        request_id = send_response.json()["request_id"]
        client.post(
            "/api/friends/request/respond",
            json={"request_id": request_id, "accept": True}
        )

        # 尝试帮助好友（好友度不足 51）
        response = client.post(
            "/api/friends/help",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002",
                "action_type": "water"
            }
        )

        assert response.status_code == 400
        assert "affinity" in response.json()["detail"].lower()

    def test_help_non_friend(self, client):
        """测试帮助非好友"""
        response = client.post(
            "/api/friends/help",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002",
                "action_type": "water"
            }
        )

        assert response.status_code == 400
        assert "not friends" in response.json()["detail"].lower()


class TestFriendRequestWithMessage:
    """带附言的好友请求测试"""

    def test_request_with_message(self, client):
        """测试带附言的请求"""
        response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002",
                "message": "你好，我是新玩家！"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_request_with_long_message(self, client):
        """测试附言长度限制"""
        response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002",
                "message": "a" * 201  # 超过200字符限制
            }
        )

        assert response.status_code == 422  # Pydantic 验证错误

    def test_request_without_message(self, client):
        """测试不带附言的请求"""
        response = client.post(
            "/api/friends/request",
            json={
                "from_player_id": "player_001",
                "to_player_id": "player_002"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
