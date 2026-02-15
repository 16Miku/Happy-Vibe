"""成就管理器模块

提供成就系统的核心逻辑，包括进度追踪、解锁检查、奖励发放等功能。
"""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.core.achievement_data import (
    ACHIEVEMENT_DEFINITIONS,
    AchievementConfig,
    get_achievement_by_id,
    get_achievements_by_category,
)
from src.storage.models import (
    AchievementDefinition,
    AchievementProgress,
    Player,
)


class AchievementManager:
    """成就管理器

    负责成就系统的核心逻辑，包括：
    - 获取玩家成就列表
    - 更新成就进度
    - 检查解锁条件
    - 发放成就奖励
    - 初始化成就定义
    """

    def __init__(self, session: Session):
        """初始化成就管理器

        Args:
            session: 数据库会话
        """
        self.session = session

    # ============================================================
    # 成就列表查询
    # ============================================================

    def get_player_achievements(
        self,
        player_id: str,
        category: str | None = None,
        include_hidden: bool = False,
        tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取玩家的成就列表

        Args:
            player_id: 玩家 ID
            category: 可选的成就类别筛选
            include_hidden: 是否包含隐藏成就
            tier: 可选的稀有度筛选

        Returns:
            成就列表，每个成就包含定义和进度信息
        """
        # 验证玩家存在
        player = (
            self.session.query(Player)
            .filter(Player.player_id == player_id)
            .first()
        )
        if not player:
            return []

        # 获取玩家的成就进度
        progress_records = (
            self.session.query(AchievementProgress)
            .filter(AchievementProgress.player_id == player_id)
            .all()
        )

        # 构建进度映射
        progress_map: dict[str, AchievementProgress] = {
            p.achievement_id: p for p in progress_records
        }

        # 获取成就定义
        definitions = (
            self.session.query(AchievementDefinition)
            .order_by(AchievementDefinition.display_order)
            .all()
        )

        achievements = []

        for definition in definitions:
            # 类别筛选
            if category and definition.category != category:
                continue

            # 稀有度筛选
            if tier and definition.tier != tier:
                continue

            # 隐藏成就处理
            if definition.is_hidden and not include_hidden:
                progress = progress_map.get(definition.achievement_id)
                if not progress or not progress.is_completed:
                    continue

            progress = progress_map.get(definition.achievement_id)

            # 解析奖励
            reward = {}
            if definition.reward_json:
                try:
                    reward = json.loads(definition.reward_json)
                except json.JSONDecodeError:
                    reward = {}

            achievement_info = {
                "achievement_id": definition.achievement_id,
                "category": definition.category,
                "tier": definition.tier,
                "title": definition.title,
                "title_zh": definition.title_zh,
                "description": definition.description,
                "icon": definition.icon,
                "is_hidden": definition.is_hidden,
                "is_secret": definition.is_secret,
                "display_order": definition.display_order,
                # 进度信息
                "current_value": progress.current_value if progress else 0,
                "target_value": progress.target_value if progress else self._get_default_target(definition),
                "progress_percent": progress.progress_percent if progress else 0.0,
                "is_unlocked": progress.is_unlocked if progress else False,
                "is_completed": progress.is_completed if progress else False,
                "is_claimed": progress.is_claimed if progress else False,
                # 时间信息
                "started_at": progress.started_at.isoformat() if progress else None,
                "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
                "claimed_at": progress.claimed_at.isoformat() if progress and progress.claimed_at else None,
                # 奖励信息
                "reward": reward,
            }

            achievements.append(achievement_info)

        return achievements

    def get_achievement_detail(
        self,
        player_id: str,
        achievement_id: str,
    ) -> dict[str, Any] | None:
        """获取单个成就的详细信息

        Args:
            player_id: 玩家 ID
            achievement_id: 成就 ID

        Returns:
            成就详细信息，不存在则返回 None
        """
        # 获取成就定义
        definition = (
            self.session.query(AchievementDefinition)
            .filter(AchievementDefinition.achievement_id == achievement_id)
            .first()
        )

        if not definition:
            return None

        # 获取玩家进度
        progress = (
            self.session.query(AchievementProgress)
            .filter(
                AchievementProgress.player_id == player_id,
                AchievementProgress.achievement_id == achievement_id,
            )
            .first()
        )

        # 解析奖励和条件参数
        reward = {}
        if definition.reward_json:
            try:
                reward = json.loads(definition.reward_json)
            except json.JSONDecodeError:
                pass

        requirement_param = {}
        if definition.requirement_param:
            try:
                requirement_param = json.loads(definition.requirement_param)
            except json.JSONDecodeError:
                pass

        return {
            "achievement_id": definition.achievement_id,
            "category": definition.category,
            "tier": definition.tier,
            "title": definition.title,
            "title_zh": definition.title_zh,
            "description": definition.description,
            "icon": definition.icon,
            "is_hidden": definition.is_hidden,
            "is_secret": definition.is_secret,
            "requirement_type": definition.requirement_type,
            "requirement_param": requirement_param,
            # 进度信息
            "current_value": progress.current_value if progress else 0,
            "target_value": progress.target_value if progress else self._get_default_target(definition),
            "progress_percent": progress.progress_percent if progress else 0.0,
            "is_unlocked": progress.is_unlocked if progress else False,
            "is_completed": progress.is_completed if progress else False,
            "is_claimed": progress.is_claimed if progress else False,
            # 时间信息
            "started_at": progress.started_at.isoformat() if progress else None,
            "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None,
            "claimed_at": progress.claimed_at.isoformat() if progress and progress.claimed_at else None,
            # 奖励信息
            "reward": reward,
        }

    def get_player_stats(self, player_id: str) -> dict[str, Any]:
        """获取玩家的成就统计信息

        Args:
            player_id: 玩家 ID

        Returns:
            成就统计信息
        """
        # 验证玩家存在
        player = (
            self.session.query(Player)
            .filter(Player.player_id == player_id)
            .first()
        )
        if not player:
            return {}

        # 获取所有进度记录
        progress_records = (
            self.session.query(AchievementProgress)
            .filter(AchievementProgress.player_id == player_id)
            .all()
        )

        # 统计
        total_count = (
            self.session.query(AchievementDefinition)
            .count()
        )

        unlocked_count = sum(1 for p in progress_records if p.is_unlocked)
        completed_count = sum(1 for p in progress_records if p.is_completed)
        claimed_count = sum(1 for p in progress_records if p.is_claimed)

        # 按类别统计
        category_stats: dict[str, dict[str, int]] = {}
        for progress in progress_records:
            definition = progress.achievement_def
            if not definition:
                continue

            category = definition.category
            if category not in category_stats:
                category_stats[category] = {
                    "total": 0,
                    "unlocked": 0,
                    "completed": 0,
                }

            category_stats[category]["total"] += 1
            if progress.is_unlocked:
                category_stats[category]["unlocked"] += 1
            if progress.is_completed:
                category_stats[category]["completed"] += 1

        return {
            "total_achievements": total_count,
            "unlocked_count": unlocked_count,
            "completed_count": completed_count,
            "claimed_count": claimed_count,
            "unlocked_percent": round(unlocked_count / total_count * 100, 2) if total_count > 0 else 0,
            "category_stats": category_stats,
        }

    # ============================================================
    # 进度更新
    # ============================================================

    def update_progress(
        self,
        player_id: str,
        event_type: str,
        event_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """根据游戏事件更新成就进度

        Args:
            player_id: 玩家 ID
            event_type: 事件类型 (coding_count, harvest_count, etc.)
            event_data: 事件数据

        Returns:
            新解锁或完成的成就列表
        """
        # 验证玩家存在
        player = (
            self.session.query(Player)
            .filter(Player.player_id == player_id)
            .first()
        )
        if not player:
            return []

        # 查找所有匹配的成就定义
        matching_definitions = (
            self.session.query(AchievementDefinition)
            .filter(AchievementDefinition.requirement_type == event_type)
            .all()
        )

        updated_achievements = []

        for definition in matching_definitions:
            # 获取或创建进度记录
            progress = (
                self.session.query(AchievementProgress)
                .filter(
                    AchievementProgress.player_id == player_id,
                    AchievementProgress.achievement_id == definition.achievement_id,
                )
                .first()
            )

            if not progress:
                target_value = self._get_default_target(definition)
                progress = AchievementProgress(
                    player_id=player_id,
                    achievement_id=definition.achievement_id,
                    current_value=0,
                    target_value=target_value,
                    progress_percent=0.0,
                )
                self.session.add(progress)

            # 如果已领取，跳过
            if progress.is_claimed:
                continue

            # 计算新值
            new_value = self._calculate_new_value(
                player_id, definition, event_data, progress.current_value
            )

            # 更新进度
            was_completed = progress.is_completed
            was_unlocked = progress.is_unlocked

            progress.current_value = min(new_value, progress.target_value)
            progress.progress_percent = (
                min(100.0, progress.current_value / progress.target_value * 100)
                if progress.target_value > 0
                else 100.0
            )

            # 检查是否完成
            if progress.current_value >= progress.target_value and not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = datetime.now(UTC)

                # 检查是否解锁（非隐藏成就自动解锁）
                if not definition.is_hidden:
                    progress.is_unlocked = True

            # 收集更新的成就
            if progress.is_completed and not was_completed:
                updated_achievements.append({
                    "achievement_id": definition.achievement_id,
                    "title_zh": definition.title_zh,
                    "tier": definition.tier,
                    "is_new": not was_completed,
                })

        self.session.commit()
        return updated_achievements

    def update_progress_direct(
        self,
        player_id: str,
        achievement_id: str,
        increment: int = 1,
    ) -> dict[str, Any] | None:
        """直接增加成就进度

        Args:
            player_id: 玩家 ID
            achievement_id: 成就 ID
            increment: 增量值

        Returns:
            更新后的进度信息，失败返回 None
        """
        # 验证玩家存在
        player = (
            self.session.query(Player)
            .filter(Player.player_id == player_id)
            .first()
        )
        if not player:
            return None

        # 获取成就定义
        definition = (
            self.session.query(AchievementDefinition)
            .filter(AchievementDefinition.achievement_id == achievement_id)
            .first()
        )
        if not definition:
            return None

        # 获取或创建进度记录
        progress = (
            self.session.query(AchievementProgress)
            .filter(
                AchievementProgress.player_id == player_id,
                AchievementProgress.achievement_id == achievement_id,
            )
            .first()
        )

        if not progress:
            target_value = self._get_default_target(definition)
            progress = AchievementProgress(
                player_id=player_id,
                achievement_id=achievement_id,
                current_value=0,
                target_value=target_value,
                progress_percent=0.0,
            )
            self.session.add(progress)

        # 如果已领取，不再更新
        if progress.is_claimed:
            return {
                "achievement_id": achievement_id,
                "current_value": progress.current_value,
                "target_value": progress.target_value,
                "is_completed": progress.is_completed,
                "is_unlocked": progress.is_unlocked,
                "is_claimed": True,
            }

        previous_value = progress.current_value
        was_completed = progress.is_completed

        # 更新进度
        progress.current_value = min(previous_value + increment, progress.target_value)
        progress.progress_percent = (
            min(100.0, progress.current_value / progress.target_value * 100)
            if progress.target_value > 0
            else 100.0
        )

        # 检查是否完成
        if progress.current_value >= progress.target_value and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = datetime.now(UTC)

            # 非隐藏成就自动解锁
            if not definition.is_hidden:
                progress.is_unlocked = True

        self.session.commit()

        return {
            "achievement_id": achievement_id,
            "previous_value": previous_value,
            "current_value": progress.current_value,
            "target_value": progress.target_value,
            "progress_percent": progress.progress_percent,
            "is_completed": progress.is_completed,
            "is_unlocked": progress.is_unlocked,
            "is_claimed": progress.is_claimed,
            "newly_completed": progress.is_completed and not was_completed,
        }

    # ============================================================
    # 奖励领取
    # ============================================================

    def claim_reward(
        self,
        player_id: str,
        achievement_id: str,
    ) -> dict[str, Any] | None:
        """领取成就奖励

        Args:
            player_id: 玩家 ID
            achievement_id: 成就 ID

        Returns:
            奖励信息，失败返回 None
        """
        # 验证玩家存在
        player = (
            self.session.query(Player)
            .filter(Player.player_id == player_id)
            .first()
        )
        if not player:
            return None

        # 获取进度记录
        progress = (
            self.session.query(AchievementProgress)
            .filter(
                AchievementProgress.player_id == player_id,
                AchievementProgress.achievement_id == achievement_id,
            )
            .first()
        )

        if not progress:
            return None

        # 检查是否已领取
        if progress.is_claimed:
            return {
                "success": False,
                "message": "奖励已领取",
            }

        # 检查是否已完成
        if not progress.is_completed:
            return {
                "success": False,
                "message": "成就未完成",
            }

        # 获取成就定义
        definition = progress.achievement_def
        if not definition:
            return None

        # 解析奖励
        reward = {}
        if definition.reward_json:
            try:
                reward = json.loads(definition.reward_json)
            except json.JSONDecodeError:
                pass

        # 发放奖励
        gold_reward = reward.get("gold", 0)
        exp_reward = reward.get("exp", 0)
        diamonds_reward = reward.get("diamonds", 0)

        player.gold += gold_reward
        player.experience += exp_reward
        player.diamonds += diamonds_reward

        # 标记为已领取
        progress.is_claimed = True
        progress.claimed_at = datetime.now(UTC)

        self.session.commit()

        return {
            "success": True,
            "achievement_id": achievement_id,
            "reward": reward,
            "gold_rewarded": gold_reward,
            "exp_rewarded": exp_reward,
            "diamonds_rewarded": diamonds_reward,
        }

    # ============================================================
    # 成就初始化
    # ============================================================

    def initialize_achievements(self) -> int:
        """初始化成就定义到数据库

        Returns:
            初始化的成就数量
        """
        count = 0

        for config in ACHIEVEMENT_DEFINITIONS:
            # 检查是否已存在
            existing = (
                self.session.query(AchievementDefinition)
                .filter(
                    AchievementDefinition.achievement_id == config.achievement_id
                )
                .first()
            )

            if not existing:
                definition = AchievementDefinition(
                    achievement_id=config.achievement_id,
                    category=config.category.value,
                    tier=config.tier.value,
                    title=config.title,
                    title_zh=config.title_zh,
                    description=config.description,
                    icon=config.icon,
                    requirement_type=config.requirement_type,
                    requirement_param=(
                        json.dumps(config.requirement_param)
                        if config.requirement_param
                        else None
                    ),
                    reward_json=json.dumps(config.reward),
                    is_hidden=config.is_hidden,
                    is_secret=config.is_secret,
                    display_order=config.display_order,
                )
                self.session.add(definition)
                count += 1

        self.session.commit()
        return count

    def ensure_player_progress(
        self,
        player_id: str,
    ) -> list[AchievementProgress]:
        """确保玩家拥有所有成就的进度记录

        Args:
            player_id: 玩家 ID

        Returns:
            新创建的进度记录列表
        """
        # 获取所有成就定义
        definitions = (
            self.session.query(AchievementDefinition)
            .all()
        )

        # 获取现有进度记录
        existing_progress = (
            self.session.query(AchievementProgress)
            .filter(AchievementProgress.player_id == player_id)
            .all()
        )
        existing_ids = {p.achievement_id for p in existing_progress}

        new_progress_records = []

        for definition in definitions:
            if definition.achievement_id not in existing_ids:
                target_value = self._get_default_target(definition)
                progress = AchievementProgress(
                    player_id=player_id,
                    achievement_id=definition.achievement_id,
                    current_value=0,
                    target_value=target_value,
                    progress_percent=0.0,
                )
                self.session.add(progress)
                new_progress_records.append(progress)

        self.session.commit()
        return new_progress_records

    # ============================================================
    # 私有辅助方法
    # ============================================================

    def _get_default_target(
        self,
        definition: AchievementDefinition,
    ) -> int:
        """获取成就的默认目标值

        Args:
            definition: 成就定义

        Returns:
            目标值
        """
        if definition.requirement_param:
            try:
                param = json.loads(definition.requirement_param)
                return param.get("target", 1)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return 1

    def _calculate_new_value(
        self,
        player_id: str,
        definition: AchievementDefinition,
        event_data: dict[str, Any],
        current_value: int,
    ) -> int:
        """根据事件数据计算新的进度值

        Args:
            player_id: 玩家 ID
            definition: 成就定义
            event_data: 事件数据
            current_value: 当前进度值

        Returns:
            新的进度值
        """
        requirement_type = definition.requirement_type

        # 解析条件参数
        param = {}
        if definition.requirement_param:
            try:
                param = json.loads(definition.requirement_param)
            except json.JSONDecodeError:
                pass

        match requirement_type:
            # 计数类事件
            case "coding_count" | "harvest_count" | "plant_count" | "water_count" | \
                 "help_count" | "visit_count" | "chat_count" | "gift_count" | \
                 "friend_count" | "trade_count" | "sell_count" | "shop_buy_count":
                increment = event_data.get("increment", 1)
                return current_value + increment

            # 时间类事件
            case "coding_time" | "flow_time":
                seconds = event_data.get("seconds", 0)
                return current_value + seconds

            # 等级/达成类
            case "level_reach":
                return event_data.get("level", current_value)

            # 质量类
            case "quality_harvest":
                quality = event_data.get("quality", 0)
                min_quality = param.get("min_quality", 3)
                if quality >= min_quality:
                    return current_value + event_data.get("increment", 1)
                return current_value

            # 多样性类
            case "task_variety" | "crop_variety":
                new_types = event_data.get("new_types", [])
                # 需要追踪历史类型，这里简化处理
                return current_value + len(new_types)

            # 连续天数类
            case "coding_streak" | "harvest_streak" | "daily_profit_streak" | "checkin_streak":
                streak = event_data.get("streak", 0)
                return streak

            # 心流计数
            case "flow_count":
                return current_value + event_data.get("increment", 1)

            # 金币/钻石类
            case "total_gold_earned" | "current_gold" | "total_diamonds":
                return event_data.get("amount", current_value)

            # 拍卖/交易类
            case "auction_win_count" | "auction_win_count":
                return current_value + event_data.get("increment", 1)

            # 利润类
            case "single_profit" | "profit":
                profit = event_data.get("profit", 0)
                return max(current_value, profit)

            # 日常完成类
            case "all_daily_quests" | "all_daily_streak":
                completed = event_data.get("completed", False)
                all_count = event_data.get("all_count", 0)
                return all_count if completed else current_value

            # 特殊掉落
            case "lucky_drop":
                drop_occurred = event_data.get("occurred", False)
                return 1 if drop_occurred else current_value

            # 公会类
            case "guild_create" | "guild_member_count":
                count = event_data.get("count", 0)
                return count

            # 默认
            case _:
                return current_value + event_data.get("increment", 1)

    def _check_unlock_condition(
        self,
        player_id: str,
        definition: AchievementDefinition,
    ) -> bool:
        """检查成就是否满足解锁条件

        对于隐藏成就，可能需要额外条件才能显示。
        对于普通成就，通常不需要额外解锁条件。

        Args:
            player_id: 玩家 ID
            definition: 成就定义

        Returns:
            是否满足解锁条件
        """
        # 非隐藏成就默认可解锁
        if not definition.is_hidden:
            return True

        # 隐藏成就需要特定条件才能显示
        # 这里可以根据需求添加特定逻辑
        requirement_type = definition.requirement_type

        # 例如：传说品质作物需要先收获过精品作物
        if requirement_type == "quality_harvest":
            # 检查玩家是否收获过精品作物
            progress_records = (
                self.session.query(AchievementProgress)
                .filter(AchievementProgress.player_id == player_id)
                .all()
            )
            for progress in progress_records:
                if progress.achievement_id == "farm_quality_excellent_10":
                    return progress.current_value >= 1

        # 默认不解锁隐藏成就
        return False


# ============================================================
# 便利函数
# ============================================================

def get_achievement_manager(session: Session) -> AchievementManager:
    """获取成就管理器实例

    Args:
        session: 数据库会话

    Returns:
        成就管理器实例
    """
    return AchievementManager(session)
