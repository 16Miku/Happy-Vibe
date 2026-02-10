"""API 路由模块"""

from .health import router as health_router
from .player import router as player_router

__all__ = ["health_router", "player_router"]
