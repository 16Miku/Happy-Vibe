"""多人联机系统数据模型

定义好友、消息等数据结构。

注意：Guild, GuildMember, Leaderboard 模型已迁移到 src/storage/models.py
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.storage.models import Base


def generate_uuid() -> str:
    """生成 UUID 字符串"""
    return str(uuid.uuid4())


# ==================== 枚举类型 ====================


class OnlineStatus(str, Enum):
    """在线状态"""

    ONLINE = "online"  # 在线
    CODING = "coding"  # 编码中
    AWAY = "away"  # 离开
    OFFLINE = "offline"  # 离线


class MessageType(str, Enum):
    """消息类型"""

    CHAT = "chat"  # 聊天消息
    SYSTEM = "system"  # 系统消息
    GIFT = "gift"  # 礼物消息
    HELP = "help"  # 帮忙消息
    GUILD = "guild"  # 公会消息


# ==================== 数据库模型 ====================


class Message(Base):
    """消息表

    存储聊天消息和系统消息。
    """

    __tablename__ = "messages"

    message_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    sender_id: Mapped[str] = mapped_column(String(36), nullable=False)
    receiver_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )  # 私聊目标，公会消息为空
    guild_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )  # 公会消息

    # 消息内容
    message_type: Mapped[str] = mapped_column(
        String(20), default=MessageType.CHAT.value
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 附加数据 (礼物、帮忙等)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 状态
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Message(type={self.message_type}, from={self.sender_id})>"


# ==================== 公会等级配置 ====================

GUILD_LEVEL_CONFIG = {
    1: {"exp_required": 0, "max_members": 10, "features": ["basic"]},
    2: {"exp_required": 5000, "max_members": 15, "features": ["chat"]},
    3: {"exp_required": 15000, "max_members": 20, "features": ["territory"]},
    4: {"exp_required": 30000, "max_members": 25, "features": ["quests"]},
    5: {"exp_required": 50000, "max_members": 30, "features": ["warehouse"]},
    7: {"exp_required": 100000, "max_members": 40, "features": ["shop_discount"]},
    10: {"exp_required": 200000, "max_members": 50, "features": ["skills"]},
    15: {"exp_required": 500000, "max_members": 100, "features": ["guild_war"]},
}

# ==================== 好友度配置 ====================

AFFINITY_LEVELS = {
    "stranger": {"min": 0, "max": 20, "title": "初识者"},
    "acquaintance": {"min": 21, "max": 50, "title": "熟人"},
    "friend": {"min": 51, "max": 100, "title": "好友"},
    "close_friend": {"min": 101, "max": 200, "title": "挚友"},
    "best_friend": {"min": 201, "max": float("inf"), "title": "至交"},
}

AFFINITY_ACTIONS = {
    "daily_chat": 5,
    "send_gift": 10,
    "help_water": 2,
    "visit_farm": 3,
    "collaborate": 15,
}
