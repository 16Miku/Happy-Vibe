"""拍卖业务逻辑

实现拍卖系统的创建、出价、一口价、结算等功能。
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.economy import economy_controller
from src.storage.models import AuctionStatus


@dataclass
class AuctionInfo:
    """拍卖信息"""

    auction_id: str
    seller_id: str
    seller_name: str
    item_type: str
    item_name: str
    quantity: int
    starting_price: int
    current_price: int
    buyout_price: int | None
    min_increment: int
    current_bidder_id: str | None
    current_bidder_name: str | None
    bid_count: int
    status: str
    created_at: datetime
    ends_at: datetime
    ended_at: datetime | None


@dataclass
class BidInfo:
    """出价信息"""

    bid_id: str
    auction_id: str
    bidder_id: str
    bidder_name: str
    bid_amount: int
    created_at: datetime
    is_winning: bool


@dataclass
class CreateAuctionResult:
    """创建拍卖结果"""

    success: bool
    message: str
    auction_id: str = ""
    listing_fee: int = 0


@dataclass
class BidResult:
    """出价结果"""

    success: bool
    message: str
    new_price: int = 0
    is_buyout: bool = False


class AuctionManager:
    """拍卖管理器

    管理拍卖系统的所有操作。

    拍卖规则：
    - 手续费: 5%（成交时收取）
    - 最小加价: 当前价格的 5%
    - 时长: 24-72 小时
    - 延时机制: 最后 5 分钟内有出价，延长 5 分钟
    """

    # 拍卖规则
    MIN_DURATION_HOURS = 24  # 最短拍卖时长
    MAX_DURATION_HOURS = 72  # 最长拍卖时长
    MIN_INCREMENT_RATE = 0.05  # 最小加价比例 (5%)
    EXTENSION_THRESHOLD_MINUTES = 5  # 延时触发阈值（分钟）
    EXTENSION_MINUTES = 5  # 延长时间（分钟）

    def __init__(self) -> None:
        """初始化拍卖管理器"""
        self._auctions: dict[str, AuctionInfo] = {}
        self._bids: dict[str, list[BidInfo]] = {}  # auction_id -> bids
        self._player_names: dict[str, str] = {}  # player_id -> name cache

    def get_auctions(
        self,
        item_type: str | None = None,
        item_name: str | None = None,
        seller_id: str | None = None,
        status: str = AuctionStatus.ACTIVE.value,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuctionInfo]:
        """获取拍卖列表

        Args:
            item_type: 物品类型过滤
            item_name: 物品名称过滤
            seller_id: 卖家 ID 过滤
            status: 状态过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            拍卖信息列表
        """
        # 检查并结算过期拍卖
        self._check_and_settle_auctions()

        results = []
        for auction in self._auctions.values():
            if auction.status != status:
                continue
            if item_type and auction.item_type != item_type:
                continue
            if item_name and auction.item_name != item_name:
                continue
            if seller_id and auction.seller_id != seller_id:
                continue
            results.append(auction)

        # 按结束时间排序（即将结束的在前）
        results.sort(key=lambda x: x.ends_at)

        return results[offset : offset + limit]

    def create_auction(
        self,
        seller_id: str,
        seller_name: str,
        item_type: str,
        item_name: str,
        quantity: int,
        starting_price: int,
        duration_hours: int = 24,
        buyout_price: int | None = None,
    ) -> CreateAuctionResult:
        """创建拍卖

        Args:
            seller_id: 卖家 ID
            seller_name: 卖家名称
            item_type: 物品类型
            item_name: 物品名称
            quantity: 数量
            starting_price: 起拍价
            duration_hours: 拍卖时长（小时）
            buyout_price: 一口价（可选）

        Returns:
            创建结果
        """
        # 验证数量
        if quantity <= 0:
            return CreateAuctionResult(
                success=False,
                message="数量必须大于 0",
            )

        # 验证起拍价
        if starting_price <= 0:
            return CreateAuctionResult(
                success=False,
                message="起拍价必须大于 0",
            )

        # 验证时长
        if duration_hours < self.MIN_DURATION_HOURS:
            return CreateAuctionResult(
                success=False,
                message=f"拍卖时长不能少于 {self.MIN_DURATION_HOURS} 小时",
            )
        if duration_hours > self.MAX_DURATION_HOURS:
            return CreateAuctionResult(
                success=False,
                message=f"拍卖时长不能超过 {self.MAX_DURATION_HOURS} 小时",
            )

        # 验证一口价
        if buyout_price is not None and buyout_price <= starting_price:
            return CreateAuctionResult(
                success=False,
                message="一口价必须高于起拍价",
            )

        # 计算最小加价
        min_increment = max(1, int(starting_price * self.MIN_INCREMENT_RATE))

        # 创建拍卖
        auction_id = str(uuid.uuid4())
        now = datetime.utcnow()
        ends_at = now + timedelta(hours=duration_hours)

        auction = AuctionInfo(
            auction_id=auction_id,
            seller_id=seller_id,
            seller_name=seller_name,
            item_type=item_type,
            item_name=item_name,
            quantity=quantity,
            starting_price=starting_price,
            current_price=starting_price,
            buyout_price=buyout_price,
            min_increment=min_increment,
            current_bidder_id=None,
            current_bidder_name=None,
            bid_count=0,
            status=AuctionStatus.ACTIVE.value,
            created_at=now,
            ends_at=ends_at,
            ended_at=None,
        )

        self._auctions[auction_id] = auction
        self._bids[auction_id] = []
        self._player_names[seller_id] = seller_name

        return CreateAuctionResult(
            success=True,
            message="拍卖创建成功",
            auction_id=auction_id,
            listing_fee=0,  # 拍卖手续费在成交时收取
        )

    def place_bid(
        self,
        auction_id: str,
        bidder_id: str,
        bidder_name: str,
        bid_amount: int,
    ) -> BidResult:
        """出价

        Args:
            auction_id: 拍卖 ID
            bidder_id: 出价者 ID
            bidder_name: 出价者名称
            bid_amount: 出价金额

        Returns:
            出价结果
        """
        auction = self._auctions.get(auction_id)
        if not auction:
            return BidResult(success=False, message="拍卖不存在")

        if auction.status != AuctionStatus.ACTIVE.value:
            return BidResult(success=False, message="拍卖已结束")

        if auction.seller_id == bidder_id:
            return BidResult(success=False, message="不能对自己的拍卖出价")

        # 检查是否已过期
        now = datetime.utcnow()
        if now >= auction.ends_at:
            self._settle_auction(auction_id)
            return BidResult(success=False, message="拍卖已结束")

        # 计算最低出价
        if auction.bid_count == 0:
            min_bid = auction.starting_price
        else:
            min_bid = auction.current_price + auction.min_increment

        if bid_amount < min_bid:
            return BidResult(
                success=False,
                message=f"出价必须至少为 {min_bid}",
            )

        # 检查是否触发一口价
        is_buyout = False
        if auction.buyout_price and bid_amount >= auction.buyout_price:
            bid_amount = auction.buyout_price
            is_buyout = True

        # 记录出价
        bid_id = str(uuid.uuid4())
        bid = BidInfo(
            bid_id=bid_id,
            auction_id=auction_id,
            bidder_id=bidder_id,
            bidder_name=bidder_name,
            bid_amount=bid_amount,
            created_at=now,
            is_winning=True,
        )

        # 更新之前的最高出价为非中标
        for old_bid in self._bids[auction_id]:
            old_bid.is_winning = False

        self._bids[auction_id].append(bid)
        self._player_names[bidder_id] = bidder_name

        # 更新拍卖信息
        auction.current_price = bid_amount
        auction.current_bidder_id = bidder_id
        auction.current_bidder_name = bidder_name
        auction.bid_count += 1
        auction.min_increment = max(1, int(bid_amount * self.MIN_INCREMENT_RATE))

        # 延时机制
        time_remaining = (auction.ends_at - now).total_seconds() / 60
        if time_remaining <= self.EXTENSION_THRESHOLD_MINUTES:
            auction.ends_at = now + timedelta(minutes=self.EXTENSION_MINUTES)

        # 一口价立即结算
        if is_buyout:
            self._settle_auction(auction_id)
            return BidResult(
                success=True,
                message="一口价购买成功",
                new_price=bid_amount,
                is_buyout=True,
            )

        return BidResult(
            success=True,
            message="出价成功",
            new_price=bid_amount,
            is_buyout=False,
        )

    def buyout(
        self,
        auction_id: str,
        buyer_id: str,
        buyer_name: str,
    ) -> BidResult:
        """一口价购买

        Args:
            auction_id: 拍卖 ID
            buyer_id: 买家 ID
            buyer_name: 买家名称

        Returns:
            购买结果
        """
        auction = self._auctions.get(auction_id)
        if not auction:
            return BidResult(success=False, message="拍卖不存在")

        if not auction.buyout_price:
            return BidResult(success=False, message="此拍卖不支持一口价")

        return self.place_bid(
            auction_id=auction_id,
            bidder_id=buyer_id,
            bidder_name=buyer_name,
            bid_amount=auction.buyout_price,
        )

    def cancel_auction(
        self, auction_id: str, player_id: str
    ) -> tuple[bool, str]:
        """取消拍卖

        Args:
            auction_id: 拍卖 ID
            player_id: 玩家 ID

        Returns:
            (是否成功, 消息)
        """
        auction = self._auctions.get(auction_id)
        if not auction:
            return False, "拍卖不存在"

        if auction.seller_id != player_id:
            return False, "只能取消自己的拍卖"

        if auction.status != AuctionStatus.ACTIVE.value:
            return False, f"拍卖状态不允许取消: {auction.status}"

        if auction.bid_count > 0:
            return False, "已有出价，无法取消"

        auction.status = AuctionStatus.CANCELLED.value
        auction.ended_at = datetime.utcnow()

        return True, "拍卖已取消"

    def get_auction(self, auction_id: str) -> AuctionInfo | None:
        """获取拍卖详情

        Args:
            auction_id: 拍卖 ID

        Returns:
            拍卖信息
        """
        return self._auctions.get(auction_id)

    def get_auction_bids(self, auction_id: str) -> list[BidInfo]:
        """获取拍卖的出价历史

        Args:
            auction_id: 拍卖 ID

        Returns:
            出价列表
        """
        return self._bids.get(auction_id, [])

    def get_player_auctions(self, player_id: str) -> list[AuctionInfo]:
        """获取玩家创建的拍卖

        Args:
            player_id: 玩家 ID

        Returns:
            拍卖列表
        """
        return [
            auction
            for auction in self._auctions.values()
            if auction.seller_id == player_id
        ]

    def get_player_bids(self, player_id: str) -> list[BidInfo]:
        """获取玩家的出价记录

        Args:
            player_id: 玩家 ID

        Returns:
            出价列表
        """
        result = []
        for bids in self._bids.values():
            for bid in bids:
                if bid.bidder_id == player_id:
                    result.append(bid)
        return result

    def calculate_settlement(self, auction_id: str) -> dict | None:
        """计算拍卖结算信息

        Args:
            auction_id: 拍卖 ID

        Returns:
            结算信息字典
        """
        auction = self._auctions.get(auction_id)
        if not auction:
            return None

        if auction.bid_count == 0:
            return {
                "has_winner": False,
                "final_price": 0,
                "fee": 0,
                "seller_receives": 0,
            }

        final_price = auction.current_price
        fee = economy_controller.calculate_auction_fee(final_price)
        seller_receives = final_price - fee

        return {
            "has_winner": True,
            "winner_id": auction.current_bidder_id,
            "winner_name": auction.current_bidder_name,
            "final_price": final_price,
            "fee": fee,
            "seller_receives": seller_receives,
        }

    def _settle_auction(self, auction_id: str) -> None:
        """结算拍卖

        Args:
            auction_id: 拍卖 ID
        """
        auction = self._auctions.get(auction_id)
        if not auction or auction.status != AuctionStatus.ACTIVE.value:
            return

        auction.status = AuctionStatus.ENDED.value
        auction.ended_at = datetime.utcnow()

    def _check_and_settle_auctions(self) -> None:
        """检查并结算过期拍卖"""
        now = datetime.utcnow()
        for auction in self._auctions.values():
            if (
                auction.status == AuctionStatus.ACTIVE.value
                and now >= auction.ends_at
            ):
                self._settle_auction(auction.auction_id)


# 全局拍卖管理器实例
auction_manager = AuctionManager()
