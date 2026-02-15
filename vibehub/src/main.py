"""Happy Vibe Hub 主应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import (
    achievement_router,
    activity_router,
    auction_router,
    check_in_router,
    economy_router,
    energy_router,
    event_router,
    farm_router,
    friends_router,
    guilds_router,
    health_router,
    leaderboard_router,
    leaderboard_v2_router,
    market_router,
    player_router,
    quest_router,
    season_router,
    shop_router,
    websocket_router,
)
from src.config.settings import settings
from src.storage.database import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("[VibeHub] Happy Vibe Hub starting...")
    print(f"[VibeHub] Version: {settings.VERSION}")
    print(f"[VibeHub] Server: http://{settings.HOST}:{settings.PORT}")
    print(f"[VibeHub] WebSocket: ws://{settings.HOST}:{settings.PORT}/ws/connect")

    # 初始化数据库
    print("[VibeHub] Initializing database...")
    db = Database()
    db.create_tables()
    print("[VibeHub] Database tables created successfully")

    yield
    # 关闭时执行
    print("[VibeHub] Happy Vibe Hub closed")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="Happy Vibe Hub",
        description="Vibe-Coding 游戏化平台本地服务 - 支持多人联机",
        version=settings.VERSION,
        lifespan=lifespan
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由 - 基础功能
    app.include_router(health_router)
    app.include_router(player_router)
    app.include_router(activity_router)
    app.include_router(farm_router)
    app.include_router(achievement_router)
    app.include_router(energy_router)
    app.include_router(check_in_router)

    # 注册路由 - 多人联机功能
    app.include_router(friends_router)
    app.include_router(guilds_router)
    app.include_router(leaderboard_router)
    app.include_router(leaderboard_v2_router)  # 新版排行榜 (基于赛季)
    app.include_router(season_router)  # 赛季管理
    app.include_router(websocket_router)

    # 注册路由 - 经济系统
    app.include_router(shop_router)
    app.include_router(market_router)
    app.include_router(auction_router)
    app.include_router(economy_router)

    # 注册路由 - 任务系统
    app.include_router(quest_router)
    app.include_router(event_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
