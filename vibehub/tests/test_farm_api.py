"""农场 API 测试"""

import pytest
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.storage.database import get_db, init_db, close_db
from src.storage.models import (
    CROP_CONFIG,
    QUALITY_MULTIPLIERS,
    Crop,
    CropQuality,
    CropType,
    Farm,
    Player,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """为每个测试创建临时数据库"""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    yield
    close_db()


@pytest.mark.asyncio
class TestGetFarm:
    """获取农场信息测试"""

    async def test_get_farm_creates_default(self):
        """测试获取农场时自动创建默认农场"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm")

        assert response.status_code == 200
        data = response.json()
        assert "farm_id" in data
        assert "player_id" in data
        assert data["name"] == "我的农场"
        assert data["plot_count"] == 6
        assert len(data["plots"]) == 6

    async def test_get_farm_plots_are_empty_initially(self):
        """测试初始农场所有地块为空"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm")

        data = response.json()
        for plot in data["plots"]:
            assert plot["is_empty"] is True
            assert plot["crop"] is None


@pytest.mark.asyncio
class TestGetPlots:
    """获取地块状态测试"""

    async def test_get_plots_returns_all_plots(self):
        """测试获取所有地块"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm/plots")

        assert response.status_code == 200
        data = response.json()
        assert data["total_plots"] == 6
        assert data["empty_plots"] == 6
        assert data["planted_plots"] == 0
        assert len(data["plots"]) == 6


@pytest.mark.asyncio
class TestPlantCrop:
    """种植作物测试"""

    async def test_plant_crop_success(self):
        """测试成功种植作物"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/farm/plant",
                json={"plot_index": 0, "crop_type": CropType.VARIABLE_GRASS.value},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "变量草" in data["message"]
        assert data["crop"]["crop_type"] == CropType.VARIABLE_GRASS.value
        assert data["crop"]["plot_index"] == 0
        assert data["crop"]["growth_progress"] >= 0

    async def test_plant_crop_invalid_type(self):
        """测试种植无效作物类型"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/farm/plant",
                json={"plot_index": 0, "crop_type": "invalid_crop"},
            )

        assert response.status_code == 400
        assert "无效的作物类型" in response.json()["detail"]

    async def test_plant_crop_invalid_plot_index(self):
        """测试种植到无效地块"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/farm/plant",
                json={"plot_index": 100, "crop_type": CropType.VARIABLE_GRASS.value},
            )

        assert response.status_code == 400
        assert "无效的地块索引" in response.json()["detail"]

    async def test_plant_crop_plot_occupied(self):
        """测试种植到已有作物的地块"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先种植一个作物
            await client.post(
                "/api/farm/plant",
                json={"plot_index": 0, "crop_type": CropType.VARIABLE_GRASS.value},
            )
            # 再次种植到同一地块
            response = await client.post(
                "/api/farm/plant",
                json={"plot_index": 0, "crop_type": CropType.FUNCTION_FLOWER.value},
            )

        assert response.status_code == 400
        assert "已有作物" in response.json()["detail"]

    async def test_plant_multiple_crops(self):
        """测试种植多个作物"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 种植不同作物到不同地块
            await client.post(
                "/api/farm/plant",
                json={"plot_index": 0, "crop_type": CropType.VARIABLE_GRASS.value},
            )
            await client.post(
                "/api/farm/plant",
                json={"plot_index": 1, "crop_type": CropType.FUNCTION_FLOWER.value},
            )

            # 检查地块状态
            response = await client.get("/api/farm/plots")

        data = response.json()
        assert data["planted_plots"] == 2
        assert data["empty_plots"] == 4


@pytest.mark.asyncio
class TestWaterCrop:
    """浇水测试"""

    async def test_water_crop_success(self):
        """测试成功浇水"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先种植
            await client.post(
                "/api/farm/plant",
                json={"plot_index": 0, "crop_type": CropType.VARIABLE_GRASS.value},
            )
            # 浇水
            response = await client.post(
                "/api/farm/water",
                json={"plot_index": 0},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["growth_boost"] == 20.0

    async def test_water_crop_already_watered(self):
        """测试重复浇水"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 种植并浇水
            await client.post(
                "/api/farm/plant",
                json={"plot_index": 0, "crop_type": CropType.VARIABLE_GRASS.value},
            )
            await client.post("/api/farm/water", json={"plot_index": 0})
            # 再次浇水
            response = await client.post("/api/farm/water", json={"plot_index": 0})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "已经浇过水" in data["message"]

    async def test_water_empty_plot(self):
        """测试浇水空地块"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/farm/water", json={"plot_index": 0})

        assert response.status_code == 404
        assert "没有作物" in response.json()["detail"]

    async def test_water_invalid_plot(self):
        """测试浇水无效地块"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/farm/water", json={"plot_index": 100})

        assert response.status_code == 400


@pytest.mark.asyncio
class TestHarvestCrop:
    """收获作物测试"""

    async def test_harvest_crop_not_ready(self):
        """测试收获未成熟作物"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 种植
            await client.post(
                "/api/farm/plant",
                json={"plot_index": 0, "crop_type": CropType.CLASS_TREE.value},
            )
            # 立即收获（未成熟）
            response = await client.post("/api/farm/harvest", json={"plot_index": 0})

        assert response.status_code == 400
        assert "尚未成熟" in response.json()["detail"]

    async def test_harvest_empty_plot(self):
        """测试收获空地块"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/farm/harvest", json={"plot_index": 0})

        assert response.status_code == 404
        assert "没有作物" in response.json()["detail"]

    async def test_harvest_invalid_plot(self):
        """测试收获无效地块"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/farm/harvest", json={"plot_index": 100})

        assert response.status_code == 400

    async def test_harvest_mature_crop(self):
        """测试收获成熟作物"""
        # 直接操作数据库创建成熟作物
        db = get_db()
        with db.get_session() as session:
            player = Player(username="test_player")
            session.add(player)
            session.flush()

            farm = Farm(player_id=player.player_id, name="测试农场", plot_count=6)
            session.add(farm)
            session.flush()

            # 创建一个已成熟的作物（种植时间设为很久以前）
            crop = Crop(
                farm_id=farm.farm_id,
                plot_index=0,
                crop_type=CropType.VARIABLE_GRASS.value,
                quality=CropQuality.NORMAL.value,
                planted_at=datetime.utcnow() - timedelta(hours=10),  # 10小时前
                is_watered=False,
            )
            session.add(crop)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/farm/harvest", json={"plot_index": 0})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["crop_type"] == CropType.VARIABLE_GRASS.value
        assert data["crop_name"] == "变量草"
        assert data["value"] == 10  # base_value * 1.0 (普通品质)


@pytest.mark.asyncio
class TestGetCropsConfig:
    """获取作物配置测试"""

    async def test_get_crops_config(self):
        """测试获取作物配置"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm/crops")

        assert response.status_code == 200
        data = response.json()
        assert "crops" in data
        assert "quality_multipliers" in data
        assert len(data["crops"]) == len(CROP_CONFIG)

    async def test_crops_config_contains_all_types(self):
        """测试配置包含所有作物类型"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm/crops")

        data = response.json()
        crop_types = {crop["crop_type"] for crop in data["crops"]}

        for crop_type in CropType:
            assert crop_type.value in crop_types

    async def test_crops_config_has_required_fields(self):
        """测试作物配置包含必要字段"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm/crops")

        data = response.json()
        for crop in data["crops"]:
            assert "crop_type" in crop
            assert "name" in crop
            assert "growth_hours" in crop
            assert "base_value" in crop
            assert "seed_cost" in crop

    async def test_quality_multipliers(self):
        """测试品质倍数配置"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm/crops")

        data = response.json()
        multipliers = data["quality_multipliers"]
        assert "普通" in multipliers
        assert "优良" in multipliers
        assert "精品" in multipliers
        assert "传说" in multipliers
        assert multipliers["普通"] == 1.0
        assert multipliers["传说"] == 5.0


@pytest.mark.asyncio
class TestGrowthCalculation:
    """生长计算测试"""

    async def test_growth_progress_increases_over_time(self):
        """测试生长进度随时间增加"""
        db = get_db()
        with db.get_session() as session:
            player = Player(username="growth_test_player")
            session.add(player)
            session.flush()

            farm = Farm(player_id=player.player_id, name="测试农场", plot_count=6)
            session.add(farm)
            session.flush()

            # 创建一个种植了30分钟的作物（变量草需要1小时成熟）
            crop = Crop(
                farm_id=farm.farm_id,
                plot_index=0,
                crop_type=CropType.VARIABLE_GRASS.value,
                quality=CropQuality.NORMAL.value,
                planted_at=datetime.utcnow() - timedelta(minutes=30),
                is_watered=False,
            )
            session.add(crop)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm/plots")

        data = response.json()
        crop_info = data["plots"][0]["crop"]
        # 30分钟 / 60分钟 = 50%
        assert 45 <= crop_info["growth_progress"] <= 55

    async def test_watered_crop_grows_faster(self):
        """测试浇水后生长更快"""
        db = get_db()
        with db.get_session() as session:
            player = Player(username="water_test_player")
            session.add(player)
            session.flush()

            farm = Farm(player_id=player.player_id, name="测试农场", plot_count=6)
            session.add(farm)
            session.flush()

            # 创建一个浇过水的作物
            crop = Crop(
                farm_id=farm.farm_id,
                plot_index=0,
                crop_type=CropType.VARIABLE_GRASS.value,
                quality=CropQuality.NORMAL.value,
                planted_at=datetime.utcnow() - timedelta(minutes=30),
                is_watered=True,  # 已浇水
            )
            session.add(crop)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/farm/plots")

        data = response.json()
        crop_info = data["plots"][0]["crop"]
        # 30分钟 * 1.2 / 60分钟 = 60%
        assert 55 <= crop_info["growth_progress"] <= 65


@pytest.mark.asyncio
class TestHarvestValue:
    """收获价值计算测试"""

    async def test_harvest_value_with_quality(self):
        """测试不同品质的收获价值"""
        db = get_db()
        with db.get_session() as session:
            player = Player(username="value_test_player")
            session.add(player)
            session.flush()

            farm = Farm(player_id=player.player_id, name="测试农场", plot_count=6)
            session.add(farm)
            session.flush()

            # 创建一个传说品质的成熟作物
            crop = Crop(
                farm_id=farm.farm_id,
                plot_index=0,
                crop_type=CropType.FUNCTION_FLOWER.value,  # base_value = 50
                quality=CropQuality.LEGENDARY.value,  # 5x multiplier
                planted_at=datetime.utcnow() - timedelta(hours=10),
                is_watered=False,
            )
            session.add(crop)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/farm/harvest", json={"plot_index": 0})

        data = response.json()
        assert data["success"] is True
        assert data["quality"] == CropQuality.LEGENDARY.value
        assert data["quality_name"] == "传说"
        assert data["value"] == 250  # 50 * 5.0
