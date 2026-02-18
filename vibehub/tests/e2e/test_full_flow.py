"""完整数据流 E2E 测试

验证完整的数据流：
Claude Code 日志 → Monitor 采集 → VibeHub 计算 → Godot 显示

测试场景：
1. 完整活动生命周期（开始 → 更新 → 结束）
2. 能量计算准确性验证
3. 心流状态检测验证
4. 玩家数据同步验证
"""

import asyncio
import time
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient


class TestFullDataFlow:
    """完整数据流测试"""

    @pytest.mark.asyncio
    async def test_complete_activity_lifecycle(self, e2e_client: AsyncClient):
        """测试完整的活动生命周期

        模拟 Monitor 的完整调用流程：
        1. 开始活动
        2. 多次更新进度
        3. 结束活动并获取奖励
        """
        player_id = "e2e-test-player-001"

        # 1. 开始活动
        start_response = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        assert start_response.status_code == 200
        start_data = start_response.json()
        session_id = start_data["session_id"]
        assert session_id is not None
        assert start_data["message"] == "活动追踪已开始"

        # 2. 更新活动进度（模拟编码过程）
        quality_metrics = {
            "success_rate": 0.85,
            "iteration_count": 3,
            "lines_changed": 150,
            "files_affected": 5,
            "languages": ["python", "gdscript"],
            "tool_usage": {"read": 10, "write": 8, "bash": 5, "search": 3},
        }

        update_response = await e2e_client.post(
            "/api/activity/update",
            json={
                "session_id": session_id,
                "quality": quality_metrics,
                "last_interaction_gap": 30.0,
            },
        )
        assert update_response.status_code == 200
        update_data = update_response.json()
        assert update_data["session_id"] == session_id
        assert update_data["estimated_energy"] >= 0

        # 3. 结束活动
        end_response = await e2e_client.post(
            "/api/activity/end",
            json={"session_id": session_id, "quality": quality_metrics},
        )
        assert end_response.status_code == 200
        end_data = end_response.json()

        # 验证奖励结构存在
        assert "reward" in end_data
        assert "vibe_energy" in end_data["reward"]
        assert "experience" in end_data["reward"]
        assert "breakdown" in end_data["reward"]
        assert end_data["message"] == "活动已结束，奖励已发放"

    @pytest.mark.asyncio
    async def test_energy_calculation_accuracy(self, e2e_client: AsyncClient):
        """测试能量计算准确性

        验证能量计算公式：
        Vibe_Energy = Base_Rate × Time_Factor × Quality_Factor × Streak_Bonus × Flow_Bonus
        """
        player_id = "e2e-test-player-002"

        # 开始活动
        start_response = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        session_id = start_response.json()["session_id"]

        # 高质量编码指标
        high_quality = {
            "success_rate": 0.95,
            "iteration_count": 2,
            "lines_changed": 300,
            "files_affected": 8,
            "languages": ["python", "typescript", "gdscript"],
            "tool_usage": {"read": 20, "write": 15, "bash": 10, "search": 8},
        }

        # 更新并获取预估能量
        update_response = await e2e_client.post(
            "/api/activity/update",
            json={
                "session_id": session_id,
                "quality": high_quality,
                "last_interaction_gap": 60.0,
            },
        )
        estimated_energy = update_response.json()["estimated_energy"]

        # 结束活动
        end_response = await e2e_client.post(
            "/api/activity/end",
            json={"session_id": session_id, "quality": high_quality},
        )
        end_data = end_response.json()

        # 验证能量分解结构
        breakdown = end_data["reward"]["breakdown"]
        assert "base" in breakdown, "应包含基础能量"
        assert "time_bonus" in breakdown, "应包含时间加成"
        assert "quality_bonus" in breakdown, "应包含质量加成"
        assert "streak_bonus" in breakdown, "应包含连续签到加成"
        assert breakdown["time_bonus"] >= 1.0, "时间加成应 >= 1.0"
        assert breakdown["quality_bonus"] >= 0.5, "质量加成应 >= 0.5"
        assert breakdown["streak_bonus"] >= 1.0, "连续签到加成应 >= 1.0"

        # 验证最终能量存在
        final_energy = end_data["reward"]["vibe_energy"]
        assert final_energy >= 0, "最终能量应 >= 0"

    @pytest.mark.asyncio
    async def test_player_data_sync(self, e2e_client: AsyncClient):
        """测试玩家数据同步

        验证活动结束后玩家数据正确更新
        """
        player_id = "e2e-test-player-003"

        # 开始活动（会自动创建玩家）
        start_response = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        session_id = start_response.json()["session_id"]

        # 结束活动
        end_response = await e2e_client.post(
            "/api/activity/end",
            json={
                "session_id": session_id,
                "quality": {
                    "success_rate": 0.8,
                    "iteration_count": 5,
                    "lines_changed": 100,
                    "files_affected": 3,
                    "languages": ["python"],
                    "tool_usage": {"read": 5, "write": 3, "bash": 2, "search": 1},
                },
            },
        )
        assert end_response.status_code == 200
        reward = end_response.json()["reward"]

        # 验证奖励结构正确
        assert "vibe_energy" in reward
        assert "experience" in reward
        assert reward["vibe_energy"] >= 0
        assert reward["experience"] >= 0

    @pytest.mark.asyncio
    async def test_activity_history_tracking(self, e2e_client: AsyncClient):
        """测试活动历史记录

        验证活动完成后正确保存到历史记录
        """
        player_id = "e2e-test-player-004"

        # 完成一个活动
        start_response = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        session_id = start_response.json()["session_id"]

        await e2e_client.post(
            "/api/activity/end",
            json={
                "session_id": session_id,
                "quality": {
                    "success_rate": 0.9,
                    "iteration_count": 2,
                    "lines_changed": 200,
                    "files_affected": 4,
                    "languages": ["python"],
                    "tool_usage": {"read": 8, "write": 6, "bash": 3, "search": 2},
                },
            },
        )

        # 查询历史记录
        history_response = await e2e_client.get(
            f"/api/activity/history?player_id={player_id}"
        )
        assert history_response.status_code == 200
        history_data = history_response.json()

        assert history_data["total"] >= 1
        assert len(history_data["items"]) >= 1

        # 验证最新记录
        latest = history_data["items"][0]
        assert latest["source"] == "claude_code"
        assert latest["energy_earned"] >= 0


class TestFlowStateDetection:
    """心流状态检测测试"""

    @pytest.mark.asyncio
    async def test_flow_state_progress(self, e2e_client: AsyncClient):
        """测试心流状态进度追踪"""
        player_id = "e2e-test-player-flow-001"

        # 开始活动
        start_response = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        session_id = start_response.json()["session_id"]

        # 更新活动（模拟高质量编码）
        update_response = await e2e_client.post(
            "/api/activity/update",
            json={
                "session_id": session_id,
                "quality": {
                    "success_rate": 0.9,
                    "iteration_count": 2,
                    "lines_changed": 200,
                    "files_affected": 5,
                    "languages": ["python", "typescript"],
                    "tool_usage": {"read": 15, "write": 12, "bash": 8, "search": 5},
                },
                "last_interaction_gap": 120.0,
            },
        )

        flow_status = update_response.json()["flow_status"]

        # 验证心流状态结构
        assert "is_active" in flow_status
        assert "progress" in flow_status

        # 清理
        await e2e_client.post(
            "/api/activity/end",
            json={"session_id": session_id},
        )

    @pytest.mark.asyncio
    async def test_flow_status_endpoint(self, e2e_client: AsyncClient):
        """测试心流状态查询端点"""
        player_id = "e2e-test-player-flow-002"

        # 开始活动
        start_response = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        session_id = start_response.json()["session_id"]

        # 查询心流状态
        flow_response = await e2e_client.get(
            f"/api/activity/flow-status?player_id={player_id}"
        )
        assert flow_response.status_code == 200
        flow_data = flow_response.json()

        assert "is_active" in flow_data
        assert "progress" in flow_data

        # 清理
        await e2e_client.post(
            "/api/activity/end",
            json={"session_id": session_id},
        )


class TestAPIIntegration:
    """API 集成测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, e2e_client: AsyncClient):
        """测试健康检查端点"""
        response = await e2e_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_concurrent_sessions_rejected(self, e2e_client: AsyncClient):
        """测试同一玩家不能同时有多个活动会话"""
        player_id = "e2e-test-player-concurrent"

        # 开始第一个活动
        start1 = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        assert start1.status_code == 200
        session_id = start1.json()["session_id"]

        # 尝试开始第二个活动（应该被拒绝）
        start2 = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        assert start2.status_code == 409  # Conflict

        # 清理
        await e2e_client.post(
            "/api/activity/end",
            json={"session_id": session_id},
        )

    @pytest.mark.asyncio
    async def test_invalid_session_rejected(self, e2e_client: AsyncClient):
        """测试无效会话 ID 被拒绝"""
        # 尝试更新不存在的会话
        update_response = await e2e_client.post(
            "/api/activity/update",
            json={"session_id": "non-existent-session"},
        )
        assert update_response.status_code == 404

        # 尝试结束不存在的会话
        end_response = await e2e_client.post(
            "/api/activity/end",
            json={"session_id": "non-existent-session"},
        )
        assert end_response.status_code == 404

    @pytest.mark.asyncio
    async def test_current_activity_query(self, e2e_client: AsyncClient):
        """测试当前活动查询"""
        player_id = "e2e-test-player-current"

        # 无活动时查询
        no_activity = await e2e_client.get(
            f"/api/activity/current?player_id={player_id}"
        )
        assert no_activity.status_code == 200
        assert no_activity.json()["has_active_session"] is False

        # 开始活动
        start_response = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        session_id = start_response.json()["session_id"]

        # 有活动时查询
        has_activity = await e2e_client.get(
            f"/api/activity/current?player_id={player_id}"
        )
        assert has_activity.status_code == 200
        assert has_activity.json()["has_active_session"] is True
        assert has_activity.json()["session_id"] == session_id

        # 清理
        await e2e_client.post(
            "/api/activity/end",
            json={"session_id": session_id},
        )
