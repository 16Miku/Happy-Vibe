"""E2E 验证脚本

手动验证完整数据流的脚本。
运行方式: python scripts/test_e2e.py
"""

import asyncio
import time
from datetime import datetime

import httpx


BASE_URL = "http://127.0.0.1:8765"


async def test_health():
    """测试健康检查"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/health")
        print(f"健康检查: {response.status_code}")
        print(f"  响应: {response.json()}")
        return response.status_code == 200


async def test_full_activity_flow():
    """测试完整活动流程"""
    player_id = f"manual-test-{int(time.time())}"

    async with httpx.AsyncClient() as client:
        # 1. 开始活动
        print("\n1. 开始活动...")
        start_resp = await client.post(
            f"{BASE_URL}/api/activity/start",
            json={"player_id": player_id, "source": "claude_code"},
        )
        if start_resp.status_code != 200:
            print(f"  失败: {start_resp.text}")
            return False

        session_id = start_resp.json()["session_id"]
        print(f"  会话ID: {session_id}")

        # 2. 更新活动
        print("\n2. 更新活动进度...")
        update_resp = await client.post(
            f"{BASE_URL}/api/activity/update",
            json={
                "session_id": session_id,
                "quality": {
                    "success_rate": 0.9,
                    "iteration_count": 3,
                    "lines_changed": 200,
                    "files_affected": 5,
                    "languages": ["python", "gdscript"],
                    "tool_usage": {"read": 15, "write": 10, "bash": 5, "search": 3},
                },
                "last_interaction_gap": 60.0,
            },
        )
        if update_resp.status_code != 200:
            print(f"  失败: {update_resp.text}")
            return False

        update_data = update_resp.json()
        print(f"  持续时长: {update_data['duration_minutes']:.2f} 分钟")
        print(f"  预估能量: {update_data['estimated_energy']}")
        print(f"  心流状态: {update_data['flow_status']['is_active']}")

        # 3. 查询心流状态
        print("\n3. 查询心流状态...")
        flow_resp = await client.get(
            f"{BASE_URL}/api/activity/flow-status",
            params={"player_id": player_id},
        )
        if flow_resp.status_code == 200:
            flow_data = flow_resp.json()
            print(f"  心流激活: {flow_data['is_active']}")
            if flow_data['progress']:
                print("  进度:")
                for key, value in flow_data['progress'].items():
                    print(f"    {key}: {value['current']}/{value['target']} ({value['progress']*100:.0f}%)")

        # 4. 结束活动
        print("\n4. 结束活动...")
        end_resp = await client.post(
            f"{BASE_URL}/api/activity/end",
            json={
                "session_id": session_id,
                "quality": {
                    "success_rate": 0.9,
                    "iteration_count": 3,
                    "lines_changed": 200,
                    "files_affected": 5,
                    "languages": ["python", "gdscript"],
                    "tool_usage": {"read": 15, "write": 10, "bash": 5, "search": 3},
                },
            },
        )
        if end_resp.status_code != 200:
            print(f"  失败: {end_resp.text}")
            return False

        end_data = end_resp.json()
        reward = end_data["reward"]
        print(f"  持续时长: {end_data['duration_minutes']:.2f} 分钟")
        print(f"  心流状态: {end_data['was_in_flow']}")
        print(f"  奖励:")
        print(f"    Vibe能量: {reward['vibe_energy']}")
        print(f"    经验值: {reward['experience']}")
        print(f"    代码精华: {reward['code_essence']}")
        print(f"  能量分解:")
        breakdown = reward["breakdown"]
        print(f"    基础能量: {breakdown['base']}")
        print(f"    时间加成: {breakdown['time_bonus']:.2f}x")
        print(f"    质量加成: {breakdown['quality_bonus']:.2f}x")
        print(f"    连续签到: {breakdown['streak_bonus']:.2f}x")
        print(f"    心流加成: {breakdown['flow_bonus']:.2f}x")

        # 5. 查询历史记录
        print("\n5. 查询活动历史...")
        history_resp = await client.get(
            f"{BASE_URL}/api/activity/history",
            params={"player_id": player_id},
        )
        if history_resp.status_code == 200:
            history_data = history_resp.json()
            print(f"  总记录数: {history_data['total']}")
            if history_data['items']:
                latest = history_data['items'][0]
                print(f"  最新记录:")
                print(f"    来源: {latest['source']}")
                print(f"    能量: {latest['energy_earned']}")
                print(f"    经验: {latest['exp_earned']}")

        return True


async def test_performance():
    """测试 API 性能"""
    print("\n性能测试...")

    async with httpx.AsyncClient() as client:
        # 测试健康检查响应时间
        times = []
        for _ in range(10):
            start = time.perf_counter()
            await client.get(f"{BASE_URL}/api/health")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        print(f"  健康检查 API:")
        print(f"    平均响应时间: {avg_time:.2f}ms")
        print(f"    最大响应时间: {max_time:.2f}ms")
        print(f"    达标 (<100ms): {'是' if avg_time < 100 else '否'}")

        return avg_time < 100


async def main():
    """主函数"""
    print("=" * 60)
    print("Happy Vibe E2E 验证")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: {BASE_URL}")
    print("=" * 60)

    results = {}

    # 健康检查
    print("\n[测试 1] 健康检查")
    results["健康检查"] = await test_health()

    # 完整活动流程
    print("\n[测试 2] 完整活动流程")
    results["活动流程"] = await test_full_activity_flow()

    # 性能测试
    print("\n[测试 3] 性能测试")
    results["性能测试"] = await test_performance()

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")

    all_passed = all(results.values())
    print("\n" + ("全部测试通过!" if all_passed else "存在失败的测试"))

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
