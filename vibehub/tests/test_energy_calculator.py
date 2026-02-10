"""能量计算器单元测试"""

import pytest
from datetime import datetime, timedelta

from src.core.models import Activity, QualityMetrics, ToolUsage
from src.core.energy_calculator import EnergyCalculator


class TestEnergyCalculator:
    """能量计算器测试"""

    @pytest.fixture
    def calculator(self) -> EnergyCalculator:
        """创建计算器实例"""
        return EnergyCalculator(
            base_rate=10,
            max_time_multiplier=2.0,
            max_quality_multiplier=1.5,
            flow_multiplier=1.5,
        )

    @pytest.fixture
    def basic_activity(self) -> Activity:
        """创建基础活动"""
        now = datetime.now()
        return Activity(
            session_id="test-session",
            started_at=now - timedelta(minutes=30),
            ended_at=now,
            duration_minutes=30,
            consecutive_minutes=30,
            consecutive_days=0,
            quality=QualityMetrics(
                success_rate=0.5,
                iteration_count=5,
                lines_changed=100,
                languages=["python"],
                tool_usage=ToolUsage(read=5, write=3, bash=2, search=1),
            ),
        )

    def test_calculate_base_energy(self, calculator: EnergyCalculator):
        """测试基础能量计算"""
        # 30分钟 × 10能量/分钟 = 300基础能量
        now = datetime.now()
        activity = Activity(
            session_id="test",
            started_at=now - timedelta(minutes=30),
            ended_at=now,
            duration_minutes=30,
            consecutive_minutes=0,  # 无连续时长加成
            consecutive_days=0,
            quality=QualityMetrics(success_rate=0.0),  # 最低质量
        )

        reward = calculator.calculate(activity)

        # 基础能量 = 30 × 10 = 300
        # 时间加成 = 1.0 (无连续时长)
        # 质量加成 = 根据实际计算器实现计算
        assert reward.breakdown.base == 300
        assert reward.breakdown.time_bonus == 1.0
        # 质量加成基于质量评分计算，不是固定的 0.5
        assert reward.breakdown.quality_bonus >= 0.5
        assert reward.vibe_energy > 0

    def test_calculate_time_bonus(self, calculator: EnergyCalculator):
        """测试时间加成计算"""
        # 0分钟 -> 1.0倍
        assert calculator._calculate_time_bonus(0) == 1.0

        # 60分钟 -> 1.1倍
        assert calculator._calculate_time_bonus(60) == pytest.approx(1.1)

        # 120分钟 -> 1.2倍
        assert calculator._calculate_time_bonus(120) == pytest.approx(1.2)

        # 600分钟 -> 2.0倍 (上限)
        assert calculator._calculate_time_bonus(600) == 2.0

        # 1200分钟 -> 仍然是2.0倍 (不超过上限)
        assert calculator._calculate_time_bonus(1200) == 2.0

    def test_calculate_quality_score(self, calculator: EnergyCalculator):
        """测试质量评分计算"""
        # 最低质量
        low_quality = QualityMetrics(
            success_rate=0.0,
            iteration_count=20,
            lines_changed=0,
            languages=[],
            tool_usage=ToolUsage(),
        )
        score = calculator._calculate_quality_score(low_quality)
        assert score == 0.5  # 基础分

        # 高质量
        high_quality = QualityMetrics(
            success_rate=1.0,        # +0.2
            iteration_count=1,       # +0.15 (迭代少)
            lines_changed=500,       # +0.1
            languages=["python", "typescript", "go"],  # +0.05
            tool_usage=ToolUsage(read=1, write=1, bash=1, search=1),  # +0.1
        )
        score = calculator._calculate_quality_score(high_quality)
        # 0.5 + 0.2 + 0.135 + 0.1 + 0.1 + 0.05 = 1.085 -> 上限1.0
        assert score == 1.0

    def test_calculate_quality_bonus(self, calculator: EnergyCalculator):
        """测试质量加成计算"""
        # 质量评分0 -> 0.5倍
        assert calculator._calculate_quality_bonus(0) == 0.5

        # 质量评分0.5 -> 1.0倍
        assert calculator._calculate_quality_bonus(0.5) == pytest.approx(1.0)

        # 质量评分1.0 -> 1.5倍
        assert calculator._calculate_quality_bonus(1.0) == 1.5

    def test_calculate_streak_bonus(self, calculator: EnergyCalculator):
        """测试连续签到加成"""
        # 0天 -> 1.0倍
        assert calculator._calculate_streak_bonus(0) == 1.0

        # 10天 -> 1.5倍
        assert calculator._calculate_streak_bonus(10) == 1.5

        # 20天 -> 2.0倍
        assert calculator._calculate_streak_bonus(20) == 2.0

        # 100天 -> 6.0倍 (无上限)
        assert calculator._calculate_streak_bonus(100) == 6.0

    def test_calculate_with_flow_state(self, calculator: EnergyCalculator, basic_activity: Activity):
        """测试心流状态加成"""
        # 普通状态
        basic_activity.is_in_flow_state = False
        normal_reward = calculator.calculate(basic_activity)

        # 心流状态
        basic_activity.is_in_flow_state = True
        flow_reward = calculator.calculate(basic_activity)

        # 心流状态能量应该是普通状态的1.5倍
        assert flow_reward.vibe_energy == int(normal_reward.vibe_energy * 1.5)
        assert flow_reward.breakdown.flow_bonus == 1.5
        assert normal_reward.breakdown.flow_bonus == 1.0

    def test_calculate_experience(self, calculator: EnergyCalculator, basic_activity: Activity):
        """测试经验值计算"""
        reward = calculator.calculate(basic_activity)

        # 经验值 = 能量 × 10%
        expected_exp = int(reward.vibe_energy * 0.1)
        assert reward.experience == expected_exp

    def test_estimate_energy(self, calculator: EnergyCalculator):
        """测试快速估算能量"""
        # 基础估算
        energy = calculator.estimate_energy(
            duration_minutes=60,
            quality_score=0.5,
            consecutive_days=0,
            is_flow_state=False,
        )

        # 60分钟 × 10 = 600基础
        # 时间加成 = 1.1 (60分钟连续)
        # 质量加成 = 1.0 (评分0.5)
        # 预期 = 600 × 1.1 × 1.0 = 660
        assert energy == 660

        # 心流状态估算
        flow_energy = calculator.estimate_energy(
            duration_minutes=60,
            quality_score=0.5,
            consecutive_days=0,
            is_flow_state=True,
        )
        assert flow_energy == int(660 * 1.5)

    def test_zero_duration_returns_zero(self, calculator: EnergyCalculator):
        """测试零时长返回零能量"""
        activity = Activity(
            session_id="test",
            started_at=datetime.now(),
            duration_minutes=0,
            consecutive_minutes=0,
        )

        reward = calculator.calculate(activity)
        assert reward.vibe_energy == 0
        assert reward.experience == 0

    def test_reward_breakdown(self, calculator: EnergyCalculator, basic_activity: Activity):
        """测试奖励分解信息"""
        reward = calculator.calculate(basic_activity)

        assert reward.breakdown.base > 0
        assert reward.breakdown.time_bonus >= 1.0
        assert reward.breakdown.quality_bonus >= 0.5
        assert reward.breakdown.streak_bonus >= 1.0
        assert reward.breakdown.flow_bonus >= 1.0

    def test_tool_usage_variety(self):
        """测试工具使用多样性计算"""
        # 无工具使用
        empty_usage = ToolUsage()
        assert empty_usage.variety_count() == 0
        assert empty_usage.total() == 0

        # 单一工具
        single_usage = ToolUsage(read=10)
        assert single_usage.variety_count() == 1
        assert single_usage.total() == 10

        # 全部工具
        full_usage = ToolUsage(read=1, write=1, bash=1, search=1)
        assert full_usage.variety_count() == 4
        assert full_usage.total() == 4
