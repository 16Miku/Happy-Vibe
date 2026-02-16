"""Happy Vibe Hub 主应用入口

VibeHub 是 Happy Vibe 游戏的本地服务端，提供：
- 玩家数据管理
- 能量计算与发放
- 农场系统
- 成就系统
- 公会系统
- PVP 竞技场
- 交易市场
- 好友系统
- 实时通信 (WebSocket)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

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
    guild_router,
    guild_war_router,
    guilds_router,
    health_router,
    leaderboard_router,
    leaderboard_v2_router,
    market_router,
    player_router,
    pvp_router,
    quest_router,
    season_router,
    shop_router,
    websocket_router,
)
from src.api.schemas import API_TAGS_METADATA
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
        title="Happy Vibe Hub API",
        description="""
## 🎮 Happy Vibe Hub - Vibe-Coding 游戏化平台

将编码活动转化为游戏体验的本地服务端。

### 主要功能

- **🧑‍💻 玩家系统** - 玩家信息、等级、经验管理
- **⚡ 能量系统** - Vibe 能量计算与发放
- **🌾 农场系统** - 种植、浇水、收获作物
- **🏆 成就系统** - 成就追踪与奖励
- **👥 公会系统** - 公会创建、管理、公会战
- **⚔️ PVP 竞技** - 匹配对战、排名系统
- **🛒 商店系统** - NPC 商店购物
- **📈 交易市场** - 玩家间物品交易
- **👫 好友系统** - 好友互动、礼物互赠
- **📅 签到系统** - 每日签到奖励
- **🎯 任务系统** - 日常/周常任务
- **🏅 排行榜** - 多维度排名

### 认证说明

当前版本为本地单机模式，无需认证。

### WebSocket 连接

实时通信端点: `ws://localhost:8000/ws/connect`
""",
        version=settings.VERSION,
        lifespan=lifespan,
        openapi_tags=API_TAGS_METADATA,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        contact={
            "name": "Happy Vibe Team",
            "url": "https://github.com/happy-vibe",
        },
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
    app.include_router(guild_router)
    app.include_router(guild_war_router)
    app.include_router(leaderboard_router)
    app.include_router(leaderboard_v2_router)  # 新版排行榜 (基于赛季)
    app.include_router(season_router)  # 赛季管理
    app.include_router(websocket_router)
    app.include_router(pvp_router)

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
