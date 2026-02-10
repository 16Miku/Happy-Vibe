"""数据库模型单元测试"""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from src.storage.database import Database, close_db, get_db, init_db
from src.storage.models import (
    Achievement,
    Base,
    CodingActivity,
    Crop,
    CropQuality,
    CropType,
    Farm,
    InventoryItem,
    Player,
    Relationship,
    RelationshipType,
)


@pytest.fixture
def temp_db():
    """创建临时数据库用于测试"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = Database(db_path)
    db.create_tables()
    yield db

    # 清理
    db.engine.dispose()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestPlayer:
    """玩家模型测试"""

    def test_create_player(self, temp_db: Database):
        """测试创建玩家"""
        with temp_db.get_session() as session:
            player = Player(username="test_user")
            session.add(player)
            session.flush()

            assert player.player_id is not None
            assert player.username == "test_user"
            assert player.level == 1
            assert player.experience == 0
            assert player.vibe_energy == 100
            assert player.gold == 500
            assert player.diamonds == 0

    def test_player_default_values(self, temp_db: Database):
        """测试玩家默认值"""
        with temp_db.get_session() as session:
            player = Player(username="default_test")
            session.add(player)
            session.flush()

            assert player.max_vibe_energy == 1000
            assert player.focus == 100
            assert player.efficiency == 100
            assert player.creativity == 100
            assert player.consecutive_days == 0

    def test_player_unique_username(self, temp_db: Database):
        """测试用户名唯一性"""
        with temp_db.get_session() as session:
            player1 = Player(username="unique_user")
            session.add(player1)
            session.flush()

        with pytest.raises(Exception):
            with temp_db.get_session() as session:
                player2 = Player(username="unique_user")
                session.add(player2)
                session.flush()

    def test_player_repr(self, temp_db: Database):
        """测试玩家字符串表示"""
        player = Player(username="repr_test", level=10)
        assert "repr_test" in repr(player)
        assert "10" in repr(player)


class TestFarm:
    """农场模型测试"""

    def test_create_farm_with_player(self, temp_db: Database):
        """测试创建农场（关联玩家）"""
        with temp_db.get_session() as session:
            player = Player(username="farmer")
            session.add(player)
            session.flush()

            farm = Farm(player_id=player.player_id, name="快乐农场")
            session.add(farm)
            session.flush()

            assert farm.farm_id is not None
            assert farm.name == "快乐农场"
            assert farm.plot_count == 6
            assert farm.decoration_score == 0

    def test_farm_player_relationship(self, temp_db: Database):
        """测试农场与玩家的关系"""
        with temp_db.get_session() as session:
            player = Player(username="farm_owner")
            farm = Farm(name="测试农场")
            player.farm = farm
            session.add(player)
            session.flush()

            # 验证关系
            assert player.farm is not None
            assert player.farm.name == "测试农场"
            assert farm.player.username == "farm_owner"

    def test_farm_repr(self, temp_db: Database):
        """测试农场字符串表示"""
        farm = Farm(name="测试农场", plot_count=10)
        assert "测试农场" in repr(farm)
        assert "10" in repr(farm)


class TestCrop:
    """作物模型测试"""

    def test_create_crop(self, temp_db: Database):
        """测试创建作物"""
        with temp_db.get_session() as session:
            player = Player(username="crop_farmer")
            farm = Farm(name="作物农场")
            player.farm = farm
            session.add(player)
            session.flush()

            crop = Crop(
                farm_id=farm.farm_id,
                plot_index=0,
                crop_type=CropType.VARIABLE_GRASS.value,
            )
            session.add(crop)
            session.flush()

            assert crop.crop_id is not None
            assert crop.crop_type == "variable_grass"
            assert crop.quality == CropQuality.NORMAL.value
            assert crop.growth_progress == 0.0
            assert crop.is_ready is False

    def test_crop_quality_values(self, temp_db: Database):
        """测试作物品质值"""
        with temp_db.get_session() as session:
            player = Player(username="quality_farmer")
            farm = Farm(name="品质农场")
            player.farm = farm
            session.add(player)
            session.flush()

            crop = Crop(
                farm_id=farm.farm_id,
                plot_index=0,
                crop_type=CropType.AI_DIVINE_FLOWER.value,
                quality=CropQuality.LEGENDARY.value,
            )
            session.add(crop)
            session.flush()

            assert crop.quality == 4  # LEGENDARY

    def test_crop_farm_relationship(self, temp_db: Database):
        """测试作物与农场的关系"""
        with temp_db.get_session() as session:
            player = Player(username="relation_farmer")
            farm = Farm(name="关系农场")
            player.farm = farm
            session.add(player)
            session.flush()

            crop1 = Crop(
                farm_id=farm.farm_id,
                plot_index=0,
                crop_type=CropType.FUNCTION_FLOWER.value,
            )
            crop2 = Crop(
                farm_id=farm.farm_id,
                plot_index=1,
                crop_type=CropType.CLASS_TREE.value,
            )
            session.add_all([crop1, crop2])
            session.flush()

            assert len(farm.crops) == 2


class TestInventoryItem:
    """库存物品模型测试"""

    def test_create_inventory_item(self, temp_db: Database):
        """测试创建库存物品"""
        with temp_db.get_session() as session:
            player = Player(username="item_owner")
            session.add(player)
            session.flush()

            item = InventoryItem(
                player_id=player.player_id,
                item_type="seed",
                item_name="变量草种子",
                quantity=10,
            )
            session.add(item)
            session.flush()

            assert item.item_id is not None
            assert item.item_name == "变量草种子"
            assert item.quantity == 10

    def test_inventory_player_relationship(self, temp_db: Database):
        """测试库存与玩家的关系"""
        with temp_db.get_session() as session:
            player = Player(username="inventory_owner")
            session.add(player)
            session.flush()

            item1 = InventoryItem(
                player_id=player.player_id,
                item_type="seed",
                item_name="函数花种子",
                quantity=5,
            )
            item2 = InventoryItem(
                player_id=player.player_id,
                item_type="material",
                item_name="木材",
                quantity=100,
            )
            session.add_all([item1, item2])
            session.flush()

            assert len(player.inventory_items) == 2


class TestAchievement:
    """成就模型测试"""

    def test_create_achievement(self, temp_db: Database):
        """测试创建成就"""
        with temp_db.get_session() as session:
            player = Player(username="achiever")
            session.add(player)
            session.flush()

            achievement = Achievement(
                player_id=player.player_id,
                achievement_id="first_coding",
                target=1,
            )
            session.add(achievement)
            session.flush()

            assert achievement.id is not None
            assert achievement.achievement_id == "first_coding"
            assert achievement.is_unlocked is False
            assert achievement.progress == 0

    def test_unlock_achievement(self, temp_db: Database):
        """测试解锁成就"""
        with temp_db.get_session() as session:
            player = Player(username="unlocker")
            session.add(player)
            session.flush()

            achievement = Achievement(
                player_id=player.player_id,
                achievement_id="flow_master",
                target=100,
                progress=100,
                is_unlocked=True,
                unlocked_at=datetime.utcnow(),
            )
            session.add(achievement)
            session.flush()

            assert achievement.is_unlocked is True
            assert achievement.unlocked_at is not None

    def test_achievement_repr(self, temp_db: Database):
        """测试成就字符串表示"""
        achievement = Achievement(
            achievement_id="test_ach",
            target=10,
            progress=5,
        )
        assert "5/10" in repr(achievement)

        achievement.is_unlocked = True
        assert "✓" in repr(achievement)


class TestCodingActivity:
    """编码活动模型测试"""

    def test_create_coding_activity(self, temp_db: Database):
        """测试创建编码活动"""
        with temp_db.get_session() as session:
            player = Player(username="coder")
            session.add(player)
            session.flush()

            activity = CodingActivity(
                player_id=player.player_id,
                started_at=datetime.utcnow(),
                duration_seconds=3600,
                energy_earned=600,
                exp_earned=60,
            )
            session.add(activity)
            session.flush()

            assert activity.activity_id is not None
            assert activity.duration_seconds == 3600
            assert activity.energy_earned == 600
            assert activity.source == "claude_code"

    def test_flow_state_activity(self, temp_db: Database):
        """测试心流状态活动"""
        with temp_db.get_session() as session:
            player = Player(username="flow_coder")
            session.add(player)
            session.flush()

            activity = CodingActivity(
                player_id=player.player_id,
                started_at=datetime.utcnow() - timedelta(hours=2),
                ended_at=datetime.utcnow(),
                duration_seconds=7200,
                is_flow_state=True,
                flow_duration_seconds=5400,
                energy_earned=1500,
            )
            session.add(activity)
            session.flush()

            assert activity.is_flow_state is True
            assert activity.flow_duration_seconds == 5400

    def test_activity_repr(self, temp_db: Database):
        """测试活动字符串表示"""
        activity = CodingActivity(
            started_at=datetime.utcnow(),
            duration_seconds=3600,
            energy_earned=500,
            is_flow_state=True,
        )
        repr_str = repr(activity)
        assert "3600" in repr_str
        assert "500" in repr_str
        assert "🌊" in repr_str


class TestRelationship:
    """社交关系模型测试"""

    def test_create_relationship(self, temp_db: Database):
        """测试创建社交关系"""
        with temp_db.get_session() as session:
            player1 = Player(username="player1")
            player2 = Player(username="player2")
            session.add_all([player1, player2])
            session.flush()

            relationship = Relationship(
                player_id=player1.player_id,
                target_id=player2.player_id,
                relationship_type=RelationshipType.FRIEND.value,
            )
            session.add(relationship)
            session.flush()

            assert relationship.relationship_id is not None
            assert relationship.relationship_type == "friend"
            assert relationship.affinity_score == 0

    def test_relationship_affinity(self, temp_db: Database):
        """测试好友度"""
        with temp_db.get_session() as session:
            player1 = Player(username="friend1")
            player2 = Player(username="friend2")
            session.add_all([player1, player2])
            session.flush()

            relationship = Relationship(
                player_id=player1.player_id,
                target_id=player2.player_id,
                affinity_score=150,
            )
            session.add(relationship)
            session.flush()

            assert relationship.affinity_score == 150


class TestDatabase:
    """数据库管理测试"""

    def test_database_init(self, temp_db: Database):
        """测试数据库初始化"""
        assert temp_db.engine is not None
        assert temp_db.SessionLocal is not None

    def test_get_session_context_manager(self, temp_db: Database):
        """测试会话上下文管理器"""
        with temp_db.get_session() as session:
            player = Player(username="context_test")
            session.add(player)

        # 验证数据已提交
        with temp_db.get_session() as session:
            from sqlalchemy import select

            result = session.execute(
                select(Player).where(Player.username == "context_test")
            )
            found_player = result.scalar_one_or_none()
            assert found_player is not None

    def test_session_rollback_on_error(self, temp_db: Database):
        """测试错误时回滚"""
        try:
            with temp_db.get_session() as session:
                player = Player(username="rollback_test")
                session.add(player)
                session.flush()
                raise ValueError("测试错误")
        except ValueError:
            pass

        # 验证数据已回滚
        with temp_db.get_session() as session:
            from sqlalchemy import select

            result = session.execute(
                select(Player).where(Player.username == "rollback_test")
            )
            found_player = result.scalar_one_or_none()
            assert found_player is None

    def test_reset_database(self, temp_db: Database):
        """测试重置数据库"""
        # 添加数据
        with temp_db.get_session() as session:
            player = Player(username="reset_test")
            session.add(player)

        # 重置
        temp_db.reset_database()

        # 验证数据已清空
        with temp_db.get_session() as session:
            from sqlalchemy import select

            result = session.execute(select(Player))
            players = result.scalars().all()
            assert len(players) == 0


class TestCascadeDelete:
    """级联删除测试"""

    def test_delete_player_cascades_to_farm(self, temp_db: Database):
        """测试删除玩家时级联删除农场"""
        with temp_db.get_session() as session:
            player = Player(username="cascade_test")
            farm = Farm(name="级联农场")
            player.farm = farm
            session.add(player)
            session.flush()

            farm_id = farm.farm_id
            session.delete(player)
            session.flush()

            # 验证农场已删除
            from sqlalchemy import select

            result = session.execute(select(Farm).where(Farm.farm_id == farm_id))
            assert result.scalar_one_or_none() is None

    def test_delete_farm_cascades_to_crops(self, temp_db: Database):
        """测试删除农场时级联删除作物"""
        with temp_db.get_session() as session:
            player = Player(username="crop_cascade")
            farm = Farm(name="作物级联农场")
            player.farm = farm
            session.add(player)
            session.flush()

            crop = Crop(
                farm_id=farm.farm_id,
                plot_index=0,
                crop_type=CropType.VARIABLE_GRASS.value,
            )
            session.add(crop)
            session.flush()

            crop_id = crop.crop_id

            # 删除玩家（级联删除农场和作物）
            session.delete(player)
            session.flush()

            from sqlalchemy import select

            result = session.execute(select(Crop).where(Crop.crop_id == crop_id))
            assert result.scalar_one_or_none() is None
