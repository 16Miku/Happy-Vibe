"""经济平衡系统测试"""

import pytest
from datetime import datetime
from src.core.economy import EconomyController, EconomySnapshot, economy_controller


class TestEconomyController:
    """经济控制器测试"""

    def setup_method(self):
        """每个测试前重置控制器"""
        self.controller = EconomyController()

    def test_initial_rates(self):
        """测试初始费率"""
        assert self.controller.tax_rate == 0.03
        assert self.controller.listing_fee_rate == 0.03
        assert self.controller.auction_fee_rate == 0.05
        assert self.controller.npc_price_modifier == 1.0
        assert self.controller.reward_modifier == 1.0

    def test_calculate_listing_fee(self):
        """测试计算挂单手续费"""
        fee = self.controller.calculate_listing_fee(1000)
        assert fee == 30  # 3%

    def test_calculate_listing_fee_minimum(self):
        """测试挂单手续费最小值"""
        fee = self.controller.calculate_listing_fee(10)
        assert fee >= 1

    def test_calculate_auction_fee(self):
        """测试计算拍卖手续费"""
        fee = self.controller.calculate_auction_fee(1000)
        assert fee == 50  # 5%

    def test_calculate_transaction_tax(self):
        """测试计算交易税"""
        tax = self.controller.calculate_transaction_tax(1000)
        assert tax == 30  # 3%

    def test_monitor_economy_health_basic(self):
        """测试基础经济监控"""
        snapshot = self.controller.monitor_economy_health(
            total_money_supply=100000,
            player_count=100,
            transaction_volume=500,
        )

        assert snapshot.total_money_supply == 100000
        assert snapshot.avg_player_wealth == 1000
        assert snapshot.transaction_volume == 500
        assert snapshot.inflation_rate == 0.0
        assert 0 <= snapshot.health_score <= 100

    def test_monitor_economy_health_with_inflation(self):
        """测试带通胀的经济监控"""
        snapshot = self.controller.monitor_economy_health(
            total_money_supply=110000,
            player_count=100,
            transaction_volume=500,
            previous_money_supply=100000,
        )

        assert snapshot.inflation_rate == 0.1  # 10% 通胀

    def test_monitor_economy_health_with_deflation(self):
        """测试带通缩的经济监控"""
        snapshot = self.controller.monitor_economy_health(
            total_money_supply=90000,
            player_count=100,
            transaction_volume=500,
            previous_money_supply=100000,
        )

        assert snapshot.inflation_rate == -0.1  # 10% 通缩

    def test_health_score_high_inflation(self):
        """测试高通胀时健康度下降"""
        snapshot = self.controller.monitor_economy_health(
            total_money_supply=150000,
            player_count=100,
            transaction_volume=500,
            previous_money_supply=100000,
        )

        # 50% 通胀应该大幅降低健康度
        assert snapshot.health_score <= 70

    def test_health_score_active_trading(self):
        """测试活跃交易时健康度提升"""
        snapshot = self.controller.monitor_economy_health(
            total_money_supply=100000,
            player_count=100,
            transaction_volume=1000,  # 每人 10 笔交易
        )

        # 活跃交易应该提升健康度
        assert snapshot.health_score >= 100

    def test_health_score_inactive_trading(self):
        """测试不活跃交易时健康度下降"""
        snapshot = self.controller.monitor_economy_health(
            total_money_supply=100000,
            player_count=100,
            transaction_volume=10,  # 每人 0.1 笔交易
        )

        # 不活跃交易应该降低健康度
        assert snapshot.health_score < 100

    def test_adjust_economy_high_inflation(self):
        """测试高通胀时的调整"""
        snapshot = EconomySnapshot(
            total_money_supply=150000,
            avg_player_wealth=1500,
            transaction_volume=500,
            inflation_rate=0.15,  # 15% 通胀
            health_score=60,
            recorded_at=datetime.utcnow(),
        )

        adjustments = self.controller.adjust_economy(snapshot)

        assert adjustments["policy"] == "tightening"
        assert self.controller.tax_rate > 0.03  # 税率提高
        assert self.controller.npc_price_modifier < 1.0  # NPC 收购价降低
        assert self.controller.reward_modifier < 1.0  # 奖励降低

    def test_adjust_economy_deflation(self):
        """测试通缩时的调整"""
        snapshot = EconomySnapshot(
            total_money_supply=90000,
            avg_player_wealth=900,
            transaction_volume=500,
            inflation_rate=-0.1,  # 10% 通缩
            health_score=70,
            recorded_at=datetime.utcnow(),
        )

        adjustments = self.controller.adjust_economy(snapshot)

        assert adjustments["policy"] == "easing"
        assert self.controller.tax_rate < 0.03  # 税率降低
        assert self.controller.npc_price_modifier > 1.0  # NPC 收购价提高
        assert self.controller.reward_modifier > 1.0  # 奖励提高

    def test_adjust_economy_stable(self):
        """测试稳定经济时的调整"""
        # 先设置一些偏离值
        self.controller._current_tax_rate = 0.05
        self.controller._npc_price_modifier = 0.8

        snapshot = EconomySnapshot(
            total_money_supply=100000,
            avg_player_wealth=1000,
            transaction_volume=500,
            inflation_rate=0.02,  # 2% 轻微通胀
            health_score=90,
            recorded_at=datetime.utcnow(),
        )

        adjustments = self.controller.adjust_economy(snapshot)

        assert adjustments["policy"] == "stable"
        # 费率应该向基准靠拢
        assert self.controller.tax_rate < 0.05

    def test_tax_rate_bounds(self):
        """测试税率边界"""
        # 多次提高税率
        for _ in range(20):
            self.controller._increase_tax_rate(0.01)

        assert self.controller.tax_rate <= 0.1  # 最高 10%

        # 多次降低税率
        for _ in range(20):
            self.controller._decrease_tax_rate(0.01)

        assert self.controller.tax_rate >= 0.01  # 最低 1%

    def test_npc_price_modifier_bounds(self):
        """测试 NPC 价格修正边界"""
        # 多次降低
        for _ in range(20):
            self.controller._reduce_npc_sell_price(0.1)

        assert self.controller.npc_price_modifier >= 0.5

        # 多次提高
        for _ in range(20):
            self.controller._increase_npc_sell_price(0.1)

        assert self.controller.npc_price_modifier <= 1.5

    def test_reward_modifier_bounds(self):
        """测试奖励修正边界"""
        # 多次降低
        for _ in range(20):
            self.controller._reduce_rewards(0.1)

        assert self.controller.reward_modifier >= 0.5

        # 多次提高
        for _ in range(20):
            self.controller._increase_rewards(0.1)

        assert self.controller.reward_modifier <= 2.0

    def test_get_economy_status(self):
        """测试获取经济状态"""
        # 先记录一些数据
        self.controller.monitor_economy_health(
            total_money_supply=100000,
            player_count=100,
            transaction_volume=500,
        )

        status = self.controller.get_economy_status()

        assert "tax_rate" in status
        assert "listing_fee_rate" in status
        assert "auction_fee_rate" in status
        assert "npc_price_modifier" in status
        assert "reward_modifier" in status
        assert "latest_snapshot" in status
        assert status["latest_snapshot"]["total_money_supply"] == 100000

    def test_get_economy_status_no_history(self):
        """测试无历史时获取经济状态"""
        status = self.controller.get_economy_status()

        assert status["latest_snapshot"]["total_money_supply"] == 0
        assert status["latest_snapshot"]["recorded_at"] is None

    def test_get_history(self):
        """测试获取历史记录"""
        # 记录多条数据
        for i in range(5):
            self.controller.monitor_economy_health(
                total_money_supply=100000 + i * 1000,
                player_count=100,
                transaction_volume=500,
            )

        history = self.controller.get_history(limit=3)

        assert len(history) == 3
        # 应该是最近的 3 条
        assert history[-1]["total_money_supply"] == 104000

    def test_history_limit(self):
        """测试历史记录限制"""
        # 记录超过 100 条
        for i in range(150):
            self.controller.monitor_economy_health(
                total_money_supply=100000 + i,
                player_count=100,
                transaction_volume=500,
            )

        # 内部应该只保留 100 条
        assert len(self.controller._history) == 100

    def test_normalize_rates(self):
        """测试费率正常化"""
        # 设置偏离值
        self.controller._current_tax_rate = 0.08
        self.controller._current_listing_fee_rate = 0.08
        self.controller._npc_price_modifier = 0.7
        self.controller._reward_modifier = 1.5

        # 多次正常化
        for _ in range(20):
            self.controller._normalize_rates()

        # 应该接近基准值
        assert abs(self.controller._current_tax_rate - 0.03) < 0.01
        assert abs(self.controller._npc_price_modifier - 1.0) < 0.1
        assert abs(self.controller._reward_modifier - 1.0) < 0.1


class TestEconomyControllerGlobal:
    """全局经济控制器测试"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert economy_controller is not None

    def test_global_instance_has_default_rates(self):
        """测试全局实例有默认费率"""
        assert economy_controller.tax_rate > 0
        assert economy_controller.listing_fee_rate > 0
        assert economy_controller.auction_fee_rate > 0
