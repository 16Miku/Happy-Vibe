"""经济平衡控制器

监控和调整游戏经济健康度，防止通胀/通缩。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class EconomySnapshot:
    """经济快照数据"""

    total_money_supply: int  # 总货币供应量
    avg_player_wealth: float  # 平均玩家财富
    transaction_volume: int  # 交易量
    inflation_rate: float  # 通胀率
    health_score: float  # 经济健康度 (0-100)
    recorded_at: datetime


class EconomyController:
    """经济平衡控制器

    监控经济健康度并动态调整参数：
    - 通胀过高时：提高税率、降低 NPC 收购价
    - 通缩时：降低税率、增加活动奖励
    """

    # 经济阈值
    INFLATION_HIGH = 0.1  # 通胀过高阈值 (10%)
    INFLATION_LOW = -0.05  # 通缩阈值 (-5%)
    HEALTH_CRITICAL = 30.0  # 经济危机阈值
    HEALTH_WARNING = 50.0  # 经济警告阈值

    # 调整参数
    BASE_TAX_RATE = 0.03  # 基础税率 3%
    BASE_LISTING_FEE_RATE = 0.03  # 基础挂单费率 3%
    BASE_AUCTION_FEE_RATE = 0.05  # 基础拍卖费率 5%

    def __init__(self) -> None:
        """初始化经济控制器"""
        self._current_tax_rate = self.BASE_TAX_RATE
        self._current_listing_fee_rate = self.BASE_LISTING_FEE_RATE
        self._current_auction_fee_rate = self.BASE_AUCTION_FEE_RATE
        self._npc_price_modifier = 1.0  # NPC 价格修正系数
        self._reward_modifier = 1.0  # 奖励修正系数
        self._history: list[EconomySnapshot] = []

    @property
    def tax_rate(self) -> float:
        """当前税率"""
        return self._current_tax_rate

    @property
    def listing_fee_rate(self) -> float:
        """当前挂单费率"""
        return self._current_listing_fee_rate

    @property
    def auction_fee_rate(self) -> float:
        """当前拍卖费率"""
        return self._current_auction_fee_rate

    @property
    def npc_price_modifier(self) -> float:
        """NPC 价格修正系数"""
        return self._npc_price_modifier

    @property
    def reward_modifier(self) -> float:
        """奖励修正系数"""
        return self._reward_modifier

    def calculate_listing_fee(self, total_price: int) -> int:
        """计算挂单手续费

        Args:
            total_price: 挂单总价

        Returns:
            手续费金额
        """
        return max(1, int(total_price * self._current_listing_fee_rate))

    def calculate_auction_fee(self, final_price: int) -> int:
        """计算拍卖手续费

        Args:
            final_price: 成交价格

        Returns:
            手续费金额
        """
        return max(1, int(final_price * self._current_auction_fee_rate))

    def calculate_transaction_tax(self, amount: int) -> int:
        """计算交易税

        Args:
            amount: 交易金额

        Returns:
            税金
        """
        return max(0, int(amount * self._current_tax_rate))

    def monitor_economy_health(
        self,
        total_money_supply: int,
        player_count: int,
        transaction_volume: int,
        previous_money_supply: int | None = None,
    ) -> EconomySnapshot:
        """监控经济健康度

        Args:
            total_money_supply: 当前总货币供应量
            player_count: 玩家数量
            transaction_volume: 交易量
            previous_money_supply: 上期货币供应量（用于计算通胀）

        Returns:
            经济快照
        """
        # 计算平均财富
        avg_wealth = total_money_supply / max(1, player_count)

        # 计算通胀率
        inflation_rate = 0.0
        if previous_money_supply and previous_money_supply > 0:
            inflation_rate = (
                total_money_supply - previous_money_supply
            ) / previous_money_supply

        # 计算健康度分数
        health_score = self._calculate_health_score(
            inflation_rate, transaction_volume, player_count
        )

        snapshot = EconomySnapshot(
            total_money_supply=total_money_supply,
            avg_player_wealth=avg_wealth,
            transaction_volume=transaction_volume,
            inflation_rate=inflation_rate,
            health_score=health_score,
            recorded_at=datetime.utcnow(),
        )

        self._history.append(snapshot)
        # 只保留最近 100 条记录
        if len(self._history) > 100:
            self._history = self._history[-100:]

        return snapshot

    def _calculate_health_score(
        self, inflation_rate: float, transaction_volume: int, player_count: int
    ) -> float:
        """计算经济健康度分数

        Args:
            inflation_rate: 通胀率
            transaction_volume: 交易量
            player_count: 玩家数量

        Returns:
            健康度分数 (0-100)
        """
        score = 100.0

        # 通胀/通缩惩罚
        if abs(inflation_rate) > 0.2:
            score -= 40  # 严重通胀/通缩
        elif abs(inflation_rate) > 0.1:
            score -= 25
        elif abs(inflation_rate) > 0.05:
            score -= 10

        # 交易活跃度奖励
        if player_count > 0:
            trades_per_player = transaction_volume / player_count
            if trades_per_player >= 5:
                score += 10  # 交易活跃
            elif trades_per_player < 1:
                score -= 15  # 交易不活跃

        return max(0.0, min(100.0, score))

    def adjust_economy(self, snapshot: EconomySnapshot) -> dict[str, float]:
        """根据经济状况动态调整参数

        Args:
            snapshot: 经济快照

        Returns:
            调整后的参数
        """
        adjustments = {}

        if snapshot.inflation_rate > self.INFLATION_HIGH:
            # 通胀过高：紧缩政策
            self._increase_tax_rate(0.01)
            self._reduce_npc_sell_price(0.05)
            self._reduce_rewards(0.1)
            adjustments["policy"] = "tightening"
        elif snapshot.inflation_rate < self.INFLATION_LOW:
            # 通缩：宽松政策
            self._decrease_tax_rate(0.01)
            self._increase_npc_sell_price(0.05)
            self._increase_rewards(0.1)
            adjustments["policy"] = "easing"
        else:
            # 经济稳定：逐步恢复基准
            self._normalize_rates()
            adjustments["policy"] = "stable"

        adjustments["tax_rate"] = self._current_tax_rate
        adjustments["listing_fee_rate"] = self._current_listing_fee_rate
        adjustments["npc_price_modifier"] = self._npc_price_modifier
        adjustments["reward_modifier"] = self._reward_modifier

        return adjustments

    def _increase_tax_rate(self, delta: float) -> None:
        """提高税率"""
        self._current_tax_rate = min(0.1, self._current_tax_rate + delta)
        self._current_listing_fee_rate = min(
            0.1, self._current_listing_fee_rate + delta
        )

    def _decrease_tax_rate(self, delta: float) -> None:
        """降低税率"""
        self._current_tax_rate = max(0.01, self._current_tax_rate - delta)
        self._current_listing_fee_rate = max(
            0.01, self._current_listing_fee_rate - delta
        )

    def _reduce_npc_sell_price(self, delta: float) -> None:
        """降低 NPC 收购价"""
        self._npc_price_modifier = max(0.5, self._npc_price_modifier - delta)

    def _increase_npc_sell_price(self, delta: float) -> None:
        """提高 NPC 收购价"""
        self._npc_price_modifier = min(1.5, self._npc_price_modifier + delta)

    def _reduce_rewards(self, delta: float) -> None:
        """降低奖励"""
        self._reward_modifier = max(0.5, self._reward_modifier - delta)

    def _increase_rewards(self, delta: float) -> None:
        """增加奖励"""
        self._reward_modifier = min(2.0, self._reward_modifier + delta)

    def _normalize_rates(self) -> None:
        """逐步恢复基准费率"""
        # 税率向基准靠拢
        if self._current_tax_rate > self.BASE_TAX_RATE:
            self._current_tax_rate = max(
                self.BASE_TAX_RATE, self._current_tax_rate - 0.005
            )
        elif self._current_tax_rate < self.BASE_TAX_RATE:
            self._current_tax_rate = min(
                self.BASE_TAX_RATE, self._current_tax_rate + 0.005
            )

        # 挂单费率向基准靠拢
        if self._current_listing_fee_rate > self.BASE_LISTING_FEE_RATE:
            self._current_listing_fee_rate = max(
                self.BASE_LISTING_FEE_RATE, self._current_listing_fee_rate - 0.005
            )
        elif self._current_listing_fee_rate < self.BASE_LISTING_FEE_RATE:
            self._current_listing_fee_rate = min(
                self.BASE_LISTING_FEE_RATE, self._current_listing_fee_rate + 0.005
            )

        # NPC 价格修正向 1.0 靠拢
        if self._npc_price_modifier > 1.0:
            self._npc_price_modifier = max(1.0, self._npc_price_modifier - 0.02)
        elif self._npc_price_modifier < 1.0:
            self._npc_price_modifier = min(1.0, self._npc_price_modifier + 0.02)

        # 奖励修正向 1.0 靠拢
        if self._reward_modifier > 1.0:
            self._reward_modifier = max(1.0, self._reward_modifier - 0.05)
        elif self._reward_modifier < 1.0:
            self._reward_modifier = min(1.0, self._reward_modifier + 0.05)

    def get_economy_status(self) -> dict:
        """获取当前经济状态

        Returns:
            经济状态字典
        """
        latest = self._history[-1] if self._history else None
        return {
            "tax_rate": self._current_tax_rate,
            "listing_fee_rate": self._current_listing_fee_rate,
            "auction_fee_rate": self._current_auction_fee_rate,
            "npc_price_modifier": self._npc_price_modifier,
            "reward_modifier": self._reward_modifier,
            "latest_snapshot": {
                "total_money_supply": latest.total_money_supply if latest else 0,
                "avg_player_wealth": latest.avg_player_wealth if latest else 0,
                "transaction_volume": latest.transaction_volume if latest else 0,
                "inflation_rate": latest.inflation_rate if latest else 0,
                "health_score": latest.health_score if latest else 100,
                "recorded_at": latest.recorded_at.isoformat() if latest else None,
            },
        }

    def get_history(self, limit: int = 10) -> list[dict]:
        """获取经济历史记录

        Args:
            limit: 返回记录数量

        Returns:
            历史记录列表
        """
        return [
            {
                "total_money_supply": s.total_money_supply,
                "avg_player_wealth": s.avg_player_wealth,
                "transaction_volume": s.transaction_volume,
                "inflation_rate": s.inflation_rate,
                "health_score": s.health_score,
                "recorded_at": s.recorded_at.isoformat(),
            }
            for s in self._history[-limit:]
        ]


# 全局经济控制器实例
economy_controller = EconomyController()
