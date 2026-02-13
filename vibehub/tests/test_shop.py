"""商店系统测试"""

import pytest
from src.core.shop import ShopManager, shop_manager
from src.storage.models import ShopType


class TestShopManager:
    """商店管理器测试"""

    def setup_method(self):
        """每个测试前重置商店"""
        self.manager = ShopManager()

    def test_get_all_shops(self):
        """测试获取所有商店列表"""
        shops = self.manager.get_all_shops()
        assert len(shops) == 4
        shop_types = [s["shop_type"] for s in shops]
        assert ShopType.SEED_SHOP.value in shop_types
        assert ShopType.MATERIAL_SHOP.value in shop_types
        assert ShopType.ALCHEMY_SHOP.value in shop_types
        assert ShopType.GIFT_SHOP.value in shop_types

    def test_get_shop_items_seed_shop(self):
        """测试获取种子店商品"""
        items = self.manager.get_shop_items(ShopType.SEED_SHOP.value)
        assert len(items) == 8
        item_names = [i.item_name for i in items]
        assert "变量草种子" in item_names
        assert "AI神花种子" in item_names

    def test_get_shop_items_invalid_shop(self):
        """测试获取不存在的商店"""
        items = self.manager.get_shop_items("invalid_shop")
        assert items == []

    def test_get_shop_info(self):
        """测试获取商店详情"""
        info = self.manager.get_shop_info(ShopType.SEED_SHOP.value)
        assert info is not None
        assert info["shop_type"] == ShopType.SEED_SHOP.value
        assert info["name"] == "种子店"
        assert "items" in info
        assert len(info["items"]) == 8

    def test_get_shop_info_invalid(self):
        """测试获取不存在的商店详情"""
        info = self.manager.get_shop_info("invalid_shop")
        assert info is None

    def test_buy_item_success(self):
        """测试成功购买商品"""
        result = self.manager.buy_item(
            shop_type=ShopType.SEED_SHOP.value,
            item_id="variable_grass_seed",
            quantity=5,
            player_gold=1000,
        )
        assert result.success is True
        assert result.item_name == "变量草种子"
        assert result.quantity == 5
        assert result.total_cost > 0
        assert result.remaining_gold < 1000

    def test_buy_item_insufficient_gold(self):
        """测试金币不足"""
        result = self.manager.buy_item(
            shop_type=ShopType.SEED_SHOP.value,
            item_id="ai_divine_flower_seed",
            quantity=3,  # 库存只有 5，购买 3 个确保不触发库存不足
            player_gold=100,  # 价格 500*3=1500，金币不足
        )
        assert result.success is False
        assert "金币不足" in result.message

    def test_buy_item_insufficient_stock(self):
        """测试库存不足"""
        result = self.manager.buy_item(
            shop_type=ShopType.SEED_SHOP.value,
            item_id="ai_divine_flower_seed",
            quantity=100,
            player_gold=100000,
        )
        assert result.success is False
        assert "库存不足" in result.message

    def test_buy_item_invalid_shop(self):
        """测试购买不存在的商店"""
        result = self.manager.buy_item(
            shop_type="invalid_shop",
            item_id="variable_grass_seed",
            quantity=1,
            player_gold=1000,
        )
        assert result.success is False
        assert "商店不存在" in result.message

    def test_buy_item_invalid_item(self):
        """测试购买不存在的商品"""
        result = self.manager.buy_item(
            shop_type=ShopType.SEED_SHOP.value,
            item_id="invalid_item",
            quantity=1,
            player_gold=1000,
        )
        assert result.success is False
        assert "物品不存在" in result.message

    def test_buy_item_zero_quantity(self):
        """测试购买数量为零"""
        result = self.manager.buy_item(
            shop_type=ShopType.SEED_SHOP.value,
            item_id="variable_grass_seed",
            quantity=0,
            player_gold=1000,
        )
        assert result.success is False
        assert "数量必须大于 0" in result.message

    def test_buy_reduces_stock(self):
        """测试购买后库存减少"""
        items_before = self.manager.get_shop_items(ShopType.SEED_SHOP.value)
        stock_before = next(
            i.stock for i in items_before if i.item_id == "variable_grass_seed"
        )

        self.manager.buy_item(
            shop_type=ShopType.SEED_SHOP.value,
            item_id="variable_grass_seed",
            quantity=5,
            player_gold=1000,
        )

        items_after = self.manager.get_shop_items(ShopType.SEED_SHOP.value)
        stock_after = next(
            i.stock for i in items_after if i.item_id == "variable_grass_seed"
        )

        assert stock_after == stock_before - 5

    def test_refresh_shop(self):
        """测试刷新商店"""
        # 先购买一些商品
        self.manager.buy_item(
            shop_type=ShopType.SEED_SHOP.value,
            item_id="variable_grass_seed",
            quantity=10,
            player_gold=1000,
        )

        # 强制刷新
        success = self.manager.refresh_shop(ShopType.SEED_SHOP.value, force=True)
        assert success is True

        # 检查库存恢复
        items = self.manager.get_shop_items(ShopType.SEED_SHOP.value)
        stock = next(
            i.stock for i in items if i.item_id == "variable_grass_seed"
        )
        assert stock == 99  # 恢复到最大库存

    def test_refresh_invalid_shop(self):
        """测试刷新不存在的商店"""
        success = self.manager.refresh_shop("invalid_shop", force=True)
        assert success is False

    def test_sell_to_npc(self):
        """测试向 NPC 出售物品"""
        gold = self.manager.sell_to_npc(
            item_id="variable_grass",
            item_name="变量草",
            quantity=10,
            base_value=10,
        )
        # NPC 收购价为基础价值的 50%
        assert gold == 50  # 10 * 10 * 0.5


class TestShopManagerGlobal:
    """全局商店管理器测试"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert shop_manager is not None

    def test_global_instance_has_shops(self):
        """测试全局实例有商店"""
        shops = shop_manager.get_all_shops()
        assert len(shops) > 0
