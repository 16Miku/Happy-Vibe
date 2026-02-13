"""每日签到系统

实现每日签到功能，包括：
- 签到状态检查
- 连续签到天数计算
- 签到奖励计算
- 签到记录管理
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional


class CheckInStatus(str, Enum):
    """签到状态"""
    SUCCESS = "success"           # 签到成功
    ALREADY_CHECKED = "already_checked"  # 今日已签到
    STREAK_BROKEN = "streak_broken"      # 连续签到中断（但仍签到成功）


@dataclass
class CheckInReward:
    """签到奖励"""
    base_energy: int = 50              # 基础能量奖励
    streak_bonus: int = 0              # 连续签到加成
    total_energy: int = 0              # 总能量奖励
    gold: int = 10                     # 金币奖励
    experience: int = 20               # 经验奖励
    special_item: Optional[str] = None # 特殊物品（7天/30天奖励）

    def __post_init__(self):
        """计算总能量"""
        if self.total_energy == 0:
            self.total_energy = self.base_energy + self.streak_bonus


@dataclass
class CheckInResult:
    """签到结果"""
    status: CheckInStatus
    check_in_date: date
    consecutive_days: int              # 当前连续签到天数
    previous_consecutive_days: int     # 签到前的连续天数
    reward: CheckInReward = field(default_factory=CheckInReward)
    message: str = ""

    @property
    def is_success(self) -> bool:
        """是否签到成功（包括连续中断但仍签到的情况）"""
        return self.status in (CheckInStatus.SUCCESS, CheckInStatus.STREAK_BROKEN)


# 签到奖励配置
CHECK_IN_CONFIG = {
    # 基础奖励
    "base_energy": 50,
    "base_gold": 10,
    "base_experience": 20,

    # 连续签到能量加成（每天额外增加）
    "streak_bonus_per_day": 10,
    "max_streak_bonus": 100,  # 最大连续签到加成

    # 里程碑奖励（连续签到天数 -> 特殊奖励）
    "milestones": {
        7: {"item": "function_flower_seed", "gold_bonus": 100, "name": "函数花种子"},
        14: {"item": "class_tree_seed", "gold_bonus": 200, "name": "类之树种子"},
        30: {"item": "algorithm_rose_seed", "gold_bonus": 500, "name": "算法玫瑰种子"},
        60: {"item": "ai_divine_flower_seed", "gold_bonus": 1000, "name": "AI神花种子"},
    }
}


class CheckInManager:
    """签到管理器

    负责处理签到逻辑，包括：
    - 检查今日是否已签到
    - 计算连续签到天数
    - 计算签到奖励
    """

    def __init__(self, config: Optional[dict] = None):
        """初始化签到管理器

        Args:
            config: 签到配置，默认使用 CHECK_IN_CONFIG
        """
        self.config = config or CHECK_IN_CONFIG

    def check_in(
        self,
        last_check_in_date: Optional[date],
        current_consecutive_days: int,
        current_date: Optional[date] = None
    ) -> CheckInResult:
        """执行签到

        Args:
            last_check_in_date: 上次签到日期
            current_consecutive_days: 当前连续签到天数
            current_date: 当前日期（用于测试，默认为今天）

        Returns:
            签到结果
        """
        today = current_date or date.today()
        previous_days = current_consecutive_days

        # 检查今日是否已签到
        if last_check_in_date == today:
            return CheckInResult(
                status=CheckInStatus.ALREADY_CHECKED,
                check_in_date=today,
                consecutive_days=current_consecutive_days,
                previous_consecutive_days=previous_days,
                reward=CheckInReward(
                    base_energy=0, streak_bonus=0, total_energy=0,
                    gold=0, experience=0
                ),
                message="今日已签到"
            )

        # 计算连续签到天数
        new_consecutive_days, streak_broken = self._calculate_streak(
            last_check_in_date, current_consecutive_days, today
        )

        # 计算奖励
        reward = self._calculate_reward(new_consecutive_days)

        # 确定签到状态
        if streak_broken:
            status = CheckInStatus.STREAK_BROKEN
            message = f"签到成功！连续签到中断，重新开始第 {new_consecutive_days} 天"
        else:
            status = CheckInStatus.SUCCESS
            message = f"签到成功！连续签到 {new_consecutive_days} 天"

        # 检查里程碑奖励
        milestone_reward = self._check_milestone(new_consecutive_days)
        if milestone_reward:
            reward.special_item = milestone_reward["item"]
            reward.gold += milestone_reward.get("gold_bonus", 0)
            message += f"，获得里程碑奖励：{milestone_reward['name']}！"

        return CheckInResult(
            status=status,
            check_in_date=today,
            consecutive_days=new_consecutive_days,
            previous_consecutive_days=previous_days,
            reward=reward,
            message=message
        )

    def _calculate_streak(
        self,
        last_check_in_date: Optional[date],
        current_consecutive_days: int,
        today: date
    ) -> tuple[int, bool]:
        """计算连续签到天数

        Args:
            last_check_in_date: 上次签到日期
            current_consecutive_days: 当前连续签到天数
            today: 今天日期

        Returns:
            (新的连续天数, 是否中断)
        """
        if last_check_in_date is None:
            # 首次签到
            return 1, False

        days_diff = (today - last_check_in_date).days

        if days_diff == 1:
            # 连续签到
            return current_consecutive_days + 1, False
        elif days_diff > 1:
            # 连续签到中断
            return 1, True
        else:
            # days_diff <= 0，理论上不应该发生（已在上面检查）
            return current_consecutive_days, False

    def _calculate_reward(self, consecutive_days: int) -> CheckInReward:
        """计算签到奖励

        Args:
            consecutive_days: 连续签到天数

        Returns:
            签到奖励
        """
        base_energy = self.config["base_energy"]
        base_gold = self.config["base_gold"]
        base_exp = self.config["base_experience"]

        # 计算连续签到加成
        streak_bonus_per_day = self.config["streak_bonus_per_day"]
        max_streak_bonus = self.config["max_streak_bonus"]

        # 连续签到加成 = (天数 - 1) * 每天加成，最大不超过上限
        streak_bonus = min(
            (consecutive_days - 1) * streak_bonus_per_day,
            max_streak_bonus
        )

        return CheckInReward(
            base_energy=base_energy,
            streak_bonus=streak_bonus,
            total_energy=base_energy + streak_bonus,
            gold=base_gold,
            experience=base_exp
        )

    def _check_milestone(self, consecutive_days: int) -> Optional[dict]:
        """检查是否达到里程碑

        Args:
            consecutive_days: 连续签到天数

        Returns:
            里程碑奖励配置，如果没有达到则返回 None
        """
        milestones = self.config.get("milestones", {})
        return milestones.get(consecutive_days)

    def get_check_in_status(
        self,
        last_check_in_date: Optional[date],
        current_consecutive_days: int,
        current_date: Optional[date] = None
    ) -> dict:
        """获取签到状态（不执行签到）

        Args:
            last_check_in_date: 上次签到日期
            current_consecutive_days: 当前连续签到天数
            current_date: 当前日期

        Returns:
            签到状态信息
        """
        today = current_date or date.today()

        # 检查今日是否已签到
        is_checked_today = last_check_in_date == today

        # 检查连续签到是否会中断
        will_break_streak = False
        if last_check_in_date and not is_checked_today:
            days_diff = (today - last_check_in_date).days
            will_break_streak = days_diff > 1

        # 预计签到后的连续天数
        if is_checked_today:
            expected_streak = current_consecutive_days
        elif will_break_streak:
            expected_streak = 1
        elif last_check_in_date is None:
            expected_streak = 1
        else:
            expected_streak = current_consecutive_days + 1

        # 预计奖励
        expected_reward = self._calculate_reward(expected_streak) if not is_checked_today else None

        # 下一个里程碑
        next_milestone = self._get_next_milestone(expected_streak)

        return {
            "is_checked_today": is_checked_today,
            "current_consecutive_days": current_consecutive_days,
            "expected_streak_after_check_in": expected_streak,
            "will_break_streak": will_break_streak,
            "expected_reward": expected_reward,
            "next_milestone": next_milestone,
            "last_check_in_date": last_check_in_date,
        }

    def _get_next_milestone(self, current_streak: int) -> Optional[dict]:
        """获取下一个里程碑

        Args:
            current_streak: 当前连续签到天数

        Returns:
            下一个里程碑信息
        """
        milestones = self.config.get("milestones", {})

        for days, reward in sorted(milestones.items()):
            if days > current_streak:
                return {
                    "days": days,
                    "days_remaining": days - current_streak,
                    "reward": reward
                }

        return None
