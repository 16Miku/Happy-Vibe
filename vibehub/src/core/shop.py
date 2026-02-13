"""商店业务逻辑

实现 NPC 商店的商品管理、购买、刷新等功能。
"""

from dataclasses import dataclass
from datetime import datetime

from src.core.pricing import pricing_engine
from src.storage.models import (
    ALCHEMY_SHOP_ITEMS,
    GIFT_SHOP_ITEMS,
    MATERIAL_SHOP_ITEMS,
    SEED_SHOP_ITEMS,
    RefreshCycle,
    ShopType,
)


@dataclass
class ShopItemInfo:
    """商店商品信息"""

    item_id: str
    item_name: str
    item_type: str
    base_price: int
    current_price: int
    stock: int
    max_stock: int


@dataclass
class PurchaseResult:
    """购买结果"""

    success: bool
    message: str
    item_name: str = ""
    quantity: int = 0
    total_cost: int = 0
    remaining_gold: int = 0


class ShopManager:
    """商店管理器

    管理所有 NPC 商店的商品、价格和库存。
    """

    # 商店配置
    SHOP_CONFIGS = {
        ShopType.SEED_SHOP.value: {
            "name": "种子店",
            "items": SEED_SHOP_ITEMS,
            "item_type": "seed",
            "refresh_cycle": RefreshCycle.DAILY.value,
        },
        ShopType.MATERIAL_SHOP.value: {
            "name": "建材店",
            "items": MATERIAL_SHOP_ITEMS,
            "item_type": "material",
            "refresh_cycle": RefreshCycle.DAILY.value,
        },
        ShopType.ALCHEMY_SHOP.value: {
            "name": "炼金店",
            "items": ALCHEMY_SHOP_ITEMS,
            "item_type": "potion",
            "refresh_cycle": RefreshCycle.WEEKLY.value,
        },
        ShopType.GIFT_SHOP.value: {
            "name": "礼品店",
            "items": GIFT_SHOP_ITEMS,
            "item_type": "gift",
            "refresh_cycle": RefreshCycle.WEEKLY.value,
        },
    }

    def __init__(self) -> None:
        """初始化商店管理器"""
        self._shop_stocks: dict[str, dict[str, int]] = {}
        self._last_refresh: dict[str, datetime] = {}
        self._initialize_shops()

    def _initialize_shops(self) -> None:
        """初始化所有商店库存"""
        now = datetime.utcnow()
        for shop_type, config in self.SHOP_CONFIGS.items():
            self._shop_stocks[shop_type] = {}
            for item_id, item_data in config["items"].items():
                self._shop_stocks[shop_type][item_id] = item_data["stock"]
            self._last_refresh[shop_type] = now

    def get_all_shops(self) -> list[dict]:
        """获取所有商店列表

        Returns:
            商店信息列表
        """
        shops = []
        for shop_type, config in self.SHOP_CONFIGS.items():
            shops.append({
                "shop_type": shop_type,
                "name": config["name"],
                "refresh_cycle": config["refresh_cycle"],
                "last_refresh": self._last_refresh.get(shop_type, datetime.utcnow()).isoformat(),
                "item_count": len(config["items"]),
            })
        return shops

    def get_shop_items(self, shop_type: str) -> list[ShopItemInfo]:
        """获取指定商店的商品列表

        Args:
            shop_type: 商店类型

        Returns:
            商品信息列表
        """
        if shop_type not in self.SHOP_CONFIGS:
            return []

        # 检查是否需要刷新
        self._check_and_refresh(shop_type)

        config = self.SHOP_CONFIGS[shop_type]
        items = []

        for item_id, item_data in config["items"].items():
            current_stock = self._shop_stocks[shop_type].get(item_id, 0)
            max_stock = item_data["stock"]
            base_price = item_data["price"]

            # 使用动态定价引擎计算当前价格
            current_price = pricing_engine.calculate_price(
                base_price=base_price,
                item_name=item_id,
                current_stock=current_stock,
                max_stock=max_stock,
            )

            items.append(ShopItemInfo(
                item_id=item_id,
                item_name=item_data["name"],
                item_type=config["item_type"],
                base_price=base_price,
                current_price=current_price,
                stock=current_stock,
                max_stock=max_stock,
            ))

        return items

    def buy_item(
        self,
        shop_type: str,
        item_id: str,
        quantity: int,
        player_gold: int,
    ) -> PurchaseResult:
        """购买商品

        Args:
            shop_type: 商店类型
            item_id: 物品 ID
            quantity: 购买数量
            player_gold: 玩家金币

        Returns:
            购买结果
        """
        # 验证商店
        if shop_type not in self.SHOP_CONFIGS:
            return PurchaseResult(
                success=False,
                message=f"商店不存在: {shop_type}",
            )

        config = self.SHOP_CONFIGS[shop_type]

        # 验证物品
        if item_id not in config["items"]:
            return PurchaseResult(
                success=False,
                message=f"物品不存在: {item_id}",
            )

        # 验证数量
        if quantity <= 0:
            return PurchaseResult(
                success=False,
                message="购买数量必须大于 0",
            )

        # 检查库存
        current_stock = self._shop_stocks[shop_type].get(item_id, 0)
        if current_stock < quantity:
            return PurchaseResult(
                success=False,
                message=f"库存不足，当前库存: {current_stock}",
            )

        # 计算价格
        item_data = config["items"][item_id]
        base_price = item_data["price"]
        max_stock = item_data["stock"]

        unit_price = pricing_engine.calculate_price(
            base_price=base_price,
            item_name=item_id,
            current_stock=current_stock,
            max_stock=max_stock,
        )

        # 计算总价（支持批量折扣）
        total_cost = pricing_engine.calculate_bulk_discount(unit_price, quantity)

        # 检查金币
        if player_gold < total_cost:
            return PurchaseResult(
                success=False,
                message=f"金币不足，需要 {total_cost}，当前 {player_gold}",
            )

        # 扣减库存
        self._shop_stocks[shop_type][item_id] = current_stock - quantity

        return PurchaseResult(
            success=True,
            message="购买成功",
            item_name=item_data["name"],
            quantity=quantity,
            total_cost=total_cost,
            remaining_gold=player_gold - total_cost,
        )

    def refresh_shop(self, shop_type: str, force: bool = False) -> bool:
        """刷新商店库存

        Args:
            shop_type: 商店类型
            force: 是否强制刷新

        Returns:
            是否刷新成功
        """
        if shop_type not in self.SHOP_CONFIGS:
            return False

        if not force and not self._should_refresh(shop_type):
            return False

        config = self.SHOP_CONFIGS[shop_type]
        for item_id, item_data in config["items"].items():
            self._shop_stocks[shop_type][item_id] = item_data["stock"]

        self._last_refresh[shop_type] = datetime.utcnow()
        return True

    def _check_and_refresh(self, shop_type: str) -> None:
        """检查并自动刷新商店"""
        if self._should_refresh(shop_type):
            self.refresh_shop(shop_type, force=True)

    def _should_refresh(self, shop_type: str) -> bool:
        """检查商店是否应该刷新

        Args:
            shop_type: 商店类型

        Returns:
            是否应该刷新
        """
        if shop_type not in self.SHOP_CONFIGS:
            return False

        config = self.SHOP_CONFIGS[shop_type]
        last_refresh = self._last_refresh.get(shop_type)

        if last_refresh is None:
            return True

        now = datetime.utcnow()
        refresh_cycle = config["refresh_cycle"]

        if refresh_cycle == RefreshCycle.DAILY.value:
            # 每日刷新：检查是否跨天
            return last_refresh.date() < now.date()
        elif refresh_cycle == RefreshCycle.WEEKLY.value:
            # 每周刷新：检查是否跨周
            return (now - last_refresh).days >= 7
        elif refresh_cycle == RefreshCycle.EVENT.value:
            # 活动刷新：不自动刷新
            return False

        return False

    def get_shop_info(self, shop_type: str) -> dict | None:
        """获取商店详细信息

        Args:
            shop_type: 商店类型

        Returns:
            商店信息字典
        """
        if shop_type not in self.SHOP_CONFIGS:
            return None

        config = self.SHOP_CONFIGS[shop_type]
        items = self.get_shop_items(shop_type)

        return {
            "shop_type": shop_type,
            "name": config["name"],
            "refresh_cycle": config["refresh_cycle"],
            "last_refresh": self._last_refresh.get(shop_type, datetime.utcnow()).isoformat(),
            "items": [
                {
                    "item_id": item.item_id,
                    "item_name": item.item_name,
                    "item_type": item.item_type,
                    "base_price": item.base_price,
                    "current_price": item.current_price,
                    "stock": item.stock,
                    "max_stock": item.max_stock,
                }
                for item in items
            ],
        }

    def sell_to_npc(
        self,
        item_id: str,
        item_name: str,
        quantity: int,
        base_value: int,
    ) -> int:
        """向 NPC 出售物品

        Args:
            item_id: 物品 ID
            item_name: 物品名称
            quantity: 数量
            base_value: 基础价值

        Returns:
            获得的金币
        """
        # NPC 收购价为基础价值的 50%
        from src.core.economy import economy_controller

        sell_price = int(base_value * 0.5 * economy_controller.npc_price_modifier)
        return sell_price * quantity


# 全局商店管理器实例
shop_manager = ShopManager()
