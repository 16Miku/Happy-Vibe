"""市场业务逻辑

实现玩家交易市场的挂单、购买、取消等功能。
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.economy import economy_controller
from src.storage.models import ListingStatus


@dataclass
class ListingInfo:
    """挂单信息"""

    listing_id: str
    seller_id: str
    seller_name: str
    item_type: str
    item_name: str
    quantity: int
    unit_price: int
    total_price: int
    listing_fee: int
    status: str
    created_at: datetime
    expires_at: datetime


@dataclass
class CreateListingResult:
    """创建挂单结果"""

    success: bool
    message: str
    listing_id: str = ""
    listing_fee: int = 0


@dataclass
class PurchaseListingResult:
    """购买挂单结果"""

    success: bool
    message: str
    item_name: str = ""
    quantity: int = 0
    total_cost: int = 0
    remaining_gold: int = 0


class MarketManager:
    """市场管理器

    管理玩家交易市场的所有挂单操作。

    交易规则：
    - 手续费: 3%
    - 挂卖限制: 每人最多 20 件
    - 价格限制: 基准价格 ±50%
    - 有效期: 7 天
    """

    # 市场规则
    MAX_LISTINGS_PER_PLAYER = 20  # 每人最多挂单数
    LISTING_DURATION_DAYS = 7  # 挂单有效期（天）
    PRICE_DEVIATION_LIMIT = 0.5  # 价格偏离限制 (±50%)

    def __init__(self) -> None:
        """初始化市场管理器"""
        # 内存存储（实际应使用数据库）
        self._listings: dict[str, ListingInfo] = {}
        self._player_listing_counts: dict[str, int] = {}
        # 价格参考（用于限制价格偏离）
        self._reference_prices: dict[str, int] = {}

    def get_listings(
        self,
        item_type: str | None = None,
        item_name: str | None = None,
        seller_id: str | None = None,
        status: str = ListingStatus.ACTIVE.value,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ListingInfo]:
        """获取市场挂单列表

        Args:
            item_type: 物品类型过滤
            item_name: 物品名称过滤
            seller_id: 卖家 ID 过滤
            status: 状态过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            挂单信息列表
        """
        # 清理过期挂单
        self._cleanup_expired_listings()

        results = []
        for listing in self._listings.values():
            # 状态过滤
            if listing.status != status:
                continue
            # 物品类型过滤
            if item_type and listing.item_type != item_type:
                continue
            # 物品名称过滤
            if item_name and listing.item_name != item_name:
                continue
            # 卖家过滤
            if seller_id and listing.seller_id != seller_id:
                continue
            results.append(listing)

        # 按价格排序
        results.sort(key=lambda x: x.unit_price)

        # 分页
        return results[offset : offset + limit]

    def create_listing(
        self,
        seller_id: str,
        seller_name: str,
        item_type: str,
        item_name: str,
        quantity: int,
        unit_price: int,
        player_gold: int,
    ) -> CreateListingResult:
        """创建挂单

        Args:
            seller_id: 卖家 ID
            seller_name: 卖家名称
            item_type: 物品类型
            item_name: 物品名称
            quantity: 数量
            unit_price: 单价
            player_gold: 玩家金币（用于支付手续费）

        Returns:
            创建结果
        """
        # 检查挂单数量限制
        current_count = self._player_listing_counts.get(seller_id, 0)
        if current_count >= self.MAX_LISTINGS_PER_PLAYER:
            return CreateListingResult(
                success=False,
                message=f"挂单数量已达上限 ({self.MAX_LISTINGS_PER_PLAYER})",
            )

        # 验证数量
        if quantity <= 0:
            return CreateListingResult(
                success=False,
                message="数量必须大于 0",
            )

        # 验证价格
        if unit_price <= 0:
            return CreateListingResult(
                success=False,
                message="价格必须大于 0",
            )

        # 检查价格偏离（如果有参考价格）
        ref_price = self._reference_prices.get(item_name)
        if ref_price:
            min_price = int(ref_price * (1 - self.PRICE_DEVIATION_LIMIT))
            max_price = int(ref_price * (1 + self.PRICE_DEVIATION_LIMIT))
            if unit_price < min_price or unit_price > max_price:
                return CreateListingResult(
                    success=False,
                    message=f"价格超出允许范围 ({min_price} - {max_price})",
                )

        # 计算总价和手续费
        total_price = unit_price * quantity
        listing_fee = economy_controller.calculate_listing_fee(total_price)

        # 检查手续费
        if player_gold < listing_fee:
            return CreateListingResult(
                success=False,
                message=f"金币不足以支付手续费 ({listing_fee})",
            )

        # 创建挂单
        listing_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(days=self.LISTING_DURATION_DAYS)

        listing = ListingInfo(
            listing_id=listing_id,
            seller_id=seller_id,
            seller_name=seller_name,
            item_type=item_type,
            item_name=item_name,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            listing_fee=listing_fee,
            status=ListingStatus.ACTIVE.value,
            created_at=now,
            expires_at=expires_at,
        )

        self._listings[listing_id] = listing
        self._player_listing_counts[seller_id] = current_count + 1

        # 更新参考价格
        self._update_reference_price(item_name, unit_price)

        return CreateListingResult(
            success=True,
            message="挂单创建成功",
            listing_id=listing_id,
            listing_fee=listing_fee,
        )

    def cancel_listing(
        self, listing_id: str, player_id: str
    ) -> tuple[bool, str]:
        """取消挂单

        Args:
            listing_id: 挂单 ID
            player_id: 玩家 ID

        Returns:
            (是否成功, 消息)
        """
        listing = self._listings.get(listing_id)
        if not listing:
            return False, "挂单不存在"

        if listing.seller_id != player_id:
            return False, "只能取消自己的挂单"

        if listing.status != ListingStatus.ACTIVE.value:
            return False, f"挂单状态不允许取消: {listing.status}"

        # 更新状态
        listing.status = ListingStatus.CANCELLED.value
        self._player_listing_counts[player_id] = max(
            0, self._player_listing_counts.get(player_id, 1) - 1
        )

        return True, "挂单已取消"

    def purchase_listing(
        self,
        listing_id: str,
        buyer_id: str,
        buyer_gold: int,
        quantity: int | None = None,
    ) -> PurchaseListingResult:
        """购买挂单

        Args:
            listing_id: 挂单 ID
            buyer_id: 买家 ID
            buyer_gold: 买家金币
            quantity: 购买数量（None 表示全部购买）

        Returns:
            购买结果
        """
        listing = self._listings.get(listing_id)
        if not listing:
            return PurchaseListingResult(
                success=False,
                message="挂单不存在",
            )

        if listing.status != ListingStatus.ACTIVE.value:
            return PurchaseListingResult(
                success=False,
                message=f"挂单不可购买: {listing.status}",
            )

        if listing.seller_id == buyer_id:
            return PurchaseListingResult(
                success=False,
                message="不能购买自己的挂单",
            )

        # 确定购买数量
        buy_quantity = quantity if quantity else listing.quantity
        if buy_quantity <= 0:
            return PurchaseListingResult(
                success=False,
                message="购买数量必须大于 0",
            )

        if buy_quantity > listing.quantity:
            return PurchaseListingResult(
                success=False,
                message=f"购买数量超过可用数量 ({listing.quantity})",
            )

        # 计算费用
        total_cost = listing.unit_price * buy_quantity

        if buyer_gold < total_cost:
            return PurchaseListingResult(
                success=False,
                message=f"金币不足，需要 {total_cost}，当前 {buyer_gold}",
            )

        # 更新挂单
        listing.quantity -= buy_quantity
        if listing.quantity <= 0:
            listing.status = ListingStatus.SOLD.value
            self._player_listing_counts[listing.seller_id] = max(
                0, self._player_listing_counts.get(listing.seller_id, 1) - 1
            )

        return PurchaseListingResult(
            success=True,
            message="购买成功",
            item_name=listing.item_name,
            quantity=buy_quantity,
            total_cost=total_cost,
            remaining_gold=buyer_gold - total_cost,
        )

    def get_listing(self, listing_id: str) -> ListingInfo | None:
        """获取挂单详情

        Args:
            listing_id: 挂单 ID

        Returns:
            挂单信息
        """
        return self._listings.get(listing_id)

    def get_player_listings(self, player_id: str) -> list[ListingInfo]:
        """获取玩家的所有挂单

        Args:
            player_id: 玩家 ID

        Returns:
            挂单列表
        """
        return [
            listing
            for listing in self._listings.values()
            if listing.seller_id == player_id
        ]

    def get_market_stats(self) -> dict:
        """获取市场统计信息

        Returns:
            统计信息字典
        """
        active_listings = [
            listing for listing in self._listings.values()
            if listing.status == ListingStatus.ACTIVE.value
        ]

        total_value = sum(listing.total_price for listing in active_listings)
        item_types = set(listing.item_type for listing in active_listings)

        return {
            "total_listings": len(active_listings),
            "total_value": total_value,
            "item_types": list(item_types),
            "unique_sellers": len(set(listing.seller_id for listing in active_listings)),
        }

    def set_reference_price(self, item_name: str, price: int) -> None:
        """设置物品参考价格

        Args:
            item_name: 物品名称
            price: 参考价格
        """
        self._reference_prices[item_name] = price

    def _update_reference_price(self, item_name: str, price: int) -> None:
        """更新参考价格（使用移动平均）

        Args:
            item_name: 物品名称
            price: 新价格
        """
        current = self._reference_prices.get(item_name)
        if current:
            # 使用加权移动平均
            self._reference_prices[item_name] = int(current * 0.7 + price * 0.3)
        else:
            self._reference_prices[item_name] = price

    def _cleanup_expired_listings(self) -> None:
        """清理过期挂单"""
        now = datetime.utcnow()
        for listing in self._listings.values():
            if (
                listing.status == ListingStatus.ACTIVE.value
                and listing.expires_at < now
            ):
                listing.status = ListingStatus.EXPIRED.value
                self._player_listing_counts[listing.seller_id] = max(
                    0, self._player_listing_counts.get(listing.seller_id, 1) - 1
                )


# 全局市场管理器实例
market_manager = MarketManager()
