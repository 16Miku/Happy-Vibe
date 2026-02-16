"""PVP 竞技场 API 路由

提供 PVP 匹配、对战、观战、排行榜等功能的 REST API 端点。
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.pvp_manager import PVPManager
from src.storage.database import get_db
from src.storage.models import Player, PVPMatchType


# ============ Pydantic 模型 ============


class MatchmakingRequest(BaseModel):
    """匹配请求模型"""

    player_id: str
    match_type: str = PVPMatchType.ARENA.value
    rating_range: int = 200


class MatchmakingResponse(BaseModel):
    """匹配响应模型"""

    status: str  # queued, matched, already_queued
    player_id: str | None = None
    rating: int | None = None
    queue_position: int | None = None
    estimated_wait_time: int | None = None
    match: dict | None = None


class CancelMatchmakingResponse(BaseModel):
    """取消匹配响应模型"""

    status: str
    player_id: str


class MatchInfoResponse(BaseModel):
    """对战信息响应模型"""

    match_id: str
    match_type: str
    player_a_id: str
    player_b_id: str
    player_a_rating: int
    player_b_rating: int
    status: str
    score_a: int
    score_b: int
    winner_id: str | None
    duration_seconds: int
    moves_a: int
    moves_b: int
    spectator_count: int
    allow_spectate: bool
    created_at: str
    started_at: str | None
    finished_at: str | None


class StartMatchRequest(BaseModel):
    """开始对战请求模型"""

    match_id: str


class StartMatchResponse(BaseModel):
    """开始对战响应模型"""

    match_id: str
    status: str
    started_at: str


class SubmitResultRequest(BaseModel):
    """提交结果请求模型"""

    match_id: str
    winner_id: str | None
    score_a: int
    score_b: int
    moves_a: int = 0
    moves_b: int = 0


class RatingChange(BaseModel):
    """积分变化模型"""

    player_id: str
    old_rating: int
    new_rating: int
    change: int


class RatingChanges(BaseModel):
    """积分变化集合模型"""

    player_a: RatingChange
    player_b: RatingChange


class SubmitResultResponse(BaseModel):
    """提交结果响应模型"""

    match_id: str
    status: str
    winner_id: str | None
    score_a: int
    score_b: int
    duration_seconds: int
    rating_changes: RatingChanges


class SpectateRequest(BaseModel):
    """观战请求模型"""

    match_id: str
    player_id: str


class SpectateResponse(BaseModel):
    """观战响应模型"""

    status: str
    match_id: str
    spectator_id: str | None = None
    spectator_count: int | None = None


class SpectatorInfo(BaseModel):
    """观战者信息模型"""

    spectator_id: str
    player_id: str
    joined_at: str


class SpectatorsResponse(BaseModel):
    """观战列表响应模型"""

    match_id: str
    spectators: list[SpectatorInfo]
    count: int


class RankingInfo(BaseModel):
    """排名信息模型"""

    player_id: str
    season_id: str
    rating: int
    max_rating: int
    rank: int
    matches_played: int
    matches_won: int
    matches_lost: int
    matches_drawn: int
    current_streak: int
    max_streak: int
    win_rate: float


class RankingListResponse(BaseModel):
    """排行榜响应模型"""

    season_id: str | None
    rankings: list[RankingInfo]
    total: int


class ActiveMatchInfo(BaseModel):
    """活跃对战信息模型"""

    match_id: str
    match_type: str
    player_a_id: str
    player_b_id: str
    player_a_rating: int
    player_b_rating: int
    status: str
    score_a: int
    score_b: int
    spectator_count: int
    allow_spectate: bool
    created_at: str
    started_at: str | None


class ActiveMatchesResponse(BaseModel):
    """活跃对战列表响应模型"""

    matches: list[ActiveMatchInfo]
    total: int


class MatchHistoryInfo(BaseModel):
    """对战历史信息模型"""

    match_id: str
    match_type: str
    opponent_id: str
    player_score: int
    opponent_score: int
    is_winner: bool
    is_draw: bool
    finished_at: str | None


class MatchHistoryResponse(BaseModel):
    """对战历史响应模型"""

    matches: list[MatchHistoryInfo]
    total: int


# ============ 依赖注入 ============


def get_db_session():
    """获取数据库会话"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


def get_pvp_manager(session: Session = Depends(get_db_session)) -> PVPManager:
    """获取 PVP 管理器"""
    return PVPManager(session)


# ============ 路由定义 ============

router = APIRouter(prefix="/api/pvp", tags=["pvp"])


@router.post(
    "/matchmaking",
    response_model=MatchmakingResponse,
    summary="加入匹配队列",
    description="加入 PVP 匹配队列，系统会自动匹配积分相近的对手。",
    responses={
        200: {"description": "成功加入队列或匹配成功"},
        400: {"description": "已在队列中"},
        404: {"description": "玩家不存在"},
    },
)
async def join_matchmaking(
    request: MatchmakingRequest,
    manager: PVPManager = Depends(get_pvp_manager),
    session: Session = Depends(get_db_session),
) -> MatchmakingResponse:
    """加入匹配队列

    Args:
        request: 匹配请求

    Returns:
        匹配结果或队列状态
    """
    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == request.player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {request.player_id}",
        )

    try:
        result = manager.add_to_matchmaking(
            player_id=request.player_id,
            match_type=request.match_type,
            rating_range=request.rating_range,
        )

        if result["status"] == "matched":
            return MatchmakingResponse(
                status="matched",
                match=result["match"],
            )

        return MatchmakingResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/matchmaking",
    response_model=CancelMatchmakingResponse,
    summary="取消匹配",
    description="取消当前的匹配队列。",
    responses={
        200: {"description": "取消成功"},
    },
)
async def cancel_matchmaking(
    player_id: str,
    manager: PVPManager = Depends(get_pvp_manager),
) -> CancelMatchmakingResponse:
    """取消匹配

    Args:
        player_id: 玩家 ID

    Returns:
        取消结果
    """
    result = manager.cancel_matchmaking(player_id)
    return CancelMatchmakingResponse(**result)


@router.get(
    "/matchmaking/queue",
    summary="获取匹配队列状态",
    description="获取当前匹配队列的状态信息。",
    responses={
        200: {"description": "成功返回队列状态"},
    },
)
async def get_matchmaking_queue(
    manager: PVPManager = Depends(get_pvp_manager),
) -> dict:
    """获取匹配队列状态

    Returns:
        当前匹配队列信息
    """
    return {
        "queue_size": len(manager.matchmaking_queue),
        "players": [
            {
                "player_id": item.player_id,
                "rating": item.rating,
                "match_type": item.match_type,
                "queued_at": item.queued_at.isoformat(),
                "wait_seconds": int((datetime.now() - item.queued_at.replace(tzinfo=None)).total_seconds()),
            }
            for item in manager.matchmaking_queue
        ],
    }


@router.get(
    "/match/{match_id}",
    response_model=MatchInfoResponse,
    summary="获取对战信息",
    description="获取指定对战的详细信息。",
    responses={
        200: {"description": "成功返回对战信息"},
        404: {"description": "对战不存在"},
    },
)
async def get_match_info(
    match_id: str,
    manager: PVPManager = Depends(get_pvp_manager),
) -> MatchInfoResponse:
    """获取对战信息

    Args:
        match_id: 对战 ID

    Returns:
        对战详情
    """
    try:
        info = manager.get_match_info(match_id)
        return MatchInfoResponse(**info)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/match/{match_id}/start",
    response_model=StartMatchResponse,
    summary="开始对战",
    description="开始指定的对战，双方玩家准备就绪后调用。",
    responses={
        200: {"description": "对战开始成功"},
        400: {"description": "对战状态不正确"},
    },
)
async def start_match(
    match_id: str,
    manager: PVPManager = Depends(get_pvp_manager),
) -> StartMatchResponse:
    """开始对战

    Args:
        match_id: 对战 ID

    Returns:
        更新后的对战信息
    """
    try:
        result = manager.start_match(match_id)
        return StartMatchResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/match/{match_id}/result",
    response_model=SubmitResultResponse,
    summary="提交对战结果",
    description="提交对战结果，系统会自动计算积分变化。",
    responses={
        200: {"description": "结果提交成功"},
        400: {"description": "对战状态不正确"},
    },
)
async def submit_match_result(
    match_id: str,
    request: SubmitResultRequest,
    manager: PVPManager = Depends(get_pvp_manager),
) -> SubmitResultResponse:
    """提交对战结果

    Args:
        match_id: 对战 ID
        request: 结果数据

    Returns:
        更新后的对战信息和积分变化
    """
    try:
        result = manager.submit_result(
            match_id=match_id,
            winner_id=request.winner_id,
            score_a=request.score_a,
            score_b=request.score_b,
            moves_a=request.moves_a,
            moves_b=request.moves_b,
        )

        rating_changes = result.pop("rating_changes")

        return SubmitResultResponse(
            **result,
            rating_changes=RatingChanges(
                player_a=RatingChange(**rating_changes["player_a"]),
                player_b=RatingChange(**rating_changes["player_b"]),
            ),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/match/{match_id}/spectate",
    response_model=SpectateResponse,
    summary="加入观战",
    description="加入指定对战的观战，需要对战允许观战。",
    responses={
        200: {"description": "加入观战成功"},
        400: {"description": "对战不允许观战"},
        404: {"description": "玩家或对战不存在"},
    },
)
async def join_spectate(
    match_id: str,
    player_id: str,
    manager: PVPManager = Depends(get_pvp_manager),
    session: Session = Depends(get_db_session),
) -> SpectateResponse:
    """加入观战

    Args:
        match_id: 对战 ID
        player_id: 玩家 ID

    Returns:
        观战结果
    """
    # 验证玩家存在
    player = session.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"玩家不存在: {player_id}",
        )

    try:
        result = manager.join_spectate(match_id, player_id)
        return SpectateResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/match/{match_id}/spectate",
    response_model=SpectateResponse,
    summary="离开观战",
    description="离开当前观战的对战。",
    responses={
        200: {"description": "离开观战成功"},
    },
)
async def leave_spectate(
    match_id: str,
    spectator_id: str,
    manager: PVPManager = Depends(get_pvp_manager),
) -> SpectateResponse:
    """离开观战

    Args:
        match_id: 对战 ID
        spectator_id: 观战记录 ID

    Returns:
        离开结果
    """
    result = manager.leave_spectate(spectator_id)
    return SpectateResponse(
        status=result["status"],
        match_id=match_id,
    )


@router.get(
    "/match/{match_id}/spectators",
    response_model=SpectatorsResponse,
    summary="获取观战列表",
    description="获取指定对战的所有观战者列表。",
    responses={
        200: {"description": "成功返回观战者列表"},
    },
)
async def get_spectators(
    match_id: str,
    manager: PVPManager = Depends(get_pvp_manager),
) -> SpectatorsResponse:
    """获取观战列表

    Args:
        match_id: 对战 ID

    Returns:
        观战者列表
    """
    spectators = manager.get_spectators(match_id)
    return SpectatorsResponse(
        match_id=match_id,
        spectators=[SpectatorInfo(**s) for s in spectators],
        count=len(spectators),
    )


@router.get(
    "/matches/active",
    response_model=ActiveMatchesResponse,
    summary="获取活跃对战列表",
    description="获取当前正在进行的对战列表。",
    responses={
        200: {"description": "成功返回活跃对战列表"},
    },
)
async def get_active_matches(
    limit: int = 50,
    manager: PVPManager = Depends(get_pvp_manager),
) -> ActiveMatchesResponse:
    """获取活跃对战列表

    Args:
        limit: 返回数量限制

    Returns:
        活跃对战列表
    """
    matches = manager.get_active_matches(limit)
    return ActiveMatchesResponse(
        matches=[ActiveMatchInfo(**m) for m in matches],
        total=len(matches),
    )


@router.get(
    "/ranking",
    response_model=RankingListResponse,
    summary="获取积分排行榜",
    description="获取 PVP 积分排行榜，支持按赛季筛选。",
    responses={
        200: {"description": "成功返回排行榜"},
    },
)
async def get_ranking_list(
    season_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    manager: PVPManager = Depends(get_pvp_manager),
) -> RankingListResponse:
    """获取积分排行榜

    Args:
        season_id: 赛季 ID，默认为当前活跃赛季
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        排行榜列表
    """
    rankings = manager.get_ranking_list(season_id, limit, offset)
    return RankingListResponse(
        season_id=season_id,
        rankings=[RankingInfo(**r) for r in rankings],
        total=len(rankings),
    )


@router.get(
    "/ranking/{player_id}",
    response_model=RankingInfo,
    summary="获取玩家积分信息",
    description="获取指定玩家的 PVP 积分和排名信息。",
    responses={
        200: {"description": "成功返回玩家排名信息"},
        404: {"description": "玩家不存在"},
    },
)
async def get_player_ranking(
    player_id: str,
    season_id: str | None = None,
    manager: PVPManager = Depends(get_pvp_manager),
) -> RankingInfo:
    """获取玩家积分信息

    Args:
        player_id: 玩家 ID
        season_id: 赛季 ID，默认为当前活跃赛季

    Returns:
        玩家排名信息
    """
    try:
        ranking = manager.get_player_ranking(player_id, season_id)
        return RankingInfo(**ranking)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/history/{player_id}",
    response_model=MatchHistoryResponse,
    summary="获取玩家对战历史",
    description="获取指定玩家的 PVP 对战历史记录。",
    responses={
        200: {"description": "成功返回对战历史"},
    },
)
async def get_player_match_history(
    player_id: str,
    limit: int = 20,
    manager: PVPManager = Depends(get_pvp_manager),
) -> MatchHistoryResponse:
    """获取玩家对战历史

    Args:
        player_id: 玩家 ID
        limit: 返回数量限制

    Returns:
        对战历史列表
    """
    matches = manager.get_player_match_history(player_id, limit)
    return MatchHistoryResponse(
        matches=[MatchHistoryInfo(**m) for m in matches],
        total=len(matches),
    )
