"""经济指标 API 路由

提供经济监控和统计的 HTTP 接口。
"""


from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.core.economy import economy_controller
from src.core.pricing import pricing_engine

router = APIRouter(prefix="/api/economy", tags=["经济"])


class EconomyStatusResponse(BaseModel):
    """经济状态响应"""

    tax_rate: float
    listing_fee_rate: float
    auction_fee_rate: float
    npc_price_modifier: float
    reward_modifier: float
    latest_snapshot: dict


class EconomyHistoryResponse(BaseModel):
    """经济历史响应"""

    total_money_supply: int
    avg_player_wealth: float
    transaction_volume: int
    inflation_rate: float
    health_score: float
    recorded_at: str


class PriceIndexResponse(BaseModel):
    """物价指数响应"""

    shop_type: str
    items: dict[str, int]


class EconomyMetricsResponse(BaseModel):
    """经济指标响应"""
    total_money_supply: int
    avg_player_wealth: float
    transaction_volume: int
    inflation_rate: float
    health_score: float
    recorded_at: str


class MonitorRequest(BaseModel):
    """监控请求"""

    total_money_supply: int = Field(..., ge=0, description="总货币供应量")
    player_count: int = Field(..., ge=1, description="玩家数量")
    transaction_volume: int = Field(..., ge=0, description="交易量")
    previous_money_supply: int | None = Field(None, ge=0, description="上期货币供应量")


class MonitorResponse(BaseModel):
    """监控响应"""

    total_money_supply: int
    avg_player_wealth: float
    transaction_volume: int
    inflation_rate: float
    health_score: float
    recorded_at: str


class AdjustResponse(BaseModel):
    """调整响应"""

    policy: str
    tax_rate: float
    listing_fee_rate: float
    npc_price_modifier: float
    reward_modifier: float


@router.get("/status", response_model=EconomyStatusResponse)
async def get_economy_status():
    """获取当前经济状态"""
    return economy_controller.get_economy_status()


@router.get("/history", response_model=list[EconomyHistoryResponse])
async def get_economy_history(
    limit: int = Query(10, ge=1, le=100, description="返回记录数量"),
):
    """获取经济历史记录"""
    history = economy_controller.get_history(limit=limit)
    return [EconomyHistoryResponse(**h) for h in history]


@router.get("/metrics", response_model=EconomyMetricsResponse)
async def get_economy_metrics(
    limit: int = Query(10, ge=1, le=100, description="返回记录数量")
):
    """获取经济指标"""
    metrics = economy_controller.get_metrics(limit=limit)
    return EconomyMetricsResponse(**metrics)


@router.get("/prices", response_model=list[PriceIndexResponse])
async def get_price_index():
    """获取当前物价指数"""
    all_prices = pricing_engine.get_all_shop_base_prices()
    return [
        PriceIndexResponse(shop_type=shop_type, items=items)
        for shop_type, items in all_prices.items()
    ]


@router.post("/monitor", response_model=MonitorResponse)
async def monitor_economy(request: MonitorRequest):
    """监控经济健康度

    提交当前经济数据，返回健康度分析。
    """
    snapshot = economy_controller.monitor_economy_health(
        total_money_supply=request.total_money_supply,
        player_count=request.player_count,
        transaction_volume=request.transaction_volume,
        previous_money_supply=request.previous_money_supply,
    )
    return MonitorResponse(
        total_money_supply=snapshot.total_money_supply,
        avg_player_wealth=snapshot.avg_player_wealth,
        transaction_volume=snapshot.transaction_volume,
        inflation_rate=snapshot.inflation_rate,
        health_score=snapshot.health_score,
        recorded_at=snapshot.recorded_at.isoformat(),
    )


@router.post("/adjust", response_model=AdjustResponse)
async def adjust_economy(request: MonitorRequest):
    """根据经济状况调整参数

    提交当前经济数据，系统自动调整税率等参数。
    """
    snapshot = economy_controller.monitor_economy_health(
        total_money_supply=request.total_money_supply,
        player_count=request.player_count,
        transaction_volume=request.transaction_volume,
        previous_money_supply=request.previous_money_supply,
    )
    adjustments = economy_controller.adjust_economy(snapshot)
    return AdjustResponse(**adjustments)


@router.get("/fees")
async def get_current_fees():
    """获取当前费率"""
    return {
        "tax_rate": economy_controller.tax_rate,
        "listing_fee_rate": economy_controller.listing_fee_rate,
        "auction_fee_rate": economy_controller.auction_fee_rate,
        "npc_price_modifier": economy_controller.npc_price_modifier,
        "reward_modifier": economy_controller.reward_modifier,
    }


@router.post("/calculate-fee")
async def calculate_fee(
    amount: int = Query(..., ge=1, description="金额"),
    fee_type: str = Query("listing", description="费用类型: listing/auction/tax"),
):
    """计算费用

    Args:
        amount: 金额
        fee_type: 费用类型
    """
    if fee_type == "listing":
        fee = economy_controller.calculate_listing_fee(amount)
    elif fee_type == "auction":
        fee = economy_controller.calculate_auction_fee(amount)
    elif fee_type == "tax":
        fee = economy_controller.calculate_transaction_tax(amount)
    else:
        fee = 0

    return {
        "amount": amount,
        "fee_type": fee_type,
        "fee": fee,
        "net_amount": amount - fee,
    }
