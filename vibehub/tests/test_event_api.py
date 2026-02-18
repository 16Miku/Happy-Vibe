"""活动 API 单元测试"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.storage.models import EventType, GameEvent


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def active_event(test_db):
    """创建活跃活动"""
    now = datetime.utcnow()
    with test_db.get_session() as session:
        event = GameEvent(
            event_type=EventType.DOUBLE_EXP.value,
            title="双倍经验活动",
            description="所有经验获取翻倍",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=23),
            effects_json='{"exp_multiplier": 2.0}',
            is_active=True,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event.event_id


class TestEventAPI:
    """活动 API 测试"""

    def test_get_active_events(self, client, active_event, test_db):
        """测试获取活跃活动"""
        response = client.get("/api/event/active")

        assert response.status_code == 200
        data = response.json()

        assert "events" in data
        assert "total" in data
        assert data["total"] >= 1
        # 检查是否包含我们创建的活动
        titles = [e["title"] for e in data["events"]]
        assert "双倍经验活动" in titles

    def test_get_active_events_empty(self, client, test_db):
        """测试无活跃活动"""
        response = client.get("/api/event/active")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "events" in data

    def test_get_event_detail(self, client, active_event, test_db):
        """测试获取活动详情"""
        response = client.get(f"/api/event/{active_event}")

        assert response.status_code == 200
        data = response.json()

        assert data["event_id"] == active_event
        assert data["title"] == "双倍经验活动"
        assert data["event_type"] == EventType.DOUBLE_EXP.value
        assert data["is_ongoing"] is True
        assert data["effects"]["exp_multiplier"] == 2.0

    def test_get_event_detail_not_found(self, client, test_db):
        """测试获取不存在的活动"""
        response = client.get("/api/event/nonexistent-event-id")

        assert response.status_code == 404
        assert "活动不存在" in response.json()["detail"]
