"""API 路由模块"""

from .achievement import router as achievement_router
from .activity import router as activity_router
from .auction import router as auction_router
from .check_in import router as check_in_router
from .economy import router as economy_router
from .energy import router as energy_router
from .event import router as event_router
from .farm import router as farm_router
from .friends import router as friends_router
from .guilds import router as guilds_router
from .health import router as health_router
from .leaderboards import router as leaderboard_router
from .market import router as market_router
from .player import router as player_router
from .quest import router as quest_router
from .shop import router as shop_router
from .websocket import router as websocket_router

__all__ = [
    "health_router",
    "player_router",
    "activity_router",
    "farm_router",
    "achievement_router",
    "energy_router",
    "friends_router",
    "check_in_router",
    "guilds_router",
    "leaderboard_router",
    "websocket_router",
    "shop_router",
    "market_router",
    "auction_router",
    "economy_router",
    "quest_router",
    "event_router",
]
