"""市场 API 路由

提供玩家交易市场的 HTTP 接口。
"""


from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.core.market import market_manager

router = APIRouter(prefix="/api/market", tags=["market"])


class CreateListingRequest(BaseModel):
    """创建挂单请求"""

    seller_id: str = Field(..., description="卖家 ID")
    seller_name: str = Field(..., description="卖家名称")
    item_type: str = Field(..., description="物品类型")
    item_name: str = Field(..., description="物品名称")
    quantity: int = Field(..., ge=1, description="数量")
    unit_price: int = Field(..., ge=1, description="单价")
    player_gold: int = Field(..., ge=0, description="玩家金币")


class CreateListingResponse(BaseModel):
    """创建挂单响应"""

    success: bool
    message: str
    listing_id: str = ""
    listing_fee: int = 0


class PurchaseRequest(BaseModel):
    """购买请求"""

    buyer_id: str = Field(..., description="买家 ID")
    buyer_gold: int = Field(..., ge=0, description="买家金币")
    quantity: int | None = Field(None, ge=1, description="购买数量")


class PurchaseResponse(BaseModel):
    """购买响应"""

    success: bool
    message: str
    item_name: str = ""
    quantity: int = 0
    total_cost: int = 0
    remaining_gold: int = 0


class ListingResponse(BaseModel):
    """挂单响应"""

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
    created_at: str
    expires_at: str


class CancelRequest(BaseModel):
    """取消挂单请求"""

    player_id: str = Field(..., description="玩家 ID")


class MarketStatsResponse(BaseModel):
    """市场统计响应"""

    total_listings: int
    total_value: int
    item_types: list[str]
    unique_sellers: int


@router.get(
    "/listings",
    response_model=list[ListingResponse],
    summary="获取市场挂单列表",
    description="获取市场上的挂单列表，支持按物品类型、名称、卖家等条件筛选。",
    responses={
        200: {"description": "成功返回挂单列表"},
    },
)
async def get_listings(
    item_type: str | None = Query(None, description="物品类型过滤"),
    item_name: str | None = Query(None, description="物品名称过滤"),
    seller_id: str | None = Query(None, description="卖家 ID 过滤"),
    status: str = Query("active", description="状态过滤"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取市场挂单列表"""
    listings = market_manager.get_listings(
        item_type=item_type,
        item_name=item_name,
        seller_id=seller_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [
        ListingResponse(
            listing_id=listing.listing_id,
            seller_id=listing.seller_id,
            seller_name=listing.seller_name,
            item_type=listing.item_type,
            item_name=listing.item_name,
            quantity=listing.quantity,
            unit_price=listing.unit_price,
            total_price=listing.total_price,
            listing_fee=listing.listing_fee,
            status=listing.status,
            created_at=listing.created_at.isoformat(),
            expires_at=listing.expires_at.isoformat(),
        )
        for listing in listings
    ]


@router.post(
    "/listings",
    response_model=CreateListingResponse,
    summary="创建挂单",
    description="在市场上创建新的挂单，需要支付挂单费用。",
    responses={
        200: {"description": "挂单创建结果"},
    },
)
async def create_listing(request: CreateListingRequest):
    """创建挂单"""
    result = market_manager.create_listing(
        seller_id=request.seller_id,
        seller_name=request.seller_name,
        item_type=request.item_type,
        item_name=request.item_name,
        quantity=request.quantity,
        unit_price=request.unit_price,
        player_gold=request.player_gold,
    )
    return CreateListingResponse(
        success=result.success,
        message=result.message,
        listing_id=result.listing_id,
        listing_fee=result.listing_fee,
    )


@router.get(
    "/listings/{listing_id}",
    response_model=ListingResponse,
    summary="获取挂单详情",
    description="获取指定挂单的详细信息。",
    responses={
        200: {"description": "成功返回挂单详情"},
        404: {"description": "挂单不存在"},
    },
)
async def get_listing(listing_id: str):
    """获取挂单详情"""
    listing = market_manager.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="挂单不存在")
    return ListingResponse(
        listing_id=listing.listing_id,
        seller_id=listing.seller_id,
        seller_name=listing.seller_name,
        item_type=listing.item_type,
        item_name=listing.item_name,
        quantity=listing.quantity,
        unit_price=listing.unit_price,
        total_price=listing.total_price,
        listing_fee=listing.listing_fee,
        status=listing.status,
        created_at=listing.created_at.isoformat(),
        expires_at=listing.expires_at.isoformat(),
    )


@router.delete(
    "/listings/{listing_id}",
    summary="取消挂单",
    description="取消指定的挂单，只有卖家本人可以取消。",
    responses={
        200: {"description": "取消成功"},
        400: {"description": "取消失败"},
    },
)
async def cancel_listing(listing_id: str, request: CancelRequest):
    """取消挂单"""
    success, message = market_manager.cancel_listing(listing_id, request.player_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.post(
    "/listings/{listing_id}/buy",
    response_model=PurchaseResponse,
    summary="购买挂单",
    description="购买市场上的挂单，可以购买部分或全部数量。",
    responses={
        200: {"description": "购买结果"},
    },
)
async def purchase_listing(listing_id: str, request: PurchaseRequest):
    """购买挂单"""
    result = market_manager.purchase_listing(
        listing_id=listing_id,
        buyer_id=request.buyer_id,
        buyer_gold=request.buyer_gold,
        quantity=request.quantity,
    )
    return PurchaseResponse(
        success=result.success,
        message=result.message,
        item_name=result.item_name,
        quantity=result.quantity,
        total_cost=result.total_cost,
        remaining_gold=result.remaining_gold,
    )


@router.get(
    "/stats",
    response_model=MarketStatsResponse,
    summary="获取市场统计信息",
    description="获取市场的整体统计数据，包括挂单数量、总价值等。",
    responses={
        200: {"description": "成功返回统计信息"},
    },
)
async def get_market_stats():
    """获取市场统计信息"""
    stats = market_manager.get_market_stats()
    return MarketStatsResponse(**stats)


@router.get(
    "/player/{player_id}/listings",
    response_model=list[ListingResponse],
    summary="获取玩家的所有挂单",
    description="获取指定玩家创建的所有挂单。",
    responses={
        200: {"description": "成功返回玩家挂单列表"},
    },
)
async def get_player_listings(player_id: str):
    """获取玩家的所有挂单"""
    listings = market_manager.get_player_listings(player_id)
    return [
        ListingResponse(
            listing_id=listing.listing_id,
            seller_id=listing.seller_id,
            seller_name=listing.seller_name,
            item_type=listing.item_type,
            item_name=listing.item_name,
            quantity=listing.quantity,
            unit_price=listing.unit_price,
            total_price=listing.total_price,
            listing_fee=listing.listing_fee,
            status=listing.status,
            created_at=listing.created_at.isoformat(),
            expires_at=listing.expires_at.isoformat(),
        )
        for listing in listings
    ]
