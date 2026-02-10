"""Happy Vibe Hub 主应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import health_router
from src.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 Happy Vibe Hub 启动中...")
    print(f"📝 版本: {settings.VERSION}")
    print(f"🌢 服务地址: http://{settings.HOST}:{settings.PORT}")
    yield
    # 关闭时执行
    print("👋 Happy Vibe Hub 已关闭")


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
