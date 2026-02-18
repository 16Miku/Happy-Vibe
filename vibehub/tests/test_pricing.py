"""动态定价引擎测试"""

import pytest
from datetime import datetime
from unittest.mock import patch
from src.core.pricing import DynamicPricingEngine, pricing_engine


class TestDynamicPricingEngine:
    """动态定价引擎测试"""

    def setup_method(self):
        """每个测试前重置引擎"""
        self.engine = DynamicPricingEngine()

    def test_calculate_price_base(self):
        """测试基础价格计算"""
        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=50,
            max_stock=100,
        )
        # 供需平衡时价格接近基础价格
        assert 80 <= price <= 120

    def test_calculate_price_low_stock(self):
        """测试低库存时价格上涨"""
        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=10,
            max_stock=100,
        )
        # 库存低时价格应该上涨
        assert price > 100

    def test_calculate_price_high_stock(self):
        """测试高库存时价格下降"""
        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=90,
            max_stock=100,
        )
        # 库存高时价格应该下降或持平
        assert price <= 100

    def test_calculate_price_very_low_stock(self):
        """测试极低库存时价格大幅上涨"""
        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=5,
            max_stock=100,
        )
        # 严重供不应求，价格应该大幅上涨
        assert price >= 130

    def test_calculate_price_oversupply(self):
        """测试供过于求时价格下降"""
        # 模拟供过于求
        self.engine.update_supply_data("test_item", 3.0)
        self.engine.update_demand_data("test_item", 1.0)

        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
        )
        # 供过于求，价格应该下降
        assert price < 100

    def test_calculate_price_min_bound(self):
        """测试价格下限"""
        # 极端供过于求
        self.engine.update_supply_data("test_item", 10.0)
        self.engine.update_demand_data("test_item", 1.0)
        self.engine.update_trend_data("test_item", -1.0)

        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
        )
        # 价格不应低于基础价格的 50%
        assert price >= 50

    def test_calculate_price_max_bound(self):
        """测试价格上限"""
        # 极端供不应求
        self.engine.update_supply_data("test_item", 0.1)
        self.engine.update_demand_data("test_item", 10.0)
        self.engine.update_trend_data("test_item", 1.0)

        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
        )
        # 价格不应高于基础价格的 200%
        assert price <= 200

    def test_calculate_price_minimum_one(self):
        """测试价格最小为 1"""
        price = self.engine.calculate_price(
            base_price=1,
            item_name="test_item",
            current_stock=100,
            max_stock=100,
        )
        assert price >= 1

    @patch.object(DynamicPricingEngine, '_is_weekend', return_value=True)
    def test_calculate_price_weekend_discount(self, mock_weekend):
        """测试周末折扣"""
        price_weekend = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=50,
            max_stock=100,
        )

        mock_weekend.return_value = False
        price_weekday = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=50,
            max_stock=100,
        )

        # 周末价格应该更低
        assert price_weekend <= price_weekday

    def test_calculate_price_event_discount(self):
        """测试活动折扣"""
        # 无活动时的价格
        price_no_event = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=50,
            max_stock=100,
        )

        # 添加活动
        self.engine.add_active_event("spring_sale")

        price_with_event = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=50,
            max_stock=100,
        )

        # 活动期间价格应该更低
        assert price_with_event <= price_no_event

        # 移除活动
        self.engine.remove_active_event("spring_sale")

    def test_update_trend_data(self):
        """测试更新趋势数据"""
        self.engine.update_trend_data("test_item", 0.5)
        assert self.engine._trend_cache["test_item"] == 0.5

        # 测试边界限制
        self.engine.update_trend_data("test_item", 2.0)
        assert self.engine._trend_cache["test_item"] == 1.0

        self.engine.update_trend_data("test_item", -2.0)
        assert self.engine._trend_cache["test_item"] == -1.0

    def test_market_trend_positive(self):
        """测试正向市场趋势"""
        self.engine.update_trend_data("test_item", 1.0)

        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=50,
            max_stock=100,
        )
        # 正向趋势应该提高价格
        assert price > 100

    def test_market_trend_negative(self):
        """测试负向市场趋势"""
        self.engine.update_trend_data("test_item", -1.0)

        # 使用供需平衡的库存（80%以上），避免供需因子干扰
        price = self.engine.calculate_price(
            base_price=100,
            item_name="test_item",
            current_stock=85,
            max_stock=100,
        )
        # 负向趋势应该降低价格（供需平衡时 multiplier=1.0，trend=-1.0 时 multiplier=0.9）
        assert price < 100

    def test_get_all_shop_base_prices(self):
        """测试获取所有商店基础价格"""
        prices = self.engine.get_all_shop_base_prices()

        assert "seed_shop" in prices
        assert "material_shop" in prices
        assert "alchemy_shop" in prices
        assert "gift_shop" in prices

        # 检查种子店价格
        assert "variable_grass_seed" in prices["seed_shop"]
        assert prices["seed_shop"]["variable_grass_seed"] == 5

    def test_calculate_bulk_discount_no_discount(self):
        """测试批量购买无折扣"""
        total = self.engine.calculate_bulk_discount(
            base_price=10,
            quantity=5,
            discount_threshold=10,
        )
        assert total == 50  # 无折扣

    def test_calculate_bulk_discount_small(self):
        """测试批量购买小折扣"""
        total = self.engine.calculate_bulk_discount(
            base_price=10,
            quantity=10,
            discount_threshold=10,
        )
        # 5% 折扣
        assert total == 95

    def test_calculate_bulk_discount_medium(self):
        """测试批量购买中等折扣"""
        total = self.engine.calculate_bulk_discount(
            base_price=10,
            quantity=20,
            discount_threshold=10,
        )
        # 8% 折扣
        assert total == 184

    def test_calculate_bulk_discount_large(self):
        """测试批量购买大折扣"""
        total = self.engine.calculate_bulk_discount(
            base_price=10,
            quantity=50,
            discount_threshold=10,
        )
        # 15% 折扣
        assert total == 425

    def test_supply_demand_multiplier_balanced(self):
        """测试供需平衡时的乘数"""
        multiplier = self.engine._get_supply_demand_multiplier(1.0)
        assert multiplier == 1.0

    def test_supply_demand_multiplier_oversupply(self):
        """测试供过于求时的乘数"""
        multiplier = self.engine._get_supply_demand_multiplier(2.5)
        assert multiplier == 0.7  # 降价 30%

    def test_supply_demand_multiplier_undersupply(self):
        """测试供不应求时的乘数"""
        multiplier = self.engine._get_supply_demand_multiplier(0.2)
        assert multiplier == 1.5  # 涨价 50%

    def test_add_remove_event(self):
        """测试添加和移除活动"""
        assert len(self.engine._active_events) == 0

        self.engine.add_active_event("event1")
        assert "event1" in self.engine._active_events

        # 重复添加不应增加
        self.engine.add_active_event("event1")
        assert self.engine._active_events.count("event1") == 1

        self.engine.remove_active_event("event1")
        assert "event1" not in self.engine._active_events

        # 移除不存在的活动不应报错
        self.engine.remove_active_event("nonexistent")


class TestPricingEngineGlobal:
    """全局定价引擎测试"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert pricing_engine is not None

    def test_global_instance_has_prices(self):
        """测试全局实例有价格数据"""
        prices = pricing_engine.get_all_shop_base_prices()
        assert len(prices) > 0
