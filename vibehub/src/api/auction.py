"""拍卖 API 路由

提供拍卖系统的 HTTP 接口。
"""


from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.core.auction import auction_manager

router = APIRouter(prefix="/api/auctions", tags=["拍卖"])


class CreateAuctionRequest(BaseModel):
    """创建拍卖请求"""

    seller_id: str = Field(..., description="卖家 ID")
    seller_name: str = Field(..., description="卖家名称")
    item_type: str = Field(..., description="物品类型")
    item_name: str = Field(..., description="物品名称")
    quantity: int = Field(..., ge=1, description="数量")
    starting_price: int = Field(..., ge=1, description="起拍价")
    duration_hours: int = Field(24, ge=24, le=72, description="拍卖时长（小时）")
    buyout_price: int | None = Field(None, ge=1, description="一口价")


class CreateAuctionResponse(BaseModel):
    """创建拍卖响应"""

    success: bool
    message: str
    auction_id: str = ""


class BidRequest(BaseModel):
    """出价请求"""

    bidder_id: str = Field(..., description="出价者 ID")
    bidder_name: str = Field(..., description="出价者名称")
    bid_amount: int = Field(..., ge=1, description="出价金额")


class BidResponse(BaseModel):
    """出价响应"""

    success: bool
    message: str
    new_price: int = 0
    is_buyout: bool = False


class BuyoutRequest(BaseModel):
    """一口价请求"""

    buyer_id: str = Field(..., description="买家 ID")
    buyer_name: str = Field(..., description="买家名称")


class AuctionResponse(BaseModel):
    """拍卖响应"""

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
    created_at: str
    ends_at: str
    ended_at: str | None


class BidHistoryResponse(BaseModel):
    """出价历史响应"""

    bid_id: str
    auction_id: str
    bidder_id: str
    bidder_name: str
    bid_amount: int
    created_at: str
    is_winning: bool


class SettlementResponse(BaseModel):
    """结算信息响应"""

    has_winner: bool
    winner_id: str | None = None
    winner_name: str | None = None
    final_price: int = 0
    fee: int = 0
    seller_receives: int = 0


class CancelRequest(BaseModel):
    """取消拍卖请求"""

    player_id: str = Field(..., description="玩家 ID")


@router.get("", response_model=list[AuctionResponse])
async def get_auctions(
    item_type: str | None = Query(None, description="物品类型过滤"),
    item_name: str | None = Query(None, description="物品名称过滤"),
    seller_id: str | None = Query(None, description="卖家 ID 过滤"),
    status: str = Query("active", description="状态过滤"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取拍卖列表"""
    auctions = auction_manager.get_auctions(
        item_type=item_type,
        item_name=item_name,
        seller_id=seller_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [
        AuctionResponse(
            auction_id=a.auction_id,
            seller_id=a.seller_id,
            seller_name=a.seller_name,
            item_type=a.item_type,
            item_name=a.item_name,
            quantity=a.quantity,
            starting_price=a.starting_price,
            current_price=a.current_price,
            buyout_price=a.buyout_price,
            min_increment=a.min_increment,
            current_bidder_id=a.current_bidder_id,
            current_bidder_name=a.current_bidder_name,
            bid_count=a.bid_count,
            status=a.status,
            created_at=a.created_at.isoformat(),
            ends_at=a.ends_at.isoformat(),
            ended_at=a.ended_at.isoformat() if a.ended_at else None,
        )
        for a in auctions
    ]


@router.post("", response_model=CreateAuctionResponse)
async def create_auction(request: CreateAuctionRequest):
    """创建拍卖"""
    result = auction_manager.create_auction(
        seller_id=request.seller_id,
        seller_name=request.seller_name,
        item_type=request.item_type,
        item_name=request.item_name,
        quantity=request.quantity,
        starting_price=request.starting_price,
        duration_hours=request.duration_hours,
        buyout_price=request.buyout_price,
    )
    return CreateAuctionResponse(
        success=result.success,
        message=result.message,
        auction_id=result.auction_id,
    )


@router.get("/{auction_id}", response_model=AuctionResponse)
async def get_auction(auction_id: str):
    """获取拍卖详情"""
    auction = auction_manager.get_auction(auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="拍卖不存在")
    return AuctionResponse(
        auction_id=auction.auction_id,
        seller_id=auction.seller_id,
        seller_name=auction.seller_name,
        item_type=auction.item_type,
        item_name=auction.item_name,
        quantity=auction.quantity,
        starting_price=auction.starting_price,
        current_price=auction.current_price,
        buyout_price=auction.buyout_price,
        min_increment=auction.min_increment,
        current_bidder_id=auction.current_bidder_id,
        current_bidder_name=auction.current_bidder_name,
        bid_count=auction.bid_count,
        status=auction.status,
        created_at=auction.created_at.isoformat(),
        ends_at=auction.ends_at.isoformat(),
        ended_at=auction.ended_at.isoformat() if auction.ended_at else None,
    )


@router.post("/{auction_id}/bid", response_model=BidResponse)
async def place_bid(auction_id: str, request: BidRequest):
    """出价"""
    result = auction_manager.place_bid(
        auction_id=auction_id,
        bidder_id=request.bidder_id,
        bidder_name=request.bidder_name,
        bid_amount=request.bid_amount,
    )
    return BidResponse(
        success=result.success,
        message=result.message,
        new_price=result.new_price,
        is_buyout=result.is_buyout,
    )


@router.post("/{auction_id}/buyout", response_model=BidResponse)
async def buyout(auction_id: str, request: BuyoutRequest):
    """一口价购买"""
    result = auction_manager.buyout(
        auction_id=auction_id,
        buyer_id=request.buyer_id,
        buyer_name=request.buyer_name,
    )
    return BidResponse(
        success=result.success,
        message=result.message,
        new_price=result.new_price,
        is_buyout=result.is_buyout,
    )


@router.delete("/{auction_id}")
async def cancel_auction(auction_id: str, request: CancelRequest):
    """取消拍卖"""
    success, message = auction_manager.cancel_auction(auction_id, request.player_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.get("/{auction_id}/bids", response_model=list[BidHistoryResponse])
async def get_auction_bids(auction_id: str):
    """获取拍卖出价历史"""
    bids = auction_manager.get_auction_bids(auction_id)
    return [
        BidHistoryResponse(
            bid_id=b.bid_id,
            auction_id=b.auction_id,
            bidder_id=b.bidder_id,
            bidder_name=b.bidder_name,
            bid_amount=b.bid_amount,
            created_at=b.created_at.isoformat(),
            is_winning=b.is_winning,
        )
        for b in bids
    ]


@router.get("/{auction_id}/settlement", response_model=SettlementResponse)
async def get_settlement(auction_id: str):
    """获取拍卖结算信息"""
    settlement = auction_manager.calculate_settlement(auction_id)
    if not settlement:
        raise HTTPException(status_code=404, detail="拍卖不存在")
    return SettlementResponse(**settlement)


@router.get("/player/{player_id}/auctions", response_model=list[AuctionResponse])
async def get_player_auctions(player_id: str):
    """获取玩家创建的拍卖"""
    auctions = auction_manager.get_player_auctions(player_id)
    return [
        AuctionResponse(
            auction_id=a.auction_id,
            seller_id=a.seller_id,
            seller_name=a.seller_name,
            item_type=a.item_type,
            item_name=a.item_name,
            quantity=a.quantity,
            starting_price=a.starting_price,
            current_price=a.current_price,
            buyout_price=a.buyout_price,
            min_increment=a.min_increment,
            current_bidder_id=a.current_bidder_id,
            current_bidder_name=a.current_bidder_name,
            bid_count=a.bid_count,
            status=a.status,
            created_at=a.created_at.isoformat(),
            ends_at=a.ends_at.isoformat(),
            ended_at=a.ended_at.isoformat() if a.ended_at else None,
        )
        for a in auctions
    ]


@router.get("/player/{player_id}/bids", response_model=list[BidHistoryResponse])
async def get_player_bids(player_id: str):
    """获取玩家的出价记录"""
    bids = auction_manager.get_player_bids(player_id)
    return [
        BidHistoryResponse(
            bid_id=b.bid_id,
            auction_id=b.auction_id,
            bidder_id=b.bidder_id,
            bidder_name=b.bidder_name,
            bid_amount=b.bid_amount,
            created_at=b.created_at.isoformat(),
            is_winning=b.is_winning,
        )
        for b in bids
    ]
