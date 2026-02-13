"""API 路由模块"""

from .achievement import router as achievement_router
from .activity import router as activity_router
from .energy import router as energy_router
from .farm import router as farm_router
from .friend import router as friend_router
from .health import router as health_router
from .player import router as player_router

__all__ = [
    "health_router",
    "player_router",
    "activity_router",
    "farm_router",
    "achievement_router",
    "energy_router",
    "friend_router",
]
