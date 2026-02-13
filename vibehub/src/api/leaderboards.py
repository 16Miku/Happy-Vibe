"""排行榜系统 API

提供排行榜相关的 REST API 端点。
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


# ==================== 枚举和模型 ====================


class LeaderboardType(str, Enum):
    """排行榜类型"""

    LEVEL = "level"  # 等级榜
    CODING_TIME = "coding_time"  # 编码时长榜
    HARVEST = "harvest"  # 丰收榜
    WEALTH = "wealth"  # 财富榜
    FLOW_TIME = "flow_time"  # 心流时长榜
    BUILDING = "building"  # 建造榜
    GUILD = "guild"  # 公会榜


class LeaderboardPeriod(str, Enum):
    """排行榜周期"""

    DAILY = "daily"  # 每日
    WEEKLY = "weekly"  # 每周
    MONTHLY = "monthly"  # 每月
    ALL_TIME = "all_time"  # 全时


class LeaderboardEntry(BaseModel):
    """排行榜条目"""

    rank: int
    player_id: str
    username: str
    level: int
    value: int  # 排行榜对应的数值
    value_label: str  # 数值标签 (如 "67h 32m", "48.2k 能量")
    change: int = 0  # 排名变化 (正数上升，负数下降)


class LeaderboardReward(BaseModel):
    """排行榜奖励"""

    rank_range: str  # 如 "1", "2-3", "4-10"
    rewards: list[dict]  # [{type: "diamond", amount: 50}, ...]


# ==================== 内存存储 (临时) ====================

# 玩家数据缓存: player_id -> player_stats
_player_stats: dict[str, dict] = {}

# 排行榜缓存: (type, period) -> [entries]
_leaderboard_cache: dict[tuple[str, str], list[dict]] = {}

# 缓存时间戳
_cache_timestamps: dict[tuple[str, str], datetime] = {}

# 缓存有效期 (秒)
CACHE_TTL = {
    LeaderboardPeriod.DAILY.value: 300,  # 5 分钟
    LeaderboardPeriod.WEEKLY.value: 600,  # 10 分钟
    LeaderboardPeriod.MONTHLY.value: 1800,  # 30 分钟
    LeaderboardPeriod.ALL_TIME.value: 3600,  # 1 小时
}

# 排行榜奖励配置
LEADERBOARD_REWARDS = {
    LeaderboardType.LEVEL.value: {
        "1": [{"type": "diamond", "amount": 50}],
        "2-3": [{"type": "diamond", "amount": 30}],
        "4-10": [{"type": "diamond", "amount": 20}],
        "11-50": [{"type": "diamond", "amount": 10}],
        "51-100": [{"type": "diamond", "amount": 5}],
    },
    LeaderboardType.CODING_TIME.value: {
        "1": [{"type": "diamond", "amount": 50}, {"type": "seed", "item": "ai_divine_flower", "amount": 5}],
        "2-3": [{"type": "diamond", "amount": 30}, {"type": "seed", "item": "algorithm_rose", "amount": 10}],
        "4-10": [{"type": "diamond", "amount": 20}, {"type": "seed", "item": "api_orchid", "amount": 15}],
    },
    LeaderboardType.FLOW_TIME.value: {
        "1": [{"type": "diamond", "amount": 100}, {"type": "title", "item": "flow_master"}],
        "2-3": [{"type": "diamond", "amount": 50}],
        "4-10": [{"type": "diamond", "amount": 30}],
    },
}


def _format_duration(minutes: int) -> str:
    """格式化时长"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def _format_value(value: int, lb_type: str) -> str:
    """格式化数值"""
    if lb_type in [LeaderboardType.CODING_TIME.value, LeaderboardType.FLOW_TIME.value]:
        return _format_duration(value)
    elif value >= 10000:
        return f"{value / 1000:.1f}k"
    return str(value)


def _get_value_field(lb_type: str) -> str:
    """获取排行榜对应的数值字段"""
    mapping = {
        LeaderboardType.LEVEL.value: "level",
        LeaderboardType.CODING_TIME.value: "total_coding_minutes",
        LeaderboardType.HARVEST.value: "total_crops_harvested",
        LeaderboardType.WEALTH.value: "gold",
        LeaderboardType.FLOW_TIME.value: "total_flow_minutes",
        LeaderboardType.BUILDING.value: "decoration_score",
    }
    return mapping.get(lb_type, "level")


def _is_cache_valid(lb_type: str, period: str) -> bool:
    """检查缓存是否有效"""
    key = (lb_type, period)
    if key not in _cache_timestamps:
        return False

    ttl = CACHE_TTL.get(period, 300)
    return datetime.utcnow() - _cache_timestamps[key] < timedelta(seconds=ttl)


def _build_leaderboard(lb_type: str, period: str, limit: int = 100) -> list[dict]:
    """构建排行榜数据"""
    value_field = _get_value_field(lb_type)

    # 根据周期筛选数据
    now = datetime.utcnow()
    filtered_stats = []

    for player_id, stats in _player_stats.items():
        # 获取对应周期的数值
        if period == LeaderboardPeriod.DAILY.value:
            value = stats.get(f"daily_{value_field}", stats.get(value_field, 0))
        elif period == LeaderboardPeriod.WEEKLY.value:
            value = stats.get(f"weekly_{value_field}", stats.get(value_field, 0))
        elif period == LeaderboardPeriod.MONTHLY.value:
            value = stats.get(f"monthly_{value_field}", stats.get(value_field, 0))
        else:
            value = stats.get(value_field, 0)

        if value > 0:
            filtered_stats.append(
                {
                    "player_id": player_id,
                    "username": stats.get("username", f"Player_{player_id[:8]}"),
                    "level": stats.get("level", 1),
                    "value": value,
                }
            )

    # 排序
    filtered_stats.sort(key=lambda x: -x["value"])

    # 添加排名和格式化
    result = []
    for i, entry in enumerate(filtered_stats[:limit]):
        result.append(
            {
                "rank": i + 1,
                "player_id": entry["player_id"],
                "username": entry["username"],
                "level": entry["level"],
                "value": entry["value"],
                "value_label": _format_value(entry["value"], lb_type),
                "change": 0,  # TODO: 计算排名变化
            }
        )

    return result


# ==================== API 端点 ====================


@router.get("/types")
async def get_leaderboard_types() -> dict:
    """获取所有排行榜类型

    Returns:
        排行榜类型列表
    """
    return {
        "types": [
            {
                "type": LeaderboardType.LEVEL.value,
                "name": "等级榜",
                "description": "按玩家等级排名",
                "icon": "🏆",
                "periods": ["weekly", "all_time"],
            },
            {
                "type": LeaderboardType.CODING_TIME.value,
                "name": "编码时长榜",
                "description": "按编码时长排名",
                "icon": "⚡",
                "periods": ["daily", "weekly", "monthly"],
            },
            {
                "type": LeaderboardType.HARVEST.value,
                "name": "丰收榜",
                "description": "按收获作物数量排名",
                "icon": "🌾",
                "periods": ["weekly", "monthly"],
            },
            {
                "type": LeaderboardType.WEALTH.value,
                "name": "财富榜",
                "description": "按金币数量排名",
                "icon": "💰",
                "periods": ["weekly", "all_time"],
            },
            {
                "type": LeaderboardType.FLOW_TIME.value,
                "name": "心流时长榜",
                "description": "按心流状态时长排名",
                "icon": "🌟",
                "periods": ["weekly", "monthly"],
            },
            {
                "type": LeaderboardType.BUILDING.value,
                "name": "建造榜",
                "description": "按装饰度排名",
                "icon": "🏠",
                "periods": ["monthly", "all_time"],
            },
            {
                "type": LeaderboardType.GUILD.value,
                "name": "公会榜",
                "description": "按公会等级和贡献排名",
                "icon": "👥",
                "periods": ["weekly", "all_time"],
            },
        ]
    }


@router.get("/{lb_type}")
async def get_leaderboard(
    lb_type: str,
    period: str = Query(LeaderboardPeriod.WEEKLY.value, description="排行榜周期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
) -> dict:
    """获取排行榜数据

    Args:
        lb_type: 排行榜类型
        period: 周期
        page: 页码
        page_size: 每页数量

    Returns:
        排行榜数据
    """
    # 验证类型
    try:
        LeaderboardType(lb_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid leaderboard type: {lb_type}")

    try:
        LeaderboardPeriod(period)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    # 检查缓存
    cache_key = (lb_type, period)
    if not _is_cache_valid(lb_type, period):
        _leaderboard_cache[cache_key] = _build_leaderboard(lb_type, period)
        _cache_timestamps[cache_key] = datetime.utcnow()

    entries = _leaderboard_cache.get(cache_key, [])

    # 分页
    total = len(entries)
    start = (page - 1) * page_size
    end = start + page_size
    page_entries = entries[start:end]

    # 计算周期结束时间
    now = datetime.utcnow()
    if period == LeaderboardPeriod.DAILY.value:
        end_time = now.replace(hour=23, minute=59, second=59)
    elif period == LeaderboardPeriod.WEEKLY.value:
        days_until_sunday = 6 - now.weekday()
        end_time = (now + timedelta(days=days_until_sunday)).replace(hour=23, minute=59, second=59)
    elif period == LeaderboardPeriod.MONTHLY.value:
        if now.month == 12:
            end_time = now.replace(year=now.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            end_time = now.replace(month=now.month + 1, day=1) - timedelta(seconds=1)
    else:
        end_time = None

    return {
        "type": lb_type,
        "period": period,
        "total": total,
        "page": page,
        "page_size": page_size,
        "entries": page_entries,
        "updated_at": _cache_timestamps.get(cache_key, now).isoformat(),
        "ends_at": end_time.isoformat() if end_time else None,
    }


@router.get("/{lb_type}/player/{player_id}")
async def get_player_rank(
    lb_type: str,
    player_id: str,
    period: str = Query(LeaderboardPeriod.WEEKLY.value),
) -> dict:
    """获取玩家在排行榜中的排名

    Args:
        lb_type: 排行榜类型
        player_id: 玩家 ID
        period: 周期

    Returns:
        玩家排名信息
    """
    # 验证类型
    try:
        LeaderboardType(lb_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid leaderboard type: {lb_type}")

    # 检查缓存
    cache_key = (lb_type, period)
    if not _is_cache_valid(lb_type, period):
        _leaderboard_cache[cache_key] = _build_leaderboard(lb_type, period)
        _cache_timestamps[cache_key] = datetime.utcnow()

    entries = _leaderboard_cache.get(cache_key, [])

    # 查找玩家
    player_entry = None
    for entry in entries:
        if entry["player_id"] == player_id:
            player_entry = entry
            break

    if not player_entry:
        # 玩家不在榜上，计算其数据
        stats = _player_stats.get(player_id, {})
        value_field = _get_value_field(lb_type)

        if period == LeaderboardPeriod.DAILY.value:
            value = stats.get(f"daily_{value_field}", 0)
        elif period == LeaderboardPeriod.WEEKLY.value:
            value = stats.get(f"weekly_{value_field}", 0)
        else:
            value = stats.get(value_field, 0)

        # 计算排名
        rank = len([e for e in entries if e["value"] > value]) + 1

        return {
            "player_id": player_id,
            "rank": rank,
            "total": len(entries) + 1,
            "value": value,
            "value_label": _format_value(value, lb_type),
            "on_leaderboard": False,
            "percentile": round((1 - rank / (len(entries) + 1)) * 100, 1),
        }

    return {
        "player_id": player_id,
        "rank": player_entry["rank"],
        "total": len(entries),
        "value": player_entry["value"],
        "value_label": player_entry["value_label"],
        "on_leaderboard": True,
        "percentile": round((1 - player_entry["rank"] / len(entries)) * 100, 1),
    }


@router.get("/{lb_type}/rewards")
async def get_leaderboard_rewards(lb_type: str) -> dict:
    """获取排行榜奖励配置

    Args:
        lb_type: 排行榜类型

    Returns:
        奖励配置
    """
    try:
        LeaderboardType(lb_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid leaderboard type: {lb_type}")

    rewards = LEADERBOARD_REWARDS.get(lb_type, {})

    result = []
    for rank_range, reward_list in rewards.items():
        result.append(
            LeaderboardReward(
                rank_range=rank_range,
                rewards=reward_list,
            ).model_dump()
        )

    return {
        "type": lb_type,
        "rewards": result,
    }


@router.get("/{lb_type}/around/{player_id}")
async def get_leaderboard_around_player(
    lb_type: str,
    player_id: str,
    period: str = Query(LeaderboardPeriod.WEEKLY.value),
    range_size: int = Query(5, ge=1, le=10, description="上下各显示多少名"),
) -> dict:
    """获取玩家周围的排行榜数据

    Args:
        lb_type: 排行榜类型
        player_id: 玩家 ID
        period: 周期
        range_size: 上下各显示多少名

    Returns:
        玩家周围的排行榜数据
    """
    # 验证类型
    try:
        LeaderboardType(lb_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid leaderboard type: {lb_type}")

    # 检查缓存
    cache_key = (lb_type, period)
    if not _is_cache_valid(lb_type, period):
        _leaderboard_cache[cache_key] = _build_leaderboard(lb_type, period)
        _cache_timestamps[cache_key] = datetime.utcnow()

    entries = _leaderboard_cache.get(cache_key, [])

    # 查找玩家位置
    player_index = -1
    for i, entry in enumerate(entries):
        if entry["player_id"] == player_id:
            player_index = i
            break

    if player_index == -1:
        # 玩家不在榜上
        return {
            "player_id": player_id,
            "on_leaderboard": False,
            "entries": [],
        }

    # 获取周围的条目
    start = max(0, player_index - range_size)
    end = min(len(entries), player_index + range_size + 1)

    around_entries = entries[start:end]

    # 标记当前玩家
    for entry in around_entries:
        entry["is_self"] = entry["player_id"] == player_id

    return {
        "player_id": player_id,
        "on_leaderboard": True,
        "player_rank": player_index + 1,
        "entries": around_entries,
    }


# ==================== 内部函数 (供其他模块调用) ====================


def update_player_stats(player_id: str, stats: dict) -> None:
    """更新玩家统计数据

    Args:
        player_id: 玩家 ID
        stats: 统计数据
    """
    if player_id not in _player_stats:
        _player_stats[player_id] = {}

    _player_stats[player_id].update(stats)


def increment_player_stat(player_id: str, stat_name: str, amount: int = 1) -> None:
    """增加玩家统计数据

    Args:
        player_id: 玩家 ID
        stat_name: 统计项名称
        amount: 增加量
    """
    if player_id not in _player_stats:
        _player_stats[player_id] = {}

    current = _player_stats[player_id].get(stat_name, 0)
    _player_stats[player_id][stat_name] = current + amount

    # 同时更新周期统计
    for period in ["daily", "weekly", "monthly"]:
        period_key = f"{period}_{stat_name}"
        current_period = _player_stats[player_id].get(period_key, 0)
        _player_stats[player_id][period_key] = current_period + amount


def reset_period_stats(period: str) -> None:
    """重置周期统计数据

    Args:
        period: 周期 (daily, weekly, monthly)
    """
    for player_id in _player_stats:
        keys_to_reset = [k for k in _player_stats[player_id] if k.startswith(f"{period}_")]
        for key in keys_to_reset:
            _player_stats[player_id][key] = 0

    # 清除对应周期的缓存
    keys_to_remove = [k for k in _leaderboard_cache if k[1] == period]
    for key in keys_to_remove:
        del _leaderboard_cache[key]
        if key in _cache_timestamps:
            del _cache_timestamps[key]
