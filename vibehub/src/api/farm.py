"""农场 API 路由

提供农场相关的 REST API 端点，包括：
- 获取农场信息
- 地块管理
- 种植/浇水/收获作物
- 作物配置查询
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.storage.database import get_db
from src.storage.models import (
    CROP_CONFIG,
    QUALITY_MULTIPLIERS,
    Crop,
    CropQuality,
    Farm,
    Player,
)

router = APIRouter(prefix="/api/farm", tags=["farm"])


# ============== Pydantic 模型 ==============


class CropInfo(BaseModel):
    """作物信息"""

    crop_id: str
    plot_index: int
    crop_type: str
    crop_name: str
    quality: int
    quality_name: str
    growth_progress: float
    is_ready: bool
    is_watered: bool
    planted_at: datetime

    class Config:
        from_attributes = True


class PlotInfo(BaseModel):
    """地块信息"""

    index: int
    is_empty: bool
    crop: CropInfo | None = None


class FarmResponse(BaseModel):
    """农场信息响应"""

    farm_id: str
    player_id: str
    name: str
    plot_count: int
    decoration_score: int
    plots: list[PlotInfo]


class PlotsResponse(BaseModel):
    """地块列表响应"""

    plots: list[PlotInfo]
    total_plots: int
    empty_plots: int
    planted_plots: int


class PlantRequest(BaseModel):
    """种植请求"""

    plot_index: int = Field(..., ge=0, description="地块索引")
    crop_type: str = Field(..., description="作物类型")


class PlantResponse(BaseModel):
    """种植响应"""

    success: bool
    message: str
    crop: CropInfo | None = None


class WaterRequest(BaseModel):
    """浇水请求"""

    plot_index: int = Field(..., ge=0, description="地块索引")


class WaterResponse(BaseModel):
    """浇水响应"""

    success: bool
    message: str
    growth_boost: float = 0.0


class HarvestRequest(BaseModel):
    """收获请求"""

    plot_index: int = Field(..., ge=0, description="地块索引")


class HarvestResponse(BaseModel):
    """收获响应"""

    success: bool
    message: str
    crop_type: str | None = None
    crop_name: str | None = None
    quality: int | None = None
    quality_name: str | None = None
    value: int | None = None


class CropConfigItem(BaseModel):
    """作物配置项"""

    crop_type: str
    name: str
    growth_hours: int
    base_value: int
    seed_cost: int


class CropsConfigResponse(BaseModel):
    """作物配置响应"""

    crops: list[CropConfigItem]
    quality_multipliers: dict[str, float]


# ============== 辅助函数 ==============


def get_db_session():
    """获取数据库会话依赖"""
    db = get_db()
    session = db.get_session_instance()
    try:
        yield session
    finally:
        session.close()


def get_quality_name(quality: int) -> str:
    """获取品质名称"""
    quality_names = {
        CropQuality.NORMAL.value: "普通",
        CropQuality.GOOD.value: "优良",
        CropQuality.EXCELLENT.value: "精品",
        CropQuality.LEGENDARY.value: "传说",
    }
    return quality_names.get(quality, "未知")


def calculate_growth_progress(crop: Crop) -> float:
    """计算作物生长进度

    Args:
        crop: 作物对象

    Returns:
        生长进度百分比 (0-100)
    """
    config = CROP_CONFIG.get(crop.crop_type)
    if not config:
        return 0.0

    growth_hours = config["growth_hours"]
    elapsed = datetime.utcnow() - crop.planted_at
    elapsed_hours = elapsed.total_seconds() / 3600

    # 浇水加速 20%
    if crop.is_watered:
        elapsed_hours *= 1.2

    progress = min(100.0, (elapsed_hours / growth_hours) * 100)
    return round(progress, 2)


def build_crop_info(crop: Crop) -> CropInfo:
    """构建作物信息"""
    config = CROP_CONFIG.get(crop.crop_type, {})
    progress = calculate_growth_progress(crop)
    is_ready = progress >= 100.0

    return CropInfo(
        crop_id=crop.crop_id,
        plot_index=crop.plot_index,
        crop_type=crop.crop_type,
        crop_name=config.get("name", "未知作物"),
        quality=crop.quality,
        quality_name=get_quality_name(crop.quality),
        growth_progress=progress,
        is_ready=is_ready,
        is_watered=crop.is_watered,
        planted_at=crop.planted_at,
    )


def build_plot_info(index: int, crop: Crop | None) -> PlotInfo:
    """构建地块信息"""
    if crop is None:
        return PlotInfo(index=index, is_empty=True, crop=None)
    return PlotInfo(index=index, is_empty=False, crop=build_crop_info(crop))


def get_or_create_default_player(session: Session) -> Player:
    """获取或创建默认玩家"""
    player = session.query(Player).first()
    if player is None:
        player = Player(username="default_player")
        session.add(player)
        session.flush()
    return player


def get_or_create_farm(session: Session, player: Player) -> Farm:
    """获取或创建农场"""
    if player.farm is None:
        farm = Farm(player_id=player.player_id, name="我的农场", plot_count=6)
        session.add(farm)
        session.flush()
        return farm
    return player.farm


# ============== API 端点 ==============


@router.get(
    "",
    response_model=FarmResponse,
    summary="获取农场信息",
    description="返回农场的基本信息和所有地块状态。",
    responses={
        200: {"description": "成功返回农场信息"},
    },
)
async def get_farm(session: Session = Depends(get_db_session)):
    """获取农场信息

    返回农场的基本信息和所有地块状态。
    """
    player = get_or_create_default_player(session)
    farm = get_or_create_farm(session, player)
    session.commit()

    # 构建地块信息
    crops_by_plot = {crop.plot_index: crop for crop in farm.crops}
    plots = [build_plot_info(i, crops_by_plot.get(i)) for i in range(farm.plot_count)]

    return FarmResponse(
        farm_id=farm.farm_id,
        player_id=farm.player_id,
        name=farm.name,
        plot_count=farm.plot_count,
        decoration_score=farm.decoration_score,
        plots=plots,
    )


@router.get(
    "/plots",
    response_model=PlotsResponse,
    summary="获取所有地块状态",
    description="返回农场中所有地块的详细信息，包括空地和已种植作物。",
    responses={
        200: {"description": "成功返回地块列表"},
    },
)
async def get_plots(session: Session = Depends(get_db_session)):
    """获取所有地块状态

    返回农场中所有地块的详细信息。
    """
    player = get_or_create_default_player(session)
    farm = get_or_create_farm(session, player)
    session.commit()

    crops_by_plot = {crop.plot_index: crop for crop in farm.crops}
    plots = [build_plot_info(i, crops_by_plot.get(i)) for i in range(farm.plot_count)]

    empty_count = sum(1 for p in plots if p.is_empty)

    return PlotsResponse(
        plots=plots,
        total_plots=farm.plot_count,
        empty_plots=empty_count,
        planted_plots=farm.plot_count - empty_count,
    )


@router.post(
    "/plant",
    response_model=PlantResponse,
    summary="种植作物",
    description="在指定地块种植作物。地块必须为空，作物类型必须有效。",
    responses={
        200: {"description": "种植成功"},
        400: {"description": "无效的作物类型或地块已有作物"},
    },
)
async def plant_crop(request: PlantRequest, session: Session = Depends(get_db_session)):
    """种植作物

    在指定地块种植作物。

    Args:
        request: 种植请求，包含地块索引和作物类型
    """
    # 验证作物类型
    if request.crop_type not in CROP_CONFIG:
        valid_types = list(CROP_CONFIG.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的作物类型: {request.crop_type}，有效类型: {valid_types}",
        )

    player = get_or_create_default_player(session)
    farm = get_or_create_farm(session, player)

    # 验证地块索引
    if request.plot_index >= farm.plot_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的地块索引: {request.plot_index}，农场只有 {farm.plot_count} 个地块",
        )

    # 检查地块是否已有作物
    existing_crop = (
        session.query(Crop)
        .filter(Crop.farm_id == farm.farm_id, Crop.plot_index == request.plot_index)
        .first()
    )

    if existing_crop:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"地块 {request.plot_index} 已有作物，请先收获或清除",
        )

    # 创建新作物
    new_crop = Crop(
        farm_id=farm.farm_id,
        plot_index=request.plot_index,
        crop_type=request.crop_type,
        quality=CropQuality.NORMAL.value,
        planted_at=datetime.utcnow(),
        growth_progress=0.0,
        is_ready=False,
        is_watered=False,
    )
    session.add(new_crop)
    session.commit()

    crop_name = CROP_CONFIG[request.crop_type]["name"]
    return PlantResponse(
        success=True,
        message=f"成功在地块 {request.plot_index} 种植了 {crop_name}",
        crop=build_crop_info(new_crop),
    )


@router.post(
    "/water",
    response_model=WaterResponse,
    summary="浇水",
    description="为指定地块的作物浇水，加速生长 20%。每个作物只能浇水一次。",
    responses={
        200: {"description": "浇水成功或已浇过水"},
        400: {"description": "无效的地块索引"},
        404: {"description": "地块没有作物"},
    },
)
async def water_crop(request: WaterRequest, session: Session = Depends(get_db_session)):
    """浇水

    为指定地块的作物浇水，加速生长 20%。

    Args:
        request: 浇水请求，包含地块索引
    """
    player = get_or_create_default_player(session)
    farm = get_or_create_farm(session, player)

    # 验证地块索引
    if request.plot_index >= farm.plot_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的地块索引: {request.plot_index}",
        )

    # 查找作物
    crop = (
        session.query(Crop)
        .filter(Crop.farm_id == farm.farm_id, Crop.plot_index == request.plot_index)
        .first()
    )

    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"地块 {request.plot_index} 没有作物",
        )

    if crop.is_watered:
        return WaterResponse(
            success=False,
            message="作物已经浇过水了",
            growth_boost=0.0,
        )

    # 浇水
    crop.is_watered = True
    session.commit()

    return WaterResponse(
        success=True,
        message="浇水成功，生长速度提升 20%",
        growth_boost=20.0,
    )


@router.post(
    "/harvest",
    response_model=HarvestResponse,
    summary="收获作物",
    description="收获指定地块的成熟作物，获得金币奖励。作物必须生长完成才能收获。",
    responses={
        200: {"description": "收获成功"},
        400: {"description": "作物尚未成熟"},
        404: {"description": "地块没有作物"},
    },
)
async def harvest_crop(request: HarvestRequest, session: Session = Depends(get_db_session)):
    """收获作物

    收获指定地块的成熟作物。

    Args:
        request: 收获请求，包含地块索引
    """
    player = get_or_create_default_player(session)
    farm = get_or_create_farm(session, player)

    # 验证地块索引
    if request.plot_index >= farm.plot_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的地块索引: {request.plot_index}",
        )

    # 查找作物
    crop = (
        session.query(Crop)
        .filter(Crop.farm_id == farm.farm_id, Crop.plot_index == request.plot_index)
        .first()
    )

    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"地块 {request.plot_index} 没有作物",
        )

    # 检查是否成熟
    progress = calculate_growth_progress(crop)
    if progress < 100.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"作物尚未成熟，当前进度: {progress:.1f}%",
        )

    # 计算收获价值
    config = CROP_CONFIG.get(crop.crop_type, {})
    base_value = config.get("base_value", 0)
    quality_multiplier = QUALITY_MULTIPLIERS.get(crop.quality, 1.0)
    final_value = int(base_value * quality_multiplier)

    crop_type = crop.crop_type
    crop_name = config.get("name", "未知作物")
    quality = crop.quality
    quality_name = get_quality_name(quality)

    # 删除作物
    session.delete(crop)
    session.commit()

    return HarvestResponse(
        success=True,
        message=f"成功收获 {crop_name}，获得 {final_value} 金币",
        crop_type=crop_type,
        crop_name=crop_name,
        quality=quality,
        quality_name=quality_name,
        value=final_value,
    )


@router.get(
    "/crops",
    response_model=CropsConfigResponse,
    summary="获取作物配置信息",
    description="返回所有可种植作物的配置信息和品质倍数。",
    responses={
        200: {"description": "成功返回作物配置"},
    },
)
async def get_crops_config():
    """获取作物配置信息

    返回所有可种植作物的配置信息和品质倍数。
    """
    crops = [
        CropConfigItem(
            crop_type=crop_type,
            name=config["name"],
            growth_hours=config["growth_hours"],
            base_value=config["base_value"],
            seed_cost=config["seed_cost"],
        )
        for crop_type, config in CROP_CONFIG.items()
    ]

    quality_multipliers = {
        get_quality_name(quality): multiplier for quality, multiplier in QUALITY_MULTIPLIERS.items()
    }

    return CropsConfigResponse(
        crops=crops,
        quality_multipliers=quality_multipliers,
    )
