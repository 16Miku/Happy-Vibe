"""拍卖系统测试"""

import pytest
from datetime import datetime, timedelta
from src.core.auction import AuctionManager, auction_manager
from src.storage.models import AuctionStatus


class TestAuctionManager:
    """拍卖管理器测试"""

    def setup_method(self):
        """每个测试前重置拍卖"""
        self.manager = AuctionManager()

    def test_create_auction_success(self):
        """测试成功创建拍卖"""
        result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )
        assert result.success is True
        assert result.auction_id != ""

    def test_create_auction_with_buyout(self):
        """测试创建带一口价的拍卖"""
        result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
            buyout_price=1000,
        )
        assert result.success is True

        auction = self.manager.get_auction(result.auction_id)
        assert auction.buyout_price == 1000

    def test_create_auction_invalid_duration_short(self):
        """测试时长过短"""
        result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=12,  # 最短 24 小时
        )
        assert result.success is False
        assert "24" in result.message

    def test_create_auction_invalid_duration_long(self):
        """测试时长过长"""
        result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=100,  # 最长 72 小时
        )
        assert result.success is False
        assert "72" in result.message

    def test_create_auction_invalid_buyout(self):
        """测试一口价低于起拍价"""
        result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
            buyout_price=400,
        )
        assert result.success is False
        assert "一口价" in result.message

    def test_create_auction_zero_quantity(self):
        """测试数量为零"""
        result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=0,
            starting_price=500,
            duration_hours=24,
        )
        assert result.success is False
        assert "数量" in result.message

    def test_create_auction_zero_price(self):
        """测试起拍价为零"""
        result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=0,
            duration_hours=24,
        )
        assert result.success is False
        assert "起拍价" in result.message

    def test_place_bid_success(self):
        """测试成功出价"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        bid_result = self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=500,
        )
        assert bid_result.success is True
        assert bid_result.new_price == 500

    def test_place_bid_higher(self):
        """测试更高出价"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        # 第一次出价
        self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=500,
        )

        # 第二次更高出价
        bid_result = self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player3",
            bidder_name="玩家3",
            bid_amount=600,
        )
        assert bid_result.success is True
        assert bid_result.new_price == 600

        # 检查拍卖状态
        auction = self.manager.get_auction(create_result.auction_id)
        assert auction.current_bidder_id == "player3"
        assert auction.bid_count == 2

    def test_place_bid_too_low(self):
        """测试出价过低"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        # 第一次出价
        self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=500,
        )

        # 出价低于最小加价
        bid_result = self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player3",
            bidder_name="玩家3",
            bid_amount=510,  # 最小加价 5% = 525
        )
        assert bid_result.success is False
        assert "至少" in bid_result.message

    def test_place_bid_on_own_auction(self):
        """测试对自己的拍卖出价"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        bid_result = self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player1",
            bidder_name="玩家1",
            bid_amount=500,
        )
        assert bid_result.success is False
        assert "自己的拍卖" in bid_result.message

    def test_place_bid_nonexistent_auction(self):
        """测试对不存在的拍卖出价"""
        bid_result = self.manager.place_bid(
            auction_id="nonexistent",
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=500,
        )
        assert bid_result.success is False
        assert "不存在" in bid_result.message

    def test_buyout_success(self):
        """测试一口价购买"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
            buyout_price=1000,
        )

        bid_result = self.manager.buyout(
            auction_id=create_result.auction_id,
            buyer_id="player2",
            buyer_name="玩家2",
        )
        assert bid_result.success is True
        assert bid_result.is_buyout is True
        assert bid_result.new_price == 1000

        # 检查拍卖已结束
        auction = self.manager.get_auction(create_result.auction_id)
        assert auction.status == AuctionStatus.ENDED.value

    def test_buyout_no_buyout_price(self):
        """测试没有一口价的拍卖"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        bid_result = self.manager.buyout(
            auction_id=create_result.auction_id,
            buyer_id="player2",
            buyer_name="玩家2",
        )
        assert bid_result.success is False
        assert "不支持一口价" in bid_result.message

    def test_cancel_auction_success(self):
        """测试成功取消拍卖"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        success, message = self.manager.cancel_auction(
            create_result.auction_id, "player1"
        )
        assert success is True

        auction = self.manager.get_auction(create_result.auction_id)
        assert auction.status == AuctionStatus.CANCELLED.value

    def test_cancel_auction_with_bids(self):
        """测试取消有出价的拍卖"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        # 先出价
        self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=500,
        )

        # 尝试取消
        success, message = self.manager.cancel_auction(
            create_result.auction_id, "player1"
        )
        assert success is False
        assert "已有出价" in message

    def test_cancel_auction_not_owner(self):
        """测试取消他人拍卖"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        success, message = self.manager.cancel_auction(
            create_result.auction_id, "player2"
        )
        assert success is False
        assert "自己的拍卖" in message

    def test_get_auctions(self):
        """测试获取拍卖列表"""
        self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )
        self.manager.create_auction(
            seller_id="player2",
            seller_name="玩家2",
            item_type="material",
            item_name="稀有木材",
            quantity=10,
            starting_price=100,
            duration_hours=48,
        )

        auctions = self.manager.get_auctions()
        assert len(auctions) == 2

    def test_get_auctions_filter_by_item_type(self):
        """测试按物品类型过滤"""
        self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )
        self.manager.create_auction(
            seller_id="player2",
            seller_name="玩家2",
            item_type="material",
            item_name="稀有木材",
            quantity=10,
            starting_price=100,
            duration_hours=48,
        )

        auctions = self.manager.get_auctions(item_type="seed")
        assert len(auctions) == 1
        assert auctions[0].item_type == "seed"

    def test_get_auction_bids(self):
        """测试获取出价历史"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=500,
        )
        self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player3",
            bidder_name="玩家3",
            bid_amount=600,
        )

        bids = self.manager.get_auction_bids(create_result.auction_id)
        assert len(bids) == 2
        # 最后一个出价应该是中标
        assert bids[-1].is_winning is True
        assert bids[0].is_winning is False

    def test_calculate_settlement_with_winner(self):
        """测试计算有中标者的结算"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        self.manager.place_bid(
            auction_id=create_result.auction_id,
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=1000,
        )

        settlement = self.manager.calculate_settlement(create_result.auction_id)
        assert settlement["has_winner"] is True
        assert settlement["winner_id"] == "player2"
        assert settlement["final_price"] == 1000
        assert settlement["fee"] > 0  # 5% 手续费
        assert settlement["seller_receives"] == 1000 - settlement["fee"]

    def test_calculate_settlement_no_bids(self):
        """测试计算无出价的结算"""
        create_result = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )

        settlement = self.manager.calculate_settlement(create_result.auction_id)
        assert settlement["has_winner"] is False
        assert settlement["final_price"] == 0

    def test_get_player_auctions(self):
        """测试获取玩家创建的拍卖"""
        self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )
        self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="material",
            item_name="稀有木材",
            quantity=10,
            starting_price=100,
            duration_hours=48,
        )
        self.manager.create_auction(
            seller_id="player2",
            seller_name="玩家2",
            item_type="seed",
            item_name="算法玫瑰种子",
            quantity=1,
            starting_price=200,
            duration_hours=24,
        )

        auctions = self.manager.get_player_auctions("player1")
        assert len(auctions) == 2

    def test_get_player_bids(self):
        """测试获取玩家出价记录"""
        create_result1 = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="seed",
            item_name="AI神花种子",
            quantity=1,
            starting_price=500,
            duration_hours=24,
        )
        create_result2 = self.manager.create_auction(
            seller_id="player1",
            seller_name="玩家1",
            item_type="material",
            item_name="稀有木材",
            quantity=10,
            starting_price=100,
            duration_hours=48,
        )

        self.manager.place_bid(
            auction_id=create_result1.auction_id,
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=500,
        )
        self.manager.place_bid(
            auction_id=create_result2.auction_id,
            bidder_id="player2",
            bidder_name="玩家2",
            bid_amount=100,
        )

        bids = self.manager.get_player_bids("player2")
        assert len(bids) == 2


class TestAuctionManagerGlobal:
    """全局拍卖管理器测试"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        assert auction_manager is not None
