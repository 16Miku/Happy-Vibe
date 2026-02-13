"""动态定价引擎

基于供需关系、时间因素和市场趋势动态调整物品价格。
"""

from datetime import datetime

from src.storage.models import (
    ALCHEMY_SHOP_ITEMS,
    GIFT_SHOP_ITEMS,
    MATERIAL_SHOP_ITEMS,
    SEED_SHOP_ITEMS,
)


class DynamicPricingEngine:
    """动态定价引擎

    根据多种因素计算物品的当前价格：
    - 供需因子：根据库存和需求调整 (±30%)
    - 时间因子：周末/活动期间折扣 (-10%)
    - 市场趋势：根据历史交易趋势调整 (±10%)
    """

    # 价格调整边界
    MIN_PRICE_MULTIPLIER = 0.5  # 最低价格为基础价格的 50%
    MAX_PRICE_MULTIPLIER = 2.0  # 最高价格为基础价格的 200%

    def __init__(self) -> None:
        """初始化定价引擎"""
        # 缓存市场数据
        self._supply_cache: dict[str, float] = {}
        self._demand_cache: dict[str, float] = {}
        self._trend_cache: dict[str, float] = {}
        self._active_events: list[str] = []

    def calculate_price(
        self,
        base_price: int,
        item_name: str,
        current_stock: int | None = None,
        max_stock: int | None = None,
    ) -> int:
        """计算物品当前价格

        Args:
            base_price: 基础价格
            item_name: 物品名称
            current_stock: 当前库存（可选）
            max_stock: 最大库存（可选）

        Returns:
            计算后的当前价格
        """
        multiplier = 1.0

        # 1. 供需因子 (±30%)
        if current_stock is not None and max_stock is not None:
            supply_demand_ratio = self._calculate_supply_demand_ratio(
                current_stock, max_stock
            )
            multiplier *= self._get_supply_demand_multiplier(supply_demand_ratio)
        else:
            # 使用缓存的供需数据
            ratio = self._get_cached_supply_demand_ratio(item_name)
            multiplier *= self._get_supply_demand_multiplier(ratio)

        # 2. 时间因子 (周末/活动 -10%)
        if self._is_weekend() or self._is_event_active():
            multiplier *= 0.9

        # 3. 市场趋势 (±10%)
        trend = self._get_market_trend(item_name)
        multiplier *= 1 + trend * 0.1

        # 限制价格范围
        multiplier = max(
            self.MIN_PRICE_MULTIPLIER,
            min(self.MAX_PRICE_MULTIPLIER, multiplier),
        )

        return max(1, int(base_price * multiplier))

    def _calculate_supply_demand_ratio(
        self, current_stock: int, max_stock: int
    ) -> float:
        """计算供需比率

        Args:
            current_stock: 当前库存
            max_stock: 最大库存

        Returns:
            供需比率 (库存/最大库存)
        """
        if max_stock <= 0:
            return 1.0
        return current_stock / max_stock

    def _get_cached_supply_demand_ratio(self, item_name: str) -> float:
        """获取缓存的供需比率

        Args:
            item_name: 物品名称

        Returns:
            供需比率，默认为 1.0
        """
        supply = self._supply_cache.get(item_name, 1.0)
        demand = self._demand_cache.get(item_name, 1.0)
        if demand <= 0:
            return 1.0
        return supply / demand

    def _get_supply_demand_multiplier(self, ratio: float) -> float:
        """根据供需比率获取价格乘数

        Args:
            ratio: 供需比率

        Returns:
            价格乘数
        """
        if ratio > 2.0:
            return 0.7  # 供过于求，降价 30%
        if ratio > 1.5:
            return 0.85  # 供应充足，降价 15%
        if ratio < 0.3:
            return 1.5  # 严重供不应求，涨价 50%
        if ratio < 0.5:
            return 1.3  # 供不应求，涨价 30%
        if ratio < 0.8:
            return 1.15  # 供应偏紧，涨价 15%
        return 1.0  # 供需平衡

    def _is_weekend(self) -> bool:
        """检查当前是否为周末

        Returns:
            是否为周末
        """
        return datetime.now().weekday() >= 5

    def _is_event_active(self) -> bool:
        """检查是否有活动进行中

        Returns:
            是否有活动
        """
        return len(self._active_events) > 0

    def _get_market_trend(self, item_name: str) -> float:
        """获取市场趋势

        Args:
            item_name: 物品名称

        Returns:
            趋势值 (-1.0 到 1.0)，正值表示上涨趋势，负值表示下跌趋势
        """
        return self._trend_cache.get(item_name, 0.0)

    def update_supply_data(self, item_name: str, supply: float) -> None:
        """更新供应数据

        Args:
            item_name: 物品名称
            supply: 供应量
        """
        self._supply_cache[item_name] = supply

    def update_demand_data(self, item_name: str, demand: float) -> None:
        """更新需求数据

        Args:
            item_name: 物品名称
            demand: 需求量
        """
        self._demand_cache[item_name] = demand

    def update_trend_data(self, item_name: str, trend: float) -> None:
        """更新市场趋势数据

        Args:
            item_name: 物品名称
            trend: 趋势值 (-1.0 到 1.0)
        """
        self._trend_cache[item_name] = max(-1.0, min(1.0, trend))

    def add_active_event(self, event_name: str) -> None:
        """添加活动

        Args:
            event_name: 活动名称
        """
        if event_name not in self._active_events:
            self._active_events.append(event_name)

    def remove_active_event(self, event_name: str) -> None:
        """移除活动

        Args:
            event_name: 活动名称
        """
        if event_name in self._active_events:
            self._active_events.remove(event_name)

    def get_all_shop_base_prices(self) -> dict[str, dict[str, int]]:
        """获取所有商店的基础价格

        Returns:
            商店类型 -> 物品名称 -> 基础价格
        """
        return {
            "seed_shop": {k: v["price"] for k, v in SEED_SHOP_ITEMS.items()},
            "material_shop": {k: v["price"] for k, v in MATERIAL_SHOP_ITEMS.items()},
            "alchemy_shop": {k: v["price"] for k, v in ALCHEMY_SHOP_ITEMS.items()},
            "gift_shop": {k: v["price"] for k, v in GIFT_SHOP_ITEMS.items()},
        }

    def calculate_bulk_discount(
        self, base_price: int, quantity: int, discount_threshold: int = 10
    ) -> int:
        """计算批量购买折扣

        Args:
            base_price: 单价
            quantity: 数量
            discount_threshold: 触发折扣的数量阈值

        Returns:
            折扣后的总价
        """
        total = base_price * quantity
        if quantity >= discount_threshold * 5:
            return int(total * 0.85)  # 15% 折扣
        if quantity >= discount_threshold * 2:
            return int(total * 0.92)  # 8% 折扣
        if quantity >= discount_threshold:
            return int(total * 0.95)  # 5% 折扣
        return total


# 全局定价引擎实例
pricing_engine = DynamicPricingEngine()
