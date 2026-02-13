"""签到系统单元测试"""

from datetime import date, timedelta
import pytest

from src.core.check_in import (
    CheckInManager,
    CheckInStatus,
    CheckInReward,
    CheckInResult,
    CHECK_IN_CONFIG,
)


class TestCheckInManager:
    """签到管理器测试"""

    def setup_method(self):
        """每个测试方法前初始化"""
        self.manager = CheckInManager()

    # ============== 首次签到测试 ==============

    def test_first_check_in(self):
        """测试首次签到"""
        result = self.manager.check_in(
            last_check_in_date=None,
            current_consecutive_days=0
        )

        assert result.status == CheckInStatus.SUCCESS
        assert result.consecutive_days == 1
        assert result.previous_consecutive_days == 0
        assert result.is_success is True
        assert result.reward.base_energy == 50
        assert result.reward.streak_bonus == 0
        assert result.reward.total_energy == 50

    # ============== 连续签到测试 ==============

    def test_consecutive_check_in_day_2(self):
        """测试连续签到第2天"""
        yesterday = date.today() - timedelta(days=1)

        result = self.manager.check_in(
            last_check_in_date=yesterday,
            current_consecutive_days=1
        )

        assert result.status == CheckInStatus.SUCCESS
        assert result.consecutive_days == 2
        assert result.previous_consecutive_days == 1
        assert result.reward.streak_bonus == 10  # (2-1) * 10

    def test_consecutive_check_in_day_7(self):
        """测试连续签到第7天（里程碑）"""
        yesterday = date.today() - timedelta(days=1)

        result = self.manager.check_in(
            last_check_in_date=yesterday,
            current_consecutive_days=6
        )

        assert result.status == CheckInStatus.SUCCESS
        assert result.consecutive_days == 7
        assert result.reward.streak_bonus == 60  # (7-1) * 10
        assert result.reward.special_item == "function_flower_seed"
        assert "里程碑" in result.message

    def test_consecutive_check_in_day_30(self):
        """测试连续签到第30天（里程碑）"""
        yesterday = date.today() - timedelta(days=1)

        result = self.manager.check_in(
            last_check_in_date=yesterday,
            current_consecutive_days=29
        )

        assert result.consecutive_days == 30
        assert result.reward.special_item == "algorithm_rose_seed"

    def test_streak_bonus_max_cap(self):
        """测试连续签到加成上限"""
        yesterday = date.today() - timedelta(days=1)

        # 连续签到15天，加成应该是 (15-1) * 10 = 140，但上限是100
        result = self.manager.check_in(
            last_check_in_date=yesterday,
            current_consecutive_days=14
        )

        assert result.consecutive_days == 15
        assert result.reward.streak_bonus == 100  # 达到上限

    # ============== 签到中断测试 ==============

    def test_streak_broken_after_2_days(self):
        """测试中断2天后签到"""
        two_days_ago = date.today() - timedelta(days=2)

        result = self.manager.check_in(
            last_check_in_date=two_days_ago,
            current_consecutive_days=5
        )

        assert result.status == CheckInStatus.STREAK_BROKEN
        assert result.consecutive_days == 1  # 重新开始
        assert result.previous_consecutive_days == 5
        assert result.is_success is True
        assert result.reward.streak_bonus == 0

    def test_streak_broken_after_week(self):
        """测试中断一周后签到"""
        week_ago = date.today() - timedelta(days=7)

        result = self.manager.check_in(
            last_check_in_date=week_ago,
            current_consecutive_days=10
        )

        assert result.status == CheckInStatus.STREAK_BROKEN
        assert result.consecutive_days == 1

    # ============== 重复签到测试 ==============

    def test_already_checked_today(self):
        """测试今日已签到"""
        today = date.today()

        result = self.manager.check_in(
            last_check_in_date=today,
            current_consecutive_days=5
        )

        assert result.status == CheckInStatus.ALREADY_CHECKED
        assert result.consecutive_days == 5  # 保持不变
        assert result.is_success is False
        assert result.reward.total_energy == 0
        assert "已签到" in result.message

    # ============== 签到状态查询测试 ==============

    def test_get_status_not_checked_today(self):
        """测试获取状态 - 今日未签到"""
        yesterday = date.today() - timedelta(days=1)

        status = self.manager.get_check_in_status(
            last_check_in_date=yesterday,
            current_consecutive_days=3
        )

        assert status["is_checked_today"] is False
        assert status["current_consecutive_days"] == 3
        assert status["expected_streak_after_check_in"] == 4
        assert status["will_break_streak"] is False
        assert status["expected_reward"] is not None
        assert status["expected_reward"].streak_bonus == 30  # (4-1) * 10

    def test_get_status_already_checked(self):
        """测试获取状态 - 今日已签到"""
        today = date.today()

        status = self.manager.get_check_in_status(
            last_check_in_date=today,
            current_consecutive_days=5
        )

        assert status["is_checked_today"] is True
        assert status["expected_streak_after_check_in"] == 5
        assert status["expected_reward"] is None

    def test_get_status_will_break_streak(self):
        """测试获取状态 - 连续签到将中断"""
        three_days_ago = date.today() - timedelta(days=3)

        status = self.manager.get_check_in_status(
            last_check_in_date=three_days_ago,
            current_consecutive_days=10
        )

        assert status["is_checked_today"] is False
        assert status["will_break_streak"] is True
        assert status["expected_streak_after_check_in"] == 1

    def test_get_status_first_time(self):
        """测试获取状态 - 首次签到"""
        status = self.manager.get_check_in_status(
            last_check_in_date=None,
            current_consecutive_days=0
        )

        assert status["is_checked_today"] is False
        assert status["expected_streak_after_check_in"] == 1
        assert status["will_break_streak"] is False

    # ============== 里程碑测试 ==============

    def test_next_milestone_from_day_1(self):
        """测试下一个里程碑 - 从第1天"""
        status = self.manager.get_check_in_status(
            last_check_in_date=None,
            current_consecutive_days=0
        )

        assert status["next_milestone"] is not None
        assert status["next_milestone"]["days"] == 7
        assert status["next_milestone"]["days_remaining"] == 6

    def test_next_milestone_from_day_8(self):
        """测试下一个里程碑 - 从第8天"""
        yesterday = date.today() - timedelta(days=1)

        status = self.manager.get_check_in_status(
            last_check_in_date=yesterday,
            current_consecutive_days=7
        )

        # 签到后是第8天，下一个里程碑是14天
        assert status["next_milestone"]["days"] == 14
        assert status["next_milestone"]["days_remaining"] == 6

    def test_no_next_milestone_after_60(self):
        """测试无下一个里程碑 - 超过60天"""
        yesterday = date.today() - timedelta(days=1)

        status = self.manager.get_check_in_status(
            last_check_in_date=yesterday,
            current_consecutive_days=60
        )

        assert status["next_milestone"] is None

    # ============== 自定义日期测试 ==============

    def test_check_in_with_custom_date(self):
        """测试使用自定义日期签到"""
        custom_date = date(2024, 1, 15)
        last_check_in = date(2024, 1, 14)

        result = self.manager.check_in(
            last_check_in_date=last_check_in,
            current_consecutive_days=5,
            current_date=custom_date
        )

        assert result.check_in_date == custom_date
        assert result.consecutive_days == 6

    # ============== 奖励计算测试 ==============

    def test_reward_calculation_day_1(self):
        """测试第1天奖励计算"""
        reward = self.manager._calculate_reward(1)

        assert reward.base_energy == 50
        assert reward.streak_bonus == 0
        assert reward.total_energy == 50
        assert reward.gold == 10
        assert reward.experience == 20

    def test_reward_calculation_day_5(self):
        """测试第5天奖励计算"""
        reward = self.manager._calculate_reward(5)

        assert reward.base_energy == 50
        assert reward.streak_bonus == 40  # (5-1) * 10
        assert reward.total_energy == 90
        assert reward.gold == 10
        assert reward.experience == 20


class TestCheckInReward:
    """签到奖励数据类测试"""

    def test_reward_auto_calculate_total(self):
        """测试奖励自动计算总能量"""
        reward = CheckInReward(base_energy=50, streak_bonus=30)

        assert reward.total_energy == 80

    def test_reward_with_explicit_total(self):
        """测试显式设置总能量"""
        reward = CheckInReward(base_energy=50, streak_bonus=30, total_energy=100)

        assert reward.total_energy == 100


class TestCheckInResult:
    """签到结果数据类测试"""

    def test_is_success_for_success_status(self):
        """测试成功状态的 is_success"""
        result = CheckInResult(
            status=CheckInStatus.SUCCESS,
            check_in_date=date.today(),
            consecutive_days=1,
            previous_consecutive_days=0
        )

        assert result.is_success is True

    def test_is_success_for_streak_broken(self):
        """测试中断状态的 is_success"""
        result = CheckInResult(
            status=CheckInStatus.STREAK_BROKEN,
            check_in_date=date.today(),
            consecutive_days=1,
            previous_consecutive_days=5
        )

        assert result.is_success is True

    def test_is_success_for_already_checked(self):
        """测试已签到状态的 is_success"""
        result = CheckInResult(
            status=CheckInStatus.ALREADY_CHECKED,
            check_in_date=date.today(),
            consecutive_days=5,
            previous_consecutive_days=5
        )

        assert result.is_success is False
