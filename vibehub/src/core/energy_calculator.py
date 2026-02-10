"""能量计算器 - 核心能量计算逻辑"""

import random
from typing import Optional

from src.config.settings import settings
from src.core.models import Activity, VibeReward, EnergyBreakdown, QualityMetrics


class EnergyCalculator:
    """Vibe能量计算器

    能量计算公式:
    Vibe_Energy = Base_Rate × Time_Factor × Quality_Factor × Streak_Bonus × Flow_Bonus

    其中:
    - Base_Rate = 10 能量/分钟
    - Time_Factor = min(1.0 + (连续时长/60) × 0.1, 2.0)  // 最高2倍
    - Quality_Factor = 0.5 + (代码质量评分 × 0.5)        // 0.5-1.5倍
    - Streak_Bonus = 1.0 + (连续天数 × 0.05)            // 每天+5%
    - Flow_Bonus = 1.5 (心流状态) 或 1.0 (普通状态)
    """

    def __init__(
        self,
        base_rate: Optional[int] = None,
        max_time_multiplier: Optional[float] = None,
        max_quality_multiplier: Optional[float] = None,
        flow_multiplier: Optional[float] = None,
    ):
        """初始化能量计算器

        Args:
            base_rate: 每分钟基础能量，默认从配置读取
            max_time_multiplier: 最大时间加成倍数，默认从配置读取
            max_quality_multiplier: 最大质量加成倍数，默认从配置读取
            flow_multiplier: 心流状态加成倍数，默认从配置读取
        """
        self.base_rate = base_rate or settings.BASE_ENERGY_RATE
        self.max_time_multiplier = max_time_multiplier or settings.MAX_ENERGY_MULTIPLIER
        self.max_quality_multiplier = max_quality_multiplier or settings.MAX_QUALITY_MULTIPLIER
        self.flow_multiplier = flow_multiplier or settings.FLOW_STATE_MULTIPLIER

    def calculate(self, activity: Activity) -> VibeReward:
        """计算活动获得的Vibe奖励

        Args:
            activity: 编码活动数据

        Returns:
            VibeReward: 包含能量、经验值和代码精华的奖励
        """
        # 计算基础能量
        base_energy = activity.duration_minutes * self.base_rate

        # 计算时间加成
        time_bonus = self._calculate_time_bonus(activity.consecutive_minutes)

        # 计算质量加成
        quality_score = self._calculate_quality_score(activity.quality)
        quality_bonus = self._calculate_quality_bonus(quality_score)

        # 计算连续签到加成
        streak_bonus = self._calculate_streak_bonus(activity.consecutive_days)

        # 计算心流状态加成
        flow_bonus = self.flow_multiplier if activity.is_in_flow_state else 1.0

        # 计算最终能量
        final_energy = int(
            base_energy * time_bonus * quality_bonus * streak_bonus * flow_bonus
        )

        # 计算经验值 (能量的10%)
        experience = int(final_energy * 0.1)

        # 计算代码精华 (稀有资源，有概率掉落)
        code_essence = self._calculate_essence_drop(activity, final_energy)

        # 构建分解信息
        breakdown = EnergyBreakdown(
            base=base_energy,
            time_bonus=time_bonus,
            quality_bonus=quality_bonus,
            streak_bonus=streak_bonus,
            flow_bonus=flow_bonus,
        )

        return VibeReward(
            vibe_energy=final_energy,
            experience=experience,
            code_essence=code_essence,
            breakdown=breakdown,
        )

    def _calculate_time_bonus(self, consecutive_minutes: float) -> float:
        """计算时间加成

        连续编码越长，加成越高，最高2倍
        公式: min(1.0 + (连续时长/60) × 0.1, 2.0)

        Args:
            consecutive_minutes: 连续编码时长(分钟)

        Returns:
            时间加成倍数 (1.0 - 2.0)
        """
        bonus = 1.0 + (consecutive_minutes / 60) * 0.1
        return min(bonus, self.max_time_multiplier)

    def _calculate_quality_score(self, quality: QualityMetrics) -> float:
        """计算代码质量评分

        质量评分范围: 0-1

        评分组成:
        1. 成功率加成 (最高+0.2)
        2. 效率加成: 低迭代次数说明prompt质量高 (最高+0.15)
        3. 产出规模加成 (最高+0.1)
        4. 工具多样性加成 (最高+0.1)
        5. 语言多样性加成 (最高+0.05)

        Args:
            quality: 质量指标

        Returns:
            质量评分 (0-1)
        """
        score = 0.5  # 基础分

        # 1. 成功率加成 (最高+0.2)
        success_bonus = min(quality.success_rate * 0.2, 0.2)
        score += success_bonus

        # 2. 效率加成: 低迭代次数说明prompt质量高 (最高+0.15)
        # 迭代次数越少越好，10次以上效率加成为0
        iteration_score = max(0, 1 - quality.iteration_count / 10)
        score += iteration_score * 0.15

        # 3. 产出规模加成 (最高+0.1)
        # 500行代码达到满分
        output_score = min(quality.lines_changed / 500, 1)
        score += output_score * 0.1

        # 4. 工具多样性加成 (最高+0.1)
        # 每种工具+0.025，最多4种
        tool_variety = quality.tool_usage.variety_count()
        score += min(tool_variety * 0.025, 0.1)

        # 5. 语言多样性加成 (最高+0.05)
        lang_variety = min(len(quality.languages) * 0.02, 0.05)
        score += lang_variety

        return min(score, 1.0)

    def _calculate_quality_bonus(self, quality_score: float) -> float:
        """根据质量评分计算质量加成倍数

        公式: 0.5 + (质量评分 × 0.5)
        范围: 0.5 - 1.0 (基于评分0-1)

        但配置允许最大1.5倍，所以实际范围是 0.5 - max_quality_multiplier

        Args:
            quality_score: 质量评分 (0-1)

        Returns:
            质量加成倍数
        """
        # 基础公式: 0.5 + score * 0.5 给出 0.5-1.0 的范围
        # 为了支持配置的 max_quality_multiplier，我们调整公式
        bonus = 0.5 + quality_score * (self.max_quality_multiplier - 0.5)
        return min(bonus, self.max_quality_multiplier)

    def _calculate_streak_bonus(self, consecutive_days: int) -> float:
        """计算连续签到加成

        公式: 1.0 + (连续天数 × 0.05)
        每天+5%，无上限

        Args:
            consecutive_days: 连续签到天数

        Returns:
            连续签到加成倍数
        """
        return 1.0 + (consecutive_days * 0.05)

    def _calculate_essence_drop(self, activity: Activity, energy: int) -> int:
        """计算代码精华掉落

        代码精华是稀有资源，有概率掉落

        基础掉落概率: 5%
        心流状态: 概率提升至15%
        掉落数量: 1-3个，基于能量值

        Args:
            activity: 活动数据
            energy: 获得的能量值

        Returns:
            代码精华数量
        """
        # 基础掉落概率
        base_chance = 0.05

        # 心流状态提升概率
        if activity.is_in_flow_state:
            base_chance = 0.15

        # 能量越高，概率略微提升
        energy_bonus = min(energy / 10000, 0.1)  # 最多+10%
        final_chance = base_chance + energy_bonus

        # 判断是否掉落
        if random.random() < final_chance:
            # 掉落数量: 1-3个，能量越高越多
            if energy >= 1000:
                return random.randint(2, 3)
            elif energy >= 500:
                return random.randint(1, 2)
            else:
                return 1

        return 0

    def estimate_energy(
        self,
        duration_minutes: float,
        consecutive_minutes: Optional[float] = None,
        quality_score: float = 0.5,
        consecutive_days: int = 0,
        is_flow_state: bool = False,
    ) -> int:
        """快速估算能量值

        用于预览或UI显示，不需要完整的Activity对象

        Args:
            duration_minutes: 编码时长(分钟)
            consecutive_minutes: 连续编码时长，默认等于duration_minutes
            quality_score: 质量评分 (0-1)
            consecutive_days: 连续签到天数
            is_flow_state: 是否处于心流状态

        Returns:
            预估能量值
        """
        if consecutive_minutes is None:
            consecutive_minutes = duration_minutes

        base_energy = duration_minutes * self.base_rate
        time_bonus = self._calculate_time_bonus(consecutive_minutes)
        quality_bonus = self._calculate_quality_bonus(quality_score)
        streak_bonus = self._calculate_streak_bonus(consecutive_days)
        flow_bonus = self.flow_multiplier if is_flow_state else 1.0

        return int(base_energy * time_bonus * quality_bonus * streak_bonus * flow_bonus)
