"""数据库模型定义

基于设计文档定义的 SQLite 数据库模型，包含：
- Player: 玩家数据
- Farm: 农场数据
- Crop: 作物数据
- InventoryItem: 物品/库存
- Achievement: 成就进度
- CodingActivity: 编码活动记录
- Relationship: 社交关系
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""

    pass


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


class CropType(str, Enum):
    """作物类型枚举"""

    VARIABLE_GRASS = "variable_grass"  # 变量草
    FUNCTION_FLOWER = "function_flower"  # 函数花
    CLASS_TREE = "class_tree"  # 类之树
    API_ORCHID = "api_orchid"  # API兰
    BUG_MUSHROOM = "bug_mushroom"  # Bug菇
    COMPONENT_SUNFLOWER = "component_sunflower"  # 组件向日葵
    ALGORITHM_ROSE = "algorithm_rose"  # 算法玫瑰
    AI_DIVINE_FLOWER = "ai_divine_flower"  # AI神花


class CropQuality(int, Enum):
    """作物品质枚举"""

    NORMAL = 1  # 普通 ⭐
    GOOD = 2  # 优良 ⭐⭐
    EXCELLENT = 3  # 精品 ⭐⭐⭐
    LEGENDARY = 4  # 传说 ⭐⭐⭐⭐


class RelationshipType(str, Enum):
    """关系类型枚举"""

    FRIEND = "friend"  # 好友
    GUILD_MEMBER = "guild_member"  # 公会成员
    BLOCKED = "blocked"  # 屏蔽


class Player(Base):
    """玩家数据表

    存储玩家的基本信息、等级、资源等数据。
    """

    __tablename__ = "players"

    player_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 等级与经验
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience: Mapped[int] = mapped_column(Integer, default=0)

    # 资源
    vibe_energy: Mapped[int] = mapped_column(Integer, default=100)
    max_vibe_energy: Mapped[int] = mapped_column(Integer, default=1000)
    gold: Mapped[int] = mapped_column(Integer, default=500)
    diamonds: Mapped[int] = mapped_column(Integer, default=0)

    # 属性
    focus: Mapped[int] = mapped_column(Integer, default=100)  # 专注力
    efficiency: Mapped[int] = mapped_column(Integer, default=100)  # 效率值
    creativity: Mapped[int] = mapped_column(Integer, default=100)  # 创造力

    # 连续签到
    consecutive_days: Mapped[int] = mapped_column(Integer, default=0)
    last_login_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # JSON 配置存储
    settings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stats_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 关系
    farm: Mapped[Optional["Farm"]] = relationship(
        "Farm", back_populates="player", uselist=False, cascade="all, delete-orphan"
    )
    inventory_items: Mapped[list["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="player", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["Achievement"]] = relationship(
        "Achievement", back_populates="player", cascade="all, delete-orphan"
    )
    coding_activities: Mapped[list["CodingActivity"]] = relationship(
        "CodingActivity", back_populates="player", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["Relationship"]] = relationship(
        "Relationship",
        back_populates="player",
        foreign_keys="Relationship.player_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Player(username={self.username}, level={self.level})>"


class Farm(Base):
    """农场数据表

    存储玩家农场的地块、建筑、装饰等数据。
    """

    __tablename__ = "farms"

    farm_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    player_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), unique=True, nullable=False
    )

    # 农场属性
    name: Mapped[str] = mapped_column(String(50), default="我的农场")
    plot_count: Mapped[int] = mapped_column(Integer, default=6)  # 地块数量
    decoration_score: Mapped[int] = mapped_column(Integer, default=0)  # 装饰度

    # JSON 数据存储
    plots_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 地块数据
    buildings_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 建筑数据
    decorations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 装饰数据

    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    player: Mapped["Player"] = relationship("Player", back_populates="farm")
    crops: Mapped[list["Crop"]] = relationship(
        "Crop", back_populates="farm", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Farm(name={self.name}, plots={self.plot_count})>"


class Crop(Base):
    """作物数据表

    存储种植的作物信息，包括类型、品质、生长进度等。
    """

    __tablename__ = "crops"

    crop_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    farm_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("farms.farm_id"), nullable=False
    )
    plot_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 地块索引

    # 作物属性
    crop_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quality: Mapped[int] = mapped_column(Integer, default=CropQuality.NORMAL.value)

    # 生长状态
    planted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    growth_progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    is_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    is_watered: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关系
    farm: Mapped["Farm"] = relationship("Farm", back_populates="crops")

    def __repr__(self) -> str:
        return f"<Crop(type={self.crop_type}, progress={self.growth_progress}%)>"


class InventoryItem(Base):
    """物品/库存表

    存储玩家拥有的物品，包括种子、材料、装饰品等。
    """

    __tablename__ = "inventory"

    item_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    player_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )

    # 物品属性
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 物品类型
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 物品名称
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # 元数据
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    player: Mapped["Player"] = relationship("Player", back_populates="inventory_items")

    def __repr__(self) -> str:
        return f"<InventoryItem(name={self.item_name}, qty={self.quantity})>"


class Achievement(Base):
    """成就进度表

    存储玩家的成就解锁状态和进度。
    """

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )
    achievement_id: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 成就标识符

    # 成就状态
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    target: Mapped[int] = mapped_column(Integer, default=1)

    # 时间戳
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    player: Mapped["Player"] = relationship("Player", back_populates="achievements")

    def __repr__(self) -> str:
        status = "✓" if self.is_unlocked else f"{self.progress}/{self.target}"
        return f"<Achievement(id={self.achievement_id}, status={status})>"


class CodingActivity(Base):
    """编码活动记录表

    存储 Vibe-Coding 活动的详细记录，用于能量计算和统计。
    """

    __tablename__ = "coding_activities"

    activity_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    player_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )

    # 时间信息
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # 数据来源
    source: Mapped[str] = mapped_column(
        String(50), default="claude_code"
    )  # claude_code, cursor, github

    # 奖励
    energy_earned: Mapped[int] = mapped_column(Integer, default=0)
    exp_earned: Mapped[int] = mapped_column(Integer, default=0)
    essence_earned: Mapped[int] = mapped_column(Integer, default=0)  # 代码精华

    # 心流状态
    is_flow_state: Mapped[bool] = mapped_column(Boolean, default=False)
    flow_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # 活动指标 (JSON)
    metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 包含: lines_changed, files_affected, success_rate, tool_usage 等

    # 关系
    player: Mapped["Player"] = relationship("Player", back_populates="coding_activities")

    def __repr__(self) -> str:
        flow = "🌊" if self.is_flow_state else ""
        return f"<CodingActivity(duration={self.duration_seconds}s, energy={self.energy_earned}{flow})>"


class Relationship(Base):
    """社交关系表

    存储玩家之间的社交关系，如好友、公会成员等。
    """

    __tablename__ = "relationships"

    relationship_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    player_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)  # 目标玩家ID

    # 关系属性
    relationship_type: Mapped[str] = mapped_column(
        String(20), default=RelationshipType.FRIEND.value
    )
    affinity_score: Mapped[int] = mapped_column(Integer, default=0)  # 好友度

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    player: Mapped["Player"] = relationship(
        "Player", back_populates="relationships", foreign_keys=[player_id]
    )

    def __repr__(self) -> str:
        return f"<Relationship(type={self.relationship_type}, affinity={self.affinity_score})>"


# 作物配置数据
CROP_CONFIG = {
    CropType.VARIABLE_GRASS.value: {
        "name": "变量草",
        "growth_hours": 1,
        "base_value": 10,
        "seed_cost": 5,
    },
    CropType.FUNCTION_FLOWER.value: {
        "name": "函数花",
        "growth_hours": 4,
        "base_value": 50,
        "seed_cost": 25,
    },
    CropType.CLASS_TREE.value: {
        "name": "类之树",
        "growth_hours": 12,
        "base_value": 200,
        "seed_cost": 100,
    },
    CropType.API_ORCHID.value: {
        "name": "API兰",
        "growth_hours": 8,
        "base_value": 150,
        "seed_cost": 75,
    },
    CropType.BUG_MUSHROOM.value: {
        "name": "Bug菇",
        "growth_hours": 2,
        "base_value": 30,
        "seed_cost": 15,
    },
    CropType.COMPONENT_SUNFLOWER.value: {
        "name": "组件向日葵",
        "growth_hours": 6,
        "base_value": 100,
        "seed_cost": 50,
    },
    CropType.ALGORITHM_ROSE.value: {
        "name": "算法玫瑰",
        "growth_hours": 24,
        "base_value": 500,
        "seed_cost": 200,
    },
    CropType.AI_DIVINE_FLOWER.value: {
        "name": "AI神花",
        "growth_hours": 48,
        "base_value": 1000,
        "seed_cost": 500,
    },
}

# 品质价值倍数
QUALITY_MULTIPLIERS = {
    CropQuality.NORMAL.value: 1.0,
    CropQuality.GOOD.value: 1.5,
    CropQuality.EXCELLENT.value: 2.5,
    CropQuality.LEGENDARY.value: 5.0,
}
