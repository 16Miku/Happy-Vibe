"""排行榜系统 API

提供排行榜相关的 REST API 端点，基于数据库的赛季排行榜系统。
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.core.leaderboard_manager import LeaderboardManager
from src.storage.database import get_db
from src.storage.models import LeaderboardType

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


# ==================== Pydantic 模型 ====================


class LeaderboardEntry(BaseModel):
    """排行榜条目"""

    rank: int
    entity_id: str
    entity_name: str
    score: float | int
    level: int | None = None
    experience: int | None = None
    gold: int | None = None
    achievement_count: int | None = None
    member_count: int | None = None
    contribution_points: int | None = None


class LeaderboardResponse(BaseModel):
    """排行榜响应"""

    leaderboard_id: str
    season_id: str
    leaderboard_type: str
    total: int
    offset: int
    limit: int
    last_updated: str
    rankings: list[LeaderboardEntry]


class PlayerRankResponse(BaseModel):
    """玩家排名响应"""

    player_id: str
    entity_name: str | None = None
    rank: int
    total: int
    score: float | int
    on_leaderboard: bool
    percentile: float | None = None
    level: int | None = None
    experience: int | None = None
    gold: int | None = None
    achievement_count: int | None = None


class SnapshotResponse(BaseModel):
    """快照响应"""

    snapshot_id: str
    leaderboard_type: str
    snapshot_time: str
    entry_count: int | None = None


# ==================== API 端点 ====================


@router.get("/types")
async def get_leaderboard_types() -> dict[str, Any]:
    """获取所有排行榜类型

    Returns:
        排行榜类型列表
    """
    return {
        "types": [
            {
                "type": LeaderboardType.INDIVIDUAL.value,
                "name": "个人排行",
                "description": "按玩家等级、经验、金币综合评分",
                "icon": "🏆",
                "scoring": "level * 100 + exp / 10 + gold / 1000",
            },
            {
                "type": LeaderboardType.GUILD.value,
                "name": "公会排行",
                "description": "按公会等级、成员数、贡献点综合评分",
                "icon": "👥",
                "scoring": "level * 500 + member_count * 50 + contribution_points",
            },
            {
                "type": LeaderboardType.ACHIEVEMENT.value,
                "name": "成就排行",
                "description": "按完成成就数量和稀有度评分",
                "icon": "🎖️",
                "scoring": "按成就完成数量统计",
            },
        ]
    }


@router.get("/{leaderboard_type}")
async def get_leaderboard(
    leaderboard_type: str,
    season_id: str | None = Query(None, description="赛季 ID，默认为当前赛季"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> dict[str, Any]:
    """获取排行榜数据

    Args:
        leaderboard_type: 排行榜类型 (individual/guild/achievement)
        season_id: 赛季 ID
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        排行榜数据
    """
    # 验证排行榜类型
    valid_types = [t.value for t in LeaderboardType]
    if leaderboard_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type: {leaderboard_type}. Must be one of: {valid_types}",
        )

    db = get_db()
    with db.get_session() as session:
        manager = LeaderboardManager(session)
        result = await manager.get_leaderboard(leaderboard_type, season_id, limit, offset)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )

    return result


@router.get("/{leaderboard_type}/rank/{player_id}")
async def get_player_rank(
    leaderboard_type: str,
    player_id: str,
    season_id: str | None = Query(None, description="赛季 ID，默认为当前赛季"),
) -> dict[str, Any]:
    """获取玩家在排行榜中的排名

    Args:
        leaderboard_type: 排行榜类型
        player_id: 玩家 ID
        season_id: 赛季 ID

    Returns:
        玩家排名信息
    """
    # 验证排行榜类型
    valid_types = [t.value for t in LeaderboardType]
    if leaderboard_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type: {leaderboard_type}",
        )

    db = get_db()
    with db.get_session() as session:
        manager = LeaderboardManager(session)
        result = await manager.get_player_rank(player_id, leaderboard_type, season_id)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )

    return result


@router.get("/{leaderboard_type}/top")
async def get_top_players(
    leaderboard_type: str,
    season_id: str | None = Query(None, description="赛季 ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
) -> dict[str, Any]:
    """获取排行榜前 N 名

    Args:
        leaderboard_type: 排行榜类型
        season_id: 赛季 ID
        limit: 返回数量

    Returns:
        前 N 名玩家列表
    """
    valid_types = [t.value for t in LeaderboardType]
    if leaderboard_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type: {leaderboard_type}",
        )

    db = get_db()
    with db.get_session() as session:
        manager = LeaderboardManager(session)
        result = await manager.get_top_players(leaderboard_type, season_id, limit)

    return {
        "leaderboard_type": leaderboard_type,
        "season_id": season_id,
        "limit": limit,
        "players": result,
    }


@router.post("/{leaderboard_type}/update")
async def update_leaderboard(
    leaderboard_type: str,
    season_id: str = Query(..., description="赛季 ID"),
) -> dict[str, Any]:
    """更新排行榜数据

    Args:
        leaderboard_type: 排行榜类型
        season_id: 赛季 ID

    Returns:
        更新后的排行榜信息
    """
    valid_types = [t.value for t in LeaderboardType]
    if leaderboard_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type: {leaderboard_type}",
        )

    db = get_db()
    with db.get_session() as session:
        manager = LeaderboardManager(session)
        result = await manager.update_leaderboard(leaderboard_type, season_id)

    return result


@router.get("/{leaderboard_type}/snapshots")
async def get_snapshots(
    leaderboard_type: str,
    season_id: str = Query(..., description="赛季 ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
) -> dict[str, Any]:
    """获取排行榜快照列表

    Args:
        leaderboard_type: 排行榜类型
        season_id: 赛季 ID
        limit: 返回数量

    Returns:
        快照列表
    """
    valid_types = [t.value for t in LeaderboardType]
    if leaderboard_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type: {leaderboard_type}",
        )

    db = get_db()
    with db.get_session() as session:
        manager = LeaderboardManager(session)
        snapshots = await manager.get_snapshots(season_id, leaderboard_type, limit)

    return {
        "leaderboard_type": leaderboard_type,
        "season_id": season_id,
        "snapshots": snapshots,
    }


@router.post("/{leaderboard_type}/snapshot")
async def create_snapshot(
    leaderboard_type: str,
    season_id: str = Query(..., description="赛季 ID"),
) -> dict[str, Any]:
    """创建排行榜快照

    Args:
        leaderboard_type: 排行榜类型
        season_id: 赛季 ID

    Returns:
        快照信息
    """
    valid_types = [t.value for t in LeaderboardType]
    if leaderboard_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type: {leaderboard_type}",
        )

    db = get_db()
    with db.get_session() as session:
        manager = LeaderboardManager(session)
        result = await manager.create_snapshot(leaderboard_type, season_id)

    return result


@router.get("/around/{player_id}")
async def get_leaderboard_around_player(
    player_id: str,
    leaderboard_type: str = Query(LeaderboardType.INDIVIDUAL.value, description="排行榜类型"),
    season_id: str | None = Query(None, description="赛季 ID"),
    range_size: int = Query(5, ge=1, le=10, description="上下各显示多少名"),
) -> dict[str, Any]:
    """获取玩家周围的排行榜数据

    Args:
        player_id: 玩家 ID
        leaderboard_type: 排行榜类型
        season_id: 赛季 ID
        range_size: 上下各显示多少名

    Returns:
        玩家周围的排行榜数据
    """
    valid_types = [t.value for t in LeaderboardType]
    if leaderboard_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type: {leaderboard_type}",
        )

    # 获取玩家排名
    db = get_db()
    with db.get_session() as session:
        manager = LeaderboardManager(session)
        player_rank = await manager.get_player_rank(player_id, leaderboard_type, season_id)

    if "error" in player_rank or not player_rank.get("on_leaderboard"):
        return {
            "player_id": player_id,
            "on_leaderboard": False,
            "entries": [],
        }

    rank = player_rank["rank"]
    total = player_rank["total"]

    # 计算范围
    start = max(1, rank - range_size)
    end = min(total, rank + range_size)
    offset = start - 1
    limit = end - start + 1

    # 获取排行榜数据
    with db.get_session() as session:
        manager = LeaderboardManager(session)
        result = await manager.get_leaderboard(leaderboard_type, season_id, limit, offset)

    # 标记当前玩家
    entries = result.get("rankings", [])
    for entry in entries:
        entry["is_self"] = entry.get("entity_id") == player_id

    return {
        "player_id": player_id,
        "on_leaderboard": True,
        "player_rank": rank,
        "entries": entries,
    }
