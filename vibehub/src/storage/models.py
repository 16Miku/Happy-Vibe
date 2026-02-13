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


class ShopType(str, Enum):
    """商店类型枚举"""

    SEED_SHOP = "seed_shop"  # 🌱 种子店 - 每日刷新
    MATERIAL_SHOP = "material_shop"  # 🪓 建材店 - 每日刷新
    ALCHEMY_SHOP = "alchemy_shop"  # 🧪 炼金店 - 每周刷新
    GIFT_SHOP = "gift_shop"  # 🎁 礼品店 - 每周刷新
    LIMITED_SHOP = "limited_shop"  # 🎪 限时商店 - 活动期间


class RefreshCycle(str, Enum):
    """刷新周期枚举"""

    DAILY = "daily"  # 每日刷新
    WEEKLY = "weekly"  # 每周刷新
    EVENT = "event"  # 活动期间


class ListingStatus(str, Enum):
    """市场挂单状态枚举"""

    ACTIVE = "active"  # 进行中
    SOLD = "sold"  # 已售出
    CANCELLED = "cancelled"  # 已取消
    EXPIRED = "expired"  # 已过期


class TransactionType(str, Enum):
    """交易类型枚举"""

    SHOP_BUY = "shop_buy"  # 商店购买
    MARKET_BUY = "market_buy"  # 市场购买
    MARKET_SELL = "market_sell"  # 市场出售
    AUCTION_WIN = "auction_win"  # 拍卖中标


class AuctionStatus(str, Enum):
    """拍卖状态枚举"""

    ACTIVE = "active"  # 进行中
    ENDED = "ended"  # 已结束
    CANCELLED = "cancelled"  # 已取消


class FriendRequestStatus(str, Enum):
    """好友请求状态枚举"""

    PENDING = "pending"  # 待处理
    ACCEPTED = "accepted"  # 已接受
    REJECTED = "rejected"  # 已拒绝


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
    last_login_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # JSON 配置存储
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    stats_json: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    plots_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # 地块数据
    buildings_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # 建筑数据
    decorations_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # 装饰数据

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
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
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
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
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
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class FriendRequest(Base):
    """好友请求表

    存储玩家之间的好友请求，支持发送、接受、拒绝操作。
    """

    __tablename__ = "friend_requests"

    request_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    sender_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )
    receiver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )

    # 请求状态
    status: Mapped[str] = mapped_column(
        String(20), default=FriendRequestStatus.PENDING.value
    )
    message: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 附言

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 关系
    sender: Mapped["Player"] = relationship(
        "Player", foreign_keys=[sender_id], backref="sent_friend_requests"
    )
    receiver: Mapped["Player"] = relationship(
        "Player", foreign_keys=[receiver_id], backref="received_friend_requests"
    )

    def __repr__(self) -> str:
        return f"<FriendRequest(sender={self.sender_id}, receiver={self.receiver_id}, status={self.status})>"


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


class CheckInRecord(Base):
    """签到记录表

    存储玩家的每日签到记录，用于历史查询和统计。
    """

    __tablename__ = "check_in_records"

    record_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    player_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )

    # 签到信息
    check_in_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consecutive_days: Mapped[int] = mapped_column(Integer, default=1)  # 签到时的连续天数

    # 奖励信息
    energy_reward: Mapped[int] = mapped_column(Integer, default=0)
    gold_reward: Mapped[int] = mapped_column(Integer, default=0)
    exp_reward: Mapped[int] = mapped_column(Integer, default=0)
    special_item: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<CheckInRecord(date={self.check_in_date.date()}, streak={self.consecutive_days})>"


class ShopItem(Base):
    """商店商品表

    存储 NPC 商店的商品信息，包括价格、库存、刷新周期等。
    """

    __tablename__ = "shop_items"

    item_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    shop_type: Mapped[str] = mapped_column(String(30), nullable=False)  # 商店类型
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 物品名称
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 物品类型
    base_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 基础价格
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 当前价格
    stock: Mapped[int] = mapped_column(Integer, default=0)  # 当前库存
    max_stock: Mapped[int] = mapped_column(Integer, default=99)  # 最大库存
    refresh_cycle: Mapped[str] = mapped_column(
        String(20), default=RefreshCycle.DAILY.value
    )  # 刷新周期
    last_refresh: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否可购买
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ShopItem(name={self.item_name}, price={self.current_price}, stock={self.stock})>"


class MarketListing(Base):
    """市场挂单表

    存储玩家在交易市场的挂单信息。
    """

    __tablename__ = "market_listings"

    listing_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    seller_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 单价
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 总价
    listing_fee: Mapped[int] = mapped_column(Integer, default=0)  # 挂单手续费 (3%)
    status: Mapped[str] = mapped_column(
        String(20), default=ListingStatus.ACTIVE.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # 过期时间
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    buyer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 关系
    seller: Mapped["Player"] = relationship(
        "Player", foreign_keys=[seller_id], backref="market_listings"
    )

    def __repr__(self) -> str:
        return f"<MarketListing(item={self.item_name}, qty={self.quantity}, price={self.unit_price})>"


class Transaction(Base):
    """交易记录表

    存储所有交易的历史记录，用于统计和审计。
    """

    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    buyer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(36), nullable=False)  # NPC 商店为 "npc"
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    fee_amount: Mapped[int] = mapped_column(Integer, default=0)  # 手续费
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Transaction(type={self.transaction_type}, item={self.item_name}, amount={self.total_amount})>"


class Auction(Base):
    """拍卖表

    存储拍卖信息，支持竞价和一口价。
    """

    __tablename__ = "auctions"

    auction_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    seller_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    starting_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 起拍价
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)  # 当前最高出价
    buyout_price: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 一口价
    min_increment: Mapped[int] = mapped_column(Integer, default=1)  # 最小加价幅度
    current_bidder_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    bid_count: Mapped[int] = mapped_column(Integer, default=0)  # 出价次数
    status: Mapped[str] = mapped_column(
        String(20), default=AuctionStatus.ACTIVE.value
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # 结束时间
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 关系
    seller: Mapped["Player"] = relationship(
        "Player", foreign_keys=[seller_id], backref="auctions"
    )
    bids: Mapped[list["Bid"]] = relationship(
        "Bid", back_populates="auction", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Auction(item={self.item_name}, current={self.current_price}, bids={self.bid_count})>"


class Bid(Base):
    """出价记录表

    存储拍卖的出价历史。
    """

    __tablename__ = "bids"

    bid_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    auction_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("auctions.auction_id"), nullable=False
    )
    bidder_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("players.player_id"), nullable=False
    )
    bid_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_winning: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否为中标出价

    # 关系
    auction: Mapped["Auction"] = relationship("Auction", back_populates="bids")
    bidder: Mapped["Player"] = relationship(
        "Player", foreign_keys=[bidder_id], backref="bids"
    )

    def __repr__(self) -> str:
        return f"<Bid(amount={self.bid_amount}, winning={self.is_winning})>"


class PriceHistory(Base):
    """价格历史表

    存储物品价格变化历史，用于市场分析。
    """

    __tablename__ = "price_history"

    record_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, default=0)  # 交易量
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PriceHistory(item={self.item_name}, price={self.price}, volume={self.volume})>"


class EconomyMetrics(Base):
    """经济指标表

    存储经济健康度指标，用于动态调整。
    """

    __tablename__ = "economy_metrics"

    metric_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    total_money_supply: Mapped[int] = mapped_column(Integer, default=0)  # 总货币供应量
    avg_player_wealth: Mapped[float] = mapped_column(Float, default=0.0)  # 平均玩家财富
    transaction_volume: Mapped[int] = mapped_column(Integer, default=0)  # 交易量
    inflation_rate: Mapped[float] = mapped_column(Float, default=0.0)  # 通胀率
    health_score: Mapped[float] = mapped_column(Float, default=100.0)  # 经济健康度 (0-100)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EconomyMetrics(health={self.health_score}, inflation={self.inflation_rate})>"


# 商店商品配置数据
SEED_SHOP_ITEMS = {
    "variable_grass_seed": {"name": "变量草种子", "price": 5, "stock": 99},
    "function_flower_seed": {"name": "函数花种子", "price": 25, "stock": 50},
    "class_tree_seed": {"name": "类之树种子", "price": 100, "stock": 20},
    "api_orchid_seed": {"name": "API兰种子", "price": 75, "stock": 30},
    "bug_mushroom_seed": {"name": "Bug菇种子", "price": 15, "stock": 75},
    "component_sunflower_seed": {"name": "组件向日葵种子", "price": 50, "stock": 40},
    "algorithm_rose_seed": {"name": "算法玫瑰种子", "price": 200, "stock": 10},
    "ai_divine_flower_seed": {"name": "AI神花种子", "price": 500, "stock": 5},
}

MATERIAL_SHOP_ITEMS = {
    "wood": {"name": "木材", "price": 2, "stock": 200},
    "stone": {"name": "石材", "price": 3, "stock": 200},
    "iron_ingot": {"name": "铁锭", "price": 10, "stock": 100},
    "brick": {"name": "砖块", "price": 5, "stock": 150},
    "glass": {"name": "玻璃", "price": 8, "stock": 80},
}

ALCHEMY_SHOP_ITEMS = {
    "growth_potion": {"name": "生长药水", "price": 50, "stock": 10},
    "quality_enhancer": {"name": "品质提升剂", "price": 100, "stock": 5},
    "flow_catalyst": {"name": "心流催化剂", "price": 200, "stock": 3},
    "rare_recipe": {"name": "稀有配方", "price": 500, "stock": 1},
}

GIFT_SHOP_ITEMS = {
    "friendship_flower": {"name": "友谊之花", "price": 30, "stock": 20},
    "thank_you_card": {"name": "感谢卡", "price": 10, "stock": 50},
    "celebration_cake": {"name": "庆祝蛋糕", "price": 80, "stock": 10},
    "lucky_charm": {"name": "幸运符", "price": 150, "stock": 5},
}
