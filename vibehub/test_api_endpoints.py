"""API 端点测试脚本

系统测试所有 VibeHub API 端点并记录结果。
"""

import requests
import json
from typing import Dict, List
from datetime import datetime

BASE_URL = "http://127.0.0.1:8765"

# 测试玩家ID（使用之前创建的）
PLAYER_ID = "0714f0dd-7a8e-4aa2-941b-845be0180136"


class APITester:
    """API 测试器"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results: List[Dict] = []
        self.session = requests.Session()

    def test_endpoint(
        self, method: str, path: str, name: str, **kwargs
    ) -> Dict:
        """测试单个端点"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, timeout=5, **kwargs)
            success = response.status_code < 400
            return {
                "name": name,
                "method": method,
                "path": path,
                "status": response.status_code,
                "success": success,
                "error": None,
            }
        except Exception as e:
            return {
                "name": name,
                "method": method,
                "path": path,
                "status": 0,
                "success": False,
                "error": str(e),
            }

    def print_results(self):
        """打印测试结果"""
        print("\n" + "=" * 80)
        print("API 测试结果报告".center(76))
        print("=" * 80)
        print(f"{'端点名称':<20} {'方法':<8} {'路径':<30} {'状态':<8} {'结果'}")
        print("-" * 80)

        for result in self.results:
            status = result["status"]
            if result["success"]:
                status_str = f"[{status}]"
                result_str = "[成功]"
            else:
                status_str = f"[{status}]"
                result_str = "[失败]"

            print(
                f"{result['name']:<20} {result['method']:<8} {result['path']:<30} "
                f"{status_str:<8} {result_str}"
            )

            if result.get("error"):
                print(f"  错误: {result['error']}")

        print("-" * 80)
        success_count = sum(1 for r in self.results if r["success"])
        total_count = len(self.results)
        print(f"总计: {success_count}/{total_count} 个端点测试通过")
        print("=" * 80 + "\n")

    def run_tests(self):
        """运行所有测试"""
        print("开始测试 VibeHub API 端点...")
        print(f"基础 URL: {self.base_url}")
        print(f"测试玩家 ID: {PLAYER_ID}\n")

        # 1. 健康检查
        self.results.append(
            self.test_endpoint("GET", "/api/health", "健康检查")
        )

        # 2. 玩家管理
        self.results.append(
            self.test_endpoint("GET", "/api/player", "获取玩家列表")
        )
        self.results.append(
            self.test_endpoint(
                "POST",
                "/api/player",
                "创建玩家",
                json={"username": "test_player_2"},
            )
        )
        self.results.append(
            self.test_endpoint(
                "GET",
                f"/api/player/{PLAYER_ID}",
                "获取玩家详情",
            )
        )

        # 3. 编码活动
        self.results.append(
            self.test_endpoint(
                "GET",
                f"/api/activity/current?player_id={PLAYER_ID}",
                "获取当前活动",
            )
        )

        # 4. 农场系统
        self.results.append(
            self.test_endpoint(
                "GET", f"/api/farm?player_id={PLAYER_ID}", "获取农场"
            )
        )
        self.results.append(
            self.test_endpoint("GET", f"/api/farm/crops?player_id={PLAYER_ID}", "获取作物配置")
        )

        # 5. 成就系统
        self.results.append(
            self.test_endpoint(
                "GET",
                f"/api/achievements/player?player_id={PLAYER_ID}",
                "获取玩家成就",
            )
        )

        # 6. 能量系统
        self.results.append(
            self.test_endpoint(
                "GET",
                f"/api/energy/status?player_id={PLAYER_ID}",
                "获取能量状态",
            )
        )

        # 7. 签到系统
        self.results.append(
            self.test_endpoint(
                "GET",
                f"/api/check-in/status?player_id={PLAYER_ID}",
                "获取签到状态",
            )
        )

        # 8. 商店系统
        self.results.append(
            self.test_endpoint(
                "GET", f"/api/shops/items?player_id={PLAYER_ID}", "获取商店物品"
            )
        )

        # 9. 市场系统
        self.results.append(
            self.test_endpoint(
                "GET",
                f"/api/market/listings?player_id={PLAYER_ID}",
                "获取市场列表",
            )
        )

        # 10. 拍卖系统
        self.results.append(
            self.test_endpoint("GET", f"/api/auctions?player_id={PLAYER_ID}", "获取拍卖列表")
        )

        # 11. 经济系统
        self.results.append(
            self.test_endpoint(
                "GET",
                f"/api/economy/metrics?player_id={PLAYER_ID}",
                "获取经济指标",
            )
        )

        # 12. 排行榜
        self.results.append(
            self.test_endpoint("GET", "/api/leaderboards?level=all", "获取排行榜")
        )

        # 打印结果
        self.print_results()

        # 保存结果到文件
        self.save_results()

    def save_results(self):
        """保存测试结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"api_test_results_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "base_url": self.base_url,
                    "player_id": PLAYER_ID,
                    "results": self.results,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"\n测试结果已保存到: {filename}")


if __name__ == "__main__":
    tester = APITester(BASE_URL)
    tester.run_tests()
