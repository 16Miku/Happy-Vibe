"""性能测试

验证系统性能指标：
1. API 响应时间 < 100ms
2. 并发处理稳定
3. 内存使用正常
"""

import asyncio
import statistics
import time
from typing import List

import pytest
from httpx import AsyncClient


class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_api_response_time(self, e2e_client: AsyncClient):
        """测试 API 响应时间

        目标：响应时间 < 100ms
        """
        response_times: List[float] = []

        # 测试健康检查端点（10次）
        for _ in range(10):
            start = time.perf_counter()
            response = await e2e_client.get("/api/health")
            elapsed = (time.perf_counter() - start) * 1000  # 转换为毫秒
            response_times.append(elapsed)
            assert response.status_code == 200

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]

        print(f"\n健康检查 API 响应时间:")
        print(f"  平均: {avg_time:.2f}ms")
        print(f"  最大: {max_time:.2f}ms")
        print(f"  P95: {p95_time:.2f}ms")

        assert avg_time < 100, f"平均响应时间 {avg_time:.2f}ms 超过 100ms"

    @pytest.mark.asyncio
    async def test_activity_api_response_time(self, e2e_client: AsyncClient):
        """测试活动 API 响应时间"""
        response_times = {"start": [], "update": [], "end": []}

        for i in range(5):
            player_id = f"perf-test-player-{i}-{time.time_ns()}"

            # 测试开始活动
            start_time = time.perf_counter()
            start_resp = await e2e_client.post(
                "/api/activity/start",
                json={"player_id": player_id, "source": "claude_code"},
            )
            response_times["start"].append((time.perf_counter() - start_time) * 1000)
            session_id = start_resp.json()["session_id"]

            # 测试更新活动
            start_time = time.perf_counter()
            await e2e_client.post(
                "/api/activity/update",
                json={
                    "session_id": session_id,
                    "quality": {
                        "success_rate": 0.8,
                        "iteration_count": 3,
                        "lines_changed": 100,
                        "files_affected": 3,
                        "languages": ["python"],
                        "tool_usage": {"read": 5, "write": 3, "bash": 2, "search": 1},
                    },
                },
            )
            response_times["update"].append((time.perf_counter() - start_time) * 1000)

            # 测试结束活动
            start_time = time.perf_counter()
            await e2e_client.post(
                "/api/activity/end",
                json={"session_id": session_id},
            )
            response_times["end"].append((time.perf_counter() - start_time) * 1000)

        print("\n活动 API 响应时间:")
        for endpoint, times in response_times.items():
            avg = statistics.mean(times)
            print(f"  {endpoint}: 平均 {avg:.2f}ms")
            assert avg < 100, f"{endpoint} 平均响应时间 {avg:.2f}ms 超过 100ms"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, e2e_client: AsyncClient):
        """测试并发请求处理

        同时发起多个请求，验证系统稳定性
        """
        num_concurrent = 10

        async def make_request(player_id: str) -> tuple[int, float]:
            """发起一个完整的活动请求"""
            start_time = time.perf_counter()

            # 开始活动
            start_resp = await e2e_client.post(
                "/api/activity/start",
                json={"player_id": player_id, "source": "claude_code"},
            )
            if start_resp.status_code != 200:
                return start_resp.status_code, 0

            session_id = start_resp.json()["session_id"]

            # 结束活动
            end_resp = await e2e_client.post(
                "/api/activity/end",
                json={"session_id": session_id},
            )

            elapsed = (time.perf_counter() - start_time) * 1000
            return end_resp.status_code, elapsed

        # 并发执行（使用唯一的 player_id）
        tasks = [
            make_request(f"concurrent-player-{i}-{time.time_ns()}") for i in range(num_concurrent)
        ]
        results = await asyncio.gather(*tasks)

        # 统计结果
        success_count = sum(1 for status, _ in results if status == 200)
        response_times = [elapsed for _, elapsed in results if elapsed > 0]

        print(f"\n并发测试结果 ({num_concurrent} 个请求):")
        print(f"  成功率: {success_count}/{num_concurrent}")
        if response_times:
            print(f"  平均响应时间: {statistics.mean(response_times):.2f}ms")
            print(f"  最大响应时间: {max(response_times):.2f}ms")

        assert success_count == num_concurrent, f"并发请求失败: {num_concurrent - success_count} 个"

    @pytest.mark.asyncio
    async def test_energy_calculation_performance(self, e2e_client: AsyncClient):
        """测试能量计算性能

        验证复杂能量计算的响应时间
        """
        response_times: List[float] = []

        for i in range(10):
            player_id = f"energy-perf-test-{i}-{time.time_ns()}"

            # 开始活动
            start_resp = await e2e_client.post(
                "/api/activity/start",
                json={"player_id": player_id, "source": "claude_code"},
            )
            session_id = start_resp.json()["session_id"]

            # 复杂质量指标
            complex_quality = {
                "success_rate": 0.95,
                "iteration_count": 2,
                "lines_changed": 500,
                "files_affected": 20,
                "languages": ["python", "typescript", "gdscript", "rust", "go"],
                "tool_usage": {"read": 50, "write": 40, "bash": 30, "search": 20},
            }

            # 测试结束活动（包含能量计算）
            start_time = time.perf_counter()
            await e2e_client.post(
                "/api/activity/end",
                json={"session_id": session_id, "quality": complex_quality},
            )
            elapsed = (time.perf_counter() - start_time) * 1000
            response_times.append(elapsed)

        avg_time = statistics.mean(response_times)
        print(f"\n能量计算性能:")
        print(f"  平均响应时间: {avg_time:.2f}ms")
        print(f"  最大响应时间: {max(response_times):.2f}ms")

        assert avg_time < 100, f"能量计算平均响应时间 {avg_time:.2f}ms 超过 100ms"


class TestStressTest:
    """压力测试"""

    @pytest.mark.asyncio
    async def test_rapid_activity_cycles(self, e2e_client: AsyncClient):
        """测试快速活动周期

        快速连续开始和结束活动，验证系统稳定性
        """
        num_cycles = 20
        success_count = 0

        for i in range(num_cycles):
            player_id = f"rapid-cycle-player-{i}-{time.time_ns()}"

            # 开始活动
            start_resp = await e2e_client.post(
                "/api/activity/start",
                json={"player_id": player_id, "source": "claude_code"},
            )
            if start_resp.status_code != 200:
                continue

            session_id = start_resp.json()["session_id"]

            # 立即结束
            end_resp = await e2e_client.post(
                "/api/activity/end",
                json={"session_id": session_id},
            )
            if end_resp.status_code == 200:
                success_count += 1

        print(f"\n快速周期测试: {success_count}/{num_cycles} 成功")
        assert success_count == num_cycles, f"快速周期测试失败: {num_cycles - success_count} 个"

    @pytest.mark.asyncio
    async def test_multiple_updates(self, e2e_client: AsyncClient):
        """测试多次更新

        单个活动多次更新，验证状态管理稳定性
        """
        player_id = "multi-update-player"

        # 开始活动
        start_resp = await e2e_client.post(
            "/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        session_id = start_resp.json()["session_id"]

        # 多次更新
        update_count = 50
        success_count = 0

        for i in range(update_count):
            update_resp = await e2e_client.post(
                "/api/activity/update",
                json={
                    "session_id": session_id,
                    "quality": {
                        "success_rate": 0.5 + (i / update_count) * 0.5,
                        "iteration_count": i + 1,
                        "lines_changed": i * 10,
                        "files_affected": min(i, 20),
                        "languages": ["python"],
                        "tool_usage": {
                            "read": i,
                            "write": i,
                            "bash": i // 2,
                            "search": i // 3,
                        },
                    },
                    "last_interaction_gap": 30.0,
                },
            )
            if update_resp.status_code == 200:
                success_count += 1

        # 结束活动
        await e2e_client.post(
            "/api/activity/end",
            json={"session_id": session_id},
        )

        print(f"\n多次更新测试: {success_count}/{update_count} 成功")
        assert success_count == update_count, f"多次更新测试失败"
