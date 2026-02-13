"""Happy Vibe Hub 主应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import (
    achievement_router,
    activity_router,
    check_in_router,
    energy_router,
    farm_router,
    friend_router,
    health_router,
    player_router,
)
from src.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("[VibeHub] Happy Vibe Hub starting...")
    print(f"[VibeHub] Version: {settings.VERSION}")
    print(f"[VibeHub] Server: http://{settings.HOST}:{settings.PORT}")
    yield
    # 关闭时执行
    print("[VibeHub] Happy Vibe Hub closed")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="Happy Vibe Hub",
        description="Vibe-Coding 游戏化平台本地服务",
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

    # 注册路由
    app.include_router(health_router)
    app.include_router(player_router)
    app.include_router(activity_router)
    app.include_router(farm_router)
    app.include_router(achievement_router)
    app.include_router(energy_router)
    app.include_router(friend_router)
    app.include_router(check_in_router)

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
