"""API 健康检查测试"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
class TestHealthAPI:
    """健康检查 API 测试"""

    async def test_health_check_returns_ok(self):
        """测试健康检查端点返回正确状态"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Happy Vibe Hub"
        assert "version" in data

    async def test_api_health_check_returns_ok(self):
        """测试 API 健康检查端点（兼容路径）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
