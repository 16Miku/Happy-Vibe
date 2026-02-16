"""API Schema 定义

统一的 Pydantic 模型定义，用于 OpenAPI 文档生成。
包含所有 API 端点的请求/响应模型和示例数据。
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ============== 通用响应模型 ==============


class SuccessResponse(BaseModel):
    """通用成功响应"""

    success: bool = Field(True, description="操作是否成功")
    message: str = Field(..., description="响应消息")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"success": True, "message": "操作成功"}
            ]
        }
    }


class ErrorResponse(BaseModel):
    """通用错误响应"""

    detail: str = Field(..., description="错误详情")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"detail": "资源不存在"}
            ]
        }
    }


class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class PaginatedResponse(BaseModel):
    """分页响应基类"""

    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    has_more: bool = Field(..., description="是否有更多数据")


# ============== API 标签定义 ==============


API_TAGS_METADATA = [
    {
        "name": "health",
        "description": "健康检查接口，用于监控服务状态",
    },
    {
        "name": "player",
        "description": "玩家系统 - 玩家信息管理、资源管理、等级经验系统",
    },
    {
        "name": "energy",
        "description": "能量系统 - Vibe 能量计算、发放、历史查询",
    },
    {
        "name": "farm",
        "description": "农场系统 - 地块管理、种植、浇水、收获作物",
    },
    {
        "name": "achievement",
        "description": "成就系统 - 成就列表、进度追踪、奖励领取",
    },
    {
        "name": "guilds",
        "description": "公会系统 - 公会创建、管理、成员操作、贡献",
    },
    {
        "name": "guild_war",
        "description": "公会战争 - 公会对战、战争管理",
    },
    {
        "name": "leaderboard",
        "description": "排行榜系统 - 个人排行、公会排行、成就排行",
    },
    {
        "name": "pvp",
        "description": "PVP 竞技场 - 匹配对战、观战、积分排名",
    },
    {
        "name": "shop",
        "description": "商店系统 - NPC 商店、商品购买、库存刷新",
    },
    {
        "name": "market",
        "description": "交易市场 - 玩家间交易、挂单、购买",
    },
    {
        "name": "auction",
        "description": "拍卖行 - 物品拍卖、竞价、结算",
    },
    {
        "name": "friends",
        "description": "好友系统 - 好友管理、礼物互赠、互助操作",
    },
    {
        "name": "check_in",
        "description": "签到系统 - 每日签到、连续签到奖励",
    },
    {
        "name": "quest",
        "description": "任务系统 - 日常任务、周常任务、任务奖励",
    },
    {
        "name": "event",
        "description": "活动系统 - 限时活动、活动奖励",
    },
    {
        "name": "season",
        "description": "赛季系统 - 赛季管理、赛季奖励",
    },
    {
        "name": "economy",
        "description": "经济系统 - 货币管理、交易记录",
    },
    {
        "name": "activity",
        "description": "活动记录 - 编码活动、活动统计",
    },
    {
        "name": "websocket",
        "description": "WebSocket 连接 - 实时通信、状态同步",
    },
]


# ============== 玩家系统示例 ==============


PLAYER_EXAMPLES = {
    "player_response": {
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "VibeCoderX",
        "created_at": "2024-01-15T08:30:00Z",
        "updated_at": "2024-02-16T10:45:00Z",
        "level": 25,
        "experience": 12500,
        "vibe_energy": 850,
        "max_vibe_energy": 1000,
        "gold": 15000,
        "diamonds": 50,
        "focus": 75,
        "efficiency": 80,
        "creativity": 65,
        "consecutive_days": 7,
        "last_login_date": "2024-02-16T10:45:00Z",
    },
    "player_create": {
        "username": "NewVibeCoder",
    },
    "player_stats": {
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "VibeCoderX",
        "level": 25,
        "experience": 12500,
        "exp_to_next_level": 1500,
        "total_coding_sessions": 150,
        "total_coding_duration": 54000,
        "total_energy_earned": 25000,
        "total_exp_earned": 15000,
        "flow_sessions": 45,
        "achievements_unlocked": 28,
        "inventory_items_count": 120,
    },
}


# ============== 能量系统示例 ==============


ENERGY_EXAMPLES = {
    "calculate_request": {
        "duration_minutes": 45.0,
        "consecutive_minutes": 45.0,
        "consecutive_days": 5,
        "is_flow_state": True,
        "quality": {
            "success_rate": 0.85,
            "iteration_count": 3,
            "lines_changed": 150,
            "files_affected": 5,
            "languages": ["python", "typescript"],
            "tool_usage": {
                "read": 20,
                "write": 15,
                "bash": 8,
                "search": 5,
            },
        },
    },
    "calculate_response": {
        "vibe_energy": 450,
        "experience": 225,
        "code_essence": 45,
        "breakdown": {
            "base": 225.0,
            "time_bonus": 1.2,
            "quality_bonus": 1.15,
            "streak_bonus": 1.1,
            "flow_bonus": 1.5,
        },
    },
    "energy_status": {
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "current_energy": 850,
        "max_energy": 1000,
        "daily_earned": 2500,
        "daily_cap": 5000,
        "daily_remaining": 2500,
    },
}


# ============== 农场系统示例 ==============


FARM_EXAMPLES = {
    "farm_response": {
        "farm_id": "farm-001",
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "我的农场",
        "plot_count": 6,
        "decoration_score": 150,
        "plots": [
            {
                "index": 0,
                "is_empty": False,
                "crop": {
                    "crop_id": "crop-001",
                    "plot_index": 0,
                    "crop_type": "tomato",
                    "crop_name": "番茄",
                    "quality": 1,
                    "quality_name": "普通",
                    "growth_progress": 75.5,
                    "is_ready": False,
                    "is_watered": True,
                    "planted_at": "2024-02-16T08:00:00Z",
                },
            },
            {"index": 1, "is_empty": True, "crop": None},
        ],
    },
    "plant_request": {
        "plot_index": 1,
        "crop_type": "carrot",
    },
    "harvest_response": {
        "success": True,
        "message": "成功收获 番茄，获得 100 金币",
        "crop_type": "tomato",
        "crop_name": "番茄",
        "quality": 2,
        "quality_name": "优良",
        "value": 120,
    },
}


# ============== 成就系统示例 ==============


ACHIEVEMENT_EXAMPLES = {
    "achievement_response": {
        "achievement_id": "ach-first-code",
        "category": "coding",
        "tier": "common",
        "title": "First Code",
        "title_zh": "初次编码",
        "description": "完成第一次编码活动",
        "icon": "🎯",
        "is_hidden": False,
        "is_secret": False,
        "display_order": 1,
        "current_value": 1,
        "target_value": 1,
        "progress_percent": 100.0,
        "is_unlocked": True,
        "is_completed": True,
        "is_claimed": False,
        "started_at": "2024-01-15T08:30:00Z",
        "completed_at": "2024-01-15T09:00:00Z",
        "claimed_at": None,
        "reward": {"gold": 100, "exp": 50},
    },
    "achievement_stats": {
        "total_achievements": 50,
        "unlocked_count": 28,
        "completed_count": 25,
        "claimed_count": 20,
        "unlocked_percent": 56.0,
        "category_stats": {
            "coding": {"total": 15, "unlocked": 10, "completed": 8},
            "farming": {"total": 12, "unlocked": 8, "completed": 7},
            "social": {"total": 10, "unlocked": 5, "completed": 5},
            "economy": {"total": 8, "unlocked": 3, "completed": 3},
            "special": {"total": 5, "unlocked": 2, "completed": 2},
        },
    },
}


# ============== 公会系统示例 ==============


GUILD_EXAMPLES = {
    "guild_create": {
        "leader_id": "550e8400-e29b-41d4-a716-446655440000",
        "guild_name": "VibeCoders",
        "guild_name_zh": "活力编码者",
        "description": "一个热爱编码的公会",
        "icon": "⚡",
        "join_type": "open",
        "min_level": 5,
    },
    "guild_info": {
        "guild_id": "guild-001",
        "guild_name": "VibeCoders",
        "guild_name_zh": "活力编码者",
        "description": "一个热爱编码的公会",
        "icon": "⚡",
        "level": 5,
        "experience": 5000,
        "member_count": 25,
        "max_members": 50,
        "contribution_points": 15000,
        "join_type": "open",
        "min_level": 5,
        "created_at": "2024-01-01T00:00:00Z",
    },
    "guild_member": {
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "VibeCoderX",
        "role": "leader",
        "contribution": 5000,
        "weekly_contribution": 500,
        "joined_at": "2024-01-01T00:00:00Z",
    },
}


# ============== PVP 系统示例 ==============


PVP_EXAMPLES = {
    "matchmaking_request": {
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "match_type": "arena",
        "rating_range": 200,
    },
    "match_info": {
        "match_id": "match-001",
        "match_type": "arena",
        "player_a_id": "player-a",
        "player_b_id": "player-b",
        "player_a_rating": 1500,
        "player_b_rating": 1480,
        "status": "in_progress",
        "score_a": 2,
        "score_b": 1,
        "winner_id": None,
        "duration_seconds": 300,
        "moves_a": 15,
        "moves_b": 12,
        "spectator_count": 5,
        "allow_spectate": True,
        "created_at": "2024-02-16T10:00:00Z",
        "started_at": "2024-02-16T10:01:00Z",
        "finished_at": None,
    },
    "ranking_info": {
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "season_id": "season-2024-02",
        "rating": 1650,
        "max_rating": 1700,
        "rank": 42,
        "matches_played": 50,
        "matches_won": 30,
        "matches_lost": 18,
        "matches_drawn": 2,
        "current_streak": 3,
        "max_streak": 7,
        "win_rate": 0.6,
    },
}


# ============== 商店系统示例 ==============


SHOP_EXAMPLES = {
    "shop_item": {
        "item_id": "seed-tomato",
        "item_name": "番茄种子",
        "item_type": "seed",
        "base_price": 50,
        "current_price": 45,
        "stock": 10,
        "max_stock": 20,
    },
    "buy_request": {
        "item_id": "seed-tomato",
        "quantity": 5,
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "player_gold": 1000,
    },
    "buy_response": {
        "success": True,
        "message": "购买成功",
        "item_name": "番茄种子",
        "quantity": 5,
        "total_cost": 225,
        "remaining_gold": 775,
    },
}


# ============== 市场系统示例 ==============


MARKET_EXAMPLES = {
    "listing": {
        "listing_id": "listing-001",
        "seller_id": "player-a",
        "seller_name": "VibeCoderX",
        "item_type": "crop",
        "item_name": "传说番茄",
        "quantity": 10,
        "unit_price": 150,
        "total_price": 1500,
        "listing_fee": 75,
        "status": "active",
        "created_at": "2024-02-16T08:00:00Z",
        "expires_at": "2024-02-23T08:00:00Z",
    },
    "create_listing": {
        "seller_id": "550e8400-e29b-41d4-a716-446655440000",
        "seller_name": "VibeCoderX",
        "item_type": "crop",
        "item_name": "传说番茄",
        "quantity": 10,
        "unit_price": 150,
        "player_gold": 5000,
    },
    "purchase_request": {
        "buyer_id": "player-b",
        "buyer_gold": 5000,
        "quantity": 5,
    },
}


# ============== 好友系统示例 ==============


FRIENDS_EXAMPLES = {
    "friend_info": {
        "player_id": "friend-001",
        "username": "FriendCoder",
        "level": 20,
        "affinity_score": 150,
        "affinity_title": "挚友",
        "is_online": True,
        "status": "online",
        "last_online": "2024-02-16T10:00:00Z",
    },
    "friend_request": {
        "from_player_id": "550e8400-e29b-41d4-a716-446655440000",
        "to_player_id": "friend-001",
        "message": "一起来编码吧！",
    },
    "gift_request": {
        "from_player_id": "550e8400-e29b-41d4-a716-446655440000",
        "to_player_id": "friend-001",
        "item_id": "gift-flower",
        "item_name": "友谊之花",
        "quantity": 1,
    },
}


# ============== 排行榜系统示例 ==============


LEADERBOARD_EXAMPLES = {
    "leaderboard_entry": {
        "rank": 1,
        "entity_id": "550e8400-e29b-41d4-a716-446655440000",
        "entity_name": "VibeCoderX",
        "score": 25000,
        "level": 30,
        "experience": 20000,
        "gold": 50000,
        "achievement_count": 45,
    },
    "player_rank": {
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "entity_name": "VibeCoderX",
        "rank": 42,
        "total": 1000,
        "score": 15000,
        "on_leaderboard": True,
        "percentile": 95.8,
        "level": 25,
        "experience": 12500,
    },
}


# ============== 签到系统示例 ==============


CHECK_IN_EXAMPLES = {
    "check_in_response": {
        "success": True,
        "message": "签到成功！",
        "consecutive_days": 7,
        "reward": {
            "gold": 100,
            "exp": 50,
            "energy": 100,
        },
        "bonus_reward": {
            "gold": 500,
            "diamonds": 10,
        },
        "next_bonus_day": 14,
    },
    "check_in_status": {
        "player_id": "550e8400-e29b-41d4-a716-446655440000",
        "consecutive_days": 6,
        "last_check_in": "2024-02-15T08:00:00Z",
        "can_check_in": True,
        "today_reward": {
            "gold": 100,
            "exp": 50,
        },
    },
}
