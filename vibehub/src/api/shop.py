"""商店 API 路由

提供 NPC 商店的 HTTP 接口。
"""


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.shop import shop_manager

router = APIRouter(prefix="/api/shop", tags=["shop"])


class BuyRequest(BaseModel):
    """购买请求"""

    item_id: str = Field(..., description="物品 ID")
    quantity: int = Field(1, ge=1, description="购买数量")
    player_id: str = Field(..., description="玩家 ID")
    player_gold: int = Field(..., ge=0, description="玩家金币")


class BuyResponse(BaseModel):
    """购买响应"""

    success: bool
    message: str
    item_name: str = ""
    quantity: int = 0
    total_cost: int = 0
    remaining_gold: int = 0


class ShopItemResponse(BaseModel):
    """商店商品响应"""

    item_id: str
    item_name: str
    item_type: str
    base_price: int
    current_price: int
    stock: int
    max_stock: int


class ShopResponse(BaseModel):
    """商店响应"""

    shop_type: str
    name: str
    refresh_cycle: str
    last_refresh: str
    item_count: int


class ShopDetailResponse(BaseModel):
    """商店详情响应"""

    shop_type: str
    name: str
    refresh_cycle: str
    last_refresh: str
    items: list[ShopItemResponse]


@router.get(
    "",
    response_model=list[ShopResponse],
    summary="获取所有商店列表",
    description="返回所有可用的 NPC 商店信息。",
    responses={
        200: {"description": "成功返回商店列表"},
    },
)
async def get_all_shops():
    """获取所有商店列表"""
    return shop_manager.get_all_shops()


@router.get(
    "/{shop_type}",
    response_model=ShopDetailResponse,
    summary="获取指定商店详情",
    description="获取指定类型商店的详细信息和商品列表。",
    responses={
        200: {"description": "成功返回商店详情"},
        404: {"description": "商店不存在"},
    },
)
async def get_shop(shop_type: str):
    """获取指定商店的商品列表"""
    shop_info = shop_manager.get_shop_info(shop_type)
    if not shop_info:
        raise HTTPException(status_code=404, detail=f"商店不存在: {shop_type}")
    return shop_info


@router.get(
    "/{shop_type}/items",
    response_model=list[ShopItemResponse],
    summary="获取商店商品列表",
    description="获取指定商店的所有商品信息。",
    responses={
        200: {"description": "成功返回商品列表"},
        404: {"description": "商店不存在"},
    },
)
async def get_shop_items(shop_type: str):
    """获取商店商品列表"""
    items = shop_manager.get_shop_items(shop_type)
    if not items:
        raise HTTPException(status_code=404, detail=f"商店不存在: {shop_type}")
    return [
        ShopItemResponse(
            item_id=item.item_id,
            item_name=item.item_name,
            item_type=item.item_type,
            base_price=item.base_price,
            current_price=item.current_price,
            stock=item.stock,
            max_stock=item.max_stock,
        )
        for item in items
    ]


@router.post(
    "/{shop_type}/buy",
    response_model=BuyResponse,
    summary="购买商品",
    description="从指定商店购买商品，需要足够的金币和库存。",
    responses={
        200: {"description": "购买结果"},
    },
)
async def buy_item(shop_type: str, request: BuyRequest):
    """购买商品"""
    result = shop_manager.buy_item(
        shop_type=shop_type,
        item_id=request.item_id,
        quantity=request.quantity,
        player_gold=request.player_gold,
    )
    return BuyResponse(
        success=result.success,
        message=result.message,
        item_name=result.item_name,
        quantity=result.quantity,
        total_cost=result.total_cost,
        remaining_gold=result.remaining_gold,
    )


@router.post(
    "/{shop_type}/refresh",
    summary="手动刷新商店",
    description="手动刷新商店库存。可选择强制刷新或等待刷新周期。",
    responses={
        200: {"description": "刷新成功"},
        400: {"description": "刷新失败"},
    },
)
async def refresh_shop(shop_type: str, force: bool = False):
    """手动刷新商店

    Args:
        shop_type: 商店类型
        force: 是否强制刷新
    """
    success = shop_manager.refresh_shop(shop_type, force=force)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="刷新失败，可能商店不存在或未到刷新时间",
        )
    return {"success": True, "message": "商店已刷新"}
