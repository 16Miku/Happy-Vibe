"""市场系统测试"""

import pytest
from datetime import datetime, timedelta
from src.core.market import MarketManager, market_manager
from src.storage.models import ListingStatus


class TestMarketManager:
    """市场管理器测试"""

    def setup_method(self):
        """每个测试前重置市场"""
        self.manager = MarketManager()

    def test_create_listing_success(self):
        """测试成功创建挂单"""
        result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )
        assert result.success is True
        assert result.listing_id != ""
        assert result.listing_fee > 0

    def test_create_listing_insufficient_gold_for_fee(self):
        """测试金币不足以支付手续费"""
        result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=100,
            unit_price=1000,
            player_gold=1,  # 手续费需要 3000 * 0.03 = 90
        )
        assert result.success is False
        assert "手续费" in result.message

    def test_create_listing_zero_quantity(self):
        """测试数量为零"""
        result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=0,
            unit_price=10,
            player_gold=100,
        )
        assert result.success is False
        assert "数量必须大于 0" in result.message

    def test_create_listing_zero_price(self):
        """测试价格为零"""
        result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=0,
            player_gold=100,
        )
        assert result.success is False
        assert "价格必须大于 0" in result.message

    def test_create_listing_max_limit(self):
        """测试挂单数量上限"""
        # 创建 20 个挂单
        for i in range(20):
            self.manager.create_listing(
                seller_id="player1",
                seller_name="玩家1",
                item_type="seed",
                item_name=f"物品{i}",
                quantity=1,
                unit_price=10,
                player_gold=100,
            )

        # 第 21 个应该失败
        result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="物品20",
            quantity=1,
            unit_price=10,
            player_gold=100,
        )
        assert result.success is False
        assert "上限" in result.message

    def test_get_listings(self):
        """测试获取挂单列表"""
        # 创建几个挂单
        self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )
        self.manager.create_listing(
            seller_id="player2",
            seller_name="玩家2",
            item_type="material",
            item_name="木材",
            quantity=50,
            unit_price=5,
            player_gold=100,
        )

        listings = self.manager.get_listings()
        assert len(listings) == 2

    def test_get_listings_filter_by_item_type(self):
        """测试按物品类型过滤"""
        self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )
        self.manager.create_listing(
            seller_id="player2",
            seller_name="玩家2",
            item_type="material",
            item_name="木材",
            quantity=50,
            unit_price=5,
            player_gold=100,
        )

        listings = self.manager.get_listings(item_type="seed")
        assert len(listings) == 1
        assert listings[0].item_type == "seed"

    def test_get_listings_filter_by_seller(self):
        """测试按卖家过滤"""
        self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )
        self.manager.create_listing(
            seller_id="player2",
            seller_name="玩家2",
            item_type="seed",
            item_name="函数花种子",
            quantity=5,
            unit_price=30,
            player_gold=100,
        )

        listings = self.manager.get_listings(seller_id="player1")
        assert len(listings) == 1
        assert listings[0].seller_id == "player1"

    def test_purchase_listing_success(self):
        """测试成功购买挂单"""
        # 创建挂单
        create_result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )

        # 购买
        result = self.manager.purchase_listing(
            listing_id=create_result.listing_id,
            buyer_id="player2",
            buyer_gold=1000,
        )
        assert result.success is True
        assert result.item_name == "变量草种子"
        assert result.quantity == 10
        assert result.total_cost == 100

    def test_purchase_listing_partial(self):
        """测试部分购买"""
        create_result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )

        result = self.manager.purchase_listing(
            listing_id=create_result.listing_id,
            buyer_id="player2",
            buyer_gold=1000,
            quantity=5,
        )
        assert result.success is True
        assert result.quantity == 5
        assert result.total_cost == 50

        # 检查剩余数量
        listing = self.manager.get_listing(create_result.listing_id)
        assert listing.quantity == 5

    def test_purchase_listing_insufficient_gold(self):
        """测试金币不足"""
        create_result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=100,
            player_gold=100,
        )

        result = self.manager.purchase_listing(
            listing_id=create_result.listing_id,
            buyer_id="player2",
            buyer_gold=100,
        )
        assert result.success is False
        assert "金币不足" in result.message

    def test_purchase_own_listing(self):
        """测试购买自己的挂单"""
        create_result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )

        result = self.manager.purchase_listing(
            listing_id=create_result.listing_id,
            buyer_id="player1",
            buyer_gold=1000,
        )
        assert result.success is False
        assert "自己的挂单" in result.message

    def test_purchase_nonexistent_listing(self):
        """测试购买不存在的挂单"""
        result = self.manager.purchase_listing(
            listing_id="nonexistent",
            buyer_id="player2",
            buyer_gold=1000,
        )
        assert result.success is False
        assert "不存在" in result.message

    def test_cancel_listing_success(self):
        """测试成功取消挂单"""
        create_result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )

        success, message = self.manager.cancel_listing(
            create_result.listing_id, "player1"
        )
        assert success is True

        # 检查状态
        listing = self.manager.get_listing(create_result.listing_id)
        assert listing.status == ListingStatus.CANCELLED.value

    def test_cancel_listing_not_owner(self):
        """测试取消他人挂单"""
        create_result = self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )

        success, message = self.manager.cancel_listing(
            create_result.listing_id, "player2"
        )
        assert success is False
        assert "自己的挂单" in message

    def test_get_market_stats(self):
        """测试获取市场统计"""
        self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )
        self.manager.create_listing(
            seller_id="player2",
            seller_name="玩家2",
            item_type="material",
            item_name="木材",
            quantity=50,
            unit_price=5,
            player_gold=100,
        )

        stats = self.manager.get_market_stats()
        assert stats["total_listings"] == 2
        assert stats["total_value"] == 350  # 100 + 250
        assert stats["unique_sellers"] == 2
        assert len(stats["item_types"]) == 2

    def test_get_player_listings(self):
        """测试获取玩家挂单"""
        self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="变量草种子",
            quantity=10,
            unit_price=10,
            player_gold=100,
        )
        self.manager.create_listing(
            seller_id="player1",
            seller_name="玩家1",
            item_type="material",
            item_name="木材",
            quantity=50,
            unit_price=5,
            player_gold=100,
        )
        self.manager.create_listing(
            seller_id="player2",
            seller_name="玩家2",
            item_type="seed",
            item_name="函数花种子",
            quantity=5,
            unit_price=30,
            player_gold=100,
        )

        listings = self.manager.get_player_listings("player1")
        assert len(listings) == 2


class TestMarketManagerGlobal:
    """全局市场管理器测试"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert market_manager is not None
