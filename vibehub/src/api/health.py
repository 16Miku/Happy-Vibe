"""健康检查 API 路由"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "service": "Happy Vibe Hub",
        "version": "0.1.0"
    }


@router.get("/api/health")
async def api_health_check():
    """API 健康检查端点（兼容路径）"""
    return {
        "status": "ok",
        "service": "Happy Vibe Hub",
        "version": "0.1.0"
    }
